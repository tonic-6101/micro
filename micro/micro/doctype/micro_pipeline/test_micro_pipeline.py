# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe.tests import IntegrationTestCase


class TestMicroPipeline(IntegrationTestCase):
	def _set_limit(self, limit):
		# Written straight to the single, so an incomplete Micro Settings
		# (e.g. no company name yet) cannot fail the test setup.
		frappe.db.set_single_value("Micro Settings", "pipeline_limit", limit)

	def _make_pipeline(self, **kwargs):
		defaults = {
			"doctype": "Micro Pipeline",
			"pipeline_name": frappe.generate_hash("_Test Pipeline", 8),
			"is_active": 1,
		}
		defaults.update(kwargs)
		return frappe.get_doc(defaults).insert(ignore_permissions=True)

	def test_create_pipeline(self):
		self._set_limit(0)
		pipeline = self._make_pipeline(pipeline_name="_Test Named Pipeline", is_default=1)
		self.assertEqual(pipeline.pipeline_name, "_Test Named Pipeline")

	def test_only_one_default_pipeline(self):
		self._set_limit(0)
		first = self._make_pipeline(is_default=1)
		second = self._make_pipeline(is_default=1)

		self.assertEqual(frappe.db.get_value("Micro Pipeline", first.name, "is_default"), 0)
		self.assertEqual(frappe.db.get_value("Micro Pipeline", second.name, "is_default"), 1)

	def test_limit_blocks_further_pipelines(self):
		self._set_limit(0)
		existing = frappe.db.count("Micro Pipeline")
		self._set_limit(existing or 1)

		with self.assertRaises(frappe.ValidationError):
			self._make_pipeline()

		self._set_limit(0)

	def test_pipeline_with_leads_cannot_be_deleted(self):
		self._set_limit(0)
		pipeline = self._make_pipeline()
		stage = frappe.get_doc(
			{
				"doctype": "Micro Pipeline Stage",
				"stage_name": "_Test Stage",
				"pipeline": pipeline.name,
				"sort_order": 10,
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Micro Lead",
				"lead_name": "_Test Blocking Lead",
				"pipeline": pipeline.name,
				"stage": stage.name,
			}
		).insert(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc("Micro Pipeline", pipeline.name)
