# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe import _


@frappe.whitelist()
def get_offers(
	filters: dict | None = None,
	order_by: str = "modified desc",
	limit_start: int = 0,
	limit_page_length: int = 20,
	search: str | None = None,
) -> dict:
	"""Get offer drafts with filters, pagination, and search."""
	frappe.has_permission("Micro Offer Draft", throw=True)

	base_filters = filters or {}

	if search:
		base_filters["reference"] = ["like", f"%{search}%"]

	default_fields = [
		"name",
		"reference",
		"title",
		"contact",
		"date",
		"valid_until",
		"status",
		"total",
	]

	offers = frappe.get_list(
		"Micro Offer Draft",
		filters=base_filters,
		fields=default_fields,
		order_by=order_by,
		start=limit_start,
		page_length=limit_page_length,
	)

	total = frappe.db.count("Micro Offer Draft", filters=base_filters)

	return {"offers": offers, "total": total}


@frappe.whitelist()
def get_offer(offer_id: str) -> dict:
	"""Get a single offer draft with items."""
	frappe.has_permission("Micro Offer Draft", throw=True)

	offer = frappe.get_doc("Micro Offer Draft", offer_id).as_dict()

	return {"offer": offer}


@frappe.whitelist()
def create_offer(contact: str, title: str | None = None, items: list | None = None) -> dict:
	"""Create a new offer draft.

	Items should be a list of dicts with: article, description, quantity, rate, unit.
	"""
	frappe.has_permission("Micro Offer Draft", "create", throw=True)

	offer = frappe.new_doc("Micro Offer Draft")
	offer.contact = contact
	if title:
		offer.title = title

	for item_data in items or []:
		item = offer.append("items", {})
		item.article = item_data.get("article")
		item.description = item_data.get("description", "")
		item.quantity = item_data.get("quantity", 1)
		item.rate = item_data.get("rate", 0)
		item.unit = item_data.get("unit", "")

	offer.insert()

	return {"offer": offer.as_dict()}
