# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Emotional design moments — backend data for celebration cards and milestones.

Provides aggregated pipeline/milestone data for the Micro SPA to render
contextual celebration moments (Offer Accepted, First Offer Sent, Annual Wrapped).
"""

import frappe
from frappe import _
from frappe.utils import getdate, get_first_day, get_last_day, nowdate


@frappe.whitelist()
def get_offer_accepted_data(offer_id: str) -> dict:
	"""Return contextual data for the Offer Accepted celebration card.

	Includes offer total, contact name, pipeline total for the current month,
	and whether this month is the user's best month to date.
	"""
	frappe.has_permission("Micro Offer Draft", throw=True)

	offer = frappe.get_doc("Micro Offer Draft", offer_id)
	offer_total = float(offer.get("total") or 0)
	contact_name = offer.get("contact") or ""

	# Pipeline total this month (sum of all accepted offers in the offer's month)
	offer_date = getdate(offer.get("date") or nowdate())
	month_start = get_first_day(offer_date)
	month_end = get_last_day(offer_date)

	pipeline_this_month = float(
		frappe.db.sql(
			"""
			SELECT COALESCE(SUM(total), 0)
			FROM `tabMicro Offer Draft`
			WHERE status = 'Accepted'
			  AND date BETWEEN %s AND %s
			""",
			(month_start, month_end),
		)[0][0]
		or 0
	)

	# Best month to date: find the month with the highest accepted pipeline
	monthly_totals = frappe.db.sql(
		"""
		SELECT DATE_FORMAT(date, '%%Y-%%m') AS month_key,
		       SUM(total) AS month_total
		FROM `tabMicro Offer Draft`
		WHERE status = 'Accepted'
		  AND date IS NOT NULL
		GROUP BY month_key
		ORDER BY month_total DESC
		LIMIT 1
		""",
		as_dict=True,
	)

	is_best_month = False
	best_month_label = None
	best_month_value = None

	if monthly_totals:
		best = monthly_totals[0]
		best_month_value = float(best.month_total or 0)
		best_month_label = best.month_key

		current_month_key = offer_date.strftime("%Y-%m")
		if best.month_key == current_month_key:
			is_best_month = True

	return {
		"offer_total": offer_total,
		"contact_name": contact_name,
		"pipeline_this_month": pipeline_this_month,
		"is_best_month": is_best_month,
		"best_month_label": best_month_label,
		"best_month_value": best_month_value,
	}


@frappe.whitelist()
def get_first_offer_sent_status(force: bool | str = False) -> dict:
	"""Check whether to show the First Offer Sent milestone overlay.

	Returns should_show=True only when the user has exactly one offer that
	has left Draft status AND has not yet dismissed the milestone.

	Pass force=1 to bypass the "already seen" check (for testing).
	"""
	frappe.has_permission("Micro Offer Draft", throw=True)

	force = force in (True, "1", "true", 1)

	if not force:
		already_seen = bool(
			frappe.db.get_single_value("Micro Settings", "first_offer_sent_seen")
		)
		if already_seen:
			return {"should_show": False}

		# Count offers that have progressed beyond Draft
		sent_count = frappe.db.count(
			"Micro Offer Draft",
			filters={"status": ["in", ["Sent", "Accepted", "Declined", "Expired"]]},
		)

		return {"should_show": sent_count == 1}

	return {"should_show": True}


@frappe.whitelist(methods=["POST"])
def dismiss_first_offer_sent() -> dict:
	"""Mark the First Offer Sent milestone as seen."""
	frappe.has_permission("Micro Settings", ptype="write", throw=True)

	frappe.db.set_single_value("Micro Settings", "first_offer_sent_seen", 1)
	frappe.db.commit()

	return {"ok": True}


# ------------------------------------------------------------------
# Annual Business Wrapped
# ------------------------------------------------------------------

_MONTH_NAMES = [
	"", "January", "February", "March", "April", "May", "June",
	"July", "August", "September", "October", "November", "December",
]


@frappe.whitelist()
def get_annual_wrapped(year: int | str, force: bool | str = False) -> dict:
	"""Return aggregated business summary for the given year.

	Only returns data if the user has not yet dismissed wrapped for this year.
	Includes soft dependency on Orga for delivered-projects count.

	Pass force=1 to bypass the "already seen" and date checks (for testing).
	"""
	frappe.has_permission("Micro Offer Draft", throw=True)

	year = int(year)
	force = force in (True, "1", "true", 1)
	current_year = getdate(nowdate()).year

	if not force:
		# Only allow previous year (or current year for testing)
		if year < 2020 or year > current_year:
			return {"should_show": False}

		# Check if already dismissed
		seen_year = int(
			frappe.db.get_single_value("Micro Settings", "annual_wrapped_year") or 0
		)
		if seen_year >= year:
			return {"should_show": False}

	year_start = f"{year}-01-01"
	year_end = f"{year}-12-31"

	# Offers sent (any status beyond Draft)
	offers_sent = frappe.db.count(
		"Micro Offer Draft",
		filters={
			"status": ["in", ["Sent", "Accepted", "Declined", "Expired"]],
			"date": ["between", [year_start, year_end]],
		},
	)

	# If no offers at all in this year, nothing to show
	if offers_sent == 0:
		return {"should_show": False}

	# Offers won
	offers_won = frappe.db.count(
		"Micro Offer Draft",
		filters={
			"status": "Accepted",
			"date": ["between", [year_start, year_end]],
		},
	)

	# Total pipeline value (accepted offers)
	pipeline_value = float(
		frappe.db.sql(
			"""
			SELECT COALESCE(SUM(total), 0)
			FROM `tabMicro Offer Draft`
			WHERE status = 'Accepted'
			  AND date BETWEEN %s AND %s
			""",
			(year_start, year_end),
		)[0][0]
		or 0
	)

	# New clients created this year
	new_clients = frappe.db.count(
		"Micro Customer",
		filters={
			"creation": ["between", [f"{year_start} 00:00:00", f"{year_end} 23:59:59"]],
		},
	)

	# Best month (highest accepted pipeline)
	best_month_row = frappe.db.sql(
		"""
		SELECT MONTH(date) AS m, SUM(total) AS month_total
		FROM `tabMicro Offer Draft`
		WHERE status = 'Accepted'
		  AND date BETWEEN %s AND %s
		GROUP BY m
		ORDER BY month_total DESC
		LIMIT 1
		""",
		(year_start, year_end),
		as_dict=True,
	)

	best_month = ""
	best_month_value = 0.0
	if best_month_row:
		month_num = int(best_month_row[0].m or 0)
		best_month = _MONTH_NAMES[month_num] if 1 <= month_num <= 12 else ""
		best_month_value = float(best_month_row[0].month_total or 0)

	# Top client (highest sum of accepted offer totals)
	top_client_row = frappe.db.sql(
		"""
		SELECT contact, SUM(total) AS client_total
		FROM `tabMicro Offer Draft`
		WHERE status = 'Accepted'
		  AND date BETWEEN %s AND %s
		  AND IFNULL(contact, '') != ''
		GROUP BY contact
		ORDER BY client_total DESC
		LIMIT 1
		""",
		(year_start, year_end),
		as_dict=True,
	)

	top_client_name = ""
	top_client_value = 0.0
	if top_client_row:
		top_client_name = top_client_row[0].contact or ""
		top_client_value = float(top_client_row[0].client_total or 0)

	# Year-over-year growth (compare to previous year)
	yoy_growth_pct = None
	prev_year_start = f"{year - 1}-01-01"
	prev_year_end = f"{year - 1}-12-31"
	prev_pipeline = float(
		frappe.db.sql(
			"""
			SELECT COALESCE(SUM(total), 0)
			FROM `tabMicro Offer Draft`
			WHERE status = 'Accepted'
			  AND date BETWEEN %s AND %s
			""",
			(prev_year_start, prev_year_end),
		)[0][0]
		or 0
	)
	if prev_pipeline > 0:
		yoy_growth_pct = round(((pipeline_value - prev_pipeline) / prev_pipeline) * 100)

	# Soft dependency: Orga projects delivered
	projects_delivered = None
	if "orga" in frappe.get_installed_apps():
		try:
			projects_delivered = frappe.db.count(
				"Orga Project",
				filters={
					"status": "Completed",
					"modified": ["between", [f"{year_start} 00:00:00", f"{year_end} 23:59:59"]],
				},
			)
		except Exception:
			projects_delivered = None

	win_rate = round((offers_won / offers_sent) * 100) if offers_sent > 0 else 0

	return {
		"should_show": True,
		"year": year,
		"offers_sent": offers_sent,
		"offers_won": offers_won,
		"win_rate": win_rate,
		"pipeline_value": pipeline_value,
		"new_clients": new_clients,
		"best_month": best_month,
		"best_month_value": best_month_value,
		"top_client_name": top_client_name,
		"top_client_value": top_client_value,
		"yoy_growth_pct": yoy_growth_pct,
		"projects_delivered": projects_delivered,
	}


@frappe.whitelist(methods=["POST"])
def dismiss_annual_wrapped(year: int | str) -> dict:
	"""Mark the Annual Wrapped as seen for the given year."""
	frappe.has_permission("Micro Settings", ptype="write", throw=True)

	year = int(year)
	frappe.db.set_single_value("Micro Settings", "annual_wrapped_year", year)
	frappe.db.commit()

	return {"ok": True}


@frappe.whitelist(methods=["POST"])
def reset_milestones() -> dict:
	"""Reset all milestone flags so emotional moments can be re-triggered.

	For testing/demo purposes only.
	"""
	frappe.has_permission("Micro Settings", ptype="write", throw=True)

	frappe.db.set_single_value("Micro Settings", "first_offer_sent_seen", 0)
	frappe.db.set_single_value("Micro Settings", "annual_wrapped_year", 0)
	frappe.db.commit()

	return {"ok": True}
