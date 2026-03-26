# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe import _
from frappe.utils import getdate, get_first_day, get_last_day


@frappe.whitelist()
def get_capacity_data() -> dict:
	"""Return capacity indicator data for the current month."""
	today = getdate()
	first_day = get_first_day(today)
	last_day = get_last_day(today)
	user = frappe.session.user

	capacity_hours = (
		frappe.db.get_single_value("Micro Settings", "monthly_capacity_hours") or 100
	)

	# Primary source: billable Watch Entry hours this month
	used_hours = _get_watch_hours(first_day, last_day, user)
	source = "watch"

	# Fallback: Orga Task estimated_hours if no Watch entries
	if used_hours == 0:
		used_hours = _get_orga_estimates(first_day, last_day, user)
		source = "orga_estimate" if used_hours > 0 else "none"

	available_hours = max(0, capacity_hours - used_hours)
	raw_percentage = (used_hours / capacity_hours * 100) if capacity_hours > 0 else 0
	percentage = min(100, int(raw_percentage))

	status_key, status_message = _get_status(raw_percentage)

	month_label = _(today.strftime("%B"))

	return {
		"month_label": month_label,
		"capacity_hours": capacity_hours,
		"used_hours": round(used_hours, 1),
		"available_hours": round(available_hours, 1),
		"percentage": percentage,
		"raw_percentage": round(raw_percentage, 1),
		"source": source,
		"status_key": status_key,
		"status_message": status_message,
	}


def _get_watch_hours(first_day, last_day, user) -> float:
	"""Sum billable Watch Entry duration_hours for the given month and user."""
	result = frappe.db.sql(
		"SELECT COALESCE(SUM(duration_hours), 0) "
		"FROM `tabWatch Entry` "
		"WHERE date BETWEEN %s AND %s "
		"AND entry_type = 'billable' "
		"AND user = %s",
		(first_day, last_day, user),
	)
	return float(result[0][0]) if result else 0.0


def _get_orga_estimates(first_day, last_day, user) -> float:
	"""Sum estimated_hours from Orga Tasks due this month (fallback)."""
	result = frappe.db.sql(
		"SELECT COALESCE(SUM(estimated_hours), 0) "
		"FROM `tabOrga Task` "
		"WHERE due_date BETWEEN %s AND %s "
		"AND status NOT IN ('Cancelled') "
		"AND assigned_to = %s",
		(first_day, last_day, user),
	)
	return float(result[0][0]) if result else 0.0


def _get_status(raw_percentage: float) -> tuple[str, str]:
	"""Return status key and translated message based on utilization percentage."""
	if raw_percentage > 95:
		return (
			"overcommitted",
			_(
				"Overcommitted — consider adjusting a timeline "
				"or raising your rate for new inquiries"
			),
		)
	if raw_percentage >= 80:
		return (
			"nearly_full",
			_("Nearly full — consider queuing new work for next month"),
		)
	if raw_percentage >= 50:
		return (
			"good",
			_("Good capacity — room for one more project"),
		)
	return (
		"low",
		_(
			"Low utilization — a good month to reach out "
			"and fill the pipeline"
		),
	)
