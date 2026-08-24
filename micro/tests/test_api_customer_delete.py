# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Removing a customer, and erasing one.

Two different requests wearing the same word. `remove` takes a contact out of
Micro and leaves every document standing; `erase` destroys the record, and is
refused while anything with a retention obligation still points at it.
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from micro.api.customers import bulk_delete_customers, delete_customer, get_delete_preview


class TestCustomerDeleteAPI(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.db.set_single_value("Micro Settings", "customer_limit", 0)
		self.tag = frappe.generate_hash(length=8)

	def _customer(self, **values):
		from micro.api.customers import create_customer

		result = create_customer(
			first_name=f"ZZ Delete {self.tag}",
			last_name="Test",
			contact_type="Person",
			**values,
		)

		return result["customer"]["name"]

	def _note(self, customer):
		return frappe.get_doc(
			{
				"doctype": "Micro Note",
				"subject": f"_Test {self.tag}",
				"content": "<p>x</p>",
				"date": "2026-03-01",
				"contact": customer,
			}
		).insert(ignore_permissions=True)

	def _offer(self, customer, status="Draft"):
		offer = frappe.get_doc(
			{
				"doctype": "Micro Offer Draft",
				"title": f"_Test {self.tag}",
				"contact": customer,
				"date": "2026-03-01",
				"items": [{"description": "x", "qty": 1, "rate": 100}],
			}
		).insert(ignore_permissions=True)

		if status != "Draft":
			frappe.db.set_value("Micro Offer Draft", offer.name, "status", status)

		return offer

	def _receipt(self, customer):
		return frappe.get_doc(
			{
				"doctype": "Micro Receipt",
				"vendor": f"_Test {self.tag}",
				"date": "2026-03-01",
				"amount": 10,
				"contact": customer,
			}
		).insert(ignore_permissions=True)

	def _call_attempt(self, customer):
		return frappe.get_doc(
			{
				"doctype": "Micro Call Attempt",
				"contact": customer,
				"outcome": "Reached",
			}
		).insert(ignore_permissions=True)

	# --- remove ---

	def test_remove_takes_the_contact_out_of_micro(self):
		customer = self._customer()

		delete_customer(customer, mode="remove")

		self.assertFalse(frappe.db.get_value("Contact", customer, "micro_status"))

	def test_remove_keeps_the_contact_itself(self):
		# The record is shared with the other apps — removal is Micro's business
		# only.
		customer = self._customer()

		delete_customer(customer, mode="remove")

		self.assertTrue(frappe.db.exists("Contact", customer))

	def test_remove_keeps_every_document(self):
		customer = self._customer()
		note = self._note(customer)

		delete_customer(customer, mode="remove")

		self.assertTrue(frappe.db.exists("Micro Note", note.name))

	def test_remove_works_even_with_a_sent_offer(self):
		customer = self._customer()
		self._offer(customer, status="Sent")

		delete_customer(customer, mode="remove")

		self.assertFalse(frappe.db.get_value("Contact", customer, "micro_status"))

	# --- erase ---

	def test_erase_destroys_a_contact_nothing_holds(self):
		customer = self._customer()

		delete_customer(customer, mode="erase")

		self.assertFalse(frappe.db.exists("Contact", customer))

	def test_erase_takes_micro_notes_with_it(self):
		customer = self._customer()
		note = self._note(customer)

		delete_customer(customer, mode="erase")

		self.assertFalse(frappe.db.exists("Micro Note", note.name))

	def test_erase_takes_call_attempts_with_it(self):
		customer = self._customer()
		attempt = self._call_attempt(customer)

		delete_customer(customer, mode="erase")

		self.assertFalse(frappe.db.exists("Micro Call Attempt", attempt.name))

	def test_erase_takes_an_unsent_draft_with_it(self):
		# A draft addressed to somebody being erased has nobody left to send to,
		# and its link would block the delete anyway.
		customer = self._customer()
		offer = self._offer(customer, status="Draft")

		delete_customer(customer, mode="erase")

		self.assertFalse(frappe.db.exists("Micro Offer Draft", offer.name))

	# --- retention ---

	def test_a_sent_offer_blocks_an_erase(self):
		customer = self._customer()
		self._offer(customer, status="Sent")

		with self.assertRaises(frappe.ValidationError):
			delete_customer(customer, mode="erase")

		self.assertTrue(frappe.db.exists("Contact", customer))

	def test_a_receipt_blocks_an_erase(self):
		customer = self._customer()
		self._receipt(customer)

		with self.assertRaises(frappe.ValidationError):
			delete_customer(customer, mode="erase")

		self.assertTrue(frappe.db.exists("Contact", customer))

	# --- preview ---

	def test_the_preview_says_what_would_go(self):
		customer = self._customer()
		self._note(customer)

		preview = get_delete_preview(customer)

		self.assertTrue(preview["can_erase"])
		self.assertEqual(preview["deletes"].get("Micro Note"), 1)

	def test_the_preview_names_the_blocker(self):
		customer = self._customer()
		self._receipt(customer)

		preview = get_delete_preview(customer)

		self.assertFalse(preview["can_erase"])
		self.assertEqual(preview["retention_blockers"][0]["doctype"], "Micro Receipt")

	# --- guards ---

	def test_an_unknown_mode_is_refused(self):
		customer = self._customer()

		with self.assertRaises(frappe.ValidationError):
			delete_customer(customer, mode="obliterate")

	def test_deleting_something_that_is_not_there_is_refused(self):
		with self.assertRaises(frappe.ValidationError):
			delete_customer(f"No Such Contact {self.tag}", mode="remove")

	# --- bulk ---

	def test_bulk_remove_takes_every_customer_out_of_micro(self):
		a, b = self._customer(), self._customer()

		result = bulk_delete_customers([a, b], mode="remove")

		self.assertEqual(sorted(result["succeeded"]), sorted([a, b]))
		self.assertEqual(result["failed"], [])
		self.assertFalse(frappe.db.get_value("Contact", a, "micro_status"))
		self.assertFalse(frappe.db.get_value("Contact", b, "micro_status"))

	def test_bulk_erase_skips_a_blocked_customer_but_takes_the_rest(self):
		blocked = self._customer()
		self._receipt(blocked)
		free = self._customer()

		result = bulk_delete_customers([blocked, free], mode="erase")

		self.assertEqual(result["succeeded"], [free])
		self.assertFalse(frappe.db.exists("Contact", free))
		self.assertTrue(frappe.db.exists("Contact", blocked))
		self.assertEqual(len(result["failed"]), 1)
		self.assertEqual(result["failed"][0]["customer"], blocked)

	def test_bulk_delete_accepts_a_json_string_of_ids(self):
		# The frontend sends the selection as a JSON-encoded string, same as any
		# other list parameter in this app.
		import json

		customer = self._customer()

		result = bulk_delete_customers(json.dumps([customer]), mode="remove")

		self.assertEqual(result["succeeded"], [customer])

	def test_bulk_delete_refuses_an_empty_selection(self):
		with self.assertRaises(frappe.ValidationError):
			bulk_delete_customers([], mode="remove")

	def test_bulk_delete_refuses_an_unknown_mode(self):
		customer = self._customer()

		with self.assertRaises(frappe.ValidationError):
			bulk_delete_customers([customer], mode="obliterate")
