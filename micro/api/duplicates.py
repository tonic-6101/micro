# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Duplicate contacts — suggest, merge, undo.

Micro suggests; the user decides. Nothing is ever merged automatically, not even
on an identical email address: un-fusing two people whose histories have been
joined costs far more than showing one suggestion twice, and a solo business
owner has no admin to appeal to when their own CRM guesses wrong.

The matching itself lives in `micro.services.duplicates`. This module is the
part that touches the database: storing suggestions, merging records, and
keeping enough of the merged-away record to put it back.
"""

import json

import frappe
from frappe import _
from frappe.model.rename_doc import get_link_fields, rename_doc
from frappe.utils import now_datetime

from micro.services.duplicates import (
	CONTACT_FIELDS,
	ContactIndex,
	band_for,
	fingerprint,
	find_pairs,
	score_pair,
)

# How long a merged-away contact can be restored. Long enough to notice the
# mistake, short enough that Micro is not a graveyard of deleted personal data.
UNDO_DAYS = 30

# Shown next to each suggestion so the user can see *why* Micro thinks these are
# one contact — a suggestion nobody can check is a suggestion nobody trusts.
SIGNAL_LABELS = {
	"email": "Same email address",
	"phone": "Same phone number",
	"name": "Similar name",
	"exact_name": "Same name",
	"phonetic": "Name sounds the same",
	"address": "Same address",
	"domain": "Same website domain",
	"-type": "Different contact type",
	"-first_name": "Different first name",
}


def _describe(signals: list[str]) -> list[str]:
	return [_(SIGNAL_LABELS[signal]) for signal in signals if signal in SIGNAL_LABELS]


def _contact(name: str) -> dict | None:
	values = frappe.db.get_value("Contact", name, list(CONTACT_FIELDS), as_dict=True)

	return dict(values) if values else None


# --- suggestions -----------------------------------------------------------


@frappe.whitelist()
def get_duplicate_summary() -> dict:
	"""Counts behind the banner on the customer list."""
	frappe.has_permission("Contact", throw=True)

	open_pairs = frappe.get_all(
		"Micro Duplicate Pair",
		filters={"status": "Open"},
		fields=["band"],
	)

	return {
		"open": len(open_pairs),
		"certain": len([pair for pair in open_pairs if pair.band == "Certain"]),
	}


@frappe.whitelist()
def get_duplicate_pairs(limit_start: int = 0, limit_page_length: int = 20, band: str | None = None) -> dict:
	"""Open suggestions, strongest first, with both records attached.

	Pairs whose contacts have since been deleted or merged elsewhere are closed
	on sight rather than returned — a suggestion pointing at a record that no
	longer exists is not something the user can act on.
	"""
	frappe.has_permission("Contact", throw=True)

	filters: dict = {"status": "Open"}
	if band:
		filters["band"] = band

	rows = frappe.get_all(
		"Micro Duplicate Pair",
		filters=filters,
		fields=["name", "contact_a", "contact_b", "score", "band", "signals"],
		order_by="score desc",
		start=int(limit_start),
		page_length=int(limit_page_length),
	)

	pairs = []
	for row in rows:
		contact_a = _contact(row.contact_a)
		contact_b = _contact(row.contact_b)
		if not contact_a or not contact_b:
			frappe.db.set_value("Micro Duplicate Pair", row.name, "status", "Merged")
			continue

		signals = json.loads(row.signals or "[]")
		pairs.append(
			{
				"name": row.name,
				"score": row.score,
				"band": row.band,
				"signals": signals,
				"reasons": _describe(signals),
				"contact_a": contact_a,
				"contact_b": contact_b,
				"documents_a": count_linked_documents(row.contact_a),
				"documents_b": count_linked_documents(row.contact_b),
			}
		)

	return {"pairs": pairs, "total": frappe.db.count("Micro Duplicate Pair", filters=filters)}


@frappe.whitelist()
def check_duplicates(
	first_name: str | None = None,
	last_name: str | None = None,
	email: str | None = None,
	phone: str | None = None,
	mobile: str | None = None,
	organization: str | None = None,
	contact_type: str = "Person",
	postal_code: str | None = None,
	address: str | None = None,
	website: str | None = None,
	exclude: str | None = None,
) -> dict:
	"""Contacts that look like the one being typed, checked before it is saved.

	Writes nothing. This is the live check behind the create form, so it has to
	stay cheap and it has to stay silent — it warns, it never blocks the save.
	"""
	frappe.has_permission("Contact", throw=True)

	if not any((first_name, last_name, email, phone, mobile, organization)):
		return {"matches": []}

	full_name = " ".join(part for part in (first_name, last_name) if part)
	candidate = {
		"name": None,
		"first_name": first_name or "",
		"last_name": last_name or "",
		"full_name": full_name or organization or "",
		"company_name": organization or "",
		"email_id": email or "",
		"phone": phone or "",
		"mobile_no": mobile or "",
		"micro_contact_type": contact_type or "Person",
		"micro_website": website or "",
		"micro_address": address or "",
		"micro_postal_code": postal_code or "",
	}

	# Every contact on the site, not just Micro's own: warning that this person
	# already exists in Dock is the whole point of asking before the save.
	matches = []
	for match in ContactIndex(micro_only=False).matches(candidate, exclude=exclude):
		matches.append(
			{
				"contact": match["contact"],
				"score": match["score"],
				"band": band_for(match["score"]),
				"reasons": _describe(match["signals"]),
			}
		)

	return {"matches": matches[:5]}


@frappe.whitelist()
def scan_for_duplicates() -> dict:
	"""Re-scan every contact and refresh the open suggestions.

	Runs daily and on demand. Dismissals survive a re-scan: a pair the user has
	already rejected only comes back if its fingerprint changed, which means one
	of the two records was actually edited since.
	"""
	frappe.has_permission("Contact", throw=True)

	existing = {
		(row.contact_a, row.contact_b): row
		for row in frappe.get_all(
			"Micro Duplicate Pair",
			fields=["name", "contact_a", "contact_b", "status", "fingerprint"],
		)
	}

	found = 0
	for pair in find_pairs():
		found += 1
		key = (pair["contact_a"], pair["contact_b"])
		row = existing.get(key)

		if row:
			if row.status == "Merged":
				continue
			if row.status == "Dismissed" and row.fingerprint == pair["fingerprint"]:
				# Rejected, and nothing about either record has changed since.
				continue

			frappe.db.set_value(
				"Micro Duplicate Pair",
				row.name,
				{
					"score": pair["score"],
					"band": pair["band"],
					"signals": json.dumps(pair["signals"]),
					"fingerprint": pair["fingerprint"],
					"status": "Open",
					"detected_on": now_datetime(),
				},
			)
			continue

		frappe.get_doc(
			{
				"doctype": "Micro Duplicate Pair",
				"contact_a": pair["contact_a"],
				"contact_b": pair["contact_b"],
				"score": pair["score"],
				"band": pair["band"],
				"signals": json.dumps(pair["signals"]),
				"fingerprint": pair["fingerprint"],
				"status": "Open",
				"detected_on": now_datetime(),
			}
		).insert(ignore_permissions=True)

	return {"found": found, **get_duplicate_summary()}


@frappe.whitelist()
def dismiss_pair(pair: str) -> dict:
	"""Mark a suggestion as "not a duplicate", and make it stay dismissed."""
	frappe.has_permission("Contact", "write", throw=True)

	doc = frappe.get_doc("Micro Duplicate Pair", pair)
	doc.status = "Dismissed"
	doc.resolved_on = now_datetime()
	doc.resolved_by = frappe.session.user
	doc.save(ignore_permissions=True)

	return {"pair": doc.name, "status": doc.status}


# --- merging ---------------------------------------------------------------

# Scalar fields carried over when the survivor has nothing in them. Never
# overwrite what the survivor already says — filling a blank is a repair, and
# replacing a value is a guess.
FILLABLE_FIELDS = (
	"first_name",
	"last_name",
	"company_name",
	"designation",
	"department",
	"micro_status",
	"micro_source",
	"micro_segment",
	"micro_contact_type",
	"micro_website",
	"micro_address",
	"micro_city",
	"micro_postal_code",
	"micro_country",
	"micro_health_score",
	"micro_client_loves",
	"micro_client_avoid",
	"micro_communication_style",
	"micro_personal_notes",
	"micro_opportunities",
	"micro_last_contact_date",
	"micro_last_contact_topic",
)

# Doctypes whose status means a document has already gone out of the house.
# Merging repoints them, which changes who they render as — worth warning about.
ISSUED_STATES = {
	"Micro Offer Draft": ("Sent", "Accepted", "Declined", "Expired"),
	"Micro Invoice Draft": ("Sent to Tax Advisor", "Archived"),
}


def count_linked_documents(contact: str) -> dict:
	"""How much history hangs off a contact, per doctype.

	Drives the default choice of survivor and the warning about documents that
	have already been sent.
	"""
	counts: dict = {}
	issued = 0

	for doctype in ("Micro Lead", "Micro Note", "Micro Task", "Micro Call Attempt", "Micro Offer Draft", "Micro Invoice Draft", "Micro Receipt"):
		count = frappe.db.count(doctype, filters={"contact": contact})
		if count:
			counts[doctype] = count

		states = ISSUED_STATES.get(doctype)
		if states:
			issued += frappe.db.count(doctype, filters={"contact": contact, "status": ["in", states]})

	counts["total"] = sum(value for key, value in counts.items() if key != "total")
	counts["issued"] = issued

	return counts


@frappe.whitelist()
def get_merge_preview(winner: str, loser: str) -> dict:
	"""What a merge would carry over, and what it would touch, before it runs."""
	frappe.has_permission("Contact", "write", throw=True)

	winner_doc = frappe.get_doc("Contact", winner)
	loser_doc = frappe.get_doc("Contact", loser)

	filled = [
		field
		for field in FILLABLE_FIELDS
		if loser_doc.get(field) and not winner_doc.get(field) and winner_doc.meta.has_field(field)
	]

	winner_emails = {row.email_id for row in winner_doc.email_ids}
	winner_phones = {row.phone for row in winner_doc.phone_nos}
	documents = count_linked_documents(loser)

	return {
		"fills": filled,
		"emails_added": sorted({row.email_id for row in loser_doc.email_ids} - winner_emails),
		"phones_added": sorted({row.phone for row in loser_doc.phone_nos} - winner_phones),
		"documents": documents,
		"issued_documents": documents["issued"],
	}


def _collect_references(contact: str) -> list[dict]:
	"""Every document pointing at this contact, so a merge can be walked back.

	Frappe repoints these itself, but it does not record what it repointed. An
	undo that cannot find its way back is not an undo, so the list is captured
	while the links still point where they originally pointed.
	"""
	references = []

	for field in get_link_fields("Contact"):
		if field.get("issingle"):
			continue
		try:
			names = frappe.get_all(
				field["parent"],
				filters={field["fieldname"]: contact},
				pluck="name",
			)
		except Exception:
			# A doctype whose table is missing must not sink the merge.
			continue

		for name in names:
			references.append({"doctype": field["parent"], "name": name, "fieldname": field["fieldname"]})

	return references


@frappe.whitelist()
def merge_contacts(winner: str, loser: str, pair: str | None = None) -> dict:
	"""Fold `loser` into `winner`, keeping everything both of them knew.

	Order matters and it is not obvious: `rename_doc(merge=True)` repoints the
	links, then *deletes* the loser, which cascades away its email and phone
	child rows. Everything worth keeping is therefore copied across first — copy
	after the rename and the numbers are already gone.
	"""
	frappe.has_permission("Contact", "write", throw=True)
	frappe.has_permission("Contact", "delete", throw=True)

	if winner == loser:
		frappe.throw(_("Cannot merge a contact into itself"))

	winner_doc = frappe.get_doc("Contact", winner)
	loser_doc = frappe.get_doc("Contact", loser)

	# Resolved before the merge, because the merge rewrites these rows too: a
	# Duplicate Pair points at Contact with ordinary Link fields, so Frappe
	# dutifully repoints them at the survivor along with everything else, and
	# afterwards the pair reads as a contact duplicating itself.
	record = frappe.get_doc("Micro Duplicate Pair", pair) if pair else _pair_for(winner, loser)
	pair_sides = (record.contact_a, record.contact_b) if record else None
	superseded = [
		name
		for name in frappe.get_all(
			"Micro Duplicate Pair",
			filters={"status": "Open"},
			or_filters={"contact_a": loser, "contact_b": loser},
			pluck="name",
		)
		if not record or name != record.name
	]

	snapshot = {
		"contact": loser_doc.as_dict(convert_dates_to_str=True),
		"references": _collect_references(loser),
		"merged_on": str(now_datetime()),
	}

	for field in FILLABLE_FIELDS:
		if winner_doc.meta.has_field(field) and loser_doc.get(field) and not winner_doc.get(field):
			winner_doc.set(field, loser_doc.get(field))

	# Conflicting contact details are kept side by side rather than chosen
	# between — Contact already holds several of each. `is_primary` stays with
	# the survivor's own row so the core controller does not reject two primaries.
	existing_emails = {row.email_id for row in winner_doc.email_ids}
	for row in loser_doc.email_ids:
		if row.email_id and row.email_id not in existing_emails:
			winner_doc.append("email_ids", {"email_id": row.email_id, "is_primary": 0})

	existing_phones = {row.phone for row in winner_doc.phone_nos}
	for row in loser_doc.phone_nos:
		if row.phone and row.phone not in existing_phones:
			winner_doc.append(
				"phone_nos",
				{"phone": row.phone, "is_primary_phone": 0, "is_primary_mobile_no": 0},
			)

	existing_links = {(row.link_doctype, row.link_name) for row in winner_doc.links}
	for row in loser_doc.links:
		if (row.link_doctype, row.link_name) not in existing_links:
			winner_doc.append("links", {"link_doctype": row.link_doctype, "link_name": row.link_name})

	# Free text is appended, never replaced: two sets of notes about one person
	# are both true.
	if loser_doc.get("micro_notes") and loser_doc.micro_notes != winner_doc.get("micro_notes"):
		merged_from = _("Merged from {0}").format(loser_doc.get("full_name") or loser)
		winner_doc.micro_notes = "\n\n".join(
			part for part in (winner_doc.get("micro_notes"), f"--- {merged_from} ---", loser_doc.micro_notes) if part
		)

	winner_doc.save(ignore_permissions=True)

	# Repoints every Link field, Dynamic Link, assignment and attachment, then
	# deletes the loser.
	rename_doc("Contact", loser, winner, merge=True, ignore_permissions=True, show_alert=False)

	if record:
		# Written straight to the database: the pair now names one contact twice
		# after the repointing above, so its own validation would reject it. The
		# original two names go back in as the audit record they are meant to be.
		frappe.db.set_value(
			"Micro Duplicate Pair",
			record.name,
			{
				"contact_a": pair_sides[0],
				"contact_b": pair_sides[1],
				"status": "Merged",
				"merged_into": winner,
				"snapshot": json.dumps(snapshot, default=str),
				"resolved_on": now_datetime(),
				"resolved_by": frappe.session.user,
			},
		)

	# Other suggestions about the record that just disappeared are deleted, not
	# closed. They were repointed at the survivor too, and a stored pair saying
	# "winner and X" with a resolved status would keep a real future duplicate of
	# those two from ever being suggested again.
	for stale in superseded:
		frappe.delete_doc("Micro Duplicate Pair", stale, ignore_permissions=True, force=True)

	return {
		"winner": winner,
		"merged": loser,
		"pair": record.name if record else None,
		"undo_days": UNDO_DAYS,
	}


def _pair_for(winner: str, loser: str):
	"""The stored suggestion for these two, in whichever order it was saved."""
	first, second = sorted((winner, loser))
	name = frappe.db.exists("Micro Duplicate Pair", {"contact_a": first, "contact_b": second})

	return frappe.get_doc("Micro Duplicate Pair", name) if name else None


@frappe.whitelist()
def undo_merge(pair: str) -> dict:
	"""Put a merged-away contact back, with the documents that pointed at it.

	Frappe's rename repoints links but records nothing about what it moved, so
	the references captured before the merge are what makes this possible. Only
	those exact documents are moved back — anything linked to the survivor since
	the merge stays where it is.
	"""
	frappe.has_permission("Contact", "create", throw=True)
	frappe.has_permission("Contact", "write", throw=True)

	record = frappe.get_doc("Micro Duplicate Pair", pair)
	if record.status != "Merged" or not record.snapshot:
		frappe.throw(_("This merge cannot be undone"))

	snapshot = json.loads(record.snapshot)
	values = snapshot["contact"]
	restored_name = values.get("name")

	if frappe.db.exists("Contact", restored_name):
		frappe.throw(_("A contact named {0} already exists").format(restored_name))

	if frappe.utils.date_diff(now_datetime(), snapshot["merged_on"]) > UNDO_DAYS:
		frappe.throw(_("Merges can only be undone within {0} days").format(UNDO_DAYS))

	restored = frappe.get_doc(values)
	restored.insert(ignore_permissions=True, set_name=restored_name)

	moved = 0
	for reference in snapshot.get("references", []):
		if not frappe.db.exists(reference["doctype"], reference["name"]):
			continue
		frappe.db.set_value(
			reference["doctype"], reference["name"], reference["fieldname"], restored_name, update_modified=False
		)
		moved += 1

	record.status = "Dismissed"
	record.merged_into = None
	record.snapshot = None
	record.resolved_on = now_datetime()
	record.resolved_by = frappe.session.user
	record.save(ignore_permissions=True)

	return {"restored": restored_name, "documents_moved": moved}
