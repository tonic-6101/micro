# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Suggesting, merging and undoing.

The merge is the only destructive action in an otherwise additive app, and its
order of operations is not obvious: Frappe's rename repoints the links and then
*deletes* the loser, taking its email and phone child rows with it. Most of what
is tested here is that nothing falls through that gap.
"""

import json

import frappe
from frappe.tests.utils import FrappeTestCase

from micro.api.duplicates import (
	check_duplicates,
	dismiss_pair,
	get_duplicate_pairs,
	get_duplicate_summary,
	merge_contacts,
	scan_for_duplicates,
	undo_merge,
)


class TestDuplicatesAPI(FrappeTestCase):
	"""Fixtures are unique per test — the runner rolls back per class, not per
	test, so a shared name would dedupe against the previous test's contacts.
	"""

	def setUp(self):
		super().setUp()
		frappe.db.set_single_value("Micro Settings", "customer_limit", 0)
		self.tag = frappe.generate_hash(length=8)
		self.digits = str(int(self.tag, 16))[:7].ljust(7, "0")

	def _contact(self, first_name, last_name=None, **values):
		"""Built through the app's own path, not by hand.

		`email_id` and `phone` on a Contact are read back out of the `email_ids`
		and `phone_nos` child tables — assigning them directly leaves both empty,
		which is exactly the trap the merge has to survive.
		"""
		from micro.api.customers import create_customer

		result = create_customer(
			first_name=first_name,
			last_name=last_name,
			contact_type="Person" if last_name else "Organization",
			**values,
		)

		return frappe.get_doc("Contact", result["customer"]["name"])

	def _pair_of(self, a, b):
		first, second = sorted((a.name, b.name))
		name = frappe.db.exists("Micro Duplicate Pair", {"contact_a": first, "contact_b": second})

		return frappe.get_doc("Micro Duplicate Pair", name) if name else None

	# --- live check ---

	def test_a_typed_contact_finds_its_twin_before_it_is_saved(self):
		self._contact(f"Thomas {self.tag}", "Müller", email=f"t{self.digits}@bau-test.de")

		result = check_duplicates(
			first_name=f"Thomas {self.tag}",
			last_name="Mueller",
			email=f"T{self.digits}@Bau-Test.de",
		)

		self.assertEqual(len(result["matches"]), 1)
		self.assertEqual(result["matches"][0]["band"], "Certain")

	def test_the_live_check_writes_nothing(self):
		self._contact(f"Thomas {self.tag}", "Müller", email=f"t{self.digits}@bau-test.de")
		before = frappe.db.count("Micro Duplicate Pair")

		check_duplicates(first_name=f"Thomas {self.tag}", last_name="Mueller")

		self.assertEqual(frappe.db.count("Micro Duplicate Pair"), before)

	def test_an_empty_form_is_not_a_query(self):
		self.assertEqual(check_duplicates()["matches"], [])

	def test_the_contact_being_edited_is_excluded_from_its_own_check(self):
		contact = self._contact(f"Thomas {self.tag}", "Müller", email=f"t{self.digits}@bau-test.de")

		result = check_duplicates(
			first_name=f"Thomas {self.tag}",
			last_name="Müller",
			email=f"t{self.digits}@bau-test.de",
			exclude=contact.name,
		)

		self.assertEqual(result["matches"], [])

	# --- scan ---

	def test_the_scan_records_a_pair_once(self):
		self._contact(f"Thomas {self.tag}", "Müller", email=f"t{self.digits}@bau-test.de")
		self._contact(f"Thomas {self.tag}", "Mueller", email=f"T{self.digits}@bau-test.de")

		scan_for_duplicates()
		scan_for_duplicates()

		pairs = frappe.get_all(
			"Micro Duplicate Pair",
			filters={"contact_a": ["like", f"%{self.tag}%"]},
		)
		self.assertEqual(len(pairs), 1)

	def test_a_dismissed_pair_does_not_come_back(self):
		a = self._contact(f"Thomas {self.tag}", "Müller", email=f"t{self.digits}@bau-test.de")
		b = self._contact(f"Thomas {self.tag}", "Mueller", email=f"T{self.digits}@bau-test.de")

		scan_for_duplicates()
		dismiss_pair(self._pair_of(a, b).name)
		scan_for_duplicates()

		self.assertEqual(self._pair_of(a, b).status, "Dismissed")

	def test_a_dismissed_pair_returns_once_a_record_changes(self):
		a = self._contact(f"Thomas {self.tag}", "Müller", email=f"t{self.digits}@bau-test.de")
		b = self._contact(f"Thomas {self.tag}", "Mueller", email=f"T{self.digits}@bau-test.de")

		scan_for_duplicates()
		dismiss_pair(self._pair_of(a, b).name)

		b.reload()
		b.add_phone(f"0171{self.digits}", is_primary_phone=1)
		b.save(ignore_permissions=True)
		scan_for_duplicates()

		self.assertEqual(self._pair_of(a, b).status, "Open")

	def test_the_summary_counts_what_is_open(self):
		self._contact(f"Thomas {self.tag}", "Müller", email=f"t{self.digits}@bau-test.de")
		self._contact(f"Thomas {self.tag}", "Mueller", email=f"T{self.digits}@bau-test.de")

		scan_for_duplicates()

		self.assertGreaterEqual(get_duplicate_summary()["open"], 1)

	def test_pairs_are_listed_with_both_records_attached(self):
		self._contact(f"Thomas {self.tag}", "Müller", email=f"t{self.digits}@bau-test.de")
		self._contact(f"Thomas {self.tag}", "Mueller", email=f"T{self.digits}@bau-test.de")
		scan_for_duplicates()

		listed = get_duplicate_pairs(limit_page_length=100)
		mine = [pair for pair in listed["pairs"] if self.tag in pair["contact_a"]["first_name"]]

		self.assertEqual(len(mine), 1)
		self.assertTrue(mine[0]["reasons"])
		self.assertIn("full_name", mine[0]["contact_b"])

	# --- merge ---

	def test_merging_keeps_the_phone_number_only_the_loser_had(self):
		# The trap: rename_doc deletes the loser and cascades its child rows, so
		# anything not copied across first is gone for good.
		winner = self._contact(f"Thomas {self.tag}", "Müller", email=f"t{self.digits}@bau-test.de")
		loser = self._contact(f"Thomas {self.tag}", "Mueller", phone=f"0171{self.digits}")

		merge_contacts(winner.name, loser.name)

		winner.reload()
		self.assertIn(f"0171{self.digits}", [row.phone for row in winner.phone_nos])

	def test_merging_keeps_the_email_only_the_loser_had(self):
		winner = self._contact(f"Thomas {self.tag}", "Müller", phone=f"0171{self.digits}")
		loser = self._contact(f"Thomas {self.tag}", "Mueller", email=f"t{self.digits}@bau-test.de")

		merge_contacts(winner.name, loser.name)

		winner.reload()
		self.assertIn(f"t{self.digits}@bau-test.de", [row.email_id for row in winner.email_ids])

	def test_merging_never_overwrites_what_the_survivor_already_says(self):
		winner = self._contact(f"Thomas {self.tag}", "Müller", city="Pottum")
		loser = self._contact(f"Thomas {self.tag}", "Mueller", city="Breitscheid")

		merge_contacts(winner.name, loser.name)

		winner.reload()
		self.assertEqual(winner.micro_city, "Pottum")

	def test_merging_fills_a_blank_on_the_survivor(self):
		winner = self._contact(f"Thomas {self.tag}", "Müller")
		loser = self._contact(f"Thomas {self.tag}", "Mueller", city="Breitscheid")

		merge_contacts(winner.name, loser.name)

		winner.reload()
		self.assertEqual(winner.micro_city, "Breitscheid")

	def test_the_loser_is_gone_afterwards(self):
		winner = self._contact(f"Thomas {self.tag}", "Müller")
		loser = self._contact(f"Thomas {self.tag}", "Mueller")

		merge_contacts(winner.name, loser.name)

		self.assertFalse(frappe.db.exists("Contact", loser.name))

	def test_documents_follow_the_surviving_contact(self):
		winner = self._contact(f"Thomas {self.tag}", "Müller")
		loser = self._contact(f"Thomas {self.tag}", "Mueller")
		note = frappe.get_doc(
			{
				"doctype": "Micro Note",
				"subject": f"_Test {self.tag}",
				"content": "<p>x</p>",
				"date": "2026-03-01",
				"contact": loser.name,
			}
		).insert(ignore_permissions=True)

		merge_contacts(winner.name, loser.name)

		self.assertEqual(frappe.db.get_value("Micro Note", note.name, "contact"), winner.name)

	def test_a_contact_cannot_be_merged_into_itself(self):
		contact = self._contact(f"Thomas {self.tag}", "Müller")

		with self.assertRaises(frappe.ValidationError):
			merge_contacts(contact.name, contact.name)

	def test_merging_closes_the_suggestion(self):
		a = self._contact(f"Thomas {self.tag}", "Müller", email=f"t{self.digits}@bau-test.de")
		b = self._contact(f"Thomas {self.tag}", "Mueller", email=f"T{self.digits}@bau-test.de")
		scan_for_duplicates()
		pair = self._pair_of(a, b)

		merge_contacts(a.name, b.name, pair=pair.name)

		pair.reload()
		self.assertEqual(pair.status, "Merged")
		self.assertEqual(pair.merged_into, a.name)

	# --- undo ---

	def test_a_merge_can_be_undone(self):
		winner = self._contact(f"Thomas {self.tag}", "Müller", email=f"t{self.digits}@bau-test.de")
		loser = self._contact(f"Thomas {self.tag}", "Mueller", email=f"T{self.digits}@bau-test.de")
		scan_for_duplicates()
		pair = self._pair_of(winner, loser)
		merge_contacts(winner.name, loser.name, pair=pair.name)

		result = undo_merge(pair.name)

		self.assertEqual(result["restored"], loser.name)
		self.assertTrue(frappe.db.exists("Contact", loser.name))

	def test_undo_puts_the_documents_back(self):
		winner = self._contact(f"Thomas {self.tag}", "Müller", email=f"t{self.digits}@bau-test.de")
		loser = self._contact(f"Thomas {self.tag}", "Mueller", email=f"T{self.digits}@bau-test.de")
		note = frappe.get_doc(
			{
				"doctype": "Micro Note",
				"subject": f"_Test {self.tag}",
				"content": "<p>x</p>",
				"date": "2026-03-01",
				"contact": loser.name,
			}
		).insert(ignore_permissions=True)
		scan_for_duplicates()
		pair = self._pair_of(winner, loser)
		merge_contacts(winner.name, loser.name, pair=pair.name)

		undo_merge(pair.name)

		self.assertEqual(frappe.db.get_value("Micro Note", note.name, "contact"), loser.name)

	def test_a_merge_that_was_never_made_cannot_be_undone(self):
		a = self._contact(f"Thomas {self.tag}", "Müller", email=f"t{self.digits}@bau-test.de")
		b = self._contact(f"Thomas {self.tag}", "Mueller", email=f"T{self.digits}@bau-test.de")
		scan_for_duplicates()
		pair = self._pair_of(a, b)

		with self.assertRaises(frappe.ValidationError):
			undo_merge(pair.name)

	def test_the_snapshot_holds_the_record_that_was_merged_away(self):
		winner = self._contact(f"Thomas {self.tag}", "Müller", email=f"t{self.digits}@bau-test.de")
		loser = self._contact(f"Thomas {self.tag}", "Mueller", email=f"T{self.digits}@bau-test.de")
		scan_for_duplicates()
		pair = self._pair_of(winner, loser)

		merge_contacts(winner.name, loser.name, pair=pair.name)

		pair.reload()
		snapshot = json.loads(pair.snapshot)
		self.assertEqual(snapshot["contact"]["name"], loser.name)
