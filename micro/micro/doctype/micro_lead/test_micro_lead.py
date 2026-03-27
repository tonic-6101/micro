# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe.tests import IntegrationTestCase


class TestMicroLead(IntegrationTestCase):
	def test_create_lead(self):
		pipeline = _get_or_create_pipeline()
		stage = _get_first_stage()
		lead = frappe.get_doc({
			"doctype": "Micro Lead",
			"lead_name": "Test Website Project",
			"status": "Open",
			"pipeline": pipeline,
			"stage": stage,
		})
		lead.insert(ignore_permissions=True)
		self.assertEqual(lead.status, "Open")
		self.assertTrue(lead.name.startswith("ML-"))

	def test_lead_defaults(self):
		pipeline = _get_or_create_pipeline()
		stage = _get_first_stage()
		lead = frappe.get_doc({
			"doctype": "Micro Lead",
			"lead_name": "Default priority test",
			"pipeline": pipeline,
			"stage": stage,
		})
		lead.insert(ignore_permissions=True)
		self.assertEqual(lead.priority, "Medium")


def _get_or_create_pipeline():
	if frappe.db.exists("Micro Pipeline", {"pipeline_name": "Sales Pipeline"}):
		return frappe.db.get_value("Micro Pipeline", {"pipeline_name": "Sales Pipeline"})
	p = frappe.get_doc({
		"doctype": "Micro Pipeline",
		"pipeline_name": "Sales Pipeline",
		"is_default": 1,
	})
	p.insert(ignore_permissions=True)
	return p.name


def _get_first_stage():
	return frappe.db.get_value(
		"Micro Pipeline Stage", {}, "name", order_by="sort_order asc"
	)
