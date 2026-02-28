# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase


class TestMicroPipelineStage(FrappeTestCase):
	def _make_stage(self, **kwargs):
		"""Helper to create a test pipeline stage."""
		defaults = {
			"doctype": "Micro Pipeline Stage",
			"stage_name": "_Test Stage",
			"sort_order": 10,
			"color": "Blue",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def test_create_stage(self):
		stage = self._make_stage()
		self.assertTrue(stage.name)
		self.assertEqual(stage.stage_name, "_Test Stage")

	def test_autoname_prefix(self):
		stage = self._make_stage()
		self.assertRegex(stage.name, r"^MPS-\d{4}$")

	def test_sort_order(self):
		s1 = self._make_stage(stage_name="_Test Sort First", sort_order=10)
		s2 = self._make_stage(stage_name="_Test Sort Second", sort_order=20)
		s3 = self._make_stage(stage_name="_Test Sort Third", sort_order=30)

		stages = frappe.get_list(
			"Micro Pipeline Stage",
			filters={"stage_name": ["like", "_Test Sort%"]},
			fields=["name", "stage_name", "sort_order"],
			order_by="sort_order asc",
		)

		names = [s.stage_name for s in stages]
		self.assertEqual(names, ["_Test Sort First", "_Test Sort Second", "_Test Sort Third"])

	def test_is_closed_default(self):
		stage = self._make_stage()
		self.assertFalse(stage.is_closed)

	def test_is_closed_flag(self):
		stage = self._make_stage(stage_name="_Test Closed", is_closed=1)
		self.assertTrue(stage.is_closed)

	def test_color_default(self):
		stage = self._make_stage(stage_name="_Test Color Default", color=None)
		self.assertEqual(stage.color, "Gray")

	def test_delete_stage(self):
		stage = self._make_stage(stage_name="_Test Delete")
		name = stage.name
		frappe.delete_doc("Micro Pipeline Stage", name)
		self.assertFalse(frappe.db.exists("Micro Pipeline Stage", name))
