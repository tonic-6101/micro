# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe import _


@frappe.whitelist()
def get_customers(
	filters: dict | None = None,
	fields: list | None = None,
	order_by: str = "modified desc",
	limit_start: int = 0,
	limit_page_length: int = 20,
	search: str | None = None,
) -> dict:
	"""Get customers with filters, pagination, and search."""
	frappe.has_permission("Micro Customer", throw=True)

	base_filters = filters or {}

	if search:
		base_filters["full_name"] = ["like", f"%{search}%"]

	default_fields = [
		"name",
		"name1",
		"last_name",
		"full_name",
		"email",
		"phone",
		"contact_type",
		"status",
		"organization",
		"city",
		"image",
		"pipeline_stage",
	]

	customers = frappe.get_list(
		"Micro Customer",
		filters=base_filters,
		fields=fields or default_fields,
		order_by=order_by,
		start=limit_start,
		page_length=limit_page_length,
	)

	total = frappe.db.count("Micro Customer", filters=base_filters)

	return {"customers": customers, "total": total}


@frappe.whitelist()
def get_customer(customer_id: str) -> dict:
	"""Get a single customer with related notes."""
	frappe.has_permission("Micro Customer", throw=True)

	customer = frappe.get_doc("Micro Customer", customer_id).as_dict()

	notes = frappe.get_list(
		"Micro Note",
		filters={"contact": customer_id},
		fields=["name", "subject", "note_type", "date", "content"],
		order_by="date desc",
		limit_page_length=20,
	)

	return {
		"customer": customer,
		"notes": notes,
	}


@frappe.whitelist()
def create_customer(
	name1: str,
	contact_type: str = "Person",
	status: str = "Potential",
	last_name: str | None = None,
	email: str | None = None,
	phone: str | None = None,
	mobile: str | None = None,
	website: str | None = None,
	organization: str | None = None,
	source: str | None = None,
	pipeline_stage: str | None = None,
	address: str | None = None,
	city: str | None = None,
	postal_code: str | None = None,
	country: str | None = None,
	notes: str | None = None,
) -> dict:
	"""Create a new customer."""
	frappe.has_permission("Micro Customer", "create", throw=True)

	if contact_type == "Person" and not last_name:
		frappe.throw(_("Last name is required for Person customers"))

	customer = frappe.new_doc("Micro Customer")
	customer.name1 = name1
	customer.contact_type = contact_type
	customer.status = status

	if last_name:
		customer.last_name = last_name
	if email:
		customer.email = email
	if phone:
		customer.phone = phone
	if mobile:
		customer.mobile = mobile
	if website:
		customer.website = website
	if organization:
		customer.organization = organization
	if source:
		customer.source = source
	if pipeline_stage:
		customer.pipeline_stage = pipeline_stage
	if address:
		customer.address = address
	if city:
		customer.city = city
	if postal_code:
		customer.postal_code = postal_code
	if country:
		customer.country = country
	if notes:
		customer.notes = notes

	customer.insert()

	return {"customer": customer.as_dict()}
