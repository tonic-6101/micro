# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import nowdate


class TestExportAPI(FrappeTestCase):
	def setUp(self):
		"""Create test receipts for export tests."""
		self.receipt1 = frappe.get_doc({
			"doctype": "Micro Receipt",
			"receipt_date": "2026-01-15",
			"vendor": "Office Supply Co",
			"amount": 49.99,
			"category": "Office",
			"description": "Printer paper",
		})
		self.receipt1.insert()

		self.receipt2 = frappe.get_doc({
			"doctype": "Micro Receipt",
			"receipt_date": "2026-02-10",
			"vendor": "Travel Express",
			"amount": 120.50,
			"category": "Travel",
			"description": "Train tickets",
		})
		self.receipt2.insert()

	def test_export_preview_returns_count(self):
		"""Export preview returns document count."""
		from micro.api.export import get_export_preview

		result = get_export_preview(doc_type="Micro Receipt")
		self.assertIn("count", result)
		self.assertGreaterEqual(result["count"], 2)

	def test_export_preview_with_category_filter(self):
		"""Export preview filters by category."""
		from micro.api.export import get_export_preview

		result = get_export_preview(
			doc_type="Micro Receipt",
			category="Office",
		)
		self.assertGreaterEqual(result["count"], 1)

	def test_export_preview_with_date_range(self):
		"""Export preview filters by date range."""
		from micro.api.export import get_export_preview

		result = get_export_preview(
			doc_type="Micro Receipt",
			from_date="2026-01-01",
			to_date="2026-01-31",
		)
		self.assertGreaterEqual(result["count"], 1)

	def test_export_receipts_csv(self):
		"""Export receipts returns CSV content."""
		from micro.api.export import export_csv

		result = export_csv(doc_type="Micro Receipt")
		self.assertIn("csv", result)
		self.assertIn("count", result)
		self.assertIn("filename", result)
		self.assertGreaterEqual(result["count"], 2)
		self.assertTrue(result["filename"].endswith(".csv"))

	def test_export_receipts_csv_has_header(self):
		"""CSV content starts with header row."""
		from micro.api.export import export_csv

		result = export_csv(doc_type="Micro Receipt")
		lines = result["csv"].strip().split("\n")
		self.assertGreaterEqual(len(lines), 2)

	def test_export_receipts_csv_semicolon_delimiter(self):
		"""CSV uses semicolon delimiter (German convention)."""
		from micro.api.export import export_csv

		result = export_csv(doc_type="Micro Receipt")
		first_line = result["csv"].strip().split("\n")[0]
		self.assertIn(";", first_line)

	def test_export_receipts_with_mark_exported(self):
		"""Export with mark_exported sets exported flag."""
		from micro.api.export import export_csv

		result = export_csv(
			doc_type="Micro Receipt",
			mark_exported=1,
		)
		self.assertGreater(result["marked_exported"], 0)

		# Verify flag was set
		receipt = frappe.get_doc("Micro Receipt", self.receipt1.name)
		self.assertEqual(receipt.exported, 1)
		self.assertTrue(receipt.export_date)

	def test_export_only_unexported(self):
		"""Only unexported filter works."""
		from micro.api.export import export_csv, get_export_preview

		# Mark one as exported
		frappe.db.set_value("Micro Receipt", self.receipt1.name, {
			"exported": 1,
			"export_date": nowdate(),
		})

		preview = get_export_preview(
			doc_type="Micro Receipt",
			only_unexported=1,
		)
		# At least receipt2 should still be unexported
		self.assertGreaterEqual(preview["count"], 1)

	def test_export_invoice_drafts_csv(self):
		"""Export invoice drafts returns CSV."""
		from micro.api.export import export_csv

		# Create an invoice draft for export
		contact = frappe.get_doc({
			"doctype": "Contact",
			"first_name": "Export",
			"last_name": "Test",
			"micro_contact_type": "Person",
			"micro_status": "Potential",
		})
		contact.insert()

		invoice = frappe.get_doc({
			"doctype": "Micro Invoice Draft",
			"contact": contact.name,
			"date": "2026-02-15",
			"items": [
				{"description": "Test service", "quantity": 1, "rate": 100},
			],
		})
		invoice.insert()

		result = export_csv(doc_type="Micro Invoice Draft")
		self.assertIn("csv", result)
		self.assertGreaterEqual(result["count"], 1)
		self.assertTrue(result["filename"].startswith("invoice_drafts_export_"))

	def test_export_unsupported_doctype_throws(self):
		"""Unsupported doc type raises error."""
		from micro.api.export import export_csv

		with self.assertRaises(frappe.ValidationError):
			export_csv(doc_type="Contact")

	def test_mark_as_exported(self):
		"""Bulk mark as exported works."""
		from micro.api.export import mark_as_exported
		import json

		result = mark_as_exported(
			doc_type="Micro Receipt",
			names=json.dumps([self.receipt1.name, self.receipt2.name]),
		)
		self.assertEqual(result["updated"], 2)

	def test_mark_as_exported_wrong_doctype_throws(self):
		"""Mark as exported only works for receipts."""
		from micro.api.export import mark_as_exported

		with self.assertRaises(frappe.ValidationError):
			mark_as_exported(doc_type="Micro Invoice Draft", names=["test"])

	def test_mark_as_exported_empty_names_throws(self):
		"""Mark as exported with no names raises error."""
		from micro.api.export import mark_as_exported

		with self.assertRaises(frappe.ValidationError):
			mark_as_exported(doc_type="Micro Receipt", names=[])

	def test_export_receipts_date_filter_from_only(self):
		"""Export with only from_date filters correctly."""
		from micro.api.export import export_csv

		result = export_csv(
			doc_type="Micro Receipt",
			from_date="2026-02-01",
		)
		# receipt2 (Feb 10) should be included, receipt1 (Jan 15) excluded
		self.assertGreaterEqual(result["count"], 1)

	def test_export_receipts_csv_amount_format(self):
		"""Amount in CSV is formatted with 2 decimal places."""
		from micro.api.export import export_csv

		result = export_csv(doc_type="Micro Receipt")
		lines = result["csv"].strip().split("\n")
		# Check a data line has amount with decimal
		for line in lines[1:]:
			fields = line.split(";")
			# Amount is the 5th field (index 4)
			if fields[4].strip('"'):
				self.assertRegex(fields[4].strip('"'), r"\d+\.\d{2}")
				break
