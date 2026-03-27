# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe import _

from micro.services.health_score import (
	_get_all_contact_revenues,
	_referral_score,
	_revenue_score,
	calculate_health_score,
	update_contact_health_score,
)


@frappe.whitelist()
def get_client_portfolio() -> dict:
	"""Return all Micro contacts ranked by health score with portfolio insights."""
	frappe.has_permission("Contact", throw=True)

	contacts = frappe.get_all(
		"Contact",
		filters={"micro_status": ["is", "set"]},
		fields=[
			"name",
			"first_name",
			"last_name",
			"full_name",
			"email_id",
			"image",
			"micro_status",
			"micro_contact_type",
			"micro_health_score",
			"micro_health_score_updated",
			"micro_referred_by",
		],
		order_by="micro_health_score asc, full_name asc",
	)

	revenues = _get_all_contact_revenues()
	total_revenue = sum(revenues.values())

	grade_order = {"A": 0, "B": 1, "C": 2, "D": 3, "": 4}

	portfolio = []
	for c in contacts:
		ltv = revenues.get(c.name, 0)
		referral_count = frappe.db.count(
			"Contact",
			filters={
				"micro_referred_by": c.name,
				"micro_status": ["is", "set"],
			},
		)
		portfolio.append({
			"name": c.name,
			"full_name": c.full_name,
			"image": c.image,
			"status": c.micro_status,
			"contact_type": c.micro_contact_type,
			"health_score": c.micro_health_score or "",
			"health_score_updated": str(c.micro_health_score_updated) if c.micro_health_score_updated else None,
			"lifetime_revenue": ltv,
			"referral_count": referral_count,
		})

	portfolio.sort(key=lambda x: (grade_order.get(x["health_score"], 4), -x["lifetime_revenue"]))

	# Portfolio insights
	a_clients = [c for c in portfolio if c["health_score"] == "A"]
	a_revenue = sum(c["lifetime_revenue"] for c in a_clients)
	a_pct_revenue = round((a_revenue / total_revenue * 100) if total_revenue else 0)
	a_pct_contacts = round((len(a_clients) / len(portfolio) * 100) if portfolio else 0)

	grade_counts = {}
	for c in portfolio:
		g = c["health_score"] or "—"
		grade_counts[g] = grade_counts.get(g, 0) + 1

	return {
		"portfolio": portfolio,
		"insights": {
			"total_contacts": len(portfolio),
			"total_revenue": total_revenue,
			"a_client_count": len(a_clients),
			"a_revenue_pct": a_pct_revenue,
			"a_contact_pct": a_pct_contacts,
			"grade_counts": grade_counts,
		},
	}


@frappe.whitelist()
def recalculate_score(contact_name: str) -> dict:
	"""Manually trigger health score recalculation for a single contact."""
	frappe.has_permission("Contact", throw=True)

	if not frappe.db.exists("Contact", contact_name):
		frappe.throw(_("Contact not found"))

	if not frappe.db.get_value("Contact", contact_name, "micro_status"):
		frappe.throw(_("Contact is not a Micro customer"))

	update_contact_health_score(contact_name)
	grade = frappe.db.get_value("Contact", contact_name, "micro_health_score")

	return {"health_score": grade}
