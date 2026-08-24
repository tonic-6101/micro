# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""People, the organizations they belong to, and the link between the two.

`company_name` was free text: the employer typed on a person and the
organization record of the same name were unrelated strings. The link makes the
relation answerable in both directions — "who is my contact at Müller Bau?" and
"who does Thomas work for?" — and the rules below are what keep it honest.
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from micro.api.customers import (
	create_customer,
	delete_customer,
	get_customer,
	get_customers,
	get_organization_members,
	set_customer_organization,
)


class TestCustomerOrganizationAPI(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.db.set_single_value("Micro Settings", "customer_limit", 0)
		self.tag = frappe.generate_hash(length=8)

	def _organization(self, name: str | None = None) -> str:
		result = create_customer(
			first_name=name or f"ZZ Org {self.tag}",
			contact_type="Organization",
			organization=name or f"ZZ Org {self.tag}",
		)

		return result["customer"]["name"]

	def _person(self, first: str = "ZZ", last: str | None = None, **values) -> str:
		result = create_customer(
			first_name=first,
			last_name=last or f"Person {self.tag}",
			contact_type="Person",
			**values,
		)

		return result["customer"]["name"]

	# --- the link itself ---

	def test_a_person_can_be_created_already_linked(self):
		organization = self._organization()
		person = self._person(organization_contact=organization)

		self.assertEqual(frappe.db.get_value("Contact", person, "micro_organization"), organization)

	def test_the_link_mirrors_the_organization_name_into_company_name(self):
		# Frappe core, the kanban cards and the print formats all read
		# `company_name`; a link that left them showing a different employer
		# would be worse than no link at all.
		organization = self._organization(f"Müller Bau {self.tag}")
		person = self._person(organization_contact=organization)

		self.assertEqual(
			frappe.db.get_value("Contact", person, "company_name"),
			frappe.db.get_value("Contact", organization, "company_name"),
		)

	def test_the_mirror_overrides_a_free_text_employer(self):
		# Both were given; the record wins over the string.
		organization = self._organization(f"Müller Bau {self.tag}")
		person = self._person(organization="Typed By Hand", organization_contact=organization)

		self.assertEqual(
			frappe.db.get_value("Contact", person, "company_name"),
			frappe.db.get_value("Contact", organization, "company_name"),
		)

	def test_a_free_text_employer_survives_when_there_is_no_record(self):
		# Most contacts have no organization of their own, and the field the
		# user typed is all there is.
		person = self._person(organization="Nowhere GmbH")

		self.assertEqual(frappe.db.get_value("Contact", person, "company_name"), "Nowhere GmbH")
		self.assertFalse(frappe.db.get_value("Contact", person, "micro_organization"))

	# --- rules that keep the link honest ---

	def test_a_contact_cannot_belong_to_itself(self):
		person = self._person()
		contact = frappe.get_doc("Contact", person)
		contact.micro_organization = person

		self.assertRaises(frappe.ValidationError, contact.save)

	def test_an_organization_cannot_belong_to_another_organization(self):
		parent = self._organization(f"ZZ Parent {self.tag}")
		child = frappe.get_doc("Contact", self._organization(f"ZZ Child {self.tag}"))
		child.micro_organization = parent

		self.assertRaises(frappe.ValidationError, child.save)

	def test_a_person_cannot_be_used_as_an_organization(self):
		colleague = self._person("ZZ Colleague")
		contact = frappe.get_doc("Contact", self._person("ZZ Other"))
		contact.micro_organization = colleague

		self.assertRaises(frappe.ValidationError, contact.save)

	def test_a_link_to_a_contact_that_does_not_exist_is_refused(self):
		contact = frappe.get_doc("Contact", self._person())
		contact.micro_organization = f"No Such Contact {self.tag}"

		self.assertRaises(Exception, contact.save)

	# --- reading it back ---

	def test_a_person_reads_back_their_organization_named(self):
		# A bare docname would make the page useless; the card carries a name.
		organization = self._organization(f"Müller Bau {self.tag}")
		person = self._person(organization_contact=organization)

		card = get_customer(person)["organization"]
		self.assertIsNotNone(card)
		self.assertEqual(card["name"], organization)
		self.assertTrue(card.get("company_name") or card.get("full_name"))

	def test_a_person_with_no_organization_reads_back_none(self):
		self.assertIsNone(get_customer(self._person())["organization"])

	def test_an_organization_reads_back_its_people(self):
		organization = self._organization()
		person = self._person(organization_contact=organization)

		detail = get_customer(organization)
		self.assertEqual([member["name"] for member in detail["members"]], [person])
		self.assertIsNone(detail["organization"])

	def test_a_person_carries_no_members(self):
		self.assertEqual(get_customer(self._person())["members"], [])

	def test_members_are_listed_by_name_with_a_total(self):
		organization = self._organization()
		zeta = self._person("ZZ Zeta", organization_contact=organization)
		alpha = self._person("ZZ Alpha", organization_contact=organization)

		result = get_organization_members(organization)
		self.assertEqual(result["total"], 2)
		self.assertEqual([member["name"] for member in result["members"]], [alpha, zeta])

	def test_the_customer_list_carries_the_link(self):
		organization = self._organization()
		person = self._person(organization_contact=organization)

		rows = get_customers(filters={"name": person})["customers"]
		self.assertEqual(rows[0]["micro_organization"], organization)

	# --- attaching and detaching ---

	def test_a_person_can_be_attached_after_the_fact(self):
		organization = self._organization()
		person = self._person()

		set_customer_organization(person, organization)
		self.assertEqual(frappe.db.get_value("Contact", person, "micro_organization"), organization)

	def test_detaching_leaves_the_employer_standing(self):
		# Dropping a relation is not a claim that the person never worked there.
		organization = self._organization(f"Müller Bau {self.tag}")
		person = self._person(organization_contact=organization)
		employer = frappe.db.get_value("Contact", person, "company_name")

		set_customer_organization(person, None)

		self.assertFalse(frappe.db.get_value("Contact", person, "micro_organization"))
		self.assertEqual(frappe.db.get_value("Contact", person, "company_name"), employer)

	# --- removal ---

	def test_erasing_an_organization_does_not_take_its_people_with_it(self):
		organization = self._organization(f"Müller Bau {self.tag}")
		person = self._person(organization_contact=organization)
		employer = frappe.db.get_value("Contact", person, "company_name")

		delete_customer(organization, mode="erase")

		self.assertFalse(frappe.db.exists("Contact", organization))
		self.assertTrue(frappe.db.exists("Contact", person))
		self.assertFalse(frappe.db.get_value("Contact", person, "micro_organization"))
		self.assertEqual(frappe.db.get_value("Contact", person, "company_name"), employer)
