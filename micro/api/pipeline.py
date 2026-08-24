# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe import _
from frappe.utils import cint, today

from micro.api.leads import ARCHIVED, attach_contact_details
from micro.micro.doctype.micro_pipeline.micro_pipeline import get_default_pipeline

LEAD_FIELDS = [
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

# A prospecting import can put thousands of leads in one stage. The board shows
# a page of each column and says how many are really there.
DEFAULT_LEADS_PER_STAGE = 100

STAGE_FIELDS = [
	"name",
	"stage_name",
	"sort_order",
	"color",
	"is_closed",
	"is_win_stage",
	"is_loss_stage",
]

# A card shows the contact's name and phone next to the lead's own name, so the
# board's search box looks at all of them — anything printed on a card is
# something the user may type to find it again.
CONTACT_SEARCH_FIELDS = [
	"first_name",
	"last_name",
	"company_name",
	"email_id",
	"phone",
	"mobile_no",
]

# A term like "a" would otherwise pull every contact into one IN clause.
MAX_SEARCH_CONTACTS = 500


@frappe.whitelist()
def get_pipelines() -> dict:
	"""All active pipelines, for the board switcher."""
	frappe.has_permission("Micro Pipeline", throw=True)

	pipelines = frappe.get_list(
		"Micro Pipeline",
		filters={"is_active": 1},
		fields=["name", "pipeline_name", "segment", "is_default", "sort_order", "description"],
		order_by="sort_order asc, pipeline_name asc",
	)

	for pipeline in pipelines:
		pipeline["open_leads"] = frappe.db.count(
			"Micro Lead", {"pipeline": pipeline["name"], "status": "Open"}
		)

	return {"pipelines": pipelines, "default": get_default_pipeline()}


@frappe.whitelist()
def get_pipeline(
	pipeline: str | None = None,
	show_closed: bool = False,
	segment: str | None = None,
	source: str | None = None,
	priority: str | None = None,
	due_only: bool = False,
	search: str | None = None,
	leads_per_stage: int = 0,
) -> dict:
	"""Kanban board: the stages of one pipeline with their leads.

	Leads — not contacts — are the cards. One contact can run through several
	pipelines at once, which is precisely why the two are kept apart.
	"""
	frappe.has_permission("Micro Lead", throw=True)

	pipeline = pipeline or get_default_pipeline()
	if not pipeline:
		return {"pipeline": None, "stages": [], "unassigned": [], "totals": {"count": 0, "value": 0}}

	stage_filters = {"pipeline": pipeline}
	if not show_closed:
		stage_filters["is_closed"] = 0

	stages = frappe.get_list(
		"Micro Pipeline Stage",
		filters=stage_filters,
		fields=STAGE_FIELDS,
		order_by="sort_order asc",
	)

	lead_filters, lead_or_filters = _build_lead_filters(pipeline, source, priority, due_only, search)

	if segment:
		contact_names = _contacts_in_segment(segment)
		if not contact_names:
			return {
				"pipeline": pipeline,
				"stages": [
					{"stage": s, "leads": [], "count": 0, "loaded": 0, "value": 0} for s in stages
				],
				"unassigned": [],
				"totals": {"count": 0, "value": 0},
			}
		lead_filters.append(["contact", "in", contact_names])

	columns = []
	total_count = 0
	total_value = 0.0
	per_stage = cint(leads_per_stage) or DEFAULT_LEADS_PER_STAGE

	for stage in stages:
		stage_filters = [*lead_filters, ["stage", "=", stage.name]]
		leads = frappe.get_list(
			"Micro Lead",
			filters=stage_filters,
			or_filters=lead_or_filters,
			fields=LEAD_FIELDS,
			order_by="next_follow_up asc, modified desc",
			page_length=per_stage,
		)
		_enrich_leads(leads)
		# Count and value describe the whole column — a prospecting list can hold
		# thousands, and only a page of them is ever sent to the board.
		count, value = _column_totals(stage_filters, lead_or_filters)
		total_count += count
		total_value += value
		columns.append(
			{"stage": stage, "leads": leads, "count": count, "loaded": len(leads), "value": value}
		)

	unassigned = frappe.get_list(
		"Micro Lead",
		filters=[*lead_filters, ["stage", "in", ["", None]]],
		or_filters=lead_or_filters,
		fields=LEAD_FIELDS,
		order_by="modified desc",
		page_length=per_stage,
	)
	_enrich_leads(unassigned)

	return {
		"pipeline": pipeline,
		"stages": columns,
		"unassigned": unassigned,
		"totals": {"count": total_count, "value": total_value},
	}


@frappe.whitelist()
def move_lead(lead_id: str, stage_id: str) -> dict:
	"""Move a lead to another stage of its own pipeline."""
	frappe.has_permission("Micro Lead", "write", throw=True)

	if not frappe.db.exists("Micro Lead", lead_id):
		frappe.throw(_("Lead not found"))
	if not frappe.db.exists("Micro Pipeline Stage", stage_id):
		frappe.throw(_("Pipeline stage not found"))

	lead = frappe.get_doc("Micro Lead", lead_id)
	lead.stage = stage_id
	lead.save()

	return {"success": True, "status": lead.status, "stage": lead.stage}


@frappe.whitelist()
def get_stages(pipeline: str | None = None) -> dict:
	"""Stages of one pipeline, or of every pipeline when none is given."""
	frappe.has_permission("Micro Pipeline Stage", throw=True)

	filters = {"pipeline": pipeline} if pipeline else {}
	stages = frappe.get_list(
		"Micro Pipeline Stage",
		filters=filters,
		fields=[*STAGE_FIELDS, "pipeline"],
		order_by="sort_order asc",
	)

	return {"stages": stages}


@frappe.whitelist()
def get_segments() -> dict:
	"""Active segments, for the filter dropdowns."""
	frappe.has_permission("Micro Segment", throw=True)

	segments = frappe.get_list(
		"Micro Segment",
		filters={"is_active": 1},
		fields=["name", "segment_name", "color", "sort_order"],
		order_by="sort_order asc, segment_name asc",
	)

	return {"segments": segments}


def _build_lead_filters(
	pipeline: str,
	source: str | None,
	priority: str | None,
	due_only: bool,
	search: str | None,
) -> tuple[list[list], list[list]]:
	"""The board's AND filters, plus the OR group the search term needs.

	List form, so `next_follow_up` can carry two conditions at once. The two are
	kept apart because a search matches any one of several fields while every
	other filter has to hold at once.
	"""
	# Archived is Micro's trash — those cards belong in the archive, not on a board.
	filters: list[list] = [["pipeline", "=", pipeline], ["status", "!=", ARCHIVED]]

	if source:
		filters.append(["source", "=", source])
	if priority:
		filters.append(["priority", "=", priority])
	if due_only:
		# An unset date is stored as '' and would otherwise compare as due.
		filters.append(["next_follow_up", "is", "set"])
		filters.append(["next_follow_up", "<=", today()])

	return filters, _search_or_filters(search)


def _search_or_filters(search: str | None) -> list[list]:
	"""Match the lead's own name, or the contact printed on its card."""
	term = (search or "").strip()
	if not term:
		return []

	like = f"%{term}%"
	or_filters: list[list] = [["lead_name", "like", like]]

	contacts = _contacts_matching(like)
	if contacts:
		or_filters.append(["contact", "in", contacts])

	return or_filters


def _contacts_matching(like: str) -> list[str]:
	"""Contacts whose name, company, mail, or phone contains the term."""
	return frappe.get_all(
		"Contact",
		or_filters=[[field, "like", like] for field in CONTACT_SEARCH_FIELDS],
		pluck="name",
		limit=MAX_SEARCH_CONTACTS,
	)


def _column_totals(filters: list[list], or_filters: list[list] | None = None) -> tuple[int, float]:
	"""How many leads a column really holds, and what they are worth.

	One light query for both — the displayed page cannot be summed, because it
	is only the first hundred.
	"""
	values = frappe.get_all(
		"Micro Lead", filters=filters, or_filters=or_filters or [], pluck="expected_value"
	)
	return len(values), sum(value or 0 for value in values)


def _contacts_in_segment(segment: str) -> list[str]:
	return [
		row["name"]
		for row in frappe.get_all("Contact", filters={"micro_segment": segment}, fields=["name"])
	]


def _enrich_leads(leads: list[dict]) -> None:
	"""Attach the contact details a card needs — one query per column, not per card."""
	attach_contact_details(leads)
