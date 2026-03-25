# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

app_name = "micro"
app_title = "Micro"
app_publisher = "Tonic"
app_description = "Business organizer for micro businesses"
app_email = "tonic@example.com"
app_license = "agpl-3.0"
app_version = "0.1.0"

# Required Apps
# ------------------
# required_apps = []

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
	{
		"name": "micro",
		"logo": "/assets/micro/logo.png",
		"title": "Micro",
		"route": "/micro",
	}
]

# Website Route Rules
# -------------------
# SPA routing — all /micro/* paths served by the Vue frontend

website_route_rules = [
	{"from_route": "/micro/<path:app_path>", "to_route": "micro"},
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/micro/css/micro.css"
# app_include_js = "/assets/micro/js/micro.js"

# include js, css files in header of web template
# web_include_css = "/assets/micro/css/micro.css"
# web_include_js = "/assets/micro/js/micro.js"

# Installation
# ------------

after_install = "micro.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "micro.uninstall.before_uninstall"
# after_uninstall = "micro.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "micro.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# }
#
# has_permission = {
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"daily": [
# 		"micro.tasks.daily"
# 	],
# }

# Testing
# -------

# before_tests = "micro.install.before_tests"

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "Micro Customer",
# 		"filter_by": "owner",
# 		"redact_fields": ["email", "phone", "mobile"],
# 		"partial": 1,
# 	},
# ]

# Automatically update python controller files with type annotations for this app.
export_python_type_annotations = True

# Dock integration
# ------------------
dock_app_registry = {
	"label": "Micro",
	"color": "#2563eb",
	"route": "/micro",
}

dock_settings_sections = [
	{
		"label": "Micro",
		"route": "micro",
		"component": "MicroSettings",
		"bundle": "/assets/micro/js/micro-settings.esm.js",
		"sections": [
			{"label": "Company Information", "key": "company"},
			{"label": "Defaults", "key": "defaults"},
			{"label": "Usage & Limits", "key": "usage"},
			{"label": "Tax Advisor", "key": "tax-advisor"},
			{"label": "Compliance", "key": "compliance"},
		],
	}
]

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
