# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Turn the employer typed on each person into a link to the organization.

`Contact.company_name` was the only place a person's employer could go, and it
is free text: "Müller Bau GmbH" on a person and the organization record called
"Müller Bau GmbH" were unrelated strings. Wherever an organization with that name
already exists, the two are joined up here.

Conservative on purpose. A person is linked only when the normalized company name
matches exactly one organization — the same normalization the duplicate detector
uses, so "Müller Bau GmbH" finds "Müller Bau". Ambiguous names are left alone:
a wrong employer is worse than a missing one, and the field the user typed stays
either way.
"""

import frappe

from micro.services.duplicates import normalize_organization


def execute():
	if not frappe.db.has_column("Contact", "micro_organization"):
		return

	organizations = _organizations_by_name()
	if not organizations:
		return

	linked = 0
	for person in frappe.get_all(
		"Contact",
		filters={
			"micro_contact_type": "Person",
			"company_name": ["is", "set"],
			"micro_organization": ["is", "not set"],
		},
		fields=["name", "company_name"],
	):
		key = normalize_organization(person.company_name)
		matches = organizations.get(key)

		# Exactly one candidate, or the link would be a guess.
		if not matches or len(matches) != 1:
			continue

		frappe.db.set_value(
			"Contact", person.name, "micro_organization", matches[0], update_modified=False
		)
		linked += 1

	if linked:
		print(f"Linked {linked} people to their organization")


def _organizations_by_name() -> dict[str, list[str]]:
	"""Organization contacts bucketed by their normalized name."""
	buckets: dict[str, list[str]] = {}

	for organization in frappe.get_all(
		"Contact",
		filters={"micro_contact_type": "Organization"},
		fields=["name", "full_name", "company_name"],
	):
		key = normalize_organization(organization.company_name or organization.full_name)
		if key:
			buckets.setdefault(key, []).append(organization.name)

	return buckets
