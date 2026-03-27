# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Weekly Business Briefing — Monday snapshot of business health.

Phase 1.5 Intelligence Layer (Community):
- Pipeline summary: open leads, won/lost this week
- Follow-up queue: overdue and upcoming follow-ups
- Capacity status: utilized vs available hours
- One suggested action based on current state
"""

import frappe
from frappe import _
from frappe.utils import add_days, get_first_day, get_last_day, getdate, nowdate


@frappe.whitelist()
def get_weekly_briefing() -> dict:
	"""Return the weekly business briefing data."""
	today = getdate(nowdate())
	week_start = add_days(today, -today.weekday())  # Monday
	week_end = add_days(week_start, 6)  # Sunday
	first_day = get_first_day(today)
	last_day = get_last_day(today)

	# Pipeline snapshot
	open_leads = frappe.db.count("Micro Lead", {"status": "Open"}) if _doctype_exists("Micro Lead") else 0
	won_this_week = frappe.db.count(
		"Micro Lead",
		{"status": "Won", "modified": ["between", [week_start, week_end]]},
	) if _doctype_exists("Micro Lead") else 0
	lost_this_week = frappe.db.count(
		"Micro Lead",
		{"status": "Lost", "modified": ["between", [week_start, week_end]]},
	) if _doctype_exists("Micro Lead") else 0

	# Offers pending
	offers_pending = frappe.db.count("Micro Offer Draft", {"status": ["in", ["Draft", "Sent"]]})
	offers_accepted_this_month = frappe.db.count(
		"Micro Offer Draft",
		{"status": "Accepted", "modified": ["between", [first_day, last_day]]},
	)

	# Invoice drafts pending
	invoices_pending = frappe.db.count(
		"Micro Invoice Draft", {"status": "Draft"}
	)

	# Receipts this month
	receipts_this_month = frappe.db.count(
		"Micro Receipt",
		{"receipt_date": ["between", [first_day, last_day]]},
	)
	receipts_amount = frappe.db.sql(
		"SELECT COALESCE(SUM(amount), 0) FROM `tabMicro Receipt` "
		"WHERE receipt_date BETWEEN %s AND %s",
		(first_day, last_day),
	)[0][0] or 0

	# Follow-up queue
	overdue_follow_ups = 0
	upcoming_follow_ups = 0
	if _doctype_exists("Micro Lead"):
		overdue_follow_ups = frappe.db.count(
			"Micro Lead",
			{"status": "Open", "next_follow_up": ["<", today]},
		)
		upcoming_follow_ups = frappe.db.count(
			"Micro Lead",
			{"status": "Open", "next_follow_up": ["between", [today, add_days(today, 7)]]},
		)

	# Suggested action
	action = _suggest_action(
		open_leads=open_leads,
		offers_pending=offers_pending,
		overdue_follow_ups=overdue_follow_ups,
		invoices_pending=invoices_pending,
	)

	return {
		"week_of": str(week_start),
		"pipeline": {
			"open_leads": open_leads,
			"won_this_week": won_this_week,
			"lost_this_week": lost_this_week,
		},
		"offers": {
			"pending": offers_pending,
			"accepted_this_month": offers_accepted_this_month,
		},
		"invoices": {
			"pending": invoices_pending,
		},
		"receipts": {
			"count_this_month": receipts_this_month,
			"amount_this_month": float(receipts_amount),
		},
		"follow_ups": {
			"overdue": overdue_follow_ups,
			"upcoming_7_days": upcoming_follow_ups,
		},
		"suggested_action": action,
	}


def _suggest_action(
	open_leads: int,
	offers_pending: int,
	overdue_follow_ups: int,
	invoices_pending: int,
) -> dict:
	"""Generate one prioritized action suggestion."""
	if overdue_follow_ups > 0:
		return {
			"priority": "high",
			"message": _(
				"You have {0} overdue follow-up(s). Reconnect with these leads today."
			).format(overdue_follow_ups),
			"action_type": "follow_up",
		}
	if invoices_pending > 2:
		return {
			"priority": "medium",
			"message": _(
				"{0} invoice draft(s) waiting. Send them to your tax advisor this week."
			).format(invoices_pending),
			"action_type": "invoices",
		}
	if offers_pending > 3:
		return {
			"priority": "medium",
			"message": _(
				"{0} offers still pending response. Consider a friendly follow-up."
			).format(offers_pending),
			"action_type": "offers",
		}
	if open_leads == 0:
		return {
			"priority": "low",
			"message": _(
				"Pipeline is empty. A good week to reach out and build new connections."
			),
			"action_type": "pipeline",
		}
	return {
		"priority": "low",
		"message": _("Business is on track. Keep up the good work!"),
		"action_type": "none",
	}


def _doctype_exists(doctype: str) -> bool:
	"""Check if a DocType exists (safe for gradual rollout)."""
	return frappe.db.exists("DocType", doctype)
