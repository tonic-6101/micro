# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase

from micro.api.receipts import get_receipt, get_receipts


class TestReceiptAPI(FrappeTestCase):
	def _make_receipt(self, **kwargs):
		defaults = {
			"doctype": "Micro Receipt",
			"receipt_date": "2026-03-15",
			"amount": 55.00,
			"vendor": "_Test API Vendor",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	# --- get_receipts ---

	def test_get_receipts_returns_dict(self):
		self._make_receipt()
		result = get_receipts()
		self.assertIsInstance(result, dict)
		self.assertIn("receipts", result)
		self.assertIn("total", result)

	def test_get_receipts_list(self):
		self._make_receipt()
		result = get_receipts()
		self.assertGreaterEqual(len(result["receipts"]), 1)

	def test_get_receipts_pagination(self):
		for i in range(3):
			self._make_receipt(vendor=f"_Test Page Vendor {i}", amount=10.00 + i)

		result = get_receipts(limit_page_length=2)
		self.assertLessEqual(len(result["receipts"]), 2)
		self.assertGreaterEqual(result["total"], 3)

	def test_get_receipts_search(self):
		self._make_receipt(vendor="_Test Unique Vendor Name")
		result = get_receipts(search="_Test Unique Vendor")
		self.assertGreaterEqual(len(result["receipts"]), 1)

	def test_get_receipts_category_filter(self):
		self._make_receipt(category="Travel", vendor="_Test Travel Vendor")
		result = get_receipts(category="Travel")
		self.assertGreaterEqual(len(result["receipts"]), 1)
		self.assertTrue(
			all(r["category"] == "Travel" for r in result["receipts"])
		)

	def test_get_receipts_fields(self):
		self._make_receipt()
		result = get_receipts()
		receipt = result["receipts"][0]
		for field in ["name", "receipt_date", "vendor", "amount", "category", "exported"]:
			self.assertIn(field, receipt)

	# --- get_receipt ---

	def test_get_receipt_detail(self):
		receipt = self._make_receipt()
		result = get_receipt(receipt.name)
		self.assertIsInstance(result, dict)
		self.assertIn("receipt", result)
		self.assertEqual(result["receipt"]["vendor"], "_Test API Vendor")

	def test_get_receipt_not_found(self):
		with self.assertRaises(frappe.DoesNotExistError):
			get_receipt("NONEXISTENT-RECEIPT")
