# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Client Health Score — auto-calculated A/B/C/D grade per Contact.

Signals (Community tier):
  - Lifetime revenue (35%): accepted offer draft totals, relative to portfolio avg
  - Referrals given (25%): contacts with referred_by = this contact
  - Payment behavior (20%): avg days between offer accepted → invoice draft created
  - Scope behavior (20%): fewer scope-change notes = higher score

Output is stored on Contact custom fields:
  - micro_health_score: A/B/C/D
  - micro_health_score_updated: datetime of last calculation
"""

import frappe
from frappe.utils import now_datetime


# ---------------------------------------------------------------------------
# Weight configuration
# ---------------------------------------------------------------------------
WEIGHT_REVENUE = 0.35
WEIGHT_REFERRALS = 0.25
WEIGHT_PAYMENT = 0.20
WEIGHT_SCOPE = 0.20


# ---------------------------------------------------------------------------
# Signal calculators (each returns 0.0–1.0)
# ---------------------------------------------------------------------------

def _get_all_contact_revenues() -> dict[str, float]:
	"""Return {contact_name: total_accepted_offer_amount} for all contacts."""
	rows = frappe.db.sql(
		"""
		SELECT contact, SUM(total) as ltv
		FROM `tabMicro Offer Draft`
		WHERE status = 'Accepted'
		GROUP BY contact
		""",
		as_dict=True,
	)
	return {r.contact: float(r.ltv or 0) for r in rows}


def _revenue_score(contact_name: str, revenues: dict[str, float]) -> float:
	"""Score lifetime revenue relative to portfolio average."""
	ltv = revenues.get(contact_name, 0)
	if not revenues:
		return 0.0
	avg = sum(revenues.values()) / len(revenues) if revenues else 0
	if avg == 0:
		return 0.5
	ratio = ltv / avg
	# Cap at 2× average → 1.0
	return min(ratio / 2.0, 1.0)


def _referral_score(contact_name: str) -> float:
	"""Score based on how many contacts were referred by this contact."""
	count = frappe.db.count(
		"Contact",
		filters={
			"micro_referred_by": contact_name,
			"micro_status": ["is", "set"],
		},
	)
	# 0 referrals = 0.0, 1 = 0.5, 2 = 0.75, 3+ = 1.0
	if count == 0:
		return 0.0
	if count == 1:
		return 0.5
	if count == 2:
		return 0.75
	return 1.0


def _payment_score(contact_name: str) -> float:
	"""Score based on avg days between offer accepted and invoice draft created.

	Faster turnaround = higher score. If no data, returns neutral 0.5.
	"""
	rows = frappe.db.sql(
		"""
		SELECT
			o.date as offer_date,
			i.date as invoice_date
		FROM `tabMicro Offer Draft` o
		INNER JOIN `tabMicro Invoice Draft` i
			ON i.offer_draft = o.name
		WHERE o.contact = %(contact)s
			AND o.status = 'Accepted'
		""",
		{"contact": contact_name},
		as_dict=True,
	)
	if not rows:
		return 0.5

	total_days = 0
	valid = 0
	for r in rows:
		if r.offer_date and r.invoice_date:
			diff = (r.invoice_date - r.offer_date).days
			if diff >= 0:
				total_days += diff
				valid += 1

	if valid == 0:
		return 0.5

	avg_days = total_days / valid
	# 0 days = 1.0, 30+ days = 0.0
	return max(0.0, 1.0 - (avg_days / 30.0))


def _scope_score(contact_name: str) -> float:
	"""Score based on scope-change notes. Fewer = higher score."""
	total_notes = frappe.db.count(
		"Micro Note",
		filters={"contact": contact_name},
	)
	scope_notes = frappe.db.count(
		"Micro Note",
		filters={"contact": contact_name, "is_scope_change": 1},
	)

	if total_notes == 0:
		return 0.5

	ratio = scope_notes / total_notes
	# 0% scope changes = 1.0, 50%+ = 0.0
	return max(0.0, 1.0 - (ratio * 2.0))


# ---------------------------------------------------------------------------
# Grade calculation
# ---------------------------------------------------------------------------

def _numeric_to_grade(score: float) -> str:
	"""Convert 0.0–1.0 numeric score to A/B/C/D letter grade."""
	if score >= 0.75:
		return "A"
	if score >= 0.50:
		return "B"
	if score >= 0.25:
		return "C"
	return "D"


def calculate_health_score(contact_name: str, revenues: dict[str, float] | None = None) -> str:
	"""Calculate and return the health score grade for a single contact.

	Args:
		contact_name: The Contact document name.
		revenues: Pre-computed revenue dict (optional, for batch efficiency).

	Returns:
		Letter grade: A, B, C, or D.
	"""
	if revenues is None:
		revenues = _get_all_contact_revenues()

	score = (
		WEIGHT_REVENUE * _revenue_score(contact_name, revenues)
		+ WEIGHT_REFERRALS * _referral_score(contact_name)
		+ WEIGHT_PAYMENT * _payment_score(contact_name)
		+ WEIGHT_SCOPE * _scope_score(contact_name)
	)

	return _numeric_to_grade(score)


def update_contact_health_score(contact_name: str, revenues: dict[str, float] | None = None):
	"""Calculate and persist health score on a Contact."""
	grade = calculate_health_score(contact_name, revenues)
	frappe.db.set_value(
		"Contact",
		contact_name,
		{
			"micro_health_score": grade,
			"micro_health_score_updated": now_datetime(),
		},
		update_modified=False,
	)


# ---------------------------------------------------------------------------
# Hooks — triggered by doc_events in hooks.py
# ---------------------------------------------------------------------------

def on_related_doc_update(doc, method):
	"""Recalculate health score when an offer/invoice draft is saved."""
	contact = getattr(doc, "contact", None)
	if contact and frappe.db.get_value("Contact", contact, "micro_status"):
		frappe.enqueue(
			update_contact_health_score,
			contact_name=contact,
			queue="short",
			deduplicate=True,
			job_id=f"health_score_{contact}",
		)


def on_note_update(doc, method):
	"""Recalculate health score when a note is saved (scope change signal)."""
	contact = getattr(doc, "contact", None)
	if contact and frappe.db.get_value("Contact", contact, "micro_status"):
		frappe.enqueue(
			update_contact_health_score,
			contact_name=contact,
			queue="short",
			deduplicate=True,
			job_id=f"health_score_{contact}",
		)


def on_contact_update(doc, method):
	"""Recalculate when referred_by changes (affects the referrer's score)."""
	if not doc.micro_status:
		return
	# Recalculate this contact's score
	frappe.enqueue(
		update_contact_health_score,
		contact_name=doc.name,
		queue="short",
		deduplicate=True,
		job_id=f"health_score_{doc.name}",
	)
	# If referred_by was set/changed, recalculate the referrer's score too
	old_referred_by = doc.get_doc_before_save()
	old_val = getattr(old_referred_by, "micro_referred_by", None) if old_referred_by else None
	new_val = doc.micro_referred_by
	affected = {v for v in (old_val, new_val) if v}
	for referrer in affected:
		if frappe.db.get_value("Contact", referrer, "micro_status"):
			frappe.enqueue(
				update_contact_health_score,
				contact_name=referrer,
				queue="short",
				deduplicate=True,
				job_id=f"health_score_{referrer}",
			)


# ---------------------------------------------------------------------------
# Scheduler — daily full recalculation
# ---------------------------------------------------------------------------

def recalculate_all_scores():
	"""Daily background job: recalculate health scores for all Micro contacts."""
	contacts = frappe.get_all(
		"Contact",
		filters={"micro_status": ["is", "set"]},
		pluck="name",
	)
	if not contacts:
		return

	revenues = _get_all_contact_revenues()

	for contact_name in contacts:
		try:
			update_contact_health_score(contact_name, revenues)
		except Exception:
			frappe.log_error(
				title=f"Health score calculation failed for {contact_name}",
			)

	frappe.db.commit()
