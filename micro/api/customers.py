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
	"""Get contacts that are Micro customers (have micro_status set)."""
	frappe.has_permission("Contact", throw=True)

	base_filters = filters or {}
	base_filters["micro_status"] = ["is", "set"]

	if search:
		base_filters["full_name"] = ["like", f"%{search}%"]

	default_fields = [
		"name",
		"first_name",
		"last_name",
		"full_name",
		"email_id",
		"phone",
		"micro_contact_type",
		"micro_status",
		"company_name",
		"micro_city",
		"image",
		"micro_pipeline_stage",
		"micro_source",
		"micro_health_score",
	]

	customers = frappe.get_list(
		"Contact",
		filters=base_filters,
		fields=fields or default_fields,
		order_by=order_by,
		start=limit_start,
		page_length=limit_page_length,
	)

	total = frappe.db.count("Contact", filters=base_filters)

	return {"customers": customers, "total": total}


@frappe.whitelist()
def get_customer(customer_id: str) -> dict:
	"""Get a single contact (Micro customer) with unified notes timeline."""
	frappe.has_permission("Contact", throw=True)

	customer = frappe.get_doc("Contact", customer_id).as_dict()

	# CRM-structured notes (Call, Meeting, Email Summary, Note)
	micro_notes = frappe.get_list(
		"Micro Note",
		filters={"contact": customer_id},
		fields=["name", "subject", "note_type", "date", "content", "modified"],
		order_by="date desc",
		limit_page_length=50,
	)

	# Dock Notes linked to this contact (quick notes + any context-linked notes)
	dock_notes = []
	if frappe.db.exists("DocType", "Dock Note"):
		dock_notes = frappe.get_list(
			"Dock Note",
			filters={
				"reference_doctype": "Contact",
				"reference_name": customer_id,
				"deleted_at": ["is", "not set"],
			},
			fields=["name", "content", "pinned", "color", "owner", "creation", "modified"],
			order_by="creation desc",
			limit_page_length=50,
		)

	# Build unified timeline sorted by date descending
	timeline = []
	for n in micro_notes:
		timeline.append({
			"name": n.name,
			"source": "micro",
			"note_type": n.note_type,
			"subject": n.subject,
			"content": n.content,
			"date": str(n.date),
			"modified": str(n.modified),
		})
	for n in dock_notes:
		timeline.append({
			"name": n.name,
			"source": "dock",
			"note_type": "Quick Note",
			"subject": None,
			"content": n.content,
			"date": str(n.creation),
			"modified": str(n.modified),
			"pinned": n.pinned,
			"color": n.color,
		})

	timeline.sort(key=lambda x: x["date"], reverse=True)

	return {
		"customer": customer,
		"notes": timeline,
	}


@frappe.whitelist()
def create_customer(
	first_name: str,
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
	"""Create a new Contact with Micro CRM fields."""
	frappe.has_permission("Contact", "create", throw=True)

	if contact_type == "Person" and not last_name:
		frappe.throw(_("Last name is required for Person customers"))

	contact = frappe.new_doc("Contact")
	contact.first_name = first_name
	if last_name:
		contact.last_name = last_name
	if email:
		contact.email_id = email
		contact.append("email_ids", {"email_id": email, "is_primary": 1})
	if phone:
		contact.phone = phone
		contact.append("phone_nos", {"phone": phone, "is_primary_phone": 1})
	if mobile:
		contact.mobile_no = mobile
		contact.append("phone_nos", {"phone": mobile, "is_primary_mobile_no": 1})
	if organization:
		contact.company_name = organization

	# Micro CRM custom fields
	contact.micro_status = status
	contact.micro_contact_type = contact_type
	if source:
		contact.micro_source = source
	if pipeline_stage:
		contact.micro_pipeline_stage = pipeline_stage
	if website:
		contact.micro_website = website
	if notes:
		contact.micro_notes = notes
	if address:
		contact.micro_address = address
	if city:
		contact.micro_city = city
	if postal_code:
		contact.micro_postal_code = postal_code
	if country:
		contact.micro_country = country

	contact.insert()

	return {"customer": contact.as_dict()}


@frappe.whitelist()
def update_intelligence(customer_id: str, **kwargs) -> dict:
	"""Update intelligence card fields on a customer contact."""
	frappe.has_permission("Contact", "write", throw=True)

	allowed_fields = {
		"micro_client_loves",
		"micro_client_avoid",
		"micro_communication_style",
		"micro_personal_notes",
		"micro_opportunities",
		"micro_last_contact_date",
		"micro_last_contact_topic",
	}

	contact = frappe.get_doc("Contact", customer_id)
	updated = False
	for field in allowed_fields:
		if field in kwargs:
			contact.set(field, kwargs[field])
			updated = True

	if updated:
		contact.save()

	return {"customer": contact.as_dict()}
