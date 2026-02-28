# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase


class TestMicroTask(FrappeTestCase):
	def _make_task(self, **kwargs):
		defaults = {
			"doctype": "Micro Task",
			"subject": "_Test Task",
			"status": "Open",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	# --- CRUD ---

	def test_create_task(self):
		task = self._make_task()
		self.assertTrue(task.name)
		self.assertTrue(task.name.startswith("MT-"))

	def test_read_task(self):
		task = self._make_task()
		loaded = frappe.get_doc("Micro Task", task.name)
		self.assertEqual(loaded.subject, "_Test Task")

	def test_update_task(self):
		task = self._make_task()
		task.status = "In Progress"
		task.save(ignore_permissions=True)
		loaded = frappe.get_doc("Micro Task", task.name)
		self.assertEqual(loaded.status, "In Progress")

	def test_delete_task(self):
		task = self._make_task()
		name = task.name
		frappe.delete_doc("Micro Task", name)
		self.assertFalse(frappe.db.exists("Micro Task", name))

	# --- Autoname ---

	def test_autoname_prefix(self):
		task = self._make_task()
		self.assertRegex(task.name, r"^MT-\d{4}$")

	# --- Status transitions ---

	def test_status_open(self):
		task = self._make_task(status="Open")
		self.assertEqual(task.status, "Open")

	def test_status_in_progress(self):
		task = self._make_task(status="In Progress")
		self.assertEqual(task.status, "In Progress")

	def test_status_completed(self):
		task = self._make_task(status="Completed")
		self.assertEqual(task.status, "Completed")

	def test_status_cancelled(self):
		task = self._make_task(status="Cancelled")
		self.assertEqual(task.status, "Cancelled")

	# --- Contact link ---

	def test_task_with_contact(self):
		contact = frappe.get_doc({
			"doctype": "Micro Customer",
			"name1": "_Test Task Contact",
			"contact_type": "Person",
		}).insert(ignore_permissions=True)

		task = self._make_task(
			subject="_Test Linked Task",
			contact=contact.name,
		)
		self.assertEqual(task.contact, contact.name)

	# --- Priority ---

	def test_task_priority(self):
		task = self._make_task(priority="High")
		self.assertEqual(task.priority, "High")

	# --- Due date ---

	def test_task_due_date(self):
		task = self._make_task(due_date="2026-03-15")
		self.assertEqual(str(task.due_date), "2026-03-15")
