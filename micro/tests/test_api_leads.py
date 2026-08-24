# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today


class TestLeadsAPI(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.db.set_single_value("Micro Settings", "customer_limit", 9999)
		frappe.db.set_single_value("Micro Settings", "pipeline_limit", 0)

		self.pipeline = frappe.get_doc(
			{
				"doctype": "Micro Pipeline",
				"pipeline_name": frappe.generate_hash("_Test Call Pipeline", 8),
				"is_active": 1,
			}
		).insert(ignore_permissions=True)
		self.stage = frappe.get_doc(
			{
				"doctype": "Micro Pipeline Stage",
				"stage_name": "_Test Call Stage",
				"pipeline": self.pipeline.name,
				"sort_order": 10,
			}
		).insert(ignore_permissions=True)

	def _make_lead(self, **kwargs):
		defaults = {
			"doctype": "Micro Lead",
			"lead_name": "_Test Call Lead",
			"pipeline": self.pipeline.name,
			"stage": self.stage.name,
		}
		defaults.update(kwargs)
		return frappe.get_doc(defaults).insert(ignore_permissions=True)

	def _make_contact(self, first_name):
		return frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": first_name,
				"micro_status": "Potential",
			}
		).insert(ignore_permissions=True)

	# --- call list ---

	def test_call_list_only_returns_due_leads(self):
		from micro.api.leads import get_call_list

		due = self._make_lead(next_follow_up=today())
		later = self._make_lead(next_follow_up=add_days(today(), 30))
		undated = self._make_lead()

		names = [lead["name"] for lead in get_call_list(pipeline=self.pipeline.name)["leads"]]

		self.assertIn(due.name, names)
		self.assertNotIn(later.name, names)
		self.assertNotIn(undated.name, names)

	def test_call_list_can_include_undated_leads(self):
		from micro.api.leads import get_call_list

		undated = self._make_lead()

		names = [
			lead["name"]
			for lead in get_call_list(pipeline=self.pipeline.name, include_undated=True)["leads"]
		]
		self.assertIn(undated.name, names)

	def test_call_list_is_scoped_to_one_pipeline(self):
		from micro.api.leads import get_call_list

		other_pipeline = frappe.get_doc(
			{
				"doctype": "Micro Pipeline",
				"pipeline_name": frappe.generate_hash("_Test Other", 8),
				"is_active": 1,
			}
		).insert(ignore_permissions=True)
		other_stage = frappe.get_doc(
			{
				"doctype": "Micro Pipeline Stage",
				"stage_name": "_Test Other Stage",
				"pipeline": other_pipeline.name,
				"sort_order": 10,
			}
		).insert(ignore_permissions=True)

		mine = self._make_lead(next_follow_up=today())
		theirs = self._make_lead(
			pipeline=other_pipeline.name, stage=other_stage.name, next_follow_up=today()
		)

		names = [lead["name"] for lead in get_call_list(pipeline=self.pipeline.name)["leads"]]
		self.assertIn(mine.name, names)
		self.assertNotIn(theirs.name, names)

	def test_call_list_flags_overdue_and_sorts_oldest_first(self):
		from micro.api.leads import get_call_list

		overdue = self._make_lead(next_follow_up=add_days(today(), -5))
		self._make_lead(next_follow_up=today())

		leads = get_call_list(pipeline=self.pipeline.name)["leads"]

		self.assertEqual(leads[0]["name"], overdue.name)
		self.assertTrue(leads[0]["is_overdue"])

	def test_call_list_attaches_phone_number(self):
		from micro.api.leads import get_call_list

		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "_Test Callee",
				"micro_status": "Potential",
			}
		)
		contact.append("phone_nos", {"phone": "+49 30 123456", "is_primary_phone": 1})
		contact.insert(ignore_permissions=True)

		lead = self._make_lead(contact=contact.name, next_follow_up=today())

		leads = get_call_list(pipeline=self.pipeline.name)["leads"]
		card = next(row for row in leads if row["name"] == lead.name)

		self.assertIsNotNone(card["contact_details"])
		self.assertEqual(card["stage_name"], self.stage.stage_name)

	# --- mutations ---

	def test_snooze_pushes_the_follow_up_date(self):
		from micro.api.leads import snooze_lead

		lead = self._make_lead(next_follow_up=today())
		result = snooze_lead(lead.name, days=7)

		self.assertEqual(str(result["next_follow_up"]), add_days(today(), 7))

	def test_snooze_of_an_overdue_lead_counts_from_today(self):
		from micro.api.leads import snooze_lead

		lead = self._make_lead(next_follow_up=add_days(today(), -10))
		result = snooze_lead(lead.name, days=1)

		self.assertEqual(str(result["next_follow_up"]), add_days(today(), 1))

	def test_create_lead_defaults_to_the_first_stage(self):
		from micro.api.leads import create_lead

		result = create_lead(lead_name="_Test Created", pipeline=self.pipeline.name)
		self.assertEqual(result["lead"]["stage"], self.stage.name)

	def test_create_lead_attaches_the_contact(self):
		from micro.api.leads import create_lead

		contact = self._make_contact("_Test Lead Contact")
		result = create_lead(
			lead_name="_Test With Contact",
			pipeline=self.pipeline.name,
			stage=self.stage.name,
			contact=contact.name,
		)

		self.assertEqual(result["lead"]["contact"], contact.name)

	def test_get_lead_resolves_the_contact_name(self):
		from micro.api.leads import get_lead

		contact = self._make_contact("_Test Named Contact")
		lead = self._make_lead(contact=contact.name)

		details = get_lead(lead.name)["lead"]["contact_details"]

		self.assertIsNotNone(details)
		self.assertEqual(details["name"], contact.name)
		self.assertIn("_Test Named Contact", details["full_name"])

	def test_get_lead_without_a_contact_has_no_details(self):
		from micro.api.leads import get_lead

		lead = self._make_lead()

		self.assertIsNone(get_lead(lead.name)["lead"]["contact_details"])

	# --- one open lead per contact per pipeline ---

	def test_a_contact_cannot_be_open_twice_in_one_pipeline(self):
		from micro.micro.doctype.micro_lead.micro_lead import DuplicateOpenLeadError

		contact = self._make_contact("_Test Twice")
		self._make_lead(contact=contact.name)

		with self.assertRaises(DuplicateOpenLeadError):
			self._make_lead(contact=contact.name, lead_name="_Test Second Attempt")

	def test_a_contact_can_be_open_in_two_pipelines(self):
		contact = self._make_contact("_Test Two Pipelines")
		other_pipeline = frappe.get_doc(
			{
				"doctype": "Micro Pipeline",
				"pipeline_name": frappe.generate_hash("_Test Other Pipeline", 8),
				"is_active": 1,
			}
		).insert(ignore_permissions=True)
		other_stage = frappe.get_doc(
			{
				"doctype": "Micro Pipeline Stage",
				"stage_name": "_Test Other Stage",
				"pipeline": other_pipeline.name,
				"sort_order": 10,
			}
		).insert(ignore_permissions=True)

		self._make_lead(contact=contact.name)
		second = self._make_lead(
			contact=contact.name, pipeline=other_pipeline.name, stage=other_stage.name
		)

		self.assertEqual(second.status, "Open")

	def test_a_closed_lead_does_not_block_a_new_attempt(self):
		"""Coming back to a lost contact is the point of the follow-up queue."""
		contact = self._make_contact("_Test Second Chance")
		lost_stage = frappe.get_doc(
			{
				"doctype": "Micro Pipeline Stage",
				"stage_name": "_Test Lost Stage",
				"pipeline": self.pipeline.name,
				"sort_order": 90,
				"is_closed": 1,
				"is_loss_stage": 1,
			}
		).insert(ignore_permissions=True)

		first = self._make_lead(contact=contact.name)
		first.stage = lost_stage.name
		first.lost_reason = "Kein Budget"
		first.save(ignore_permissions=True)
		self.assertEqual(first.status, "Lost")

		second = self._make_lead(contact=contact.name, lead_name="_Test Six Months Later")

		self.assertEqual(second.status, "Open")

	def test_an_archived_lead_does_not_block_a_new_attempt(self):
		contact = self._make_contact("_Test Binned")
		first = self._make_lead(contact=contact.name)
		first.status = "Archived"
		first.save(ignore_permissions=True)

		second = self._make_lead(contact=contact.name, lead_name="_Test After Trash")

		self.assertEqual(second.status, "Open")

	def test_a_lead_without_a_contact_never_collides(self):
		"""Unassigned leads are placeholders — several may sit on one board."""
		self._make_lead()
		second = self._make_lead(lead_name="_Test Another Placeholder")

		self.assertEqual(second.status, "Open")

	def test_get_lead_resolves_the_stage_name(self):
		from micro.api.leads import get_lead

		lead = self._make_lead()

		# The detail page shows a stage, not a docname like MPS-1035.
		self.assertEqual(get_lead(lead.name)["lead"]["stage_name"], "_Test Call Stage")

	def test_update_lead_saves_notes(self):
		from micro.api.leads import get_lead, update_lead

		lead = self._make_lead()

		update_lead(lead.name, notes="Called, wants a callback in May.")

		self.assertEqual(get_lead(lead.name)["lead"]["notes"], "Called, wants a callback in May.")

	def test_update_lead_moves_the_stage_and_returns_its_name(self):
		from micro.api.leads import update_lead

		later = frappe.get_doc(
			{
				"doctype": "Micro Pipeline Stage",
				"stage_name": "_Test Later Stage",
				"pipeline": self.pipeline.name,
				"sort_order": 20,
			}
		).insert(ignore_permissions=True)
		lead = self._make_lead()

		moved = update_lead(lead.name, stage=later.name)

		self.assertEqual(moved["lead"]["stage"], later.name)
		self.assertEqual(moved["lead"]["stage_name"], "_Test Later Stage")

	def test_update_lead_can_set_and_clear_the_contact(self):
		from micro.api.leads import update_lead

		contact = self._make_contact("_Test Reassigned")
		lead = self._make_lead()

		attached = update_lead(lead.name, contact=contact.name)
		self.assertEqual(attached["lead"]["contact"], contact.name)
		self.assertEqual(attached["lead"]["contact_details"]["name"], contact.name)

		cleared = update_lead(lead.name, contact="")
		self.assertFalse(cleared["lead"]["contact"])
		self.assertIsNone(cleared["lead"]["contact_details"])

	# --- archive (soft delete) and hard delete ---

	def test_archive_lead_sets_the_status(self):
		from micro.api.leads import archive_lead

		lead = self._make_lead()
		self.assertEqual(archive_lead(lead.name)["status"], "Archived")

	def test_archiving_twice_is_harmless(self):
		from micro.api.leads import archive_lead

		lead = self._make_lead()
		archive_lead(lead.name)

		self.assertEqual(archive_lead(lead.name)["status"], "Archived")

	def test_archive_survives_a_closing_stage(self):
		"""The stage a lead is parked in must not undo an explicit archive."""
		from micro.api.leads import archive_lead

		win_stage = frappe.get_doc(
			{
				"doctype": "Micro Pipeline Stage",
				"stage_name": "_Test Win Stage",
				"pipeline": self.pipeline.name,
				"sort_order": 20,
				"is_closed": 1,
				"is_win_stage": 1,
			}
		).insert(ignore_permissions=True)
		lead = self._make_lead(stage=win_stage.name)
		self.assertEqual(frappe.db.get_value("Micro Lead", lead.name, "status"), "Won")

		archive_lead(lead.name)

		self.assertEqual(frappe.db.get_value("Micro Lead", lead.name, "status"), "Archived")

	def test_restore_lead_returns_it_to_open(self):
		from micro.api.leads import archive_lead, restore_lead

		lead = self._make_lead()
		archive_lead(lead.name)

		self.assertEqual(restore_lead(lead.name)["status"], "Open")

	def test_restore_refuses_a_lead_that_is_not_archived(self):
		from micro.api.leads import restore_lead

		lead = self._make_lead()

		with self.assertRaises(frappe.ValidationError):
			restore_lead(lead.name)

	def test_archived_leads_stay_out_of_the_lead_list(self):
		from micro.api.leads import archive_lead, get_leads

		kept = self._make_lead(lead_name="_Test Kept")
		gone = self._make_lead(lead_name="_Test Archived")
		archive_lead(gone.name)

		names = [row["name"] for row in get_leads(limit_page_length=100)["leads"]]

		self.assertIn(kept.name, names)
		self.assertNotIn(gone.name, names)

	def test_archived_leads_are_listed_in_the_archive(self):
		from micro.api.leads import archive_lead, get_archived_leads

		contact = self._make_contact("_Test Archived Contact")
		lead = self._make_lead(contact=contact.name)
		archive_lead(lead.name)

		result = get_archived_leads(pipeline=self.pipeline.name)
		row = next(r for r in result["leads"] if r["name"] == lead.name)

		self.assertEqual(row["contact_details"]["name"], contact.name)
		self.assertEqual(row["stage_name"], self.stage.stage_name)
		self.assertIn("can_delete", result)

	def test_delete_lead_removes_it(self):
		from micro.api.leads import delete_lead

		lead = self._make_lead()
		delete_lead(lead.name)

		self.assertFalse(frappe.db.exists("Micro Lead", lead.name))

	def test_delete_lead_rejects_an_unknown_lead(self):
		from micro.api.leads import delete_lead

		with self.assertRaises(frappe.ValidationError):
			delete_lead("ML-does-not-exist")

	def test_deleting_a_lead_clears_the_contact_stage_mirror(self):
		from micro.api.leads import delete_lead

		contact = self._make_contact("_Test Mirror Contact")
		lead = self._make_lead(contact=contact.name)
		self.assertEqual(
			frappe.db.get_value("Contact", contact.name, "micro_pipeline_stage"), self.stage.name
		)

		delete_lead(lead.name)

		self.assertFalse(frappe.db.get_value("Contact", contact.name, "micro_pipeline_stage"))

	def test_update_lead_ignores_unknown_fields(self):
		from micro.api.leads import update_lead

		lead = self._make_lead()
		result = update_lead(lead.name, priority="High", bogus_field="nope")

		self.assertEqual(result["lead"]["priority"], "High")
