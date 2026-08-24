# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe.tests import IntegrationTestCase


class TestMicroCallAttempt(IntegrationTestCase):
	def test_create_call_attempt(self):
		contact = frappe.get_doc({
			"doctype": "Contact",
			"first_name": "Test Call Attempt Contact",
		}).insert(ignore_permissions=True)

		attempt = frappe.get_doc({
			"doctype": "Micro Call Attempt",
			"contact": contact.name,
			"outcome": "Reached",
		})
		attempt.insert(ignore_permissions=True)
		self.assertEqual(attempt.outcome, "Reached")
		self.assertTrue(attempt.name.startswith("MCA-"))
		self.assertIsNotNone(attempt.attempted_at)
