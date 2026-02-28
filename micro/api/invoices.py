# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe import _


@frappe.whitelist()
def get_invoices(
	filters: dict | None = None,
	order_by: str = "modified desc",
	limit_start: int = 0,
	limit_page_length: int = 20,
	search: str | None = None,
) -> dict:
	"""Get invoice drafts with filters, pagination, and search."""
	frappe.has_permission("Micro Invoice Draft", throw=True)

	base_filters = filters or {}

	if search:
		base_filters["reference"] = ["like", f"%{search}%"]

	default_fields = [
		"name",
		"reference",
		"title",
		"contact",
		"date",
		"status",
		"source",
		"total",
	]

	invoices = frappe.get_list(
		"Micro Invoice Draft",
		filters=base_filters,
		fields=default_fields,
		order_by=order_by,
		start=limit_start,
		page_length=limit_page_length,
	)

	total = frappe.db.count("Micro Invoice Draft", filters=base_filters)

	return {"invoices": invoices, "total": total}


@frappe.whitelist()
def get_invoice(invoice_id: str) -> dict:
	"""Get a single invoice draft with items."""
	frappe.has_permission("Micro Invoice Draft", throw=True)

	invoice = frappe.get_doc("Micro Invoice Draft", invoice_id).as_dict()

	return {"invoice": invoice}


@frappe.whitelist()
def create_invoice(
	contact: str,
	title: str | None = None,
	items: list | None = None,
) -> dict:
	"""Create a new invoice draft manually."""
	frappe.has_permission("Micro Invoice Draft", "create", throw=True)

	invoice = frappe.new_doc("Micro Invoice Draft")
	invoice.contact = contact
	if title:
		invoice.title = title

	for item_data in items or []:
		invoice.append("items", {
			"article": item_data.get("article"),
			"description": item_data.get("description", ""),
			"quantity": item_data.get("quantity", 1),
			"rate": item_data.get("rate", 0),
			"unit": item_data.get("unit", ""),
		})

	invoice.insert()

	return {"invoice": invoice.as_dict()}
