# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase

from micro.micro.doctype.micro_invoice_draft.micro_invoice_draft import create_from_offer


class TestMicroInvoiceDraft(FrappeTestCase):
	def setUp(self):
		super().setUp()
		settings = frappe.get_single("Micro Settings")
		settings.customer_limit = 9999
		settings.article_limit = 9999
		settings.save(ignore_permissions=True)

	def _make_contact(self, **kwargs):
		defaults = {
			"doctype": "Micro Customer",
			"name1": "_Test Invoice Contact",
			"contact_type": "Person",
			"email": "invoice-contact@example.com",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def _make_invoice(self, contact=None, items=None, **kwargs):
		if not contact:
			contact = self._make_contact()

		defaults = {
			"doctype": "Micro Invoice Draft",
			"contact": contact.name,
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)

		if items:
			for item_data in items:
				doc.append("items", item_data)
		else:
			doc.append("items", {
				"description": "_Test Invoice Item",
				"quantity": 1,
				"rate": 100.00,
			})

		doc.insert(ignore_permissions=True)
		return doc

	def _make_offer(self, contact=None, items=None, **kwargs):
		if not contact:
			contact = self._make_contact()

		defaults = {
			"doctype": "Micro Offer Draft",
			"contact": contact.name,
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)

		if items:
			for item_data in items:
				doc.append("items", item_data)
		else:
			doc.append("items", {
				"description": "_Test Offer Item",
				"quantity": 2,
				"rate": 75.00,
			})

		doc.insert(ignore_permissions=True)
		return doc

	# --- CRUD ---

	def test_create_invoice(self):
		invoice = self._make_invoice()
		self.assertTrue(invoice.name)

	def test_read_invoice(self):
		invoice = self._make_invoice()
		loaded = frappe.get_doc("Micro Invoice Draft", invoice.name)
		self.assertTrue(loaded.reference)

	def test_update_invoice(self):
		invoice = self._make_invoice()
		invoice.title = "Updated Title"
		invoice.save(ignore_permissions=True)
		loaded = frappe.get_doc("Micro Invoice Draft", invoice.name)
		self.assertEqual(loaded.title, "Updated Title")

	def test_delete_invoice(self):
		invoice = self._make_invoice()
		name = invoice.name
		frappe.delete_doc("Micro Invoice Draft", name)
		self.assertFalse(frappe.db.exists("Micro Invoice Draft", name))

	# --- G2: Non-sequential reference ---

	def test_reference_auto_generated(self):
		invoice = self._make_invoice()
		self.assertTrue(invoice.reference)
		self.assertRegex(invoice.reference, r"^INV-\d{8}-[A-Z0-9]{4}$")

	def test_reference_unique(self):
		contact = self._make_contact()
		inv1 = self._make_invoice(contact=contact)
		contact2 = self._make_contact(
			name1="_Test Invoice Contact 2",
			email="inv-contact2@example.com",
		)
		inv2 = self._make_invoice(contact=contact2)
		self.assertNotEqual(inv1.reference, inv2.reference)

	def test_reference_not_sequential(self):
		invoice = self._make_invoice()
		self.assertFalse(invoice.reference.isdigit())
		self.assertTrue(invoice.reference.startswith("INV-"))

	# --- G1: Draft watermark ---

	def test_is_draft_always_true(self):
		invoice = self._make_invoice()
		self.assertEqual(invoice.is_draft, 1)

	def test_watermark_text_set(self):
		invoice = self._make_invoice()
		self.assertTrue(invoice.watermark_text)

	def test_watermark_text_language_aware(self):
		invoice = self._make_invoice(language="en")
		self.assertEqual(invoice.watermark_text, "DRAFT")

	def test_watermark_german(self):
		invoice = self._make_invoice(language="de")
		self.assertEqual(invoice.watermark_text, "ENTWURF")

	# --- G4: Disclaimer footer ---

	def test_disclaimer_set(self):
		invoice = self._make_invoice()
		self.assertTrue(invoice.disclaimer)

	def test_disclaimer_english(self):
		invoice = self._make_invoice(language="en")
		self.assertIn("DRAFT", invoice.disclaimer)
		self.assertIn("not a legally binding", invoice.disclaimer)

	def test_disclaimer_german(self):
		invoice = self._make_invoice(language="de")
		self.assertIn("Entwurf", invoice.disclaimer)
		self.assertIn("Steuerberater", invoice.disclaimer)

	# --- G3: No tax fields ---

	def test_no_tax_fields_on_invoice(self):
		meta = frappe.get_meta("Micro Invoice Draft")
		forbidden = ["tax_rate", "vat", "vat_amount", "tax_amount", "tax_category", "tax_template"]
		for field in forbidden:
			self.assertFalse(
				meta.has_field(field),
				f"Invoice should not have field '{field}' (G3)",
			)

	def test_no_tax_fields_on_invoice_item(self):
		meta = frappe.get_meta("Micro Invoice Item")
		forbidden = ["tax_rate", "vat", "vat_amount", "tax_amount", "tax_category", "tax_template"]
		for field in forbidden:
			self.assertFalse(
				meta.has_field(field),
				f"Invoice Item should not have field '{field}' (G3)",
			)

	# --- Total calculation ---

	def test_total_calculated(self):
		invoice = self._make_invoice(items=[
			{"description": "Item A", "quantity": 2, "rate": 50.00},
			{"description": "Item B", "quantity": 3, "rate": 30.00},
		])
		self.assertEqual(invoice.total, 190.00)

	def test_item_amount_calculated(self):
		invoice = self._make_invoice(items=[
			{"description": "Item A", "quantity": 5, "rate": 20.00},
		])
		self.assertEqual(invoice.items[0].amount, 100.00)

	def test_total_updates_on_save(self):
		invoice = self._make_invoice(items=[
			{"description": "Item A", "quantity": 1, "rate": 100.00},
		])
		self.assertEqual(invoice.total, 100.00)

		invoice.items[0].rate = 200.00
		invoice.save(ignore_permissions=True)
		self.assertEqual(invoice.total, 200.00)

	# --- Items required ---

	def test_invoice_requires_items(self):
		contact = self._make_contact()
		doc = frappe.get_doc({
			"doctype": "Micro Invoice Draft",
			"contact": contact.name,
		})
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)

	# --- Status ---

	def test_default_status_draft(self):
		invoice = self._make_invoice()
		self.assertEqual(invoice.status, "Draft")

	def test_status_sent_to_tax_advisor(self):
		invoice = self._make_invoice()
		invoice.status = "Sent to Tax Advisor"
		invoice.save(ignore_permissions=True)
		self.assertEqual(invoice.status, "Sent to Tax Advisor")

	# --- Source ---

	def test_default_source_manual(self):
		invoice = self._make_invoice()
		self.assertEqual(invoice.source, "Manual")

	# --- Name = reference ---

	def test_name_equals_reference(self):
		invoice = self._make_invoice()
		self.assertEqual(invoice.name, invoice.reference)

	# --- Create from offer ---

	def test_create_from_offer(self):
		contact = self._make_contact()
		offer = self._make_offer(
			contact=contact,
			items=[
				{"description": "Design Work", "quantity": 10, "rate": 80.00, "unit": "Stunde"},
				{"description": "Materials", "quantity": 5, "rate": 25.00},
			],
		)

		invoice_dict = create_from_offer(offer.name)
		invoice = frappe.get_doc("Micro Invoice Draft", invoice_dict["name"])

		self.assertEqual(invoice.contact, contact.name)
		self.assertEqual(invoice.source, "From Offer")
		self.assertEqual(invoice.offer_draft, offer.name)
		self.assertEqual(len(invoice.items), 2)
		self.assertEqual(invoice.items[0].description, "Design Work")
		self.assertEqual(invoice.items[0].quantity, 10)
		self.assertEqual(invoice.items[0].rate, 80.00)
		self.assertEqual(invoice.items[0].unit, "Stunde")
		self.assertEqual(invoice.total, 925.00)

	def test_create_from_offer_has_guardrails(self):
		"""Invoice created from offer still has all guardrails."""
		contact = self._make_contact()
		offer = self._make_offer(contact=contact)
		invoice_dict = create_from_offer(offer.name)
		invoice = frappe.get_doc("Micro Invoice Draft", invoice_dict["name"])

		self.assertEqual(invoice.is_draft, 1)
		self.assertTrue(invoice.watermark_text)
		self.assertTrue(invoice.disclaimer)
		self.assertRegex(invoice.reference, r"^INV-\d{8}-[A-Z0-9]{4}$")

	def test_create_from_offer_copies_title(self):
		contact = self._make_contact()
		offer = self._make_offer(contact=contact, title="Website Redesign")
		invoice_dict = create_from_offer(offer.name)
		self.assertEqual(invoice_dict.get("title"), "Website Redesign")

	def test_create_from_offer_copies_language(self):
		contact = self._make_contact()
		offer = self._make_offer(contact=contact, language="en")
		invoice_dict = create_from_offer(offer.name)
		invoice = frappe.get_doc("Micro Invoice Draft", invoice_dict["name"])
		self.assertEqual(invoice.language, "en")
		self.assertEqual(invoice.watermark_text, "DRAFT")
