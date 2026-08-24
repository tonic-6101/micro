# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

"""Tests for Micro's Contact override (MicroContact).

After M1 migration, Micro Customer no longer exists. CRM pipeline data
lives as custom fields on Frappe Contact. These tests verify the
override class behaviour.
"""

import frappe
from frappe.tests.utils import FrappeTestCase


class TestMicroContact(FrappeTestCase):
	def setUp(self):
		super().setUp()
		# Ensure customer limit is high enough for tests
		settings = frappe.get_single("Micro Settings")
		settings.customer_limit = 9999
		settings.save(ignore_permissions=True)

	def _make_customer(self, **kwargs):
		"""Helper to create a test Contact with Micro CRM fields."""
		defaults = {
			"doctype": "Contact",
			"first_name": "_Test First",
			"last_name": "Customer",
			"micro_contact_type": "Person",
			"micro_status": "Potential",
			"email_id": "test@example.com",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		if defaults.get("email_id"):
			doc.append("email_ids", {"email_id": defaults["email_id"], "is_primary": 1})
		doc.insert(ignore_permissions=True)
		return doc

	# --- CRUD ---

	def test_create_customer(self):
		customer = self._make_customer()
		self.assertTrue(customer.name)

	def test_read_customer(self):
		customer = self._make_customer()
		loaded = frappe.get_doc("Contact", customer.name)
		self.assertEqual(loaded.first_name, "_Test First")
		self.assertEqual(loaded.email_id, "test@example.com")

	def test_update_customer(self):
		# `phone` is fetched from the `phone_nos` child table on save, so a
		# direct assignment alone is discarded — the child row is what has to
		# change.
		customer = self._make_customer()
		customer.append("phone_nos", {"phone": "+49 123 456", "is_primary_phone": 1})
		customer.save(ignore_permissions=True)
		loaded = frappe.get_doc("Contact", customer.name)
		self.assertEqual(loaded.phone, "+49 123 456")

	def test_delete_customer(self):
		customer = self._make_customer()
		name = customer.name
		frappe.delete_doc("Contact", name, force=True)
		self.assertFalse(frappe.db.exists("Contact", name))

	# --- full_name computation ---

	def test_full_name_first_and_last(self):
		customer = self._make_customer(first_name="_Test John", last_name="Doe", email_id="john@example.com")
		self.assertIn("John", customer.full_name)
		self.assertIn("Doe", customer.full_name)

	def test_full_name_first_only(self):
		customer = self._make_customer(first_name="_Test Jane", last_name=None, email_id="jane@example.com")
		self.assertIn("Jane", customer.full_name)

	# --- Micro CRM fields ---

	def test_micro_status_set(self):
		customer = self._make_customer()
		self.assertEqual(customer.micro_status, "Potential")

	def test_micro_status_active(self):
		customer = self._make_customer(micro_status="Active", email_id="active@example.com")
		self.assertEqual(customer.micro_status, "Active")

	def test_micro_source(self):
		customer = self._make_customer(micro_source="Google Ads", email_id="gads@example.com")
		self.assertEqual(customer.micro_source, "Google Ads")

	def test_micro_contact_type(self):
		customer = self._make_customer(micro_contact_type="Organization", email_id="org@example.com")
		self.assertEqual(customer.micro_contact_type, "Organization")

	# --- Pipeline stage ---

	def test_contact_has_no_pipeline_stage_without_lead(self):
		"""Pipeline position belongs to Micro Lead — a bare contact has none."""
		customer = self._make_customer(email_id="pipeline@example.com")
		self.assertFalse(customer.micro_pipeline_stage)

	# --- Community limit ---

	def test_community_limit_enforcement(self):
		"""Test that customer limit from settings is enforced."""
		existing_count = frappe.db.count(
			"Contact",
			filters={"micro_status": ["is", "set"]},
		)

		settings = frappe.get_single("Micro Settings")
		settings.customer_limit = existing_count + 1
		settings.save(ignore_permissions=True)

		self._make_customer(first_name="_Test Limit1", email_id="limit1@example.com")

		with self.assertRaises(frappe.ValidationError):
			self._make_customer(first_name="_Test Limit2", email_id="limit2@example.com")
