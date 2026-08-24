# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Bulk contact import — Zone 1 only.

Contacts carry no financial data, so importing them needs no guardrails. Nothing
here touches receipts, offers or invoice drafts: bulk-loading financial documents
is Zone 2 territory and stays out on purpose.

Rows arrive already parsed — the frontend reads CSV or JSONL and posts batches of
plain dicts, so a 3,000-row file never has to fit in one request and the user
gets progress instead of a spinner.
"""

import re

import frappe
from frappe import _

from micro.api.customers import create_customer
from micro.limits import DEFAULT_CUSTOMER_LIMIT, get_limit
from micro.services.duplicates import ContactIndex, display_name, normalize_email, phone_key

# What an imported column can be pointed at. `address_full` is the odd one out:
# it takes "Gartenstraße 3, 56459 Pottum" and splits it three ways.
IMPORT_FIELDS = [
	{"field": "name", "label": "Name", "hints": ["name", "company", "firma", "business", "title"]},
	{"field": "last_name", "label": "Last Name", "hints": ["last_name", "lastname", "nachname"]},
	{"field": "organization", "label": "Organization", "hints": ["organization", "company_name", "firma"]},
	{"field": "email", "label": "Email", "hints": ["email", "e-mail", "mail", "email_id"]},
	{"field": "phone", "label": "Phone", "hints": ["phone", "phones", "telefon", "tel"]},
	{"field": "mobile", "label": "Mobile", "hints": ["mobile", "mobil", "handy", "cell"]},
	{"field": "website", "label": "Website", "hints": ["website", "site", "url", "web", "homepage"]},
	{"field": "address_full", "label": "Address (street, postcode city)", "hints": ["address", "adresse"]},
	{"field": "address", "label": "Street", "hints": ["street", "strasse", "straße"]},
	{"field": "postal_code", "label": "Postal Code", "hints": ["postal_code", "plz", "zip", "postcode"]},
	{"field": "city", "label": "City", "hints": ["city", "ort", "stadt"]},
	{"field": "country", "label": "Country", "hints": ["country", "land"]},
	{"field": "notes", "label": "Notes", "hints": ["notes", "notiz", "description", "categories", "tags"]},
]

DEDUPE_KEYS = ("email", "phone", "name", "none")

# Frappe Data columns hold 140 characters. Scraped sites overrun it — one long
# URL must not cost the whole business, and a truncated URL is worse than none.
DATA_FIELD_LIMIT = 140
LENGTH_LIMITED = frozenset(
	{"first_name", "last_name", "organization", "email", "phone", "mobile", "website", "city", "postal_code"}
)

# "Gartenstraße 3, 56459 Pottum" and also the street-less "35767 Breitscheid".
ADDRESS_PATTERN = re.compile(r"^\s*(?:(?P<street>.+?),\s*)?(?P<postal>\d{4,5})\s+(?P<city>.+?)\s*$")

# Fields an existing contact may have filled in from an import when it is empty.
FILLABLE_ON_UPDATE = (
	"micro_website",
	"micro_address",
	"micro_city",
	"micro_postal_code",
	"micro_country",
	"micro_notes",
)


@frappe.whitelist()
def get_import_setup() -> dict:
	"""Target fields and how much room is left under the customer limit."""
	frappe.has_permission("Contact", "create", throw=True)

	return {
		"fields": IMPORT_FIELDS,
		"dedupe_keys": list(DEDUPE_KEYS),
		"capacity": get_capacity(),
	}


@frappe.whitelist()
def get_capacity() -> dict:
	"""How many more Micro contacts fit before the community limit bites.

	Worth knowing *before* a 3,000-row import rather than at row 79.
	"""
	frappe.has_permission("Contact", throw=True)

	limit = get_limit("customer_limit", DEFAULT_CUSTOMER_LIMIT)
	used = frappe.db.count("Contact", {"micro_status": ["is", "set"]})

	return {
		"limit": limit,
		"used": used,
		"remaining": max(limit - used, 0) if limit > 0 else None,
		"unlimited": limit <= 0,
	}


@frappe.whitelist()
def import_contacts(
	rows: list | str,
	mapping: dict | str,
	contact_type: str = "Organization",
	status: str = "Potential",
	source: str = "Import",
	dedupe_by: str = "phone",
	on_duplicate: str = "skip",
	create_leads: bool = False,
	pipeline: str | None = None,
	stage: str | None = None,
) -> dict:
	"""Import one batch of rows. Returns an outcome per row, never a bare count."""
	frappe.has_permission("Contact", "create", throw=True)

	rows = frappe.parse_json(rows) if isinstance(rows, str) else rows
	mapping = frappe.parse_json(mapping) if isinstance(mapping, str) else mapping

	if dedupe_by not in DEDUPE_KEYS:
		frappe.throw(_("Unknown duplicate check: {0}").format(dedupe_by))
	if create_leads and not pipeline:
		frappe.throw(_("Choose a pipeline for the leads, or turn lead creation off."))

	# Suppresses the per-contact health-score job. Our own flag rather than
	# frappe.flags.in_import, which would also stop DocType defaults being set.
	was_bulk_import = frappe.flags.get("micro_bulk_import")
	frappe.flags.micro_bulk_import = True

	try:
		return _import_rows(
			rows,
			mapping,
			contact_type,
			status,
			source,
			dedupe_by,
			on_duplicate,
			create_leads,
			pipeline,
			stage,
		)
	finally:
		frappe.flags.micro_bulk_import = was_bulk_import


def _import_rows(
	rows: list,
	mapping: dict,
	contact_type: str,
	status: str,
	source: str,
	dedupe_by: str,
	on_duplicate: str,
	create_leads: bool,
	pipeline: str | None,
	stage: str | None,
) -> dict:
	capacity = get_capacity()
	# One query for the whole batch instead of one per row. A 3,000-row file used
	# to issue 3,000 `exists()` calls; contacts created along the way are added
	# to the index as they go, so rows still dedupe against their own file.
	contact_index = ContactIndex(micro_only=False) if dedupe_by != "none" else ContactIndex(records=[])
	created = 0
	skipped = 0
	updated = 0
	leads_created = 0
	# Adopting a contact from another app into Micro spends the same quota that
	# creating one does — `contact.save()` never reaches the insert-time check.
	consumed = 0
	failures: list[dict] = []
	warnings: list[dict] = []

	for index, row in enumerate(rows):
		if not capacity["unlimited"] and consumed >= (capacity["remaining"] or 0):
			# Stop cleanly rather than let every remaining row throw the same error.
			return _result(
				created,
				updated,
				skipped,
				failures,
				warnings,
				limit_reached=True,
				leads_created=leads_created,
			)

		values, dropped = _map_row(row, mapping)
		if not values.get("first_name"):
			failures.append({"row": index, "error": _("No name in this row")})
			continue
		for field in dropped:
			warnings.append({"row": index, "field": field, "reason": _("Too long, left empty")})

		existing = _find_duplicate(contact_index, values, dedupe_by, contact_type)
		if existing:
			if on_duplicate == "update":
				if _fill_blanks(existing, values, status, source):
					consumed += 1
				updated += 1
			else:
				skipped += 1
			# The contact is a duplicate; the campaign is not. A second list run
			# over people you already know is exactly how a follow-up campaign
			# starts, so they still get a lead — unless they are already open in
			# this pipeline, which `_open_lead` checks.
			if create_leads and _add_import_lead(existing, values, pipeline, stage, source):
				leads_created += 1
			continue

		savepoint = "micro_import_row"
		frappe.db.savepoint(savepoint)
		try:
			result = create_customer(
				contact_type=contact_type,
				status=status,
				source=source,
				**values,
			)
			if create_leads and _add_import_lead(
				result["customer"].get("name"), values, pipeline, stage, source
			):
				leads_created += 1
			contact_index.add({**_as_record(values, contact_type), "name": result["customer"].get("name")})
			created += 1
			consumed += 1
		except Exception as exc:
			frappe.db.rollback(save_point=savepoint)
			failures.append({"row": index, "error": str(exc)})

	return _result(created, updated, skipped, failures, warnings, leads_created=leads_created)


def _result(created, updated, skipped, failures, warnings, limit_reached=False, leads_created=0) -> dict:
	return {
		"created": created,
		"updated": updated,
		"skipped": skipped,
		"leads_created": leads_created,
		"failed": len(failures),
		"failures": failures[:50],
		"warnings": warnings[:50],
		"warned": len(warnings),
		"limit_reached": limit_reached,
		"capacity": get_capacity(),
	}


def _map_row(row: dict, mapping: dict) -> tuple[dict, list[str]]:
	"""Turn one source row into create_customer kwargs.

	Returns the values and the names of any fields dropped for being too long.
	"""
	values: dict = {}
	dropped: list[str] = []

	for target, column in mapping.items():
		if not column:
			continue
		raw = row.get(column)
		text = "" if raw is None else str(raw).strip()
		if not text:
			continue

		if target in LENGTH_LIMITED and len(text) > DATA_FIELD_LIMIT:
			dropped.append(target)
			continue

		if target == "name":
			values["first_name"] = text
		elif target == "address_full":
			values.update(_split_address(text))
		else:
			values[target] = text

	# An organization's name belongs in both places: it is the contact's whole
	# name and its company at the same time.
	if values.get("first_name") and not values.get("organization"):
		values["organization"] = values["first_name"]

	return values, dropped


def _split_address(value: str) -> dict:
	"""Split a German address; keep it whole when it does not fit the pattern."""
	match = ADDRESS_PATTERN.match(value)
	if not match:
		return {"address": value}

	parts = {"postal_code": match.group("postal"), "city": match.group("city")}
	if match.group("street"):
		parts["address"] = match.group("street")

	return parts


def _as_record(values: dict, contact_type: str) -> dict:
	"""An import row in the shape the matcher compares."""
	full_name = " ".join(part for part in (values.get("first_name"), values.get("last_name")) if part)

	return {
		"name": None,
		"first_name": values.get("first_name") or "",
		"last_name": values.get("last_name") or "",
		"full_name": full_name,
		"company_name": values.get("organization") or "",
		"email_id": values.get("email") or "",
		"phone": values.get("phone") or "",
		"mobile_no": values.get("mobile") or "",
		"micro_contact_type": contact_type,
		"micro_website": values.get("website") or "",
		"micro_address": values.get("address") or "",
		"micro_postal_code": values.get("postal_code") or "",
	}


def _find_duplicate(index: ContactIndex, values: dict, dedupe_by: str, contact_type: str) -> str | None:
	"""Existing Contact matching this row, across all apps — a person is a person.

	The key the user picked still decides what counts as the same contact; what
	changed is that the comparison happens on normalized values. Matching on
	phone used to mean matching the exact string that was typed, so one number
	written `+49 171 1234567` here and `0171 1234567` there slipped straight
	past and became a second contact.
	"""
	if dedupe_by == "none":
		return None

	record = _as_record(values, contact_type)

	for candidate in index.candidates(record):
		if dedupe_by == "email":
			email = normalize_email(values.get("email"))
			if email and email == normalize_email(candidate.get("email_id")):
				return candidate["name"]

		elif dedupe_by == "phone":
			row_phones = {phone_key(values.get("phone")), phone_key(values.get("mobile"))} - {""}
			candidate_phones = {phone_key(candidate.get("phone")), phone_key(candidate.get("mobile_no"))} - {""}
			if row_phones & candidate_phones:
				return candidate["name"]

		elif dedupe_by == "name":
			name = display_name(record)
			if name and name == display_name(candidate):
				return candidate["name"]

	return None


def _fill_blanks(contact_name: str, values: dict, status: str, source: str) -> bool:
	"""Fill what the existing contact is missing; never overwrite what it has.

	Returns whether this contact was newly adopted into Micro, because that is
	what spends a slot under the customer limit.
	"""
	contact = frappe.get_doc("Contact", contact_name)
	changed = False
	adopted = False

	# A contact another app created is adopted into Micro rather than duplicated.
	if not contact.micro_status:
		contact.micro_status = status
		contact.micro_source = source
		changed = True
		adopted = True

	for target, fieldname in (
		("website", "micro_website"),
		("address", "micro_address"),
		("city", "micro_city"),
		("postal_code", "micro_postal_code"),
		("country", "micro_country"),
		("notes", "micro_notes"),
	):
		if values.get(target) and not contact.get(fieldname) and fieldname in FILLABLE_ON_UPDATE:
			contact.set(fieldname, values[target])
			changed = True

	for target, fieldname in (("phone", "phone"), ("mobile", "mobile_no"), ("email", "email_id")):
		if values.get(target) and not contact.get(fieldname):
			contact.set(fieldname, values[target])
			changed = True

	if changed:
		contact.save(ignore_permissions=True)

	return adopted


def _add_import_lead(
	contact: str, values: dict, pipeline: str, stage: str | None, source: str
) -> bool:
	"""One lead per imported row, so the list can be worked straight away.

	Returns whether a lead was actually added. A contact already open in this
	pipeline keeps the lead they have: re-importing the same list must not
	produce two cards for the same conversation.
	"""
	from micro.api.leads import create_lead

	if frappe.db.exists(
		"Micro Lead", {"contact": contact, "pipeline": pipeline, "status": "Open"}
	):
		return False

	create_lead(
		lead_name=values.get("first_name") or contact,
		contact=contact,
		pipeline=pipeline,
		stage=stage,
		source=source,
	)
	return True
