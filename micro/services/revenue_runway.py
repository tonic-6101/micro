# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Revenue Runway — Timeline of confirmed and pipeline weeks.

Phase 1.5 Intelligence Layer (Community):
- Confirmed: sum of accepted offer drafts
- Pipeline: sum of open/sent offer drafts (weighted by stage probability)
- Runway: how many weeks/months the pipeline covers based on monthly average
"""

import frappe
from frappe import _
from frappe.utils import getdate, add_months, nowdate


@frappe.whitelist()
def get_revenue_runway() -> dict:
	"""Return revenue runway data."""
	today = getdate(nowdate())

	# Confirmed revenue: accepted offers
	confirmed = frappe.db.sql(
		"SELECT COALESCE(SUM(total), 0) FROM `tabMicro Offer Draft` WHERE status = 'Accepted'"
	)[0][0] or 0

	# Pipeline: open/sent offers (not yet decided)
	pipeline = frappe.db.sql(
		"SELECT COALESCE(SUM(total), 0) FROM `tabMicro Offer Draft` "
		"WHERE status IN ('Draft', 'Sent')"
	)[0][0] or 0

	# Monthly average from accepted offers in last 6 months
	six_months_ago = add_months(today, -6)
	monthly_totals = frappe.db.sql(
		"SELECT COALESCE(SUM(total), 0) FROM `tabMicro Offer Draft` "
		"WHERE status = 'Accepted' AND date >= %s",
		six_months_ago,
	)[0][0] or 0
	monthly_average = float(monthly_totals) / 6.0

	# Runway calculation
	weekly_average = monthly_average / 4.33 if monthly_average > 0 else 0
	confirmed_weeks = round(float(confirmed) / weekly_average, 1) if weekly_average > 0 else 0
	pipeline_weeks = round(float(pipeline) * 0.5 / weekly_average, 1) if weekly_average > 0 else 0

	# Monthly breakdown (last 6 months of accepted offers)
	monthly_breakdown = []
	for i in range(5, -1, -1):
		month_start = add_months(today.replace(day=1), -i)
		month_end = add_months(month_start, 1)

		month_total = frappe.db.sql(
			"SELECT COALESCE(SUM(total), 0) FROM `tabMicro Offer Draft` "
			"WHERE status = 'Accepted' AND date BETWEEN %s AND %s",
			(month_start, month_end),
		)[0][0] or 0

		monthly_breakdown.append({
			"month": month_start.strftime("%Y-%m"),
			"label": _(month_start.strftime("%B %Y")),
			"total": float(month_total),
		})

	return {
		"confirmed": float(confirmed),
		"pipeline": float(pipeline),
		"monthly_average": round(monthly_average, 2),
		"weekly_average": round(weekly_average, 2),
		"confirmed_weeks": confirmed_weeks,
		"pipeline_weeks": pipeline_weeks,
		"total_runway_weeks": round(confirmed_weeks + pipeline_weeks, 1),
		"monthly_breakdown": monthly_breakdown,
	}
