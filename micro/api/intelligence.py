# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Intelligence Layer API — Phase 1.5 endpoints.

Aggregates nudges, win rate, revenue runway, and weekly briefing
into a single API module for the frontend.
"""

import frappe
from frappe import _


@frappe.whitelist()
def get_nudges() -> dict:
	"""Get follow-up nudges (unanswered offers, dormant contacts, upcoming follow-ups)."""
	from micro.services.nudges import get_nudges as _get_nudges

	return _get_nudges()


@frappe.whitelist()
def get_win_rate() -> dict:
	"""Get win rate intelligence data."""
	from micro.services.win_rate import get_win_rate_data

	return get_win_rate_data()


@frappe.whitelist()
def get_revenue_runway() -> dict:
	"""Get revenue runway data."""
	from micro.services.revenue_runway import get_revenue_runway as _get_runway

	return _get_runway()


@frappe.whitelist()
def get_weekly_briefing() -> dict:
	"""Get the weekly business briefing."""
	from micro.services.weekly_briefing import get_weekly_briefing as _get_briefing

	return _get_briefing()
