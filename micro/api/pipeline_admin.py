# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Pipeline and stage management from the Micro UI, so nobody has to open Desk."""

import frappe
from frappe import _

# A stage is open, or it closes the deal one way or the other. One value beats
# two checkboxes that can contradict each other.
OUTCOME_OPEN = "open"
OUTCOME_WIN = "win"
OUTCOME_LOSS = "loss"

STARTER_STAGES = [
	("New", "Blue", OUTCOME_OPEN),
	("Contacted", "Yellow", OUTCOME_OPEN),
	("Offer Sent", "Orange", OUTCOME_OPEN),
	("Won", "Green", OUTCOME_WIN),
	("Lost", "Red", OUTCOME_LOSS),
]


@frappe.whitelist()
def get_pipeline_setup(pipeline: str) -> dict:
	"""Everything the management dialog needs, including what blocks deletion."""
	frappe.has_permission("Micro Pipeline", throw=True)

	doc = frappe.get_doc("Micro Pipeline", pipeline)

	stages = frappe.get_list(
		"Micro Pipeline Stage",
		filters={"pipeline": pipeline},
		fields=["name", "stage_name", "sort_order", "color", "is_closed", "is_win_stage", "is_loss_stage"],
		order_by="sort_order asc",
	)
	for stage in stages:
		stage["outcome"] = _outcome_of(stage)
		stage["lead_count"] = frappe.db.count("Micro Lead", {"stage": stage["name"]})

	return {
		"pipeline": {
			"name": doc.name,
			"pipeline_name": doc.pipeline_name,
			"segment": doc.segment,
			"description": doc.description,
			"sort_order": doc.sort_order,
			"is_default": doc.is_default,
			"is_active": doc.is_active,
		},
		"stages": stages,
		"lead_count": frappe.db.count("Micro Lead", {"pipeline": pipeline}),
	}


@frappe.whitelist()
def create_pipeline(
	pipeline_name: str,
	segment: str | None = None,
	description: str | None = None,
	with_starter_stages: bool = True,
) -> dict:
	"""Create a pipeline and give it stages, so the board is never born empty."""
	frappe.has_permission("Micro Pipeline", "create", throw=True)

	if frappe.db.exists("Micro Pipeline", pipeline_name):
		frappe.throw(_("A pipeline named {0} already exists.").format(frappe.bold(pipeline_name)))

	last_order = (
		frappe.db.get_value("Micro Pipeline", {}, "sort_order", order_by="sort_order desc") or 0
	)

	pipeline = frappe.new_doc("Micro Pipeline")
	pipeline.pipeline_name = pipeline_name
	pipeline.segment = segment
	pipeline.description = description
	pipeline.sort_order = last_order + 10
	pipeline.is_active = 1
	pipeline.insert()

	if with_starter_stages:
		for index, (stage_name, color, outcome) in enumerate(STARTER_STAGES):
			_insert_stage(pipeline.name, stage_name, color, outcome, (index + 1) * 10)

	return {"pipeline": pipeline.name}


@frappe.whitelist()
def update_pipeline(
	pipeline: str,
	pipeline_name: str | None = None,
	segment: str | None = None,
	description: str | None = None,
	is_default: bool | None = None,
	is_active: bool | None = None,
) -> dict:
	"""Update a pipeline. A changed name is a real rename — links follow along."""
	frappe.has_permission("Micro Pipeline", "write", throw=True)

	doc = frappe.get_doc("Micro Pipeline", pipeline)

	if segment is not None:
		doc.segment = segment or None
	if description is not None:
		doc.description = description or None
	if is_default is not None:
		doc.is_default = 1 if frappe.utils.cint(is_default) else 0
	if is_active is not None:
		doc.is_active = 1 if frappe.utils.cint(is_active) else 0
	doc.save()

	new_name = (pipeline_name or "").strip()
	if new_name and new_name != doc.name:
		if frappe.db.exists("Micro Pipeline", new_name):
			frappe.throw(_("A pipeline named {0} already exists.").format(frappe.bold(new_name)))
		# Renames the document and rewrites every link on leads and stages.
		frappe.rename_doc("Micro Pipeline", doc.name, new_name)
		return {"pipeline": new_name, "renamed": True}

	return {"pipeline": doc.name, "renamed": False}


@frappe.whitelist()
def delete_pipeline(pipeline: str) -> dict:
	"""Delete a pipeline with its stages. Refuses while leads still live in it."""
	frappe.has_permission("Micro Pipeline", "delete", throw=True)

	lead_count = frappe.db.count("Micro Lead", {"pipeline": pipeline})
	if lead_count:
		frappe.throw(
			_(
				"{0} lead(s) are still in this pipeline. Move or delete them first, "
				"or deactivate the pipeline to keep its history."
			).format(lead_count)
		)

	for stage in frappe.get_all("Micro Pipeline Stage", filters={"pipeline": pipeline}, pluck="name"):
		frappe.delete_doc("Micro Pipeline Stage", stage)

	frappe.delete_doc("Micro Pipeline", pipeline)

	return {"success": True}


@frappe.whitelist()
def reorder_pipelines(pipeline_ids: list | str) -> dict:
	"""Persist the tab order."""
	frappe.has_permission("Micro Pipeline", "write", throw=True)

	for index, name in enumerate(_as_list(pipeline_ids)):
		frappe.db.set_value("Micro Pipeline", name, "sort_order", (index + 1) * 10)

	return {"success": True}


@frappe.whitelist()
def create_stage(
	pipeline: str,
	stage_name: str,
	color: str = "Gray",
	outcome: str = OUTCOME_OPEN,
) -> dict:
	"""Append a stage to a pipeline."""
	frappe.has_permission("Micro Pipeline Stage", "create", throw=True)

	last_order = (
		frappe.db.get_value(
			"Micro Pipeline Stage", {"pipeline": pipeline}, "sort_order", order_by="sort_order desc"
		)
		or 0
	)
	stage = _insert_stage(pipeline, stage_name, color, outcome, last_order + 10)

	return {"stage": stage.name}


@frappe.whitelist()
def update_stage(
	stage: str,
	stage_name: str | None = None,
	color: str | None = None,
	outcome: str | None = None,
) -> dict:
	"""Rename/recolour a stage or change what it means for the deal."""
	frappe.has_permission("Micro Pipeline Stage", "write", throw=True)

	doc = frappe.get_doc("Micro Pipeline Stage", stage)

	if stage_name:
		doc.stage_name = stage_name
	if color:
		doc.color = color
	if outcome is not None:
		_apply_outcome(doc, outcome)
	doc.save()

	return {"stage": doc.name}


@frappe.whitelist()
def delete_stage(stage: str, move_leads_to: str | None = None) -> dict:
	"""Delete a stage, optionally moving its leads to another stage first."""
	frappe.has_permission("Micro Pipeline Stage", "delete", throw=True)

	leads = frappe.get_all("Micro Lead", filters={"stage": stage}, pluck="name")

	if leads and not move_leads_to:
		frappe.throw(
			_("{0} lead(s) are in this stage. Choose a stage to move them to first.").format(len(leads))
		)

	if leads:
		if frappe.db.get_value("Micro Pipeline Stage", move_leads_to, "pipeline") != frappe.db.get_value(
			"Micro Pipeline Stage", stage, "pipeline"
		):
			frappe.throw(_("Leads can only be moved to a stage of the same pipeline."))

		for lead_name in leads:
			lead = frappe.get_doc("Micro Lead", lead_name)
			lead.stage = move_leads_to
			lead.save()

	frappe.delete_doc("Micro Pipeline Stage", stage)

	return {"success": True, "moved": len(leads)}


@frappe.whitelist()
def reorder_stages(pipeline: str, stage_ids: list | str) -> dict:
	"""Persist the column order of one pipeline."""
	frappe.has_permission("Micro Pipeline Stage", "write", throw=True)

	for index, name in enumerate(_as_list(stage_ids)):
		if frappe.db.get_value("Micro Pipeline Stage", name, "pipeline") != pipeline:
			frappe.throw(_("Stage {0} does not belong to this pipeline.").format(name))
		frappe.db.set_value("Micro Pipeline Stage", name, "sort_order", (index + 1) * 10)

	return {"success": True}


@frappe.whitelist()
def create_segment(segment_name: str, color: str = "Gray") -> dict:
	"""Create a segment without leaving the pipeline dialog."""
	frappe.has_permission("Micro Segment", "create", throw=True)

	if frappe.db.exists("Micro Segment", segment_name):
		return {"segment": segment_name, "created": False}

	last_order = frappe.db.get_value("Micro Segment", {}, "sort_order", order_by="sort_order desc") or 0

	segment = frappe.new_doc("Micro Segment")
	segment.segment_name = segment_name
	segment.color = color
	segment.sort_order = last_order + 10
	segment.is_active = 1
	segment.insert()

	return {"segment": segment.name, "created": True}


def _insert_stage(pipeline: str, stage_name: str, color: str, outcome: str, sort_order: int):
	stage = frappe.new_doc("Micro Pipeline Stage")
	stage.pipeline = pipeline
	stage.stage_name = stage_name
	stage.color = color
	stage.sort_order = sort_order
	_apply_outcome(stage, outcome)
	stage.insert()
	return stage


def _apply_outcome(stage, outcome: str) -> None:
	if outcome not in (OUTCOME_OPEN, OUTCOME_WIN, OUTCOME_LOSS):
		frappe.throw(_("Unknown stage outcome: {0}").format(outcome))

	stage.is_win_stage = 1 if outcome == OUTCOME_WIN else 0
	stage.is_loss_stage = 1 if outcome == OUTCOME_LOSS else 0
	if outcome == OUTCOME_OPEN:
		stage.is_closed = 0


def _outcome_of(stage: dict) -> str:
	if stage.get("is_win_stage"):
		return OUTCOME_WIN
	if stage.get("is_loss_stage"):
		return OUTCOME_LOSS
	return OUTCOME_OPEN


def _as_list(value: list | str) -> list:
	if isinstance(value, str):
		return frappe.parse_json(value)
	return value or []
