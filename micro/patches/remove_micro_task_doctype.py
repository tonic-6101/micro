# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe


def execute():
	"""Remove Micro Task DocType.

	Task management belongs to the Orga app. Micro no longer ships its own
	task feature.
	"""
	if frappe.db.exists("DocType", "Micro Task"):
		table_name = "tabMicro Task"
		if frappe.db.table_exists(table_name):
			frappe.db.sql(f"DELETE FROM `{table_name}`")

		frappe.delete_doc("DocType", "Micro Task", force=True, ignore_permissions=True)

	frappe.db.commit()
