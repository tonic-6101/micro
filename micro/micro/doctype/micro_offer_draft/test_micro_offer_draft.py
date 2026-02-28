# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase


class TestMicroOfferDraft(FrappeTestCase):
	def setUp(self):
		super().setUp()
		settings = frappe.get_single("Micro Settings")
		settings.customer_limit = 9999
		settings.article_limit = 9999
		settings.save(ignore_permissions=True)

	def _make_contact(self, **kwargs):
		"""Helper to create a test contact."""
		defaults = {
			"doctype": "Micro Customer",
			"name1": "_Test Offer Contact",
			"contact_type": "Person",
			"email": "offer-contact@example.com",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def _make_article(self, **kwargs):
		"""Helper to create a test article."""
		defaults = {
			"doctype": "Micro Article",
			"article_name": "_Test Offer Article",
			"selling_price": 100.00,
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def _make_offer(self, contact=None, items=None, **kwargs):
		"""Helper to create an offer draft with items."""
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
				"description": "_Test Item",
				"quantity": 2,
				"rate": 50.00,
			})

		doc.insert(ignore_permissions=True)
		return doc

	# --- CRUD ---

	def test_create_offer(self):
		offer = self._make_offer()
		self.assertTrue(offer.name)

	def test_read_offer(self):
		offer = self._make_offer()
		loaded = frappe.get_doc("Micro Offer Draft", offer.name)
		self.assertTrue(loaded.reference)

	def test_update_offer(self):
		offer = self._make_offer()
		offer.title = "Updated Title"
		offer.save(ignore_permissions=True)
		loaded = frappe.get_doc("Micro Offer Draft", offer.name)
		self.assertEqual(loaded.title, "Updated Title")

	def test_delete_offer(self):
		offer = self._make_offer()
		name = offer.name
		frappe.delete_doc("Micro Offer Draft", name)
		self.assertFalse(frappe.db.exists("Micro Offer Draft", name))

	# --- G2: Non-sequential reference ---

	def test_reference_auto_generated(self):
		"""G2: Reference is auto-generated on insert."""
		offer = self._make_offer()
		self.assertTrue(offer.reference)
		self.assertRegex(offer.reference, r"^OFF-\d{8}-[A-Z0-9]{4}$")

	def test_reference_unique(self):
		"""G2: Each offer gets a unique reference."""
		contact = self._make_contact()
		offer1 = self._make_offer(contact=contact)
		# New contact for second offer to avoid duplicate link
		contact2 = self._make_contact(
			name1="_Test Offer Contact 2",
			email="offer-contact2@example.com",
		)
		offer2 = self._make_offer(contact=contact2)
		self.assertNotEqual(offer1.reference, offer2.reference)

	def test_reference_not_sequential(self):
		"""G2: References must not be sequential numbers."""
		offer = self._make_offer()
		# Should NOT be a simple integer or sequential format
		self.assertFalse(offer.reference.isdigit())
		self.assertTrue(offer.reference.startswith("OFF-"))

	# --- G1: Draft watermark ---

	def test_is_draft_always_true(self):
		"""G1: is_draft is always enforced to 1."""
		offer = self._make_offer()
		self.assertEqual(offer.is_draft, 1)

	def test_watermark_text_set(self):
		"""G1: Watermark text is auto-set."""
		offer = self._make_offer()
		self.assertTrue(offer.watermark_text)

	def test_watermark_text_default_entwurf(self):
		"""G1: Default watermark is ENTWURF."""
		offer = self._make_offer()
		# Without language set, falls back to settings default
		self.assertIn(offer.watermark_text, ["ENTWURF", "DRAFT"])

	def test_watermark_text_language_aware(self):
		"""G1: Watermark changes with language."""
		offer = self._make_offer(language="en")
		self.assertEqual(offer.watermark_text, "DRAFT")

	def test_watermark_german(self):
		offer = self._make_offer(language="de")
		self.assertEqual(offer.watermark_text, "ENTWURF")

	def test_watermark_french(self):
		offer = self._make_offer(language="fr")
		self.assertEqual(offer.watermark_text, "BROUILLON")

	# --- G4: Disclaimer footer ---

	def test_disclaimer_set(self):
		"""G4: Disclaimer is auto-set on all offers."""
		offer = self._make_offer()
		self.assertTrue(offer.disclaimer)

	def test_disclaimer_contains_draft_notice(self):
		"""G4: Disclaimer mentions draft/non-binding nature."""
		offer = self._make_offer(language="en")
		self.assertIn("DRAFT", offer.disclaimer)
		self.assertIn("not a legally binding", offer.disclaimer)

	def test_disclaimer_german(self):
		offer = self._make_offer(language="de")
		self.assertIn("Entwurf", offer.disclaimer)
		self.assertIn("Steuerberater", offer.disclaimer)

	# --- G3: No tax fields ---

	def test_no_tax_fields_on_offer(self):
		"""G3: Offer DocType must not have tax-related fields."""
		meta = frappe.get_meta("Micro Offer Draft")
		forbidden = ["tax_rate", "vat", "vat_amount", "tax_amount", "tax_category", "tax_template"]
		for field in forbidden:
			self.assertFalse(
				meta.has_field(field),
				f"Offer should not have field '{field}' (G3 compliance)",
			)

	def test_no_tax_fields_on_offer_item(self):
		"""G3: Offer Item child table must not have tax-related fields."""
		meta = frappe.get_meta("Micro Offer Item")
		forbidden = ["tax_rate", "vat", "vat_amount", "tax_amount", "tax_category", "tax_template"]
		for field in forbidden:
			self.assertFalse(
				meta.has_field(field),
				f"Offer Item should not have field '{field}' (G3 compliance)",
			)

	# --- Total calculation ---

	def test_total_calculated(self):
		"""Total is computed from item amounts."""
		offer = self._make_offer(items=[
			{"description": "Item A", "quantity": 2, "rate": 50.00},
			{"description": "Item B", "quantity": 3, "rate": 30.00},
		])
		self.assertEqual(offer.total, 190.00)

	def test_item_amount_calculated(self):
		"""Each item's amount = quantity * rate."""
		offer = self._make_offer(items=[
			{"description": "Item A", "quantity": 5, "rate": 20.00},
		])
		self.assertEqual(offer.items[0].amount, 100.00)

	def test_total_with_zero_rate(self):
		offer = self._make_offer(items=[
			{"description": "Free item", "quantity": 1, "rate": 0},
		])
		self.assertEqual(offer.total, 0)

	def test_total_updates_on_save(self):
		"""Total recalculates when items change."""
		offer = self._make_offer(items=[
			{"description": "Item A", "quantity": 1, "rate": 100.00},
		])
		self.assertEqual(offer.total, 100.00)

		offer.items[0].rate = 200.00
		offer.save(ignore_permissions=True)
		self.assertEqual(offer.total, 200.00)

	# --- Items ---

	def test_offer_requires_items(self):
		"""Offer must have at least one item."""
		contact = self._make_contact()
		doc = frappe.get_doc({
			"doctype": "Micro Offer Draft",
			"contact": contact.name,
		})
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)

	# --- Status ---

	def test_default_status_draft(self):
		offer = self._make_offer()
		self.assertEqual(offer.status, "Draft")

	def test_status_sent(self):
		offer = self._make_offer()
		offer.status = "Sent"
		offer.save(ignore_permissions=True)
		self.assertEqual(offer.status, "Sent")

	# --- Naming / autoname ---

	def test_name_equals_reference(self):
		"""Document name should be the reference field value."""
		offer = self._make_offer()
		self.assertEqual(offer.name, offer.reference)

	# --- Language ---

	def test_language_field(self):
		offer = self._make_offer(language="en")
		self.assertEqual(offer.language, "en")

	# --- Article link on items ---

	def test_item_with_article_link(self):
		article = self._make_article()
		offer = self._make_offer(items=[{
			"article": article.name,
			"description": "From article",
			"quantity": 1,
			"rate": article.selling_price,
		}])
		self.assertEqual(offer.items[0].article, article.name)
