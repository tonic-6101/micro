# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe import _


@frappe.whitelist()
def get_dashboard_kpis() -> dict:
	"""Return aggregated KPIs for the Micro dashboard.

	Customers are Contacts carrying `micro_status`. That field is what makes a
	Contact a customer — an address book entry Micro has never worked with is
	not one, and counting the whole `tabContact` would report the address book
	rather than the business.
	"""
	customers_total = frappe.db.count("Contact", {"micro_status": ["is", "set"]})

	customers_by_status = {}
	for row in frappe.db.sql(
		"SELECT micro_status, COUNT(*) as cnt FROM `tabContact` "
		"WHERE IFNULL(micro_status, '') != '' GROUP BY micro_status",
		as_dict=True,
	):
		customers_by_status[row.micro_status] = row.cnt

	customers_by_source = {}
	for row in frappe.db.sql(
		"SELECT COALESCE(NULLIF(micro_source, ''), 'Unknown') as source, COUNT(*) as cnt "
		"FROM `tabContact` WHERE IFNULL(micro_status, '') != '' GROUP BY source",
		as_dict=True,
	):
		customers_by_source[row.source] = row.cnt

	offers_total = frappe.db.count("Micro Offer Draft")
	offers_by_status = {}
	for row in frappe.db.sql(
		"SELECT status, COUNT(*) as cnt FROM `tabMicro Offer Draft` GROUP BY status",
		as_dict=True,
	):
		offers_by_status[row.status] = row.cnt

	invoices_total = frappe.db.count("Micro Invoice Draft")
	invoices_by_status = {}
	for row in frappe.db.sql(
		"SELECT status, COUNT(*) as cnt FROM `tabMicro Invoice Draft` GROUP BY status",
		as_dict=True,
	):
		invoices_by_status[row.status] = row.cnt

	receipts_total = frappe.db.count("Micro Receipt")
	receipts_unexported = frappe.db.count("Micro Receipt", {"exported": 0})

	receipts_by_category = {}
	for row in frappe.db.sql(
		"SELECT category, COUNT(*) as cnt FROM `tabMicro Receipt` GROUP BY category",
		as_dict=True,
	):
		receipts_by_category[row.category] = row.cnt

	receipt_total_amount = (
		frappe.db.sql(
			"SELECT COALESCE(SUM(amount), 0) FROM `tabMicro Receipt`"
		)[0][0]
		or 0
	)

	recent_activity = _get_recent_activity()

	return {
		"customers": {
			"total": customers_total,
			"by_status": customers_by_status,
			"by_source": customers_by_source,
		},
		"offers": {"total": offers_total, "by_status": offers_by_status},
		"invoices": {"total": invoices_total, "by_status": invoices_by_status},
		"receipts": {
			"total": receipts_total,
			"unexported": receipts_unexported,
			"by_category": receipts_by_category,
			"total_amount": float(receipt_total_amount),
		},
		"recent_activity": recent_activity,
	}


def _get_recent_activity(limit: int = 10) -> list[dict]:
	"""Get the most recently modified documents across all Micro DocTypes."""
	doctypes = [
		("Micro Offer Draft", "reference"),
		("Micro Invoice Draft", "reference"),
		("Micro Receipt", "vendor"),
	]

	activity = []

	# Customers, which are Contacts that Micro has a status for.
	customers = frappe.get_all(
		"Contact",
		filters={"micro_status": ["is", "set"]},
		fields=["name", "full_name as label", "modified"],
		order_by="modified desc",
		limit_page_length=3,
	)
	for doc in customers:
		activity.append(
			{
				"doctype": "Contact",
				"name": doc.name,
				"label": doc.label or doc.name,
				"modified": str(doc.modified),
			}
		)

	for doctype, label_field in doctypes:
		docs = frappe.get_all(
			doctype,
			fields=["name", f"{label_field} as label", "modified"],
			order_by="modified desc",
			limit_page_length=3,
		)
		for doc in docs:
			activity.append(
				{
					"doctype": doctype,
					"name": doc.name,
					"label": doc.label or doc.name,
					"modified": str(doc.modified),
				}
			)

	activity.sort(key=lambda x: x["modified"], reverse=True)
	return activity[:limit]
