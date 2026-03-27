# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Dock Notification integration — publishes Micro events to Dock's bell icon.

Uses dock.api.notifications.publish() which validates notification_type
against dock_notification_types declared in micro/hooks.py, creates a
Dock Notification record, and pushes a realtime event to the recipient.
"""

import frappe
from frappe import _

# Route templates for deep-linking from Dock bell -> Micro SPA
_ROUTE_MAP = {
	"Micro Offer Draft": "/micro/offers/{name}",
	"Micro Invoice Draft": "/micro/invoices/{name}",
	"Micro Lead": "/micro/leads/{name}",
	"Micro Task": "/micro/tasks/{name}",
	"Micro Receipt": "/micro/receipts/{name}",
	"Contact": "/micro/customers/{name}",
}


def _dock_installed() -> bool:
	return "dock" in frappe.get_installed_apps()


def _build_action_url(reference_doctype: str, reference_name: str) -> str:
	"""Build a deep-link URL for the Dock notification."""
	template = _ROUTE_MAP.get(reference_doctype)
	if not template or not reference_name:
		return ""
	return template.format(name=reference_name)


def publish(
	notification_type: str,
	title: str,
	for_user: str,
	message: str = None,
	reference_doctype: str = None,
	reference_name: str = None,
):
	"""
	Publish a notification to Dock's bell icon.

	Safe to call when Dock is not installed — silently returns.
	Failures are logged but never break the calling code.
	"""
	if not _dock_installed():
		return

	action_url = _build_action_url(reference_doctype, reference_name)

	try:
		from dock.api.notifications import publish as dock_publish
		dock_publish(
			for_user=for_user,
			from_app="micro",
			notification_type=notification_type,
			title=title,
			message=message,
			reference_doctype=reference_doctype,
			reference_name=reference_name,
			action_url=action_url,
		)
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			"Micro: failed to publish Dock notification",
		)


# ------------------------------------------------------------------
# Offer events
# ------------------------------------------------------------------

def on_offer_status_change(doc, method=None):
	"""Publish notification when an offer status changes to a key state."""
	if not _dock_installed():
		return

	old_doc = doc.get_doc_before_save()
	if not old_doc:
		return

	new_status = doc.get("status")
	old_status = old_doc.get("status")
	if not new_status or new_status == old_status:
		return

	contact_name = doc.get("contact_name") or doc.get("customer_name") or ""

	if new_status == "Accepted":
		publish(
			notification_type="offer_accepted",
			title=_("Offer accepted: {0}").format(contact_name or doc.name),
			for_user=doc.owner,
			message=_("Your offer {0} for {1} was accepted.").format(
				doc.name, contact_name
			),
			reference_doctype="Micro Offer Draft",
			reference_name=doc.name,
		)
	elif new_status == "Declined":
		publish(
			notification_type="offer_declined",
			title=_("Offer declined: {0}").format(contact_name or doc.name),
			for_user=doc.owner,
			message=_("Your offer {0} for {1} was declined.").format(
				doc.name, contact_name
			),
			reference_doctype="Micro Offer Draft",
			reference_name=doc.name,
		)
	elif new_status == "Sent" and old_status == "Draft":
		publish(
			notification_type="offer_sent",
			title=_("Offer sent: {0}").format(contact_name or doc.name),
			for_user=doc.owner,
			message=_("Offer {0} for {1} marked as sent.").format(
				doc.name, contact_name
			),
			reference_doctype="Micro Offer Draft",
			reference_name=doc.name,
		)


# ------------------------------------------------------------------
# Invoice events
# ------------------------------------------------------------------

def on_invoice_insert(doc, method=None):
	"""Publish notification when a new invoice is created."""
	if not _dock_installed():
		return

	contact_name = doc.get("contact_name") or doc.get("customer_name") or ""

	publish(
		notification_type="invoice_created",
		title=_("Invoice created: {0}").format(doc.name),
		for_user=doc.owner,
		message=_("New invoice {0} for {1}.").format(doc.name, contact_name),
		reference_doctype="Micro Invoice Draft",
		reference_name=doc.name,
	)


# ------------------------------------------------------------------
# Lead events
# ------------------------------------------------------------------

def on_lead_status_change(doc, method=None):
	"""Publish notification when a lead is won or lost."""
	if not _dock_installed():
		return

	old_doc = doc.get_doc_before_save()
	if not old_doc:
		return

	new_status = doc.get("status")
	old_status = old_doc.get("status")
	if not new_status or new_status == old_status:
		return

	lead_title = doc.get("lead_name") or doc.get("contact_name") or doc.name

	if new_status == "Won":
		publish(
			notification_type="lead_won",
			title=_("Lead won: {0}").format(lead_title),
			for_user=doc.owner,
			message=_("Congratulations! Lead '{0}' was marked as won.").format(lead_title),
			reference_doctype="Micro Lead",
			reference_name=doc.name,
		)
	elif new_status == "Lost":
		publish(
			notification_type="lead_lost",
			title=_("Lead lost: {0}").format(lead_title),
			for_user=doc.owner,
			message=_("Lead '{0}' was marked as lost.").format(lead_title),
			reference_doctype="Micro Lead",
			reference_name=doc.name,
		)


# ------------------------------------------------------------------
# Task events
# ------------------------------------------------------------------

def on_task_status_change(doc, method=None):
	"""Publish notification when a task status changes."""
	if not _dock_installed():
		return

	old_doc = doc.get_doc_before_save()
	if not old_doc:
		return

	new_status = doc.get("status")
	old_status = old_doc.get("status")
	if not new_status or new_status == old_status:
		return

	subject = doc.get("subject") or doc.name
	assignee = doc.get("assigned_to")

	# Notify assignee about status change (if not the one making the change)
	if assignee and assignee != frappe.session.user:
		publish(
			notification_type="task_status_changed",
			title=_("Task {0}: {1}").format(new_status, subject[:50]),
			for_user=assignee,
			message=_("Task '{0}' changed from {1} to {2}.").format(
				subject, old_status, new_status
			),
			reference_doctype="Micro Task",
			reference_name=doc.name,
		)

	# Notify owner (if not the assignee and not the one making the change)
	if doc.owner != frappe.session.user and doc.owner != assignee:
		publish(
			notification_type="task_status_changed",
			title=_("Task {0}: {1}").format(new_status, subject[:50]),
			for_user=doc.owner,
			message=_("Task '{0}' changed from {1} to {2}.").format(
				subject, old_status, new_status
			),
			reference_doctype="Micro Task",
			reference_name=doc.name,
		)


# ------------------------------------------------------------------
# Nudge notifications (called from scheduled tasks)
# ------------------------------------------------------------------

def notify_unanswered_offer(user: str, offer_name: str, contact_name: str, days_waiting: int):
	"""Nudge about an offer that has been in 'Sent' status for too long."""
	publish(
		notification_type="unanswered_offer_nudge",
		title=_("Follow up: offer to {0} ({1}d)").format(contact_name, days_waiting),
		for_user=user,
		message=_("Your offer {0} to {1} has been waiting for {2} days.").format(
			offer_name, contact_name, days_waiting
		),
		reference_doctype="Micro Offer Draft",
		reference_name=offer_name,
	)


def notify_dormant_contact(user: str, contact_name: str, contact_ref: str, days_inactive: int):
	"""Nudge about a dormant active client."""
	publish(
		notification_type="dormant_contact_nudge",
		title=_("Reconnect: {0} ({1}d inactive)").format(contact_name, days_inactive),
		for_user=user,
		message=_("No activity with {0} for {1} days. Consider reaching out.").format(
			contact_name, days_inactive
		),
		reference_doctype="Contact",
		reference_name=contact_ref,
	)


def notify_task_overdue(user: str, task_name: str, subject: str, days_overdue: int):
	"""Nudge about an overdue task."""
	publish(
		notification_type="task_overdue",
		title=_("Overdue: {0}").format(subject[:50]),
		for_user=user,
		message=_("Task '{0}' is {1} days overdue.").format(subject, days_overdue),
		reference_doctype="Micro Task",
		reference_name=task_name,
	)
