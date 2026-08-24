# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase

from micro.api.customers import create_customer, get_customer, get_customers, update_customer


class TestCustomersAPI(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		# Ensure limit is high enough
		settings = frappe.get_single("Micro Settings")
		settings.customer_limit = 9999
		settings.save(ignore_permissions=True)
		self.customers = []
		for i in range(3):
			doc = frappe.get_doc({
				"doctype": "Contact",
				"first_name": f"_Test API Customer {i}",
				"last_name": "User",
				"micro_contact_type": "Person",
				"micro_status": "Potential",
				"email_id": f"apitest{i}@example.com",
				"phone": f"+49 100 {i:03d}",
			})
			doc.append("email_ids", {"email_id": f"apitest{i}@example.com", "is_primary": 1})
			doc.insert(ignore_permissions=True)
			self.customers.append(doc)

	# --- get_customers ---

	def test_get_customers_returns_list(self):
		result = get_customers()
		self.assertIn("customers", result)
		self.assertIn("total", result)
		self.assertIsInstance(result["customers"], list)

	def test_get_customers_pagination(self):
		result = get_customers(limit_start=0, limit_page_length=2)
		self.assertLessEqual(len(result["customers"]), 2)

	def test_get_customers_search(self):
		result = get_customers(search="_Test API Customer 0")
		self.assertGreaterEqual(result["total"], 1)

	def test_get_customers_default_fields(self):
		result = get_customers()
		if result["customers"]:
			customer = result["customers"][0]
			self.assertIn("name", customer)
			self.assertIn("full_name", customer)
			self.assertIn("email_id", customer)

	def test_get_customers_custom_fields(self):
		result = get_customers(fields=["name", "email_id"])
		if result["customers"]:
			customer = result["customers"][0]
			self.assertIn("name", customer)
			self.assertIn("email_id", customer)

	def test_get_customers_total_count(self):
		result = get_customers()
		self.assertGreaterEqual(result["total"], 3)

	# --- get_customer ---

	def test_get_customer_returns_detail(self):
		result = get_customer(self.customers[0].name)
		self.assertIn("customer", result)
		self.assertIn("notes", result)

	def test_get_customer_has_full_data(self):
		result = get_customer(self.customers[0].name)
		customer = result["customer"]
		self.assertEqual(customer["first_name"], "_Test API Customer 0")
		self.assertEqual(customer["email_id"], "apitest0@example.com")

	def test_get_customer_with_related_note(self):
		customer_id = self.customers[0].name

		frappe.get_doc({
			"doctype": "Micro Note",
			"subject": "_Test Related Note",
			"content": "<p>Related note</p>",
			"contact": customer_id,
			"date": "2026-03-01",
		}).insert(ignore_permissions=True)

		result = get_customer(customer_id)
		self.assertGreaterEqual(len(result["notes"]), 1)

	def test_get_customer_nonexistent(self):
		with self.assertRaises(frappe.DoesNotExistError):
			get_customer("NONEXISTENT-CONTACT-9999")

	# --- create_customer ---

	def test_create_customer_minimal(self):
		result = create_customer(first_name="_Test Create Min", last_name="Person")
		self.assertIn("customer", result)
		self.assertEqual(result["customer"]["first_name"], "_Test Create Min")
		self.assertEqual(result["customer"]["micro_contact_type"], "Person")

	def test_create_customer_full(self):
		result = create_customer(
			first_name="_Test Create Full",
			last_name="Vollständig",
			contact_type="Organization",
			email="full@example.com",
			phone="+49 123 456",
			mobile="+49 170 789",
			website="https://example.com",
			city="Berlin",
			postal_code="10115",
			country="Germany",
			address="Hauptstr. 1",
			source="Referral",
			notes="Test notes",
		)
		customer = result["customer"]
		self.assertEqual(customer["last_name"], "Vollständig")
		self.assertEqual(customer["micro_contact_type"], "Organization")
		self.assertEqual(customer["email_id"], "full@example.com")
		self.assertEqual(customer["micro_city"], "Berlin")
		self.assertEqual(customer["micro_source"], "Referral")

	def test_create_customer_returns_name(self):
		result = create_customer(first_name="_Test Create Name", last_name="Ret")
		self.assertIn("name", result["customer"])

	def test_create_customer_computes_full_name(self):
		result = create_customer(first_name="_Test First", last_name="Last")
		self.assertIn("First", result["customer"]["full_name"])
		self.assertIn("Last", result["customer"]["full_name"])

	def test_create_customer_invalid_email_raises(self):
		with self.assertRaises(frappe.ValidationError):
			create_customer(first_name="_Test Bad Email", email="not-an-email")

	# --- leads on the customer page ---

	def _make_pipeline_with_stage(self, label: str):
		pipeline = frappe.get_doc(
			{
				"doctype": "Micro Pipeline",
				"pipeline_name": frappe.generate_hash(label, 8),
				"is_active": 1,
			}
		).insert(ignore_permissions=True)
		stage = frappe.get_doc(
			{
				"doctype": "Micro Pipeline Stage",
				"stage_name": f"{label} Stage",
				"pipeline": pipeline.name,
				"sort_order": 10,
			}
		).insert(ignore_permissions=True)
		return pipeline, stage

	def test_get_customer_lists_leads_across_pipelines(self):
		customer = self.customers[0]
		first, first_stage = self._make_pipeline_with_stage("_Test Cust Pipe A")
		second, second_stage = self._make_pipeline_with_stage("_Test Cust Pipe B")

		for pipeline, stage in ((first, first_stage), (second, second_stage)):
			frappe.get_doc(
				{
					"doctype": "Micro Lead",
					"lead_name": f"_Test Lead {pipeline.name}",
					"contact": customer.name,
					"pipeline": pipeline.name,
					"stage": stage.name,
				}
			).insert(ignore_permissions=True)

		leads = get_customer(customer.name)["leads"]

		self.assertEqual(len(leads), 2)
		self.assertEqual({lead["pipeline"] for lead in leads}, {first.name, second.name})
		# The page shows names, not docnames.
		self.assertTrue(all(lead["pipeline_name"] for lead in leads))
		self.assertTrue(all(lead["stage_name"] for lead in leads))

	def test_get_customer_puts_open_leads_before_closed_ones(self):
		customer = self.customers[1]
		pipeline, stage = self._make_pipeline_with_stage("_Test Cust Order")
		lost_stage = frappe.get_doc(
			{
				"doctype": "Micro Pipeline Stage",
				"stage_name": "_Test Cust Lost",
				"pipeline": pipeline.name,
				"sort_order": 90,
				"is_closed": 1,
				"is_loss_stage": 1,
			}
		).insert(ignore_permissions=True)

		closed = frappe.get_doc(
			{
				"doctype": "Micro Lead",
				"lead_name": "_Test Closed Attempt",
				"contact": customer.name,
				"pipeline": pipeline.name,
				"stage": lost_stage.name,
				"lost_reason": "Kein Budget",
			}
		).insert(ignore_permissions=True)
		open_lead = frappe.get_doc(
			{
				"doctype": "Micro Lead",
				"lead_name": "_Test Open Attempt",
				"contact": customer.name,
				"pipeline": pipeline.name,
				"stage": stage.name,
			}
		).insert(ignore_permissions=True)

		leads = get_customer(customer.name)["leads"]

		self.assertEqual(leads[0]["name"], open_lead.name)
		self.assertTrue(leads[0]["is_open"])
		self.assertEqual(leads[1]["name"], closed.name)
		self.assertFalse(leads[1]["is_open"])

	def test_get_customers_filters_by_what_happened_in_a_pipeline(self):
		pipeline, stage = self._make_pipeline_with_stage("_Test Audience")
		worked = self.customers[0]
		untouched = self.customers[1]

		frappe.get_doc(
			{
				"doctype": "Micro Lead",
				"lead_name": "_Test Audience Lead",
				"contact": worked.name,
				"pipeline": pipeline.name,
				"stage": stage.name,
			}
		).insert(ignore_permissions=True)

		def names(state):
			return {
				row["name"]
				for row in get_customers(
					pipeline=pipeline.name, pipeline_state=state, limit_page_length=100
				)["customers"]
			}

		self.assertIn(worked.name, names("open"))
		self.assertNotIn(untouched.name, names("open"))

		self.assertIn(worked.name, names("ever"))

		self.assertIn(untouched.name, names("never"))
		self.assertNotIn(worked.name, names("never"))

	# --- categories: one segment, many tags ---

	def _make_segment(self, label: str):
		return frappe.get_doc(
			{
				"doctype": "Micro Segment",
				"segment_name": frappe.generate_hash(label, 8),
				"color": "Blue",
				"is_active": 1,
			}
		).insert(ignore_permissions=True)

	def test_get_customers_filters_by_segment(self):
		from micro.api.customers import NO_SEGMENT

		segment = self._make_segment("_Test Architekt")
		filed = self.customers[0]
		frappe.db.set_value("Contact", filed.name, "micro_segment", segment.name)

		names = {
			row["name"]
			for row in get_customers(segment=segment.name, limit_page_length=100)["customers"]
		}
		self.assertEqual(names, {filed.name})

		unfiled = {
			row["name"]
			for row in get_customers(segment=NO_SEGMENT, limit_page_length=100)["customers"]
		}
		self.assertNotIn(filed.name, unfiled)
		self.assertIn(self.customers[1].name, unfiled)

	def test_tags_are_added_and_removed(self):
		from micro.api.customers import add_customer_tag, remove_customer_tag

		customer = self.customers[0]

		self.assertEqual(add_customer_tag(customer.name, "Altbau")["tags"], ["Altbau"])
		self.assertEqual(
			sorted(add_customer_tag(customer.name, "Messe 2026")["tags"]),
			["Altbau", "Messe 2026"],
		)
		self.assertEqual(remove_customer_tag(customer.name, "Altbau")["tags"], ["Messe 2026"])

	def test_get_customers_filters_by_tag(self):
		from micro.api.customers import add_customer_tag

		tagged = self.customers[0]
		add_customer_tag(tagged.name, "_TestTagFilter")

		names = {
			row["name"]
			for row in get_customers(tag="_TestTagFilter", limit_page_length=100)["customers"]
		}

		self.assertEqual(names, {tagged.name})

	def test_a_tag_filter_does_not_cancel_a_pipeline_filter(self):
		"""Both narrow by contact id — the second must not replace the first."""
		from micro.api.customers import add_customer_tag

		pipeline, stage = self._make_pipeline_with_stage("_Test Combined")
		tagged_and_worked = self.customers[0]
		only_tagged = self.customers[1]

		for customer in (tagged_and_worked, only_tagged):
			add_customer_tag(customer.name, "_TestCombined")

		frappe.get_doc(
			{
				"doctype": "Micro Lead",
				"lead_name": "_Test Combined Lead",
				"contact": tagged_and_worked.name,
				"pipeline": pipeline.name,
				"stage": stage.name,
			}
		).insert(ignore_permissions=True)

		names = {
			row["name"]
			for row in get_customers(
				tag="_TestCombined",
				pipeline=pipeline.name,
				pipeline_state="open",
				limit_page_length=100,
			)["customers"]
		}

		self.assertEqual(names, {tagged_and_worked.name})

	def test_facets_count_the_whole_base_not_one_page(self):
		from micro.api.customers import add_customer_tag, get_customer_facets

		segment = self._make_segment("_Test Facet")
		for customer in self.customers[:2]:
			frappe.db.set_value("Contact", customer.name, "micro_segment", segment.name)
		add_customer_tag(self.customers[0].name, "_TestFacetTag")

		facets = get_customer_facets()

		counted = next(s for s in facets["segments"] if s["name"] == segment.name)
		self.assertEqual(counted["count"], 2)
		self.assertEqual(counted["color"], "Blue")
		self.assertGreaterEqual(facets["unsegmented"], 1)
		self.assertIn("_TestFacetTag", {tag["tag"] for tag in facets["tags"]})

	# --- update ---

	def test_update_customer_writes_its_own_fields(self):
		customer = self.customers[0]

		update_customer(
			customer.name,
			micro_website="https://example.de",
			micro_city="Pottum",
			micro_postal_code="56459",
			micro_notes="Rief zurück, will ein Angebot.",
			micro_status="Active",
		)

		updated = get_customer(customer.name)["customer"]
		self.assertEqual(updated["micro_website"], "https://example.de")
		self.assertEqual(updated["micro_city"], "Pottum")
		self.assertEqual(updated["micro_postal_code"], "56459")
		self.assertEqual(updated["micro_notes"], "Rief zurück, will ein Angebot.")
		self.assertEqual(updated["micro_status"], "Active")

	def test_update_customer_keeps_the_email_after_save(self):
		"""Frappe rebuilds email_id from the child table — the write must land there."""
		customer = self.customers[0]

		update_customer(customer.name, email_id="neu@example.de")

		updated = get_customer(customer.name)["customer"]
		self.assertEqual(updated["email_id"], "neu@example.de")

	def test_update_customer_sets_a_phone_that_had_none(self):
		customer = create_customer(first_name="_Test Phoneless", last_name="Contact")["customer"]

		update_customer(customer["name"], phone="+49 2661 123456")

		updated = get_customer(customer["name"])["customer"]
		self.assertEqual(updated["phone"], "+49 2661 123456")

	def test_update_customer_keeps_the_mobile_when_the_phone_is_cleared(self):
		customer = create_customer(
			first_name="_Test Both Numbers",
			last_name="Contact",
			phone="+49 2661 123456",
			mobile="+49 171 1234567",
		)["customer"]

		update_customer(customer["name"], phone="")

		updated = get_customer(customer["name"])["customer"]
		self.assertFalse(updated["phone"])
		self.assertEqual(updated["mobile_no"], "+49 171 1234567")

	def test_update_customer_ignores_fields_it_does_not_own(self):
		customer = self.customers[0]

		update_customer(customer.name, micro_health_score="A")

		self.assertFalse(get_customer(customer.name)["customer"]["micro_health_score"])

	# --- status field ---

	def test_default_status_potential(self):
		"""New customers default to 'Potential' status."""
		result = create_customer(first_name="_Test Status", last_name="Default")
		self.assertEqual(result["customer"]["micro_status"], "Potential")
