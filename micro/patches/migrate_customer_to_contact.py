# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic


def execute():
	"""No-op: Micro Customer is retained as the standalone CRM record per spec.

	The original plan was to migrate Micro Customer data into Frappe Contact
	custom fields (D1 pattern). Instead, Micro Customer now coexists with
	Contact via the `linked_contact` bridge field — Micro Customer is the CRM
	entity, Contact is the shared Frappe identity for Dock integration.

	This patch is retained as a no-op so Frappe does not re-run it.
	"""
	pass
