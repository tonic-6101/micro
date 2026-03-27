# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Seed default Sales Pipeline and backfill is_win_stage/is_loss_stage on existing stages."""

import frappe


def execute():
	# 1. Create default pipeline if none exists
	if not frappe.db.exists("DocType", "Micro Pipeline"):
		return

	if frappe.db.count("Micro Pipeline") == 0:
		pipeline = frappe.new_doc("Micro Pipeline")
		pipeline.pipeline_name = "Sales Pipeline"
		pipeline.is_default = 1
		pipeline.insert(ignore_permissions=True)
		frappe.db.commit()

	# 2. Get default pipeline
	default_pipeline = frappe.db.get_value("Micro Pipeline", {"is_default": 1}, "name")
	if not default_pipeline:
		return

	# 3. Backfill existing stages
	stages = frappe.get_all(
		"Micro Pipeline Stage",
		fields=["name", "stage_name", "pipeline", "is_win_stage", "is_loss_stage"],
	)

	for stage in stages:
		updates = {}

		# Link to default pipeline if unset
		if not stage.pipeline:
			updates["pipeline"] = default_pipeline

		# Set win/loss flags if unset (based on stage name)
		stage_lower = (stage.stage_name or "").lower()
		if not stage.is_win_stage and not stage.is_loss_stage:
			if "won" in stage_lower:
				updates["is_win_stage"] = 1
			elif "lost" in stage_lower:
				updates["is_loss_stage"] = 1

		if updates:
			frappe.db.set_value("Micro Pipeline Stage", stage.name, updates)

	frappe.db.commit()
