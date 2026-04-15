# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Follow-Up Nudges — Smart reminders for client engagement.

Phase 1.5 Intelligence Layer (Community):
- Unanswered offers: offers in "Sent" status for 5+ days
- Dormant clients: contacts with no activity for 30+ days
- Upcoming follow-ups: leads with next_follow_up approaching
"""

import frappe
from frappe import _
from frappe.utils import add_days, getdate, nowdate


@frappe.whitelist()
def get_nudges() -> dict:
	"""Return all active nudges for the current user."""
	today = getdate(nowdate())

	return {
		"unanswered_offers": _get_unanswered_offers(today),
		"dormant_contacts": _get_dormant_contacts(today),
		"upcoming_follow_ups": _get_upcoming_follow_ups(today),
	}


def send_nudge_notifications():
	"""Daily scheduled task: publish Dock bell notifications for active nudges.

	Deduplicates by checking for existing unread notifications of the same type
	and reference within the last 7 days.
	"""
	today = getdate(nowdate())
	user = frappe.session.user

	# Only run for users with Micro access (System Users)
	users = frappe.get_all(
		"Has Role",
		filters={"role": "System Manager", "parenttype": "User"},
		pluck="parent",
	)
	# Also include all users who have Micro Offer Drafts
	offer_owners = frappe.get_all(
		"Micro Offer Draft",
		filters={"status": "Sent"},
		pluck="owner",
		distinct=True,
	)
	all_users = set(users) | set(offer_owners)

	from micro.integrations.dock_notification import (
		notify_dormant_contact,
		notify_task_overdue,
		notify_unanswered_offer,
	)

	for nudge_user in all_users:
		# Unanswered offers (owned by this user)
		offers = frappe.get_all(
			"Micro Offer Draft",
			filters={
				"status": "Sent",
				"date": ["<=", add_days(today, -5)],
				"owner": nudge_user,
			},
			fields=["name", "title", "contact", "date"],
		)
		for offer in offers:
			contact_name = offer.get("contact") or offer.get("title") or offer.name
			days_waiting = (today - getdate(offer["date"])).days
			if not _nudge_already_sent(nudge_user, "unanswered_offer_nudge", "Micro Offer Draft", offer.name):
				notify_unanswered_offer(nudge_user, offer.name, contact_name, days_waiting)

		# Dormant contacts (owned by this user)
		dormant = _get_dormant_contacts(today)
		for contact in dormant:
			if not _nudge_already_sent(nudge_user, "dormant_contact_nudge", "Contact", contact["name"]):
				notify_dormant_contact(
					nudge_user,
					contact.get("full_name", contact["name"]),
					contact["name"],
					contact["days_inactive"],
				)

		# Overdue tasks (assigned to this user)
		overdue_tasks = frappe.get_all(
			"Micro Task",
			filters={
				"status": ["in", ["Open", "In Progress"]],
				"due_date": ["<", today],
				"assigned_to": nudge_user,
			},
			fields=["name", "subject", "due_date"],
		)
		for task in overdue_tasks:
			days_overdue = (today - getdate(task["due_date"])).days
			if not _nudge_already_sent(nudge_user, "task_overdue", "Micro Task", task["name"]):
				notify_task_overdue(nudge_user, task["name"], task["subject"], days_overdue)


def _nudge_already_sent(user: str, notification_type: str, ref_doctype: str, ref_name: str) -> bool:
	"""Check if an unread notification of this type already exists for this reference in the last 7 days."""
	if "dock" not in frappe.get_installed_apps():
		return False
	cutoff = add_days(nowdate(), -7)
	return bool(frappe.db.exists(
		"Dock Notification",
		{
			"for_user": user,
			"notification_type": notification_type,
			"reference_doctype": ref_doctype,
			"reference_name": ref_name,
			"read": 0,
			"creation": [">=", cutoff],
		},
	))


def _get_unanswered_offers(today, threshold_days: int = 5) -> list[dict]:
	"""Offers in 'Sent' status for more than threshold_days."""
	cutoff = add_days(today, -threshold_days)

	offers = frappe.get_all(
		"Micro Offer Draft",
		filters={
			"status": "Sent",
			"date": ["<=", cutoff],
		},
		fields=["name", "reference", "title", "contact", "date", "total"],
		order_by="date asc",
	)

	for offer in offers:
		offer["days_waiting"] = (today - getdate(offer["date"])).days

	return offers


def _get_dormant_contacts(today, threshold_days: int = 30) -> list[dict]:
	"""Contacts with micro_status set but no recent activity (notes, offers, invoices)."""
	cutoff = add_days(today, -threshold_days)

	# Get active contacts
	contacts = frappe.get_all(
		"Contact",
		filters={
			"micro_status": "Active",
			"modified": ["<", cutoff],
		},
		fields=["name", "first_name", "last_name", "email_id", "modified"],
		order_by="modified asc",
		limit_page_length=20,
	)

	dormant = []
	for contact in contacts:
		# Check if there's recent activity via notes, offers, or invoices
		recent_note = frappe.db.exists(
			"Micro Note",
			{"contact": contact.name, "date": [">=", cutoff]},
		)
		recent_offer = frappe.db.exists(
			"Micro Offer Draft",
			{"contact": contact.name, "modified": [">=", cutoff]},
		)
		if not recent_note and not recent_offer:
			contact["days_inactive"] = (today - getdate(contact["modified"])).days
			contact["full_name"] = " ".join(
				filter(None, [contact.get("first_name"), contact.get("last_name")])
			)
			dormant.append(contact)

	return dormant


def _get_upcoming_follow_ups(today, lookahead_days: int = 7) -> list[dict]:
	"""Leads with next_follow_up within the next lookahead_days."""
	future = add_days(today, lookahead_days)

	leads = frappe.get_all(
		"Micro Lead",
		filters={
			"status": "Open",
			"next_follow_up": ["between", [today, future]],
		},
		fields=["name", "lead_name", "contact", "next_follow_up", "stage", "priority"],
		order_by="next_follow_up asc",
	)

	for lead in leads:
		lead["days_until"] = (getdate(lead["next_follow_up"]) - today).days

	return leads
