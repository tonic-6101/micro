# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase


class TestMicroReceipt(FrappeTestCase):
	def setUp(self):
		super().setUp()
		settings = frappe.get_single("Micro Settings")
		settings.customer_limit = 9999
		settings.save(ignore_permissions=True)

	def _make_receipt(self, **kwargs):
		defaults = {
			"doctype": "Micro Receipt",
			"receipt_date": "2026-03-15",
			"amount": 42.50,
			"vendor": "_Test Vendor",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def _make_contact(self, **kwargs):
		defaults = {
			"doctype": "Contact",
			"first_name": "_Test Receipt Contact",
			"micro_contact_type": "Person",
			"micro_status": "Potential",
			"email_id": "receipt-contact@example.com",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	# --- CRUD ---

	def test_create_receipt(self):
		receipt = self._make_receipt()
		self.assertTrue(receipt.name)
		self.assertTrue(receipt.name.startswith("MR-"))

	def test_read_receipt(self):
		receipt = self._make_receipt()
		loaded = frappe.get_doc("Micro Receipt", receipt.name)
		self.assertEqual(loaded.vendor, "_Test Vendor")
		self.assertEqual(loaded.amount, 42.50)

	def test_update_receipt(self):
		receipt = self._make_receipt()
		receipt.amount = 99.99
		receipt.save(ignore_permissions=True)
		loaded = frappe.get_doc("Micro Receipt", receipt.name)
		self.assertEqual(loaded.amount, 99.99)

	def test_delete_receipt(self):
		receipt = self._make_receipt()
		name = receipt.name
		frappe.delete_doc("Micro Receipt", name)
		self.assertFalse(frappe.db.exists("Micro Receipt", name))

	# --- Autoname ---

	def test_autoname_prefix(self):
		receipt = self._make_receipt()
		self.assertRegex(receipt.name, r"^MR-\d{4}$")

	# --- Fields ---

	def test_default_category(self):
		receipt = self._make_receipt()
		self.assertEqual(receipt.category, "Other")

	def test_category_materials(self):
		receipt = self._make_receipt(category="Materials")
		self.assertEqual(receipt.category, "Materials")

	def test_category_travel(self):
		receipt = self._make_receipt(category="Travel")
		self.assertEqual(receipt.category, "Travel")

	def test_description(self):
		receipt = self._make_receipt(description="Printer paper")
		self.assertEqual(receipt.description, "Printer paper")

	def test_contact_link(self):
		contact = self._make_contact()
		receipt = self._make_receipt(contact=contact.name)
		self.assertEqual(receipt.contact, contact.name)

	def test_notes(self):
		receipt = self._make_receipt(notes="Business lunch with client")
		self.assertEqual(receipt.notes, "Business lunch with client")

	# --- Export tracking ---

	def test_default_not_exported(self):
		receipt = self._make_receipt()
		self.assertEqual(receipt.exported, 0)

	def test_mark_exported(self):
		receipt = self._make_receipt()
		receipt.exported = 1
		receipt.export_date = "2026-03-20"
		receipt.save(ignore_permissions=True)
		loaded = frappe.get_doc("Micro Receipt", receipt.name)
		self.assertEqual(loaded.exported, 1)
		self.assertEqual(str(loaded.export_date), "2026-03-20")

	# --- Default fields ---

	def test_amount_defaults_to_zero(self):
		"""Amount defaults to 0 when not specified."""
		receipt = frappe.get_doc({
			"doctype": "Micro Receipt",
			"receipt_date": "2026-03-15",
			"vendor": "_Test Vendor",
		})
		receipt.insert(ignore_permissions=True)
		self.assertEqual(receipt.amount, 0)

	def test_receipt_date_defaults_to_today(self):
		"""Receipt date defaults to today when not specified."""
		receipt = frappe.get_doc({
			"doctype": "Micro Receipt",
			"amount": 10.00,
			"vendor": "_Test Vendor",
		})
		receipt.insert(ignore_permissions=True)
		self.assertTrue(receipt.receipt_date)
