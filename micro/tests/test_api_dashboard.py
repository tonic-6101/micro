# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase


class TestDashboardAPI(FrappeTestCase):
	def test_get_dashboard_kpis_returns_all_sections(self):
		"""Dashboard KPIs response has all expected keys."""
		from micro.api.dashboard import get_dashboard_kpis

		result = get_dashboard_kpis()
		self.assertIn("customers", result)
		self.assertIn("offers", result)
		self.assertIn("invoices", result)
		self.assertIn("receipts", result)
		self.assertIn("recent_activity", result)

	def test_customers_section_has_total(self):
		"""Customers section returns total count."""
		from micro.api.dashboard import get_dashboard_kpis

		result = get_dashboard_kpis()
		self.assertIn("total", result["customers"])
		self.assertIsInstance(result["customers"]["total"], int)

	def test_customers_section_has_by_status(self):
		"""Customers section returns by_status breakdown."""
		from micro.api.dashboard import get_dashboard_kpis

		result = get_dashboard_kpis()
		self.assertIn("by_status", result["customers"])
		self.assertIsInstance(result["customers"]["by_status"], dict)

	def test_receipts_section_has_unexported_count(self):
		"""Receipts section includes unexported count."""
		from micro.api.dashboard import get_dashboard_kpis

		result = get_dashboard_kpis()
		receipts = result["receipts"]
		self.assertIn("unexported", receipts)
		self.assertIn("total_amount", receipts)
		self.assertIn("by_category", receipts)

	def test_offers_section_has_status_breakdown(self):
		"""Offers section returns by_status dict."""
		from micro.api.dashboard import get_dashboard_kpis

		result = get_dashboard_kpis()
		self.assertIn("by_status", result["offers"])
		self.assertIsInstance(result["offers"]["by_status"], dict)

	def test_invoices_section_has_status_breakdown(self):
		"""Invoices section returns by_status dict."""
		from micro.api.dashboard import get_dashboard_kpis

		result = get_dashboard_kpis()
		self.assertIn("by_status", result["invoices"])
		self.assertIsInstance(result["invoices"]["by_status"], dict)

	def test_recent_activity_is_list(self):
		"""Recent activity returns a list."""
		from micro.api.dashboard import get_dashboard_kpis

		result = get_dashboard_kpis()
		self.assertIsInstance(result["recent_activity"], list)

	def test_recent_activity_has_correct_fields(self):
		"""Each activity item has doctype, name, label, modified."""
		from micro.api.dashboard import get_dashboard_kpis

		# Create a customer to ensure at least one activity item
		customer = frappe.get_doc({
			"doctype": "Micro Customer",
			"name1": "Dashboard",
			"last_name": "Test",
			"contact_type": "Person",
		})
		customer.insert()

		result = get_dashboard_kpis()
		if result["recent_activity"]:
			item = result["recent_activity"][0]
			self.assertIn("doctype", item)
			self.assertIn("name", item)
			self.assertIn("label", item)
			self.assertIn("modified", item)

	def test_kpis_reflect_created_data(self):
		"""KPIs update when new documents are created."""
		from micro.api.dashboard import get_dashboard_kpis

		before = get_dashboard_kpis()
		customers_before = before["customers"]["total"]

		customer = frappe.get_doc({
			"doctype": "Micro Customer",
			"name1": "KPI",
			"last_name": "Verify",
			"contact_type": "Person",
		})
		customer.insert()

		after = get_dashboard_kpis()
		self.assertEqual(after["customers"]["total"], customers_before + 1)

	def test_receipts_total_amount_is_float(self):
		"""Receipt total amount is a float value."""
		from micro.api.dashboard import get_dashboard_kpis

		result = get_dashboard_kpis()
		self.assertIsInstance(result["receipts"]["total_amount"], float)

	def test_customers_section_has_by_source(self):
		"""Customers section returns by_source breakdown."""
		from micro.api.dashboard import get_dashboard_kpis

		result = get_dashboard_kpis()
		self.assertIn("by_source", result["customers"])
		self.assertIsInstance(result["customers"]["by_source"], dict)

	def test_by_source_reflects_created_data(self):
		"""by_source counts update when customers with source are created."""
		from micro.api.dashboard import get_dashboard_kpis

		customer = frappe.get_doc({
			"doctype": "Micro Customer",
			"name1": "Source",
			"last_name": "Test",
			"contact_type": "Person",
			"source": "Google Ads",
		})
		customer.insert()

		result = get_dashboard_kpis()
		self.assertIn("Google Ads", result["customers"]["by_source"])
		self.assertGreater(result["customers"]["by_source"]["Google Ads"], 0)
