# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

"""Jana Daily Briefing source — Micro CRM and sales data."""

from __future__ import annotations

import frappe
from frappe.utils import add_days, getdate, nowdate


@frappe.whitelist()
def get_briefing(date: str | None = None) -> dict:
	"""Return a briefing summary of sales intelligence data.

	Includes follow-up nudges, pipeline snapshot, and top KPIs.
	"""
	today = getdate(date or nowdate())

	return {
		"nudges": _get_nudges(today),
		"pipeline": _get_pipeline_snapshot(),
		"kpis": _get_kpis(),
	}


def _get_nudges(today) -> dict:
	"""Return leads and offers needing follow-up."""
	stale_days = 7

	stale_leads = frappe.get_all(
		"Micro Lead",
		filters={
			"owner": frappe.session.user,
			"status": ["not in", ["Won", "Lost", "Closed"]],
			"modified": ["<", add_days(today, -stale_days)],
		},
		fields=["name", "lead_name", "status", "modified"],
		order_by="modified asc",
		limit_page_length=5,
	)

	unanswered_offers = frappe.get_all(
		"Micro Offer Draft",
		filters={
			"owner": frappe.session.user,
			"status": "Sent",
			"modified": ["<", add_days(today, -stale_days)],
		},
		fields=["name", "title", "contact", "modified"],
		order_by="modified asc",
		limit_page_length=5,
	)

	return {
		"stale_leads": stale_leads,
		"unanswered_offers": unanswered_offers,
	}


def _get_pipeline_snapshot() -> dict:
	"""Return a high-level pipeline summary."""
	# Count leads per status using SQL (Frappe v16 disallows SQL functions in fields)
	stages = frappe.db.sql(
		"""
		SELECT status, COUNT(name) as cnt
		FROM `tabMicro Lead`
		WHERE owner = %(user)s
		  AND status NOT IN ('Won', 'Lost', 'Closed')
		GROUP BY status
		ORDER BY cnt DESC
		""",
		{"user": frappe.session.user},
		as_dict=True,
	)

	return {
		"active_leads": sum(s.cnt for s in stages),
		"by_stage": {s.status: s.cnt for s in stages},
	}


def _get_kpis() -> dict:
	"""Return top-level sales KPIs for the current month."""
	from frappe.utils import get_first_day, get_last_day

	today = getdate(nowdate())
	month_start = get_first_day(today)
	month_end = get_last_day(today)

	won_this_month = frappe.db.count(
		"Micro Lead",
		filters={
			"owner": frappe.session.user,
			"status": "Won",
			"modified": ["between", [month_start, month_end]],
		},
	)

	lost_this_month = frappe.db.count(
		"Micro Lead",
		filters={
			"owner": frappe.session.user,
			"status": "Lost",
			"modified": ["between", [month_start, month_end]],
		},
	)

	return {
		"won_this_month": won_this_month,
		"lost_this_month": lost_this_month,
	}
