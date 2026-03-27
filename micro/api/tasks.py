# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe import _


@frappe.whitelist()
def get_tasks(
	filters: dict | None = None,
	order_by: str = "modified desc",
	limit_start: int = 0,
	limit_page_length: int = 20,
	search: str | None = None,
) -> dict:
	"""Get tasks with filters, pagination, and search."""
	frappe.has_permission("Micro Task", throw=True)

	base_filters = filters or {}
	if search:
		base_filters["subject"] = ["like", f"%{search}%"]

	tasks = frappe.get_list(
		"Micro Task",
		filters=base_filters,
		fields=[
			"name", "subject", "status", "priority",
			"due_date", "contact", "lead", "assigned_to",
		],
		order_by=order_by,
		start=limit_start,
		page_length=limit_page_length,
	)

	total = frappe.db.count("Micro Task", filters=base_filters)
	return {"tasks": tasks, "total": total}


@frappe.whitelist()
def get_task(task_id: str) -> dict:
	"""Get a single task."""
	frappe.has_permission("Micro Task", throw=True)
	task = frappe.get_doc("Micro Task", task_id).as_dict()
	return {"task": task}
