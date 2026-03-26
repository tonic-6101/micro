# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase

from micro.api.offers import create_offer, get_offer, get_offers


class TestOfferAPI(FrappeTestCase):
	def setUp(self):
		super().setUp()
		settings = frappe.get_single("Micro Settings")
		settings.customer_limit = 9999
		settings.article_limit = 9999
		settings.save(ignore_permissions=True)

	def _make_contact(self, **kwargs):
		defaults = {
			"doctype": "Contact",
			"first_name": "_Test Offer API Contact",
			"micro_contact_type": "Person",
			"micro_status": "Potential",
			"email_id": "offer-api@example.com",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def _make_offer(self, contact=None, **kwargs):
		if not contact:
			contact = self._make_contact()
		defaults = {
			"doctype": "Micro Offer Draft",
			"contact": contact.name,
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.append("items", {
			"description": "_Test API Item",
			"quantity": 1,
			"rate": 100.00,
		})
		doc.insert(ignore_permissions=True)
		return doc

	# --- get_offers ---

	def test_get_offers_returns_dict(self):
		self._make_offer()
		result = get_offers()
		self.assertIsInstance(result, dict)
		self.assertIn("offers", result)
		self.assertIn("total", result)

	def test_get_offers_list(self):
		self._make_offer()
		result = get_offers()
		self.assertGreaterEqual(len(result["offers"]), 1)

	def test_get_offers_pagination(self):
		for i in range(3):
			contact = self._make_contact(
				first_name=f"_Test Page Contact {i}",
				email_id=f"page{i}@example.com",
			)
			self._make_offer(contact=contact)

		result = get_offers(limit_page_length=2)
		self.assertLessEqual(len(result["offers"]), 2)
		self.assertGreaterEqual(result["total"], 3)

	def test_get_offers_search(self):
		offer = self._make_offer()
		ref = offer.reference
		result = get_offers(search=ref[:8])
		self.assertGreaterEqual(len(result["offers"]), 1)

	def test_get_offers_fields(self):
		self._make_offer()
		result = get_offers()
		offer = result["offers"][0]
		for field in ["name", "reference", "contact", "status", "total"]:
			self.assertIn(field, offer)

	# --- get_offer ---

	def test_get_offer_detail(self):
		offer = self._make_offer()
		result = get_offer(offer.name)
		self.assertIsInstance(result, dict)
		self.assertIn("offer", result)
		self.assertEqual(result["offer"]["reference"], offer.reference)

	def test_get_offer_includes_items(self):
		offer = self._make_offer()
		result = get_offer(offer.name)
		self.assertIn("items", result["offer"])
		self.assertGreaterEqual(len(result["offer"]["items"]), 1)

	def test_get_offer_not_found(self):
		with self.assertRaises(frappe.DoesNotExistError):
			get_offer("NONEXISTENT-OFFER")

	# --- create_offer ---

	def test_create_offer_api(self):
		contact = self._make_contact()
		result = create_offer(
			contact=contact.name,
			title="API Test Offer",
			items=[{
				"description": "API Item",
				"quantity": 3,
				"rate": 25.00,
			}],
		)
		self.assertIn("offer", result)
		self.assertEqual(result["offer"]["contact"], contact.name)
		self.assertEqual(result["offer"]["total"], 75.00)

	def test_create_offer_auto_reference(self):
		"""G2: Created offer gets auto-generated reference."""
		contact = self._make_contact()
		result = create_offer(
			contact=contact.name,
			items=[{"description": "Item", "quantity": 1, "rate": 10.00}],
		)
		self.assertRegex(result["offer"]["reference"], r"^OFF-\d{8}-[A-Z0-9]{4}$")

	def test_create_offer_has_watermark(self):
		"""G1: Created offer has watermark."""
		contact = self._make_contact()
		result = create_offer(
			contact=contact.name,
			items=[{"description": "Item", "quantity": 1, "rate": 10.00}],
		)
		self.assertTrue(result["offer"]["watermark_text"])

	def test_create_offer_has_disclaimer(self):
		"""G4: Created offer has disclaimer."""
		contact = self._make_contact()
		result = create_offer(
			contact=contact.name,
			items=[{"description": "Item", "quantity": 1, "rate": 10.00}],
		)
		self.assertTrue(result["offer"]["disclaimer"])
