# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe import _
from frappe.utils import add_days, today

from micro.services.distance import attach_distance

CALL_LIST_FIELDS = [
	"name",
	"lead_name",
	"contact",
	"status",
	"pipeline",
	"stage",
	"priority",
	"expected_value",
	"source",
	"next_follow_up",
]

CONTACT_DETAIL_FIELDS = [
	"name",
	"first_name",
	"last_name",
	"full_name",
	"company_name",
	"email_id",
	"phone",
	"mobile_no",
	"micro_segment",
	"image",
	# Feeds the distance on the card — see micro.services.distance.
	"micro_postal_code",
	# Frappe's display copy of the contact's tags — same row, no extra query.
	"_user_tags",
]

# The call list wants to know how to speak to someone, not what they look like.
CALL_CONTACT_FIELDS = [
	"name",
	"first_name",
	"last_name",
	"full_name",
	"company_name",
	"email_id",
	"phone",
	"mobile_no",
	"micro_segment",
	"micro_communication_style",
	"micro_client_loves",
	# Worth knowing before offering to come round.
	"micro_postal_code",
]

PRIORITY_RANK = {"High": 0, "Medium": 1, "Low": 2}

# Micro has no separate trash table: an archived lead *is* a deleted one, kept
# whole so it can be restored. Only a manager can destroy it for good.
ARCHIVED = "Archived"

EDITABLE_LEAD_FIELDS = {
	"lead_name",
	"contact",
	"pipeline",
	"stage",
	"priority",
	"source",
	"expected_value",
	"next_follow_up",
	"lost_reason",
	"status",
	"notes",
}


@frappe.whitelist()
def get_leads(
	filters: dict | None = None,
	order_by: str = "modified desc",
	limit_start: int = 0,
	limit_page_length: int = 20,
	search: str | None = None,
	include_archived: bool = False,
) -> dict:
	"""Get leads with filters, pagination, and search.

	Archived leads are the app's trash and stay out of every list that does not
	ask for them by name.
	"""
	frappe.has_permission("Micro Lead", throw=True)

	base_filters = filters or {}
	if search:
		base_filters["lead_name"] = ["like", f"%{search}%"]
	if not include_archived and "status" not in base_filters:
		base_filters["status"] = ["!=", ARCHIVED]

	leads = frappe.get_list(
		"Micro Lead",
		filters=base_filters,
		fields=[
			"name", "lead_name", "contact", "status",
			"pipeline", "stage", "priority",
			"expected_value", "next_follow_up",
		],
		order_by=order_by,
		start=limit_start,
		page_length=limit_page_length,
	)

	total = frappe.db.count("Micro Lead", filters=base_filters)
	return {"leads": leads, "total": total}


@frappe.whitelist()
def get_lead(lead_id: str) -> dict:
	"""Get a single lead, with its contact and stage resolved to names."""
	frappe.has_permission("Micro Lead", throw=True)
	lead = frappe.get_doc("Micro Lead", lead_id).as_dict()
	lead["contact_details"] = _contact_details(lead.get("contact"))
	attach_stage_names([lead])
	return {"lead": lead, "can_delete": _can_delete()}


@frappe.whitelist()
def create_lead(
	lead_name: str,
	pipeline: str | None = None,
	stage: str | None = None,
	contact: str | None = None,
	priority: str = "Medium",
	source: str | None = None,
	expected_value: float | None = None,
	next_follow_up: str | None = None,
	notes: str | None = None,
) -> dict:
	"""Create a lead. Pipeline and stage default to the board it is created from."""
	frappe.has_permission("Micro Lead", "create", throw=True)

	lead = frappe.new_doc("Micro Lead")
	lead.lead_name = lead_name
	lead.priority = priority

	for fieldname, value in (
		("pipeline", pipeline),
		("stage", stage),
		("contact", contact),
		("source", source),
		("expected_value", expected_value),
		("next_follow_up", next_follow_up),
		("notes", notes),
	):
		if value:
			setattr(lead, fieldname, value)

	lead.insert()

	return {"lead": lead.as_dict()}


@frappe.whitelist()
def update_lead(lead_id: str, **values) -> dict:
	"""Update editable lead fields (used by the call list and the detail page)."""
	frappe.has_permission("Micro Lead", "write", throw=True)

	lead = frappe.get_doc("Micro Lead", lead_id)
	for fieldname, value in values.items():
		if fieldname in EDITABLE_LEAD_FIELDS:
			setattr(lead, fieldname, value)
	lead.save()

	updated = lead.as_dict()
	updated["contact_details"] = _contact_details(updated.get("contact"))
	attach_stage_names([updated])
	return {"lead": updated}


@frappe.whitelist()
def move_lead(lead_id: str, stage_id: str) -> dict:
	"""Move a lead to a different pipeline stage."""
	frappe.has_permission("Micro Lead", "write", throw=True)

	if not frappe.db.exists("Micro Lead", lead_id):
		frappe.throw(_("Lead not found"))
	if not frappe.db.exists("Micro Pipeline Stage", stage_id):
		frappe.throw(_("Pipeline stage not found"))

	lead = frappe.get_doc("Micro Lead", lead_id)
	lead.stage = stage_id
	lead.save()

	return {"success": True, "status": lead.status}


@frappe.whitelist()
def archive_lead(lead_id: str) -> dict:
	"""Soft delete: off every board and list, but recoverable from the archive.

	This is the delete an ordinary user gets. Nothing is destroyed, so it needs
	no more than write access.
	"""
	frappe.has_permission("Micro Lead", "write", throw=True)

	lead = frappe.get_doc("Micro Lead", lead_id)
	if lead.status == ARCHIVED:
		return {"success": True, "status": lead.status}

	lead.status = ARCHIVED
	lead.save()

	return {"success": True, "status": lead.status}


@frappe.whitelist()
def restore_lead(lead_id: str) -> dict:
	"""Take a lead back out of the archive.

	The status goes back to Open and the controller re-derives it from whatever
	stage the lead was parked in — a lead restored into a win stage is Won again.
	"""
	frappe.has_permission("Micro Lead", "write", throw=True)

	lead = frappe.get_doc("Micro Lead", lead_id)
	if lead.status != ARCHIVED:
		frappe.throw(_("This lead is not archived."))

	lead.status = "Open"
	lead.save()

	return {"success": True, "status": lead.status}


@frappe.whitelist()
def delete_lead(lead_id: str) -> dict:
	"""Hard delete — manager only, and gone for good.

	`Micro Lead.on_trash` re-points the contact's stage mirror at whatever open
	lead is left, so the contact never keeps a stage badge for a deleted deal.
	"""
	frappe.has_permission("Micro Lead", "delete", throw=True)

	if not frappe.db.exists("Micro Lead", lead_id):
		frappe.throw(_("Lead not found"))

	frappe.delete_doc("Micro Lead", lead_id)

	return {"success": True}


@frappe.whitelist()
def get_archived_leads(
	pipeline: str | None = None,
	limit_start: int = 0,
	limit_page_length: int = 50,
	search: str | None = None,
) -> dict:
	"""The archive view — Micro's trash, most recently archived first."""
	frappe.has_permission("Micro Lead", throw=True)

	filters: dict = {"status": ARCHIVED}
	if pipeline:
		filters["pipeline"] = pipeline
	if search:
		filters["lead_name"] = ["like", f"%{search}%"]

	leads = frappe.get_list(
		"Micro Lead",
		filters=filters,
		fields=[*CALL_LIST_FIELDS, "modified"],
		order_by="modified desc",
		start=limit_start,
		page_length=limit_page_length,
	)

	attach_contact_details(leads)
	attach_stage_names(leads)

	return {
		"leads": leads,
		"total": frappe.db.count("Micro Lead", filters=filters),
		"can_delete": _can_delete(),
	}


@frappe.whitelist()
def snooze_lead(lead_id: str, days: int = 7) -> dict:
	"""Push the follow-up date out — the 'not today' button on the call list."""
	frappe.has_permission("Micro Lead", "write", throw=True)

	lead = frappe.get_doc("Micro Lead", lead_id)
	base = str(lead.next_follow_up or today())
	if base < today():
		base = today()
	lead.next_follow_up = add_days(base, int(days))
	lead.save()

	return {"success": True, "next_follow_up": lead.next_follow_up}


@frappe.whitelist()
def get_call_list(
	pipeline: str | None = None,
	segment: str | None = None,
	include_undated: bool = False,
	limit: int = 50,
) -> dict:
	"""Today's work queue: open leads that are due, most urgent first.

	The Kanban board is for sorting; this is for working through. One pipeline
	at a time by default, so a calling session stays in a single mode of speaking.
	"""
	frappe.has_permission("Micro Lead", throw=True)

	filters: list[list] = [["status", "=", "Open"]]
	if pipeline:
		filters.append(["pipeline", "=", pipeline])
	if not include_undated:
		# An unset date is stored as '' and would otherwise compare as due.
		filters.append(["next_follow_up", "is", "set"])
		filters.append(["next_follow_up", "<=", today()])

	if segment:
		contact_names = [
			row["name"]
			for row in frappe.get_all("Contact", filters={"micro_segment": segment}, fields=["name"])
		]
		if not contact_names:
			return {"leads": [], "total": 0}
		filters.append(["contact", "in", contact_names])

	leads = frappe.get_list(
		"Micro Lead",
		filters=filters,
		fields=CALL_LIST_FIELDS,
		order_by="next_follow_up asc",
		page_length=int(limit),
	)

	_attach_call_context(leads)
	leads.sort(
		key=lambda lead: (
			str(lead.get("next_follow_up") or "9999-12-31"),
			PRIORITY_RANK.get(lead.get("priority"), 1),
		)
	)

	return {"leads": leads, "total": len(leads)}


def _can_delete() -> bool:
	"""Whether this user may destroy a lead — the UI hides the button otherwise."""
	return bool(frappe.has_permission("Micro Lead", "delete"))


def _contact_details(contact: str | None) -> dict | None:
	"""The contact card of a single lead — so a detail view never shows a bare docname."""
	if not contact:
		return None

	details = frappe.db.get_value("Contact", contact, CONTACT_DETAIL_FIELDS, as_dict=True)
	attach_distance([details] if details else [])

	return details


def attach_contact_details(leads: list[dict], fields: list[str] | None = None) -> None:
	"""Attach each lead's contact — one query for the whole set, never one per card."""
	if not leads:
		return

	contact_ids = {lead["contact"] for lead in leads if lead.get("contact")}
	if not contact_ids:
		for lead in leads:
			lead["contact_details"] = None
		return

	by_name = {
		row["name"]: row
		for row in frappe.get_all(
			"Contact",
			filters={"name": ["in", list(contact_ids)]},
			fields=fields or CONTACT_DETAIL_FIELDS,
		)
	}

	# Once per contact, not once per lead — several leads can share one.
	attach_distance(list(by_name.values()))

	for lead in leads:
		lead["contact_details"] = by_name.get(lead.get("contact"))


def attach_stage_names(leads: list[dict]) -> None:
	"""Resolve stage links to their names, in one query."""
	stage_ids = {lead["stage"] for lead in leads if lead.get("stage")}
	stages = {}
	if stage_ids:
		stages = {
			row["name"]: row["stage_name"]
			for row in frappe.get_all(
				"Micro Pipeline Stage",
				filters={"name": ["in", list(stage_ids)]},
				fields=["name", "stage_name"],
			)
		}

	for lead in leads:
		lead["stage_name"] = stages.get(lead.get("stage"))


def _attach_call_context(leads: list[dict]) -> None:
	"""Phone number, stage name and last note — what you want before dialling."""
	if not leads:
		return

	attach_contact_details(leads, CALL_CONTACT_FIELDS)
	attach_stage_names(leads)

	contact_ids = {lead["contact"] for lead in leads if lead.get("contact")}
	notes: dict = {}
	if contact_ids:
		for row in frappe.get_all(
			"Micro Note",
			filters={"contact": ["in", list(contact_ids)]},
			fields=["contact", "subject", "date"],
			order_by="date desc",
		):
			notes.setdefault(row["contact"], row)

	for lead in leads:
		lead["last_note"] = notes.get(lead.get("contact"))
		lead["is_overdue"] = bool(lead.get("next_follow_up")) and str(lead["next_follow_up"]) < today()
