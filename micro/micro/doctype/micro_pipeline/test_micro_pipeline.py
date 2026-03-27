# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe.tests import IntegrationTestCase


class TestMicroPipeline(IntegrationTestCase):
	def test_create_pipeline(self):
		if frappe.db.exists("Micro Pipeline", "Test Pipeline"):
			frappe.delete_doc("Micro Pipeline", "Test Pipeline", force=True)
		pipeline = frappe.get_doc({
			"doctype": "Micro Pipeline",
			"pipeline_name": "Test Pipeline",
			"is_default": 1,
		})
		pipeline.insert(ignore_permissions=True)
		self.assertEqual(pipeline.pipeline_name, "Test Pipeline")
