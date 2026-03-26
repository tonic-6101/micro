# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe


def after_install():
	"""Set up defaults after Micro is installed."""
	create_roles()
	setup_defaults()
	seed_pipeline_stages()


def create_roles():
	"""Create Micro-specific roles."""
	roles = [
		{"role_name": "Micro User", "desk_access": 1},
		{"role_name": "Micro Manager", "desk_access": 1},
	]

	for role_data in roles:
		if not frappe.db.exists("Role", role_data["role_name"]):
			role = frappe.new_doc("Role")
			role.role_name = role_data["role_name"]
			role.desk_access = role_data["desk_access"]
			role.save(ignore_permissions=True)

	frappe.db.commit()


def setup_defaults():
	"""Set up Micro Settings defaults (only if DocType exists)."""
	try:
		if not frappe.db.exists("DocType", "Micro Settings"):
			return

		if not frappe.db.exists("Micro Settings"):
			settings = frappe.new_doc("Micro Settings")
			settings.default_currency = "EUR"
			settings.default_language = "de"
			settings.customer_limit = 100
			settings.article_limit = 50
			settings.monthly_capacity_hours = 100
			settings.draft_watermark_text = "ENTWURF"
			settings.save(ignore_permissions=True)
			frappe.db.commit()
	except Exception:
		# Settings DocType not yet created — will be set up during migrate
		pass


def seed_pipeline_stages():
	"""Create default pipeline stages if none exist."""
	try:
		if not frappe.db.exists("DocType", "Micro Pipeline Stage"):
			return

		if frappe.db.count("Micro Pipeline Stage") > 0:
			return

		default_stages = [
			{"stage_name": "New", "sort_order": 10, "color": "Blue", "is_closed": 0},
			{"stage_name": "Contacted", "sort_order": 20, "color": "Yellow", "is_closed": 0},
			{"stage_name": "Offer Sent", "sort_order": 30, "color": "Orange", "is_closed": 0},
			{"stage_name": "Negotiating", "sort_order": 40, "color": "Purple", "is_closed": 0},
			{"stage_name": "Won", "sort_order": 50, "color": "Green", "is_closed": 1},
			{"stage_name": "Lost", "sort_order": 60, "color": "Red", "is_closed": 1},
		]

		for stage_data in default_stages:
			stage = frappe.new_doc("Micro Pipeline Stage")
			stage.stage_name = stage_data["stage_name"]
			stage.sort_order = stage_data["sort_order"]
			stage.color = stage_data["color"]
			stage.is_closed = stage_data["is_closed"]
			stage.insert(ignore_permissions=True)

		frappe.db.commit()
	except Exception:
		pass
