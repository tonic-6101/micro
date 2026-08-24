# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""The matcher, tested without a database.

Every case here is a shape that showed up in the real contact list: German
spelling variants, phone formats, legal forms, and the two kinds of near-miss
that must *not* merge — a shared switchboard and a franchise branch.
"""

from frappe.tests.utils import FrappeTestCase

from micro.services.duplicates import (
	band_for,
	cologne_phonetic,
	display_name,
	normalize_email,
	normalize_organization,
	phone_key,
	score_pair,
)


def record(**values) -> dict:
	base = {
		"name": values.pop("id", "CONTACT"),
		"first_name": "",
		"last_name": "",
		"full_name": "",
		"company_name": "",
		"email_id": "",
		"phone": "",
		"mobile_no": "",
		"micro_contact_type": "Person",
		"micro_organization": "",
		"micro_status": "Potential",
		"micro_website": "",
		"micro_address": "",
		"micro_postal_code": "",
	}
	base.update(values)

	return base


def person(first: str, last: str, **values) -> dict:
	return record(first_name=first, last_name=last, full_name=f"{first} {last}", **values)


def org(name: str, **values) -> dict:
	return record(full_name=name, company_name=name, micro_contact_type="Organization", **values)


class TestNormalization(FrappeTestCase):
	def test_umlauts_fold_to_their_transliteration(self):
		self.assertEqual(cologne_phonetic("Müller"), cologne_phonetic("Mueller"))
		self.assertEqual(cologne_phonetic("Müller"), cologne_phonetic("Muller"))

	def test_cologne_phonetic_separates_unrelated_names(self):
		self.assertNotEqual(cologne_phonetic("Müller"), cologne_phonetic("Schmidt"))

	def test_cologne_phonetic_joins_names_that_sound_alike(self):
		self.assertEqual(cologne_phonetic("Meier"), cologne_phonetic("Mayer"))

	def test_a_name_of_only_h_has_no_code(self):
		# H is the one letter carrying no code of its own.
		self.assertEqual(cologne_phonetic("H"), "")

	def test_phone_formats_collapse_to_one_key(self):
		keys = {phone_key(value) for value in ("+49 171 1234567", "0049 171 1234567", "0171 1234567", "(0171) 123 45 67")}
		self.assertEqual(len(keys), 1)

	def test_a_number_too_short_to_identify_anyone_has_no_key(self):
		self.assertEqual(phone_key("123"), "")

	def test_email_is_lowercased_and_untagged(self):
		self.assertEqual(normalize_email("Info+CRM@Mueller-Bau.de"), "info@mueller-bau.de")

	def test_legal_forms_are_stripped_from_organizations(self):
		self.assertEqual(normalize_organization("Müller Bau GmbH"), normalize_organization("Müller Bau"))
		self.assertEqual(
			normalize_organization("Müller Bau UG (haftungsbeschränkt)"), normalize_organization("Müller Bau")
		)

	def test_a_company_called_only_by_a_legal_form_keeps_its_name(self):
		# Stripping everything would leave an empty string that matches every
		# other stripped-to-nothing record.
		self.assertEqual(normalize_organization("Co"), "co")

	def test_organizations_are_compared_without_their_legal_form(self):
		self.assertEqual(display_name(org("Müller Bau GmbH")), display_name(org("Müller Bau")))


class TestScoring(FrappeTestCase):
	def assertBand(self, expected, left, right):
		score, signals = score_pair(left, right)
		self.assertEqual(
			band_for(score),
			expected,
			f"scored {score:.3f} on {signals}",
		)

	# --- duplicates that must be caught ---

	def test_same_email_and_name_is_certain(self):
		self.assertBand(
			"Certain",
			person("Thomas", "Müller", email_id="t.mueller@bau.de"),
			person("Thomas", "Mueller", email_id="T.Mueller@bau.de"),
		)

	def test_same_phone_across_phone_and_mobile_fields_is_certain(self):
		# The same number routinely lands in the phone field on one record and
		# the mobile field on the other.
		self.assertBand(
			"Certain",
			person("Thomas", "Müller", phone="+49 171 1234567"),
			person("Thomas", "Mueller", mobile_no="0171 1234567"),
		)

	def test_an_identical_name_alone_is_worth_suggesting(self):
		# Roughly what an iPhone suggests on: name only, nothing else.
		self.assertBand("Possible", person("Thomas", "Müller"), person("Thomas", "Mueller"))

	def test_an_organization_differing_only_by_legal_form_is_likely(self):
		self.assertBand(
			"Likely",
			org("Müller Bau GmbH", micro_website="https://www.mueller-bau.de/"),
			org("Müller Bau", email_id="info@mueller-bau.de"),
		)

	def test_a_moved_business_still_matches_on_an_identical_name(self):
		# An exactly equal name plus a shared phone outweighs a stale postcode.
		self.assertBand(
			"Certain",
			org("Gebäudetechnik Karuth GmbH & Co. KG", phone="02662 464341", micro_postal_code="56459"),
			org("Gebäudetechnik Karuth GmbH & CO KG", phone="02662 464341", micro_postal_code="57518"),
		)

	# --- near misses that must NOT be merged ---

	def test_a_shared_switchboard_does_not_make_two_people_one(self):
		score, _ = score_pair(
			person("Thomas", "Müller", phone="02662 111111"),
			person("Anna", "Schmidt", phone="02662 111111"),
		)
		self.assertIsNone(band_for(score))

	def test_franchise_branches_are_not_certain(self):
		# Five hallo.solar branches share a head office number, a domain and
		# every word of a long name; only the town differs.
		score, signals = score_pair(
			org("hallo.solar Viersen - Ihre Experten für Photovoltaik", phone="0221 1234567", micro_website="hallo.solar"),
			org("hallo.solar Wiehl - Ihre Experten für Photovoltaik", phone="0221 1234567", micro_website="hallo.solar"),
		)
		self.assertIn("-distinct_name", signals)
		self.assertNotEqual(band_for(score), "Certain")

	def test_a_branch_marker_on_one_side_alone_is_distinguishing(self):
		score, signals = score_pair(
			org("Remotex Gebäudetechnik GmbH", phone="0561 111111"),
			org("Remotex Gebäudetechnik GmbH (NL Kassel)", phone="0561 111111"),
		)
		self.assertIn("-distinct_name", signals)
		self.assertNotEqual(band_for(score), "Certain")

	def test_spelling_variants_are_not_treated_as_distinguishing(self):
		# Meier and Maier are one surname spelled twice, not two words.
		_, signals = score_pair(
			person("Anna", "Meier", phone="0171 1234567"),
			person("Anna", "Maier", phone="0171 1234567"),
		)
		self.assertNotIn("-distinct_name", signals)

	def test_a_person_is_never_their_own_company(self):
		score, _ = score_pair(person("Thomas", "Müller"), org("Müller GmbH"))
		self.assertIsNone(band_for(score))

	def test_a_member_and_their_organization_are_never_a_duplicate(self):
		# The pair that would otherwise score highest: same surname, same
		# switchboard, same domain. The link says outright they are two records
		# on purpose, and that beats every signal.
		employer = org("Müller Bau GmbH", id="ORG", phone="02662 111111", email_id="info@mueller-bau.de")
		employee = person(
			"Thomas",
			"Müller",
			id="PERSON",
			micro_organization="ORG",
			phone="02662 111111",
			email_id="info@mueller-bau.de",
		)

		score, signals = score_pair(employee, employer)
		self.assertEqual(signals, ["-same_organization"])
		self.assertIsNone(band_for(score))

	def test_the_membership_suppression_does_not_depend_on_argument_order(self):
		employer = org("Müller Bau GmbH", id="ORG", email_id="info@mueller-bau.de")
		employee = person("Thomas", "Müller", id="PERSON", micro_organization="ORG", email_id="info@mueller-bau.de")

		score, _ = score_pair(employer, employee)
		self.assertIsNone(band_for(score))

	def test_a_link_to_some_other_organization_suppresses_nothing(self):
		# Membership only excuses the pair it actually joins.
		employer = org("Müller Bau GmbH", id="ORG", email_id="info@mueller-bau.de")
		stranger = person(
			"Thomas", "Müller", id="PERSON", micro_organization="OTHER", email_id="info@mueller-bau.de"
		)

		_, signals = score_pair(stranger, employer)
		self.assertNotIn("-same_organization", signals)

	def test_unrelated_contacts_score_nothing(self):
		score, _ = score_pair(
			person("Thomas", "Müller", email_id="a@x.de"),
			person("Petra", "Wagner", email_id="b@y.de"),
		)
		self.assertIsNone(band_for(score))

	def test_a_shared_free_mail_host_is_not_evidence(self):
		# Half a contact list is on gmx.de.
		_, signals = score_pair(
			person("Thomas", "Müller", email_id="thomas@gmx.de"),
			person("Petra", "Wagner", email_id="petra@gmx.de"),
		)
		self.assertNotIn("domain", signals)
