# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase

MAPPING = {
	"name": "name",
	"phone": "phones",
	"website": "site",
	"address_full": "address",
	"notes": "categories",
}


class TestImportsAPI(FrappeTestCase):
	"""Rows mirror the aparser scrape shape: one business per row, no email.

	Fixtures are unique per test — the runner rolls back per class, not per
	test, so shared names and phone numbers would dedupe against each other.
	"""

	def setUp(self):
		super().setUp()
		frappe.db.set_single_value("Micro Settings", "customer_limit", 0)
		frappe.db.set_single_value("Micro Settings", "pipeline_limit", 0)

		self.tag = frappe.generate_hash(length=8)
		# Frappe validates phone format, so the unique part has to stay numeric.
		digits = str(int(self.tag, 16))[:7].ljust(7, "0")
		self.rows = [
			{
				"name": f"Hering & Heinz {self.tag}",
				"phones": f"0266{digits}",
				"site": "https://www.hering-heinz.de/",
				"address": "Gartenstraße 3, 56459 Pottum",
				"categories": "Sanitärinstallateur, Heizungsmonteur",
				"rating": 4.1,
			},
			{
				"name": f"Wärmepumpen Müller {self.tag}",
				"phones": f"0267{digits}",
				"site": "",
				"address": "35767 Breitscheid",
				"categories": "Heizungsbauer",
				"rating": "",
			},
		]

	def _import(self, rows=None, **kwargs):
		from micro.api.imports import import_contacts

		params = {
			"rows": rows if rows is not None else self.rows,
			"mapping": MAPPING,
			"contact_type": "Organization",
		}
		params.update(kwargs)
		return import_contacts(**params)

	def _imported(self, row):
		return frappe.get_doc("Contact", {"first_name": row["name"]})

	# --- mapping ---

	def test_import_creates_contacts_from_scraped_rows(self):
		result = self._import()

		self.assertEqual(result["created"], 2)
		self.assertEqual(result["failed"], 0)

	def test_import_splits_a_german_address(self):
		self._import(rows=[self.rows[0]])
		contact = self._imported(self.rows[0])

		self.assertEqual(contact.micro_address, "Gartenstraße 3")
		self.assertEqual(contact.micro_postal_code, "56459")
		self.assertEqual(contact.micro_city, "Pottum")

	def test_import_handles_an_address_without_a_street(self):
		self._import(rows=[self.rows[1]])
		contact = self._imported(self.rows[1])

		self.assertFalse(contact.micro_address)
		self.assertEqual(contact.micro_postal_code, "35767")
		self.assertEqual(contact.micro_city, "Breitscheid")

	def test_import_keeps_an_unparseable_address_whole(self):
		row = {**self.rows[0], "address": "irgendwo im Wald"}
		self._import(rows=[row])
		contact = self._imported(row)

		self.assertEqual(contact.micro_address, "irgendwo im Wald")
		self.assertFalse(contact.micro_city)

	def test_business_name_lands_in_both_name_and_company(self):
		self._import(rows=[self.rows[0]])
		contact = self._imported(self.rows[0])

		self.assertEqual(contact.first_name, self.rows[0]["name"])
		self.assertEqual(contact.company_name, self.rows[0]["name"])

	def test_import_marks_the_source(self):
		self._import(rows=[self.rows[0]])

		self.assertEqual(self._imported(self.rows[0]).micro_source, "Import")

	def test_row_without_a_name_is_reported_not_swallowed(self):
		result = self._import(rows=[{"name": "", "phones": "12345"}])

		self.assertEqual(result["created"], 0)
		self.assertEqual(result["failed"], 1)
		self.assertEqual(result["failures"][0]["row"], 0)

	def test_an_overlong_value_is_dropped_but_the_contact_is_kept(self):
		"""A 200-character URL cost a whole business before — Data holds 140."""
		row = {**self.rows[0], "site": "https://www.example.de/" + ("a" * 200)}

		result = self._import(rows=[row])

		self.assertEqual(result["created"], 1)
		self.assertEqual(result["failed"], 0)
		self.assertEqual(result["warned"], 1)
		self.assertEqual(result["warnings"][0]["field"], "website")
		self.assertFalse(self._imported(row).micro_website)

	def test_notes_are_not_length_limited(self):
		"""micro_notes is a Text field — long categories must survive."""
		row = {**self.rows[0], "categories": "Heizungsbauer, " * 60}

		result = self._import(rows=[row])

		self.assertEqual(result["warned"], 0)
		self.assertGreater(len(self._imported(row).micro_notes), 140)

	# --- duplicates ---

	def test_duplicate_phone_is_skipped(self):
		self._import(rows=[self.rows[0]])
		result = self._import(rows=[self.rows[0]])

		self.assertEqual(result["created"], 0)
		self.assertEqual(result["skipped"], 1)

	def test_duplicates_inside_one_file_are_caught(self):
		"""The scrape repeats a business across search queries."""
		result = self._import(rows=[self.rows[0], self.rows[0]])

		self.assertEqual(result["created"], 1)
		self.assertEqual(result["skipped"], 1)

	def test_update_fills_blanks_without_overwriting(self):
		self._import(rows=[{**self.rows[0], "site": ""}])
		contact_name = self._imported(self.rows[0]).name
		frappe.db.set_value("Contact", contact_name, "micro_city", "Handgepflegt")

		self._import(rows=[self.rows[0]], on_duplicate="update")

		contact = frappe.get_doc("Contact", contact_name)
		self.assertEqual(contact.micro_website, "https://www.hering-heinz.de/")
		self.assertEqual(contact.micro_city, "Handgepflegt")

	def test_dedupe_can_be_turned_off(self):
		self._import(rows=[self.rows[0]])
		result = self._import(rows=[self.rows[0]], dedupe_by="none")

		self.assertEqual(result["created"], 1)

	def test_dedupe_by_name_matches_on_the_business_name(self):
		self._import(rows=[self.rows[0]], dedupe_by="name")
		result = self._import(rows=[{**self.rows[0], "phones": "0000000"}], dedupe_by="name")

		self.assertEqual(result["skipped"], 1)

	# --- limits ---

	def test_import_stops_at_the_customer_limit(self):
		used = frappe.db.count("Contact", {"micro_status": ["is", "set"]})
		frappe.db.set_single_value("Micro Settings", "customer_limit", used + 1)

		result = self._import()

		self.assertEqual(result["created"], 1)
		self.assertTrue(result["limit_reached"])

	def test_capacity_reports_remaining_slots(self):
		from micro.api.imports import get_capacity

		used = frappe.db.count("Contact", {"micro_status": ["is", "set"]})
		frappe.db.set_single_value("Micro Settings", "customer_limit", used + 5)

		capacity = get_capacity()

		self.assertEqual(capacity["remaining"], 5)
		self.assertFalse(capacity["unlimited"])

	def test_capacity_is_unlimited_when_the_limit_is_zero(self):
		from micro.api.imports import get_capacity

		frappe.db.set_single_value("Micro Settings", "customer_limit", 0)

		self.assertTrue(get_capacity()["unlimited"])

	def test_a_zero_limit_really_lets_contacts_through(self):
		"""`settings.customer_limit or 100` read a deliberate 0 as unset and put
		the Community cap back — an import stopped dead at 100 contacts."""
		frappe.db.set_single_value("Micro Settings", "customer_limit", 0)

		result = self._import()

		self.assertEqual(result["created"], 2)
		self.assertFalse(result["limit_reached"])
		self.assertEqual(result["failed"], 0)

	def test_an_unset_limit_still_falls_back_to_the_community_cap(self):
		from micro.limits import DEFAULT_CUSTOMER_LIMIT, get_limit

		frappe.db.set_single_value("Micro Settings", "customer_limit", None)

		self.assertEqual(get_limit("customer_limit", DEFAULT_CUSTOMER_LIMIT), DEFAULT_CUSTOMER_LIMIT)

	# --- background work ---

	def test_import_does_not_enqueue_a_job_per_contact(self):
		"""One health-score job per row overflowed the queue at ~550 pending,
		after which every further insert failed outright."""
		enqueued = []
		original = frappe.enqueue

		def spy(*args, **kwargs):
			enqueued.append(kwargs.get("job_id") or args)
			return None

		frappe.enqueue = spy
		try:
			result = self._import()
		finally:
			frappe.enqueue = original

		self.assertEqual(result["created"], 2)
		self.assertEqual(enqueued, [])

	def test_the_flag_is_cleared_afterwards(self):
		self._import()

		self.assertFalse(frappe.flags.get("micro_bulk_import"))

	def test_health_score_recalc_still_runs_outside_an_import(self):
		from micro.services.health_score import skip_health_score_recalc

		self.assertFalse(skip_health_score_recalc())

	# --- leads ---

	def test_import_can_create_a_lead_per_contact(self):
		pipeline = frappe.get_doc(
			{
				"doctype": "Micro Pipeline",
				"pipeline_name": frappe.generate_hash("_Test Import Pipeline", 8),
				"is_active": 1,
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Micro Pipeline Stage",
				"stage_name": "_Test Import Stage",
				"pipeline": pipeline.name,
				"sort_order": 10,
			}
		).insert(ignore_permissions=True)

		self._import(create_leads=True, pipeline=pipeline.name)

		leads = frappe.get_all(
			"Micro Lead", filters={"pipeline": pipeline.name}, fields=["lead_name", "source", "contact"]
		)
		self.assertEqual(len(leads), 2)
		self.assertTrue(all(lead["contact"] for lead in leads))
		self.assertTrue(all(lead["source"] == "Import" for lead in leads))

	def _import_pipeline(self, label="_Test Import Pipeline"):
		pipeline = frappe.get_doc(
			{
				"doctype": "Micro Pipeline",
				"pipeline_name": frappe.generate_hash(label, 8),
				"is_active": 1,
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Micro Pipeline Stage",
				"stage_name": f"{label} Stage",
				"pipeline": pipeline.name,
				"sort_order": 10,
			}
		).insert(ignore_permissions=True)
		return pipeline

	def test_a_second_campaign_reaches_contacts_that_already_exist(self):
		"""The contact is a duplicate; the campaign is not."""
		first = self._import_pipeline("_Test Campaign One")
		second = self._import_pipeline("_Test Campaign Two")

		self._import(create_leads=True, pipeline=first.name)
		result = self._import(create_leads=True, pipeline=second.name)

		self.assertEqual(result["created"], 0)
		self.assertEqual(result["skipped"], 2)
		self.assertEqual(result["leads_created"], 2)
		self.assertEqual(frappe.db.count("Micro Lead", {"pipeline": second.name}), 2)

	def test_reimporting_the_same_list_does_not_double_the_leads(self):
		pipeline = self._import_pipeline("_Test Rerun")

		self._import(create_leads=True, pipeline=pipeline.name)
		result = self._import(create_leads=True, pipeline=pipeline.name)

		self.assertEqual(result["leads_created"], 0)
		self.assertEqual(frappe.db.count("Micro Lead", {"pipeline": pipeline.name}), 2)

	def test_lead_creation_without_a_pipeline_is_refused(self):
		with self.assertRaises(frappe.ValidationError):
			self._import(create_leads=True)

	def test_unknown_dedupe_key_is_refused(self):
		with self.assertRaises(frappe.ValidationError):
			self._import(dedupe_by="astrology")

	# --- json transport ---

	def test_rows_and_mapping_accept_json_strings(self):
		"""The frontend posts them as JSON strings."""
		result = self._import(rows=frappe.as_json(self.rows[:1]), mapping=frappe.as_json(MAPPING))

		self.assertEqual(result["created"], 1)
