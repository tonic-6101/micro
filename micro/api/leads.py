# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe import _


@frappe.whitelist()
def get_leads(
	filters: dict | None = None,
	order_by: str = "modified desc",
	limit_start: int = 0,
	limit_page_length: int = 20,
	search: str | None = None,
) -> dict:
	"""Get leads with filters, pagination, and search."""
	frappe.has_permission("Micro Lead", throw=True)

	base_filters = filters or {}
	if search:
		base_filters["lead_name"] = ["like", f"%{search}%"]

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
	"""Get a single lead."""
	frappe.has_permission("Micro Lead", throw=True)
	lead = frappe.get_doc("Micro Lead", lead_id).as_dict()
	return {"lead": lead}


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
