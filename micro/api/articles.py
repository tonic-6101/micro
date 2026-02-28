# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe import _


@frappe.whitelist()
def get_articles(
	filters: dict | None = None,
	order_by: str = "modified desc",
	limit_start: int = 0,
	limit_page_length: int = 20,
	search: str | None = None,
) -> dict:
	"""Get articles with filters, pagination, and search."""
	frappe.has_permission("Micro Article", throw=True)

	base_filters = filters or {}

	if search:
		base_filters["article_name"] = ["like", f"%{search}%"]

	default_fields = [
		"name",
		"article_name",
		"article_code",
		"category",
		"unit",
		"selling_price",
		"purchase_price",
		"is_active",
	]

	articles = frappe.get_list(
		"Micro Article",
		filters=base_filters,
		fields=default_fields,
		order_by=order_by,
		start=limit_start,
		page_length=limit_page_length,
	)

	total = frappe.db.count("Micro Article", filters=base_filters)

	return {"articles": articles, "total": total}


@frappe.whitelist()
def get_article(article_id: str) -> dict:
	"""Get a single article."""
	frappe.has_permission("Micro Article", throw=True)

	article = frappe.get_doc("Micro Article", article_id).as_dict()

	return {"article": article}
