# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe


def get_people_context(contact_name: str) -> dict | None:
	"""Provide Micro CRM context for a Contact in Dock People Hub.

	Returns pipeline stage, CRM status, acquisition source, and counts of
	linked offers, invoices, and notes for the given contact.
	"""
	contact = frappe.db.get_value(
		"Contact",
		contact_name,
		["micro_status", "micro_pipeline_stage", "micro_source"],
		as_dict=True,
	)

	if not contact or not contact.micro_status:
		return None

	fields = []

	if contact.micro_status:
		fields.append({"label": "Status", "value": contact.micro_status})

	if contact.micro_pipeline_stage:
		stage_name = frappe.db.get_value(
			"Micro Pipeline Stage", contact.micro_pipeline_stage, "stage_name"
		)
		fields.append({"label": "Pipeline", "value": stage_name or contact.micro_pipeline_stage})

	if contact.micro_source:
		fields.append({"label": "Source", "value": contact.micro_source})

	offer_count = frappe.db.count("Micro Offer Draft", {"contact": contact_name})
	if offer_count:
		fields.append({"label": "Offers", "value": str(offer_count)})

	invoice_count = frappe.db.count("Micro Invoice Draft", {"contact": contact_name})
	if invoice_count:
		fields.append({"label": "Invoice Drafts", "value": str(invoice_count)})

	return {
		"label": "CRM",
		"icon": "briefcase",
		"link": f"/micro/customers/{contact_name}",
		"fields": fields,
	}
