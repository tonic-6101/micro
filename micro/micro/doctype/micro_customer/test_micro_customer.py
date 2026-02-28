# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase


class TestMicroCustomer(FrappeTestCase):
	def setUp(self):
		super().setUp()
		# Ensure customer limit is high enough for tests
		settings = frappe.get_single("Micro Settings")
		settings.customer_limit = 9999
		settings.save(ignore_permissions=True)

	def _make_customer(self, **kwargs):
		"""Helper to create a test customer."""
		defaults = {
			"doctype": "Micro Customer",
			"name1": "_Test First",
			"last_name": "Customer",
			"contact_type": "Person",
			"email": "test@example.com",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	# --- CRUD ---

	def test_create_customer(self):
		customer = self._make_customer()
		self.assertTrue(customer.name)
		self.assertTrue(customer.name.startswith("MC-"))

	def test_read_customer(self):
		customer = self._make_customer()
		loaded = frappe.get_doc("Micro Customer", customer.name)
		self.assertEqual(loaded.name1, "_Test First")
		self.assertEqual(loaded.email, "test@example.com")

	def test_update_customer(self):
		customer = self._make_customer()
		customer.phone = "+49 123 456"
		customer.save(ignore_permissions=True)
		loaded = frappe.get_doc("Micro Customer", customer.name)
		self.assertEqual(loaded.phone, "+49 123 456")

	def test_delete_customer(self):
		customer = self._make_customer()
		name = customer.name
		frappe.delete_doc("Micro Customer", name)
		self.assertFalse(frappe.db.exists("Micro Customer", name))

	# --- full_name computation ---

	def test_full_name_first_and_last(self):
		customer = self._make_customer(name1="_Test John", last_name="Doe")
		self.assertEqual(customer.full_name, "_Test John Doe")

	def test_full_name_first_only(self):
		customer = self._make_customer(name1="_Test Jane", last_name=None)
		self.assertEqual(customer.full_name, "_Test Jane")

	def test_full_name_updates_on_save(self):
		customer = self._make_customer(name1="_Test Alice", last_name="Smith")
		self.assertEqual(customer.full_name, "_Test Alice Smith")
		customer.last_name = "Jones"
		customer.save(ignore_permissions=True)
		self.assertEqual(customer.full_name, "_Test Alice Jones")

	# --- Email validation ---

	def test_valid_email(self):
		customer = self._make_customer(email="valid@example.com")
		self.assertEqual(customer.email, "valid@example.com")

	def test_invalid_email_throws(self):
		with self.assertRaises(frappe.ValidationError):
			self._make_customer(email="not-an-email")

	def test_empty_email_allowed(self):
		customer = self._make_customer(email=None)
		self.assertTrue(customer.name)

	# --- Organization link ---

	def test_organization_type_clears_org_link(self):
		# Create a real org customer first so the link is valid
		org = self._make_customer(
			name1="_Test Real Org",
			contact_type="Organization",
			email="realorg@example.com",
		)
		# Now create an Organization customer with an organization link — should be cleared
		customer = self._make_customer(
			name1="_Test Org With Link",
			contact_type="Organization",
			organization=org.name,
			email="orgwithlink@example.com",
		)
		self.assertIsNone(customer.organization)

	def test_person_type_keeps_org_link(self):
		org = self._make_customer(
			name1="_Test Org",
			contact_type="Organization",
			email="org@example.com",
		)
		customer = self._make_customer(
			name1="_Test Person",
			contact_type="Person",
			organization=org.name,
			email="person@example.com",
		)
		self.assertEqual(customer.organization, org.name)

	# --- Autoname ---

	def test_autoname_prefix(self):
		customer = self._make_customer()
		self.assertRegex(customer.name, r"^MC-\d{4}$")

	# --- Contact type ---

	def test_default_contact_type_person(self):
		doc = frappe.get_doc({
			"doctype": "Micro Customer",
			"name1": "_Test Default Type",
		})
		doc.insert(ignore_permissions=True)
		self.assertEqual(doc.contact_type, "Person")

	def test_contact_type_organization(self):
		customer = self._make_customer(
			name1="_Test Corp",
			contact_type="Organization",
			email="corp@example.com",
		)
		self.assertEqual(customer.contact_type, "Organization")

	# --- Status field ---

	def test_default_status_potential(self):
		"""New customers default to 'Potential' status."""
		customer = self._make_customer()
		self.assertEqual(customer.status, "Potential")

	def test_status_active(self):
		"""Customer status can be set to 'Active'."""
		customer = self._make_customer()
		customer.status = "Active"
		customer.save(ignore_permissions=True)
		loaded = frappe.get_doc("Micro Customer", customer.name)
		self.assertEqual(loaded.status, "Active")

	# --- Source field ---

	def test_source_default_empty(self):
		"""Source field defaults to empty (not required)."""
		customer = self._make_customer()
		self.assertFalse(customer.source)

	def test_source_google_ads(self):
		"""Source can be set to 'Google Ads'."""
		customer = self._make_customer(source="Google Ads", email="gads@example.com")
		self.assertEqual(customer.source, "Google Ads")

	def test_source_referral(self):
		"""Source can be set to 'Referral'."""
		customer = self._make_customer(source="Referral", email="ref@example.com")
		loaded = frappe.get_doc("Micro Customer", customer.name)
		self.assertEqual(loaded.source, "Referral")

	# --- Community limit ---

	def test_community_limit_enforcement(self):
		"""Test that customer limit from settings is enforced."""
		existing_count = frappe.db.count("Micro Customer")

		settings = frappe.get_single("Micro Settings")
		settings.customer_limit = existing_count + 1
		settings.save(ignore_permissions=True)

		self._make_customer(name1="_Test Limit1", email="limit1@example.com")

		with self.assertRaises(frappe.ValidationError):
			self._make_customer(name1="_Test Limit2", email="limit2@example.com")
