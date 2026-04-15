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
		"barcode",
		"category",
		"unit",
		"selling_price",
		"purchase_price",
		"is_active",
		"image",
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


@frappe.whitelist()
def get_categories() -> dict:
	"""Get all article categories for dropdowns."""
	frappe.has_permission("Micro Article", throw=True)

	categories = frappe.get_list(
		"Micro Article Category",
		fields=["name", "category_name"],
		order_by="category_name asc",
		limit_page_length=0,
	)

	return {"categories": categories}


@frappe.whitelist()
def create_category(category_name: str) -> dict:
	"""Create a new article category (inline from article form)."""
	frappe.has_permission("Micro Article Category", "create", throw=True)

	category = frappe.new_doc("Micro Article Category")
	category.category_name = category_name.strip()
	category.insert()

	return {"category": category.as_dict()}


@frappe.whitelist()
def create_article(
	article_name: str,
	selling_price: float = 0,
	article_code: str | None = None,
	barcode: str | None = None,
	category: str | None = None,
	unit: str = "Stück",
	is_active: bool = True,
	purchase_price: float = 0,
	description: str | None = None,
	supplier: str | None = None,
	notes: str | None = None,
) -> dict:
	"""Create a new article."""
	frappe.has_permission("Micro Article", "create", throw=True)

	article = frappe.new_doc("Micro Article")
	article.article_name = article_name
	article.selling_price = selling_price
	article.unit = unit
	article.is_active = 1 if is_active else 0
	article.purchase_price = purchase_price
	if article_code:
		article.article_code = article_code
	if barcode:
		article.barcode = barcode
	if category:
		article.category = category
	if description:
		article.description = description
	if supplier:
		article.supplier = supplier
	if notes:
		article.notes = notes

	article.insert()

	return {"article": article.as_dict()}


@frappe.whitelist(methods=["POST"])
def update_article(
	article_id: str,
	article_name: str | None = None,
	article_code: str | None = None,
	barcode: str | None = None,
	category: str | None = None,
	unit: str | None = None,
	is_active: bool | None = None,
	selling_price: float | None = None,
	purchase_price: float | None = None,
	description: str | None = None,
	supplier: str | None = None,
	notes: str | None = None,
) -> dict:
	"""Update an existing article."""
	frappe.has_permission("Micro Article", "write", throw=True)

	article = frappe.get_doc("Micro Article", article_id)

	if article_name is not None:
		article.article_name = article_name
	if article_code is not None:
		article.article_code = article_code
	if barcode is not None:
		article.barcode = barcode
	if category is not None:
		article.category = category
	if unit is not None:
		article.unit = unit
	if is_active is not None:
		article.is_active = 1 if is_active else 0
	if selling_price is not None:
		article.selling_price = selling_price
	if purchase_price is not None:
		article.purchase_price = purchase_price
	if description is not None:
		article.description = description
	if supplier is not None:
		article.supplier = supplier
	if notes is not None:
		article.notes = notes

	article.save()

	return {"article": article.as_dict()}
