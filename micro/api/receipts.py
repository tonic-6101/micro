# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe import _


@frappe.whitelist()
def get_receipts(
	filters: dict | None = None,
	order_by: str = "receipt_date desc",
	limit_start: int = 0,
	limit_page_length: int = 20,
	search: str | None = None,
	category: str | None = None,
) -> dict:
	"""Get receipts with filters, pagination, and search."""
	frappe.has_permission("Micro Receipt", throw=True)

	base_filters = filters or {}

	if search:
		base_filters["vendor"] = ["like", f"%{search}%"]

	if category:
		base_filters["category"] = category

	default_fields = [
		"name",
		"receipt_date",
		"vendor",
		"amount",
		"category",
		"description",
		"exported",
		"export_date",
	]

	receipts = frappe.get_list(
		"Micro Receipt",
		filters=base_filters,
		fields=default_fields,
		order_by=order_by,
		start=limit_start,
		page_length=limit_page_length,
	)

	total = frappe.db.count("Micro Receipt", filters=base_filters)

	return {"receipts": receipts, "total": total}


@frappe.whitelist()
def get_receipt(receipt_id: str) -> dict:
	"""Get a single receipt."""
	frappe.has_permission("Micro Receipt", throw=True)

	receipt = frappe.get_doc("Micro Receipt", receipt_id).as_dict()

	return {"receipt": receipt}
