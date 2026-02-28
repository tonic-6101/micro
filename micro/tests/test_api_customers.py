# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase

from micro.api.customers import create_customer, get_customer, get_customers


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
				"doctype": "Micro Customer",
				"name1": f"_Test API Customer {i}",
				"last_name": "User",
				"contact_type": "Person",
				"email": f"apitest{i}@example.com",
				"phone": f"+49 100 {i:03d}",
			})
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
			self.assertIn("email", customer)

	def test_get_customers_custom_fields(self):
		result = get_customers(fields=["name", "email"])
		if result["customers"]:
			customer = result["customers"][0]
			self.assertIn("name", customer)
			self.assertIn("email", customer)

	def test_get_customers_total_count(self):
		result = get_customers()
		self.assertGreaterEqual(result["total"], 3)

	# --- get_customer ---

	def test_get_customer_returns_detail(self):
		result = get_customer(self.customers[0].name)
		self.assertIn("customer", result)
		self.assertIn("notes", result)
		self.assertIn("tasks", result)

	def test_get_customer_has_full_data(self):
		result = get_customer(self.customers[0].name)
		customer = result["customer"]
		self.assertEqual(customer["name1"], "_Test API Customer 0")
		self.assertEqual(customer["email"], "apitest0@example.com")

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

	def test_get_customer_with_related_task(self):
		customer_id = self.customers[0].name

		frappe.get_doc({
			"doctype": "Micro Task",
			"subject": "_Test Related Task",
			"contact": customer_id,
			"status": "Open",
		}).insert(ignore_permissions=True)

		result = get_customer(customer_id)
		self.assertGreaterEqual(len(result["tasks"]), 1)

	def test_get_customer_nonexistent(self):
		with self.assertRaises(frappe.DoesNotExistError):
			get_customer("MC-9999")

	# --- create_customer ---

	def test_create_customer_minimal(self):
		result = create_customer(name1="_Test Create Min", last_name="Person")
		self.assertIn("customer", result)
		self.assertEqual(result["customer"]["name1"], "_Test Create Min")
		self.assertEqual(result["customer"]["contact_type"], "Person")

	def test_create_customer_full(self):
		result = create_customer(
			name1="_Test Create Full",
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
		self.assertEqual(customer["contact_type"], "Organization")
		self.assertEqual(customer["email"], "full@example.com")
		self.assertEqual(customer["city"], "Berlin")
		self.assertEqual(customer["source"], "Referral")

	def test_create_customer_returns_name(self):
		result = create_customer(name1="_Test Create Name", last_name="Ret")
		self.assertIn("name", result["customer"])
		self.assertTrue(result["customer"]["name"].startswith("MC-"))

	def test_create_customer_computes_full_name(self):
		result = create_customer(name1="_Test First", last_name="Last")
		self.assertEqual(result["customer"]["full_name"], "_Test First Last")

	def test_create_customer_invalid_email_raises(self):
		with self.assertRaises(frappe.ValidationError):
			create_customer(name1="_Test Bad Email", email="not-an-email")

	# --- status field ---

	def test_default_status_potential(self):
		"""New customers default to 'Potential' status."""
		result = create_customer(name1="_Test Status", last_name="Default")
		self.assertEqual(result["customer"]["status"], "Potential")
