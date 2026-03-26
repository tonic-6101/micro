# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe import _


@frappe.whitelist()
def get_pipeline(show_closed: bool = False) -> dict:
	"""Get pipeline stages with grouped contacts for Kanban view."""
	frappe.has_permission("Contact", throw=True)

	stage_filters = {}
	if not show_closed:
		stage_filters["is_closed"] = 0

	stages = frappe.get_list(
		"Micro Pipeline Stage",
		filters=stage_filters,
		fields=["name", "stage_name", "sort_order", "color", "is_closed"],
		order_by="sort_order asc",
	)

	customer_fields = [
		"name",
		"full_name",
		"micro_contact_type",
		"email_id",
		"phone",
		"micro_source",
		"micro_status",
		"image",
		"micro_pipeline_stage",
	]

	result = []
	for stage in stages:
		customers = frappe.get_list(
			"Contact",
			filters={"micro_pipeline_stage": stage.name},
			fields=customer_fields,
			order_by="modified desc",
		)
		result.append({"stage": stage, "customers": customers})

	# Contacts with micro_status set but no pipeline stage
	unassigned = frappe.get_list(
		"Contact",
		filters={
			"micro_status": ["is", "set"],
			"micro_pipeline_stage": ["in", ["", None]],
		},
		fields=customer_fields,
		order_by="modified desc",
	)

	return {"stages": result, "unassigned": unassigned}


@frappe.whitelist()
def move_customer(customer_id: str, stage_id: str) -> dict:
	"""Move a contact to a different pipeline stage."""
	frappe.has_permission("Contact", "write", throw=True)

	if not frappe.db.exists("Contact", customer_id):
		frappe.throw(_("Customer not found"))

	if not frappe.db.exists("Micro Pipeline Stage", stage_id):
		frappe.throw(_("Pipeline stage not found"))

	frappe.db.set_value("Contact", customer_id, "micro_pipeline_stage", stage_id)

	return {"success": True}


@frappe.whitelist()
def get_stages() -> dict:
	"""Get all pipeline stages ordered by sort_order."""
	frappe.has_permission("Micro Pipeline Stage", throw=True)

	stages = frappe.get_list(
		"Micro Pipeline Stage",
		fields=["name", "stage_name", "sort_order", "color", "is_closed"],
		order_by="sort_order asc",
	)

	return {"stages": stages}
