# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase


class TestMicroNote(FrappeTestCase):
	def _make_note(self, **kwargs):
		defaults = {
			"doctype": "Micro Note",
			"subject": "_Test Note",
			"content": "<p>Test note content</p>",
			"date": "2026-03-01",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	# --- CRUD ---

	def test_create_note(self):
		note = self._make_note()
		self.assertTrue(note.name)
		self.assertTrue(note.name.startswith("MN-"))

	def test_read_note(self):
		note = self._make_note()
		loaded = frappe.get_doc("Micro Note", note.name)
		self.assertEqual(loaded.subject, "_Test Note")

	def test_update_note(self):
		note = self._make_note()
		note.content = "<p>Updated content</p>"
		note.save(ignore_permissions=True)
		loaded = frappe.get_doc("Micro Note", note.name)
		self.assertIn("Updated content", loaded.content)

	def test_delete_note(self):
		note = self._make_note()
		name = note.name
		frappe.delete_doc("Micro Note", name)
		self.assertFalse(frappe.db.exists("Micro Note", name))

	# --- Autoname ---

	def test_autoname_prefix(self):
		note = self._make_note()
		self.assertRegex(note.name, r"^MN-\d{4}$")

	# --- Note type ---

	def test_default_note_type(self):
		note = self._make_note()
		self.assertEqual(note.note_type, "Note")

	def test_note_type_call(self):
		note = self._make_note(note_type="Call")
		self.assertEqual(note.note_type, "Call")

	def test_note_type_meeting(self):
		note = self._make_note(note_type="Meeting")
		self.assertEqual(note.note_type, "Meeting")

	def test_note_type_email_summary(self):
		note = self._make_note(note_type="Email Summary")
		self.assertEqual(note.note_type, "Email Summary")

	# --- Contact link ---

	def test_note_with_contact(self):
		contact = frappe.get_doc({
			"doctype": "Contact",
			"first_name": "_Test Note Contact",
			"micro_contact_type": "Person",
			"micro_status": "Potential",
		}).insert(ignore_permissions=True)

		note = self._make_note(
			subject="_Test Linked Note",
			contact=contact.name,
		)
		self.assertEqual(note.contact, contact.name)

	# --- Content required ---

	def test_content_required(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({
				"doctype": "Micro Note",
				"subject": "_Test No Content",
				"date": "2026-03-01",
			}).insert(ignore_permissions=True)
