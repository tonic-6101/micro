# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""When someone actually picks up.

A call attempt is logged against the *contact*, not the lead that happened to
be open when the call was made — the same person runs through several deals
over time, and the pattern of when they answer belongs to them, not to any one
of those deals. `get_best_time_to_call` turns the logged attempts into the
single answer a caller actually wants: which weekday and time of day has
paid off before.
"""

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

from micro.constants import CALL_OUTCOMES

# A day is sliced into the spans a caller actually thinks in, not raw hours.
# "Other" catches attempts logged outside normal calling hours.
_BUCKET_ORDER = ("morning", "midday", "afternoon", "evening", "other")

# Below this many *reached* attempts in a slot, a "best time" would be reading
# a pattern into one lucky call.
MIN_REACHED_FOR_CONFIDENCE = 2


def _time_bucket(hour: int) -> str:
	if 6 <= hour < 12:
		return "morning"
	if 12 <= hour < 14:
		return "midday"
	if 14 <= hour < 18:
		return "afternoon"
	if 18 <= hour < 21:
		return "evening"
	return "other"


@frappe.whitelist()
def log_call_attempt(
	contact: str,
	outcome: str,
	lead: str | None = None,
	attempted_at: str | None = None,
	notes: str | None = None,
) -> dict:
	"""Record one attempt to reach a contact by phone."""
	frappe.has_permission("Micro Call Attempt", "create", throw=True)

	if not frappe.db.exists("Contact", contact):
		frappe.throw(_("Contact not found"))

	if outcome not in CALL_OUTCOMES:
		frappe.throw(_("Unknown call outcome: {0}").format(outcome))

	if lead and not frappe.db.exists("Micro Lead", lead):
		frappe.throw(_("Lead not found"))

	doc = frappe.get_doc(
		{
			"doctype": "Micro Call Attempt",
			"contact": contact,
			"lead": lead,
			"outcome": outcome,
			"attempted_at": attempted_at or now_datetime(),
			"notes": notes,
		}
	)
	doc.insert(ignore_permissions=True)

	return {"attempt": doc.as_dict()}


@frappe.whitelist()
def get_call_attempts(contact: str, limit: int = 10) -> dict:
	"""The most recent attempts for a contact, newest first."""
	frappe.has_permission("Micro Call Attempt", "read", throw=True)

	attempts = frappe.get_all(
		"Micro Call Attempt",
		filters={"contact": contact},
		fields=["name", "attempted_at", "outcome", "lead", "notes"],
		order_by="attempted_at desc",
		limit_page_length=limit,
	)

	return {"attempts": attempts}


@frappe.whitelist()
def get_best_time_to_call(contact: str) -> dict:
	"""When the logged attempts say this contact tends to pick up.

	Every attempt lands in a (weekday, time-of-day) cell; the "best" cell is
	whichever one has reached the contact most often, once there is enough of
	a pattern to trust.
	"""
	frappe.has_permission("Micro Call Attempt", "read", throw=True)

	if not frappe.db.exists("Contact", contact):
		frappe.throw(_("Contact not found"))

	rows = frappe.get_all(
		"Micro Call Attempt",
		filters={"contact": contact},
		fields=["attempted_at", "outcome"],
	)

	cells: dict[tuple[int, str], dict[str, int]] = {}
	reached_total = 0

	for row in rows:
		dt = get_datetime(row.attempted_at)
		key = (dt.weekday(), _time_bucket(dt.hour))
		cell = cells.setdefault(key, {"attempts": 0, "reached": 0})
		cell["attempts"] += 1
		if row.outcome == "Reached":
			cell["reached"] += 1
			reached_total += 1

	grid = [
		{"weekday": weekday, "bucket": bucket, "attempts": cell["attempts"], "reached": cell["reached"]}
		for (weekday, bucket), cell in cells.items()
	]
	grid.sort(key=lambda cell: (cell["weekday"], _BUCKET_ORDER.index(cell["bucket"])))

	candidates = [cell for cell in grid if cell["reached"] >= MIN_REACHED_FOR_CONFIDENCE]
	best = None
	if candidates:
		best = max(candidates, key=lambda cell: (cell["reached"], cell["reached"] / cell["attempts"]))

	return {
		"total_attempts": len(rows),
		"reached_count": reached_total,
		"best": best,
		"grid": grid,
	}
