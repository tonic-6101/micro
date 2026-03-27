# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Win Rate Intelligence — Offer outcome tracking and insights.

Phase 1.5 Intelligence Layer (Community):
- Tracks offer outcomes (Accepted/Declined/Expired)
- Calculates win rate after 10+ data points
- Provides insights by source, contact, and time period
"""

import frappe
from frappe import _
from frappe.utils import getdate, add_months, nowdate


@frappe.whitelist()
def get_win_rate_data() -> dict:
	"""Return win rate intelligence data."""
	today = getdate(nowdate())

	# Overall stats
	total_offers = frappe.db.count("Micro Offer Draft")
	accepted = frappe.db.count("Micro Offer Draft", {"status": "Accepted"})
	declined = frappe.db.count("Micro Offer Draft", {"status": "Declined"})
	expired = frappe.db.count("Micro Offer Draft", {"status": "Expired"})
	resolved = accepted + declined + expired

	has_enough_data = resolved >= 10
	win_rate = round((accepted / resolved * 100), 1) if resolved > 0 else 0

	# Monthly trend (last 6 months)
	monthly_trend = []
	for i in range(5, -1, -1):
		month_start = add_months(today.replace(day=1), -i)
		month_end = add_months(month_start, 1)

		month_accepted = frappe.db.count(
			"Micro Offer Draft",
			{"status": "Accepted", "date": ["between", [month_start, month_end]]},
		)
		month_resolved = 0
		for status in ("Accepted", "Declined", "Expired"):
			month_resolved += frappe.db.count(
				"Micro Offer Draft",
				{"status": status, "date": ["between", [month_start, month_end]]},
			)

		monthly_trend.append({
			"month": month_start.strftime("%Y-%m"),
			"label": _(month_start.strftime("%B %Y")),
			"accepted": month_accepted,
			"resolved": month_resolved,
			"win_rate": round((month_accepted / month_resolved * 100), 1) if month_resolved > 0 else 0,
		})

	# Average deal size
	avg_accepted = frappe.db.sql(
		"SELECT COALESCE(AVG(total), 0) FROM `tabMicro Offer Draft` WHERE status = 'Accepted'"
	)[0][0] or 0

	avg_declined = frappe.db.sql(
		"SELECT COALESCE(AVG(total), 0) FROM `tabMicro Offer Draft` WHERE status = 'Declined'"
	)[0][0] or 0

	return {
		"total_offers": total_offers,
		"accepted": accepted,
		"declined": declined,
		"expired": expired,
		"resolved": resolved,
		"win_rate": win_rate,
		"has_enough_data": has_enough_data,
		"monthly_trend": monthly_trend,
		"avg_accepted_value": float(avg_accepted),
		"avg_declined_value": float(avg_declined),
	}
