# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe


def execute():
	"""Rename Micro Contact to Micro Customer and set default status.

	This patch runs in post_model_sync after the new Micro Customer DocType
	definition is synced from the filesystem.
	"""
	# Rename DocType if the old one still exists
	if frappe.db.exists("DocType", "Micro Contact") and not frappe.db.exists(
		"DocType", "Micro Customer"
	):
		frappe.rename_doc("DocType", "Micro Contact", "Micro Customer", force=True)

	# Set default status on all existing customers that don't have one
	if frappe.db.table_exists("tabMicro Customer"):
		frappe.db.sql(
			"""
			UPDATE `tabMicro Customer`
			SET `status` = 'Active'
			WHERE `status` IS NULL OR `status` = ''
			"""
		)

	# Rename contact_limit to customer_limit in Micro Settings (Singles table)
	frappe.db.sql(
		"""
		UPDATE `tabSingles`
		SET `field` = 'customer_limit'
		WHERE `doctype` = 'Micro Settings' AND `field` = 'contact_limit'
		"""
	)

	# Drop is_lead column if it still exists
	if frappe.db.table_exists("tabMicro Customer") and frappe.db.has_column(
		"tabMicro Customer", "is_lead"
	):
		frappe.db.sql("ALTER TABLE `tabMicro Customer` DROP COLUMN `is_lead`")

	frappe.db.commit()
