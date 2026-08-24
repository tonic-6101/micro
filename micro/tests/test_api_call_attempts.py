# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Logging when someone was called, and reading back when they tend to answer."""

from datetime import datetime

import frappe
from frappe.tests.utils import FrappeTestCase

from micro.api.call_attempts import get_best_time_to_call, get_call_attempts, log_call_attempt


class TestCallAttemptsAPI(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.tag = frappe.generate_hash(length=8)
		self.contact = frappe.get_doc(
			{"doctype": "Contact", "first_name": f"ZZ Call {self.tag}"}
		).insert(ignore_permissions=True).name

	def _attempt(self, when: str, outcome: str = "Reached"):
		return frappe.get_doc(
			{
				"doctype": "Micro Call Attempt",
				"contact": self.contact,
				"outcome": outcome,
				"attempted_at": when,
			}
		).insert(ignore_permissions=True)

	# --- log_call_attempt ---

	def test_logs_an_attempt_against_the_contact(self):
		result = log_call_attempt(self.contact, outcome="Reached")

		self.assertEqual(result["attempt"]["contact"], self.contact)
		self.assertTrue(frappe.db.exists("Micro Call Attempt", result["attempt"]["name"]))

	def test_defaults_the_time_to_now(self):
		result = log_call_attempt(self.contact, outcome="No Answer")

		self.assertIsNotNone(result["attempt"]["attempted_at"])

	def test_refuses_an_unknown_outcome(self):
		with self.assertRaises(frappe.ValidationError):
			log_call_attempt(self.contact, outcome="Ghosted")

	def test_refuses_a_contact_that_is_not_there(self):
		with self.assertRaises(frappe.ValidationError):
			log_call_attempt(f"No Such Contact {self.tag}", outcome="Reached")

	def test_refuses_a_lead_that_is_not_there(self):
		with self.assertRaises(frappe.ValidationError):
			log_call_attempt(self.contact, outcome="Reached", lead=f"No Such Lead {self.tag}")

	# --- get_call_attempts ---

	def test_lists_attempts_newest_first(self):
		self._attempt("2026-03-02 09:00:00", outcome="No Answer")
		self._attempt("2026-03-03 09:00:00", outcome="Reached")

		result = get_call_attempts(self.contact)

		self.assertEqual(len(result["attempts"]), 2)
		self.assertEqual(result["attempts"][0]["outcome"], "Reached")

	# --- get_best_time_to_call ---

	def test_no_attempts_means_no_best_time(self):
		result = get_best_time_to_call(self.contact)

		self.assertEqual(result["total_attempts"], 0)
		self.assertIsNone(result["best"])
		self.assertEqual(result["grid"], [])

	def test_a_single_reached_call_is_not_enough_to_call_it_a_pattern(self):
		self._attempt("2026-03-02 15:00:00", outcome="Reached")

		result = get_best_time_to_call(self.contact)

		self.assertEqual(result["reached_count"], 1)
		self.assertIsNone(result["best"])

	def test_a_repeated_slot_becomes_the_best_time(self):
		# Both land in the same weekday + afternoon slot.
		first = datetime(2026, 3, 2, 15, 0, 0)
		second = datetime(2026, 3, 9, 16, 0, 0)
		self.assertEqual(first.weekday(), second.weekday())

		self._attempt(first.strftime("%Y-%m-%d %H:%M:%S"), outcome="Reached")
		self._attempt(second.strftime("%Y-%m-%d %H:%M:%S"), outcome="Reached")
		# A morning call that never got picked up should not outrank it.
		self._attempt("2026-03-04 08:00:00", outcome="No Answer")

		result = get_best_time_to_call(self.contact)

		self.assertIsNotNone(result["best"])
		self.assertEqual(result["best"]["weekday"], first.weekday())
		self.assertEqual(result["best"]["bucket"], "afternoon")
		self.assertEqual(result["best"]["reached"], 2)
		self.assertEqual(result["total_attempts"], 3)
		self.assertEqual(result["reached_count"], 2)

	def test_the_grid_only_lists_slots_that_were_actually_tried(self):
		self._attempt("2026-03-02 07:00:00", outcome="Reached")

		result = get_best_time_to_call(self.contact)

		self.assertEqual(len(result["grid"]), 1)
		self.assertEqual(result["grid"][0]["bucket"], "morning")
