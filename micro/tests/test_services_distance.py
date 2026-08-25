# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""How far away a lead sits.

Distances are straight-line and worked out from a bundled postal-code table,
so these tests can assert real numbers against known German geography without
touching the network.
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from micro.services.distance import (
	attach_distance,
	centroid,
	distance_km,
	haversine_km,
	origin_centroid,
)

# Cologne and Berlin are ~475 km apart in a straight line — the textbook check.
KOELN = "50667"
BERLIN = "10115"
KOELN_NEIGHBOUR = "50668"
NOT_A_PLZ = "99999999"


class TestDistanceService(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.db.set_single_value("Micro Settings", "company_postal_code", KOELN)

	# --- the table ---

	def test_a_known_postal_code_resolves(self):
		lat, lon = centroid(BERLIN)

		self.assertAlmostEqual(lat, 52.53, places=1)
		self.assertAlmostEqual(lon, 13.38, places=1)

	def test_a_postal_code_that_does_not_exist_resolves_to_nothing(self):
		self.assertIsNone(centroid("00000"))

	def test_a_four_digit_code_is_not_guessed_at(self):
		# Austrian and Swiss codes are four digits and the contact's country is
		# almost never set — answering would mean answering wrongly.
		self.assertIsNone(centroid("8032"))

	def test_junk_is_not_a_postal_code(self):
		for value in (None, "", "   ", "abcde", NOT_A_PLZ, "5066"):
			self.assertIsNone(centroid(value), value)

	# --- the maths ---

	def test_the_distance_from_a_place_to_itself_is_zero(self):
		self.assertEqual(haversine_km(centroid(KOELN), centroid(KOELN)), 0)

	def test_cologne_to_berlin_is_about_475_km(self):
		km = haversine_km(centroid(KOELN), centroid(BERLIN))

		self.assertAlmostEqual(km, 475, delta=15)

	def test_the_distance_is_the_same_in_both_directions(self):
		there = haversine_km(centroid(KOELN), centroid(BERLIN))
		back = haversine_km(centroid(BERLIN), centroid(KOELN))

		self.assertAlmostEqual(there, back, places=6)

	# --- against the configured origin ---

	def test_the_origin_comes_from_settings(self):
		self.assertEqual(origin_centroid(), centroid(KOELN))

	def test_a_lead_across_the_country_reports_the_distance(self):
		self.assertAlmostEqual(distance_km(BERLIN), 475, delta=15)

	def test_a_neighbouring_postal_code_rounds_to_nearby(self):
		self.assertLess(distance_km(KOELN_NEIGHBOUR), 5)

	def test_a_contact_in_the_same_postal_code_is_zero_km_away(self):
		# Zero is a real answer, not a missing one — the card has to tell them
		# apart, so this stays an int rather than becoming falsy-None.
		self.assertEqual(distance_km(KOELN), 0)

	def test_an_unknown_postal_code_has_no_distance(self):
		self.assertIsNone(distance_km(NOT_A_PLZ))

	def test_without_a_company_postal_code_nothing_has_a_distance(self):
		frappe.db.set_single_value("Micro Settings", "company_postal_code", "")

		self.assertIsNone(origin_centroid())
		self.assertIsNone(distance_km(BERLIN))

	def test_a_nonsense_company_postal_code_is_not_an_origin(self):
		frappe.db.set_single_value("Micro Settings", "company_postal_code", "Köln")

		self.assertIsNone(distance_km(BERLIN))

	# --- annotating a batch ---

	def test_attach_distance_annotates_every_row(self):
		rows = [
			{"micro_postal_code": BERLIN},
			{"micro_postal_code": KOELN},
			{"micro_postal_code": None},
		]

		attach_distance(rows)

		self.assertAlmostEqual(rows[0]["distance_km"], 475, delta=15)
		self.assertEqual(rows[1]["distance_km"], 0)
		self.assertIsNone(rows[2]["distance_km"])

	def test_attach_distance_survives_an_empty_batch(self):
		rows = []
		attach_distance(rows)

		self.assertEqual(rows, [])

	def test_attach_distance_sets_the_key_even_with_no_origin(self):
		# The frontend distinguishes "no distance" from "field absent", so the
		# key has to be there either way.
		frappe.db.set_single_value("Micro Settings", "company_postal_code", "")
		rows = [{"micro_postal_code": BERLIN}]

		attach_distance(rows)

		self.assertIn("distance_km", rows[0])
		self.assertIsNone(rows[0]["distance_km"])
