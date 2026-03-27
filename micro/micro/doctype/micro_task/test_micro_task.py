# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe.tests import IntegrationTestCase


class TestMicroTask(IntegrationTestCase):
	def test_create_task(self):
		task = frappe.get_doc({
			"doctype": "Micro Task",
			"subject": "Test task",
			"status": "Open",
			"priority": "Medium",
		})
		task.insert(ignore_permissions=True)
		self.assertEqual(task.status, "Open")
		self.assertTrue(task.name.startswith("MT-"))

	def test_task_default_status(self):
		task = frappe.get_doc({
			"doctype": "Micro Task",
			"subject": "Default status test",
		})
		task.insert(ignore_permissions=True)
		self.assertEqual(task.status, "Open")
		self.assertEqual(task.priority, "Medium")
