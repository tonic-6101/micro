# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe


def execute():
	"""Remove Micro Lead, Micro Pipeline, and Micro Pipeline Stage DocTypes.

	This patch runs in pre_model_sync to clean up data and DocType records
	before the filesystem-level DocType definitions are removed.
	"""
	doctypes_to_remove = [
		"Micro Lead",
		"Micro Pipeline Stage",
		"Micro Pipeline",
	]

	for dt in doctypes_to_remove:
		if frappe.db.exists("DocType", dt):
			# Delete all documents of this type
			table_name = f"tab{dt}"
			if frappe.db.table_exists(table_name):
				frappe.db.sql(f"DELETE FROM `{table_name}`")

			# Remove the DocType record itself
			frappe.delete_doc("DocType", dt, force=True, ignore_permissions=True)

	# Remove the lead field from Note table if it exists
	for table in ["tabMicro Note"]:
		if frappe.db.table_exists(table) and frappe.db.has_column(table, "lead"):
			frappe.db.sql(f"ALTER TABLE `{table}` DROP COLUMN `lead`")

	# Remove is_lead field from Contact table if it exists
	if frappe.db.table_exists("tabMicro Contact") and frappe.db.has_column(
		"tabMicro Contact", "is_lead"
	):
		frappe.db.sql("ALTER TABLE `tabMicro Contact` DROP COLUMN `is_lead`")

	frappe.db.commit()
