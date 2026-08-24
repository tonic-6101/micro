# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today


class TestPipelineAPI(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.db.set_single_value("Micro Settings", "customer_limit", 9999)
		frappe.db.set_single_value("Micro Settings", "pipeline_limit", 0)  # unlimited, so tests can build several boards

	# --- factories ---

	def _make_pipeline(self, **kwargs):
		defaults = {
			"doctype": "Micro Pipeline",
			"pipeline_name": frappe.generate_hash("_Test Pipeline", 8),
			"is_active": 1,
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def _make_stage(self, pipeline, **kwargs):
		defaults = {
			"doctype": "Micro Pipeline Stage",
			"stage_name": "_Test Stage",
			"pipeline": pipeline,
			"sort_order": 10,
			"color": "Blue",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def _make_contact(self, **kwargs):
		defaults = {
			"doctype": "Contact",
			"first_name": "_Test Pipeline",
			"last_name": "Contact",
			"micro_contact_type": "Person",
			"micro_status": "Potential",
			"email_id": f"{frappe.generate_hash(length=8)}@example.com",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		if defaults.get("email_id"):
			doc.append("email_ids", {"email_id": defaults["email_id"], "is_primary": 1})
		doc.insert(ignore_permissions=True)
		return doc

	def _make_lead(self, pipeline, stage=None, **kwargs):
		defaults = {
			"doctype": "Micro Lead",
			"lead_name": "_Test Lead",
			"pipeline": pipeline,
			"priority": "Medium",
		}
		if stage:
			defaults["stage"] = stage
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	# --- board scoping: the whole point of the rework ---

	def test_board_only_returns_its_own_pipeline(self):
		"""Two pipelines must not bleed into each other's board."""
		from micro.api.pipeline import get_pipeline

		shk = self._make_pipeline()
		buyers = self._make_pipeline()
		shk_stage = self._make_stage(shk.name, stage_name="_Test SHK Contact Made")
		buyer_stage = self._make_stage(buyers.name, stage_name="_Test Buyer Asked")

		shk_lead = self._make_lead(shk.name, shk_stage.name, lead_name="_Test SHK Lead")
		buyer_lead = self._make_lead(buyers.name, buyer_stage.name, lead_name="_Test Buyer Lead")

		result = get_pipeline(pipeline=shk.name, show_closed=True)

		stage_names = [col["stage"]["name"] for col in result["stages"]]
		self.assertIn(shk_stage.name, stage_names)
		self.assertNotIn(buyer_stage.name, stage_names)

		lead_names = [lead["name"] for col in result["stages"] for lead in col["leads"]]
		self.assertIn(shk_lead.name, lead_names)
		self.assertNotIn(buyer_lead.name, lead_names)

	def test_board_returns_leads_with_contact_details(self):
		from micro.api.pipeline import get_pipeline

		pipeline = self._make_pipeline()
		stage = self._make_stage(pipeline.name)
		contact = self._make_contact(first_name="_Test Enriched")
		lead = self._make_lead(pipeline.name, stage.name, contact=contact.name)

		result = get_pipeline(pipeline=pipeline.name, show_closed=True)
		cards = [card for col in result["stages"] for card in col["leads"] if card["name"] == lead.name]

		self.assertEqual(len(cards), 1)
		self.assertEqual(cards[0]["contact_details"]["name"], contact.name)

	def test_board_cards_carry_the_contact_tags(self):
		"""The card shows tags, so they must ride along with the contact."""
		from frappe.desk.doctype.tag.tag import add_tag

		from micro.api.pipeline import get_pipeline

		pipeline = self._make_pipeline()
		stage = self._make_stage(pipeline.name)
		contact = self._make_contact(first_name="_Test Tagged")
		add_tag("_Test Altbau", "Contact", contact.name)
		lead = self._make_lead(pipeline.name, stage.name, contact=contact.name)

		result = get_pipeline(pipeline=pipeline.name, show_closed=True)
		card = next(c for col in result["stages"] for c in col["leads"] if c["name"] == lead.name)

		self.assertIn("_Test Altbau", card["contact_details"]["_user_tags"])

	def test_board_pages_a_large_column_but_counts_all_of_it(self):
		"""A prospecting import puts thousands in one stage; the board sends a page."""
		from micro.api.pipeline import get_pipeline

		pipeline = self._make_pipeline()
		stage = self._make_stage(pipeline.name)
		for _ in range(5):
			self._make_lead(pipeline.name, stage.name, expected_value=100)

		result = get_pipeline(pipeline=pipeline.name, leads_per_stage=2)
		column = result["stages"][0]

		self.assertEqual(len(column["leads"]), 2)
		self.assertEqual(column["loaded"], 2)
		self.assertEqual(column["count"], 5)
		# The value is the column's, not the page's.
		self.assertEqual(column["value"], 500)
		self.assertEqual(result["totals"]["count"], 5)
		self.assertEqual(result["totals"]["value"], 500)

	def test_board_hides_archived_leads(self):
		"""Archiving is Micro's delete — the card must leave the board."""
		from micro.api.leads import archive_lead
		from micro.api.pipeline import get_pipeline

		pipeline = self._make_pipeline()
		stage = self._make_stage(pipeline.name)
		kept = self._make_lead(pipeline.name, stage.name, lead_name="_Test Kept Lead")
		archived = self._make_lead(pipeline.name, stage.name, lead_name="_Test Archived Lead")
		archive_lead(archived.name)

		result = get_pipeline(pipeline=pipeline.name, show_closed=True)
		names = [lead["name"] for col in result["stages"] for lead in col["leads"]]

		self.assertIn(kept.name, names)
		self.assertNotIn(archived.name, names)
		self.assertEqual(result["totals"]["count"], 1)

	def test_board_hides_archived_leads_that_have_no_stage(self):
		"""The unassigned bucket holds legacy rows, and must honour the archive too."""
		from micro.api.leads import archive_lead
		from micro.api.pipeline import get_pipeline

		pipeline = self._make_pipeline()
		stage = self._make_stage(pipeline.name)
		archived = self._make_lead(pipeline.name, stage.name, lead_name="_Test Archived Unassigned")
		archive_lead(archived.name)
		# `stage` is mandatory, so an unassigned lead can only predate that rule.
		frappe.db.set_value("Micro Lead", archived.name, "stage", "", update_modified=False)

		result = get_pipeline(pipeline=pipeline.name)

		self.assertNotIn(archived.name, [lead["name"] for lead in result["unassigned"]])

	def test_board_hides_closed_stages_by_default(self):
		from micro.api.pipeline import get_pipeline

		pipeline = self._make_pipeline()
		open_stage = self._make_stage(pipeline.name, stage_name="_Test Open", sort_order=10)
		closed_stage = self._make_stage(
			pipeline.name, stage_name="_Test Closed", sort_order=20, is_closed=1
		)

		result = get_pipeline(pipeline=pipeline.name, show_closed=False)
		stage_names = [col["stage"]["name"] for col in result["stages"]]
		self.assertIn(open_stage.name, stage_names)
		self.assertNotIn(closed_stage.name, stage_names)

	def test_board_totals_sum_expected_value(self):
		from micro.api.pipeline import get_pipeline

		pipeline = self._make_pipeline()
		stage = self._make_stage(pipeline.name)
		self._make_lead(pipeline.name, stage.name, expected_value=1000)
		self._make_lead(pipeline.name, stage.name, expected_value=500)

		result = get_pipeline(pipeline=pipeline.name, show_closed=True)
		self.assertEqual(result["totals"]["count"], 2)
		self.assertEqual(result["totals"]["value"], 1500)

	# --- filters ---

	def test_segment_filter_narrows_the_board(self):
		from micro.api.pipeline import get_pipeline

		segment = frappe.get_doc(
			{"doctype": "Micro Segment", "segment_name": frappe.generate_hash("_Test Seg", 8)}
		).insert(ignore_permissions=True)

		pipeline = self._make_pipeline()
		stage = self._make_stage(pipeline.name)
		in_segment = self._make_contact(micro_segment=segment.name)
		out_segment = self._make_contact()

		matching = self._make_lead(pipeline.name, stage.name, contact=in_segment.name)
		other = self._make_lead(pipeline.name, stage.name, contact=out_segment.name)

		result = get_pipeline(pipeline=pipeline.name, show_closed=True, segment=segment.name)
		lead_names = [lead["name"] for col in result["stages"] for lead in col["leads"]]

		self.assertIn(matching.name, lead_names)
		self.assertNotIn(other.name, lead_names)

	def test_search_matches_lead_name(self):
		from micro.api.pipeline import get_pipeline

		pipeline = self._make_pipeline()
		stage = self._make_stage(pipeline.name)
		wanted = self._make_lead(pipeline.name, stage.name, lead_name="_Test Roofing Job Meier")
		other = self._make_lead(pipeline.name, stage.name, lead_name="_Test Bathroom Job Schulz")

		result = get_pipeline(pipeline=pipeline.name, show_closed=True, search="roofing")
		lead_names = [lead["name"] for col in result["stages"] for lead in col["leads"]]

		self.assertIn(wanted.name, lead_names)
		self.assertNotIn(other.name, lead_names)

	def test_search_matches_the_contact_on_the_card(self):
		"""The card prints the contact's name, so searching it must find the lead."""
		from micro.api.pipeline import get_pipeline

		pipeline = self._make_pipeline()
		stage = self._make_stage(pipeline.name)
		term = frappe.generate_hash(length=8)
		contact = self._make_contact(first_name="_Test", last_name=term)

		wanted = self._make_lead(pipeline.name, stage.name, contact=contact.name)
		other = self._make_lead(pipeline.name, stage.name)

		result = get_pipeline(pipeline=pipeline.name, show_closed=True, search=term)
		lead_names = [lead["name"] for col in result["stages"] for lead in col["leads"]]

		self.assertIn(wanted.name, lead_names)
		self.assertNotIn(other.name, lead_names)

	def test_search_narrows_the_column_counts(self):
		"""Counts and totals describe the search, not the unfiltered column."""
		from micro.api.pipeline import get_pipeline

		pipeline = self._make_pipeline()
		stage = self._make_stage(pipeline.name)
		term = frappe.generate_hash(length=8)
		self._make_lead(pipeline.name, stage.name, lead_name=f"_Test {term}", expected_value=250)
		self._make_lead(pipeline.name, stage.name, lead_name="_Test Unrelated", expected_value=999)

		result = get_pipeline(pipeline=pipeline.name, show_closed=True, search=term)

		self.assertEqual(result["stages"][0]["count"], 1)
		self.assertEqual(result["totals"]["count"], 1)
		self.assertEqual(result["totals"]["value"], 250)

	def test_search_still_honours_the_other_filters(self):
		"""Search is one more condition, not a way around priority or pipeline."""
		from micro.api.pipeline import get_pipeline

		pipeline = self._make_pipeline()
		stage = self._make_stage(pipeline.name)
		term = frappe.generate_hash(length=8)
		high = self._make_lead(pipeline.name, stage.name, lead_name=f"_Test {term} A", priority="High")
		low = self._make_lead(pipeline.name, stage.name, lead_name=f"_Test {term} B", priority="Low")

		result = get_pipeline(pipeline=pipeline.name, show_closed=True, search=term, priority="High")
		lead_names = [lead["name"] for col in result["stages"] for lead in col["leads"]]

		self.assertIn(high.name, lead_names)
		self.assertNotIn(low.name, lead_names)

	def test_search_reaches_unassigned_leads(self):
		from micro.api.pipeline import get_pipeline

		pipeline = self._make_pipeline()
		self._make_stage(pipeline.name)
		term = frappe.generate_hash(length=8)
		lead = self._make_lead(pipeline.name, lead_name=f"_Test {term}")
		frappe.db.set_value("Micro Lead", lead.name, "stage", None)

		result = get_pipeline(pipeline=pipeline.name, show_closed=True, search=term)
		self.assertIn(lead.name, [row["name"] for row in result["unassigned"]])

	def test_due_only_filter(self):
		from micro.api.pipeline import get_pipeline

		pipeline = self._make_pipeline()
		stage = self._make_stage(pipeline.name)
		due = self._make_lead(pipeline.name, stage.name, next_follow_up=today())
		later = self._make_lead(pipeline.name, stage.name, next_follow_up=add_days(today(), 14))

		result = get_pipeline(pipeline=pipeline.name, show_closed=True, due_only=True)
		lead_names = [lead["name"] for col in result["stages"] for lead in col["leads"]]

		self.assertIn(due.name, lead_names)
		self.assertNotIn(later.name, lead_names)

	# --- moving cards ---

	def test_move_lead(self):
		from micro.api.pipeline import move_lead

		pipeline = self._make_pipeline()
		stage1 = self._make_stage(pipeline.name, stage_name="_Test From", sort_order=10)
		stage2 = self._make_stage(pipeline.name, stage_name="_Test To", sort_order=20)
		lead = self._make_lead(pipeline.name, stage1.name)

		result = move_lead(lead.name, stage2.name)
		self.assertTrue(result["success"])
		self.assertEqual(frappe.db.get_value("Micro Lead", lead.name, "stage"), stage2.name)

	def test_move_lead_across_pipelines_is_rejected(self):
		"""A stage from another pipeline is not a valid drop target."""
		from micro.api.pipeline import move_lead

		pipeline_a = self._make_pipeline()
		pipeline_b = self._make_pipeline()
		stage_a = self._make_stage(pipeline_a.name, stage_name="_Test A")
		stage_b = self._make_stage(pipeline_b.name, stage_name="_Test B")
		lead = self._make_lead(pipeline_a.name, stage_a.name)

		with self.assertRaises(frappe.ValidationError):
			move_lead(lead.name, stage_b.name)

	def test_move_lead_invalid_lead(self):
		from micro.api.pipeline import move_lead

		pipeline = self._make_pipeline()
		stage = self._make_stage(pipeline.name)
		with self.assertRaises(frappe.ValidationError):
			move_lead("NONEXISTENT", stage.name)

	def test_move_lead_invalid_stage(self):
		from micro.api.pipeline import move_lead

		pipeline = self._make_pipeline()
		stage = self._make_stage(pipeline.name)
		lead = self._make_lead(pipeline.name, stage.name)
		with self.assertRaises(frappe.ValidationError):
			move_lead(lead.name, "NONEXISTENT")

	# --- lookups ---

	def test_get_pipelines_counts_open_leads(self):
		from micro.api.pipeline import get_pipelines

		pipeline = self._make_pipeline()
		stage = self._make_stage(pipeline.name)
		self._make_lead(pipeline.name, stage.name)

		result = get_pipelines()
		row = next(p for p in result["pipelines"] if p["name"] == pipeline.name)
		self.assertEqual(row["open_leads"], 1)

	def test_get_stages_scoped_to_pipeline(self):
		from micro.api.pipeline import get_stages

		pipeline_a = self._make_pipeline()
		pipeline_b = self._make_pipeline()
		stage_a = self._make_stage(pipeline_a.name, stage_name="_Test Scoped A")
		stage_b = self._make_stage(pipeline_b.name, stage_name="_Test Scoped B")

		names = [s["name"] for s in get_stages(pipeline=pipeline_a.name)["stages"]]
		self.assertIn(stage_a.name, names)
		self.assertNotIn(stage_b.name, names)

	def test_unassigned_leads(self):
		"""Leads without a stage surface in their own column."""
		from micro.api.pipeline import get_pipeline

		pipeline = self._make_pipeline()
		self._make_stage(pipeline.name)
		lead = self._make_lead(pipeline.name)
		frappe.db.set_value("Micro Lead", lead.name, "stage", None)

		result = get_pipeline(pipeline=pipeline.name, show_closed=True)
		self.assertIn(lead.name, [row["name"] for row in result["unassigned"]])
