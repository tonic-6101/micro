# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase

from micro.api.invoices import create_invoice, get_invoice, get_invoices


class TestInvoiceAPI(FrappeTestCase):
	def setUp(self):
		super().setUp()
		settings = frappe.get_single("Micro Settings")
		settings.customer_limit = 9999
		settings.article_limit = 9999
		settings.save(ignore_permissions=True)

	def _make_contact(self, **kwargs):
		defaults = {
			"doctype": "Contact",
			"first_name": "_Test Invoice API Contact",
			"micro_contact_type": "Person",
			"micro_status": "Potential",
			"email_id": "inv-api@example.com",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def _make_invoice(self, contact=None, **kwargs):
		if not contact:
			contact = self._make_contact()
		defaults = {
			"doctype": "Micro Invoice Draft",
			"contact": contact.name,
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.append("items", {
			"description": "_Test API Invoice Item",
			"quantity": 1,
			"rate": 200.00,
		})
		doc.insert(ignore_permissions=True)
		return doc

	# --- get_invoices ---

	def test_get_invoices_returns_dict(self):
		self._make_invoice()
		result = get_invoices()
		self.assertIsInstance(result, dict)
		self.assertIn("invoices", result)
		self.assertIn("total", result)

	def test_get_invoices_list(self):
		self._make_invoice()
		result = get_invoices()
		self.assertGreaterEqual(len(result["invoices"]), 1)

	def test_get_invoices_pagination(self):
		for i in range(3):
			contact = self._make_contact(
				first_name=f"_Test Inv Page Contact {i}",
				email_id=f"inv-page{i}@example.com",
			)
			self._make_invoice(contact=contact)

		result = get_invoices(limit_page_length=2)
		self.assertLessEqual(len(result["invoices"]), 2)
		self.assertGreaterEqual(result["total"], 3)

	def test_get_invoices_fields(self):
		self._make_invoice()
		result = get_invoices()
		invoice = result["invoices"][0]
		for field in ["name", "reference", "contact", "status", "total", "source"]:
			self.assertIn(field, invoice)

	# --- get_invoice ---

	def test_get_invoice_detail(self):
		invoice = self._make_invoice()
		result = get_invoice(invoice.name)
		self.assertIsInstance(result, dict)
		self.assertIn("invoice", result)
		self.assertEqual(result["invoice"]["reference"], invoice.reference)

	def test_get_invoice_includes_items(self):
		invoice = self._make_invoice()
		result = get_invoice(invoice.name)
		self.assertIn("items", result["invoice"])
		self.assertGreaterEqual(len(result["invoice"]["items"]), 1)

	def test_get_invoice_not_found(self):
		with self.assertRaises(frappe.DoesNotExistError):
			get_invoice("NONEXISTENT-INVOICE")

	# --- create_invoice ---

	def test_create_invoice_api(self):
		contact = self._make_contact()
		result = create_invoice(
			contact=contact.name,
			title="API Test Invoice",
			items=[{
				"description": "API Item",
				"quantity": 4,
				"rate": 50.00,
			}],
		)
		self.assertIn("invoice", result)
		self.assertEqual(result["invoice"]["contact"], contact.name)
		self.assertEqual(result["invoice"]["total"], 200.00)

	def test_create_invoice_has_guardrails(self):
		contact = self._make_contact()
		result = create_invoice(
			contact=contact.name,
			items=[{"description": "Item", "quantity": 1, "rate": 10.00}],
		)
		self.assertRegex(result["invoice"]["reference"], r"^INV-\d{8}-[A-Z0-9]{4}$")
		self.assertTrue(result["invoice"]["watermark_text"])
		self.assertTrue(result["invoice"]["disclaimer"])
