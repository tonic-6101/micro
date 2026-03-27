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
required_apps = ["frappe", "dock", "watch", "orga"]

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

# DocType Class Overrides
# -----------------------
# Extend Frappe Contact with Micro CRM pipeline fields (D1 pattern from OWNERSHIP.md)

override_doctype_class = {
	"Contact": "micro.overrides.contact.MicroContact",
}

# Custom Fields
# -------------
# CRM metadata fields added to Frappe Contact — visible only when Micro is installed.

custom_fields = {
	"Contact": [
		{
			"fieldname": "micro_crm_section",
			"fieldtype": "Section Break",
			"label": "CRM (Micro)",
			"insert_after": "image",
			"collapsible": 1,
		},
		{
			"fieldname": "micro_status",
			"fieldtype": "Select",
			"label": "CRM Status",
			"options": "\nPotential\nActive\nInactive",
			"insert_after": "micro_crm_section",
			"in_standard_filter": 1,
		},
		{
			"fieldname": "micro_pipeline_stage",
			"fieldtype": "Link",
			"label": "Pipeline Stage",
			"options": "Micro Pipeline Stage",
			"insert_after": "micro_status",
		},
		{
			"fieldname": "micro_source",
			"fieldtype": "Select",
			"label": "Acquisition Source",
			"options": "\nManual\nGoogle Ads\nFacebook\nInstagram\nLinkedIn\nEmail Campaign\nCold Call\nWeb Form\nOrganic Search\nReferral\nPartner\nEvent\nImport\nOther",
			"insert_after": "micro_pipeline_stage",
		},
		{
			"fieldname": "micro_crm_column",
			"fieldtype": "Column Break",
			"insert_after": "micro_source",
		},
		{
			"fieldname": "micro_contact_type",
			"fieldtype": "Select",
			"label": "Contact Type",
			"options": "\nPerson\nOrganization",
			"insert_after": "micro_crm_column",
		},
		{
			"fieldname": "micro_website",
			"fieldtype": "Data",
			"label": "Website",
			"insert_after": "micro_contact_type",
		},
		{
			"fieldname": "micro_notes",
			"fieldtype": "Text",
			"label": "Notes",
			"insert_after": "micro_website",
		},
		# Client Intelligence Card fields
		{
			"fieldname": "micro_intelligence_section",
			"fieldtype": "Section Break",
			"label": "Client Intelligence",
			"insert_after": "micro_notes",
			"collapsible": 0,
		},
		{
			"fieldname": "micro_client_loves",
			"fieldtype": "Small Text",
			"label": "What They Love",
			"insert_after": "micro_intelligence_section",
		},
		{
			"fieldname": "micro_client_avoid",
			"fieldtype": "Small Text",
			"label": "What to Avoid",
			"insert_after": "micro_client_loves",
		},
		{
			"fieldname": "micro_communication_style",
			"fieldtype": "Select",
			"label": "Communication Style",
			"options": "\nEmail-first\nPhone-first\nWhatsApp\nAsync (slow replies OK)\nNeeds quick responses",
			"insert_after": "micro_client_avoid",
		},
		{
			"fieldname": "micro_intelligence_column",
			"fieldtype": "Column Break",
			"insert_after": "micro_communication_style",
		},
		{
			"fieldname": "micro_personal_notes",
			"fieldtype": "Small Text",
			"label": "Personal Notes",
			"insert_after": "micro_intelligence_column",
		},
		{
			"fieldname": "micro_opportunities",
			"fieldtype": "Small Text",
			"label": "Opportunities Spotted",
			"insert_after": "micro_personal_notes",
		},
		{
			"fieldname": "micro_last_contact_section",
			"fieldtype": "Section Break",
			"label": "Last Meaningful Contact",
			"insert_after": "micro_opportunities",
			"collapsible": 1,
		},
		{
			"fieldname": "micro_last_contact_date",
			"fieldtype": "Date",
			"label": "Last Contact Date",
			"insert_after": "micro_last_contact_section",
		},
		{
			"fieldname": "micro_last_contact_topic",
			"fieldtype": "Data",
			"label": "Topic",
			"insert_after": "micro_last_contact_date",
		},
		{
			"fieldname": "micro_referred_by",
			"fieldtype": "Link",
			"label": "Referred By",
			"options": "Contact",
			"insert_after": "micro_last_contact_topic",
		},
		{
			"fieldname": "micro_health_section",
			"fieldtype": "Section Break",
			"label": "Health Score (Micro)",
			"insert_after": "micro_referred_by",
			"collapsible": 1,
		},
		{
			"fieldname": "micro_health_score",
			"fieldtype": "Data",
			"label": "Health Score",
			"insert_after": "micro_health_section",
			"read_only": 1,
			"in_standard_filter": 1,
			"length": 1,
		},
		{
			"fieldname": "micro_health_score_updated",
			"fieldtype": "Datetime",
			"label": "Health Score Updated",
			"insert_after": "micro_health_score",
			"read_only": 1,
		},
		{
			"fieldname": "micro_address_section",
			"fieldtype": "Section Break",
			"label": "Address (Micro)",
			"insert_after": "micro_health_score_updated",
			"collapsible": 1,
		},
		{
			"fieldname": "micro_address",
			"fieldtype": "Small Text",
			"label": "Street Address",
			"insert_after": "micro_address_section",
		},
		{
			"fieldname": "micro_city",
			"fieldtype": "Data",
			"label": "City",
			"insert_after": "micro_address",
		},
		{
			"fieldname": "micro_address_column",
			"fieldtype": "Column Break",
			"insert_after": "micro_city",
		},
		{
			"fieldname": "micro_postal_code",
			"fieldtype": "Data",
			"label": "Postal Code",
			"insert_after": "micro_address_column",
		},
		{
			"fieldname": "micro_country",
			"fieldtype": "Link",
			"label": "Country",
			"options": "Country",
			"insert_after": "micro_postal_code",
		},
	],
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Micro Offer Draft": {
		"on_update": [
			"micro.services.health_score.on_related_doc_update",
			"micro.integrations.dock_notification.on_offer_status_change",
		],
	},
	"Micro Invoice Draft": {
		"on_update": "micro.services.health_score.on_related_doc_update",
		"after_insert": "micro.integrations.dock_notification.on_invoice_insert",
	},
	"Micro Note": {
		"on_update": "micro.services.health_score.on_note_update",
	},
	"Contact": {
		"on_update": "micro.services.health_score.on_contact_update",
	},
	"Micro Lead": {
		"on_update": [
			"micro.services.health_score.on_related_doc_update",
			"micro.integrations.dock_notification.on_lead_status_change",
		],
	},
	"Micro Task": {
		"on_update": "micro.integrations.dock_notification.on_task_status_change",
	},
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"micro.services.health_score.recalculate_all_scores",
	],
}

# Testing
# -------

# before_tests = "micro.install.before_tests"

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "Contact",
# 		"filter_by": "owner",
# 		"redact_fields": ["email_id", "phone", "mobile_no"],
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

dock_people_context = "micro.integrations.dock.get_people_context"

dock_notification_types = [
	{"type": "offer_accepted", "label": "Offer Accepted", "icon": "check-circle"},
	{"type": "offer_declined", "label": "Offer Declined", "icon": "x-circle"},
	{"type": "offer_sent", "label": "Offer Sent", "icon": "send"},
	{"type": "invoice_created", "label": "Invoice Created", "icon": "file-text"},
	{"type": "lead_won", "label": "Lead Won", "icon": "trophy"},
	{"type": "lead_lost", "label": "Lead Lost", "icon": "x-circle"},
	{"type": "task_status_changed", "label": "Task Status Changed", "icon": "refresh-cw"},
	{"type": "task_overdue", "label": "Task Overdue", "icon": "alert-circle"},
	{"type": "unanswered_offer_nudge", "label": "Unanswered Offer", "icon": "clock"},
	{"type": "dormant_contact_nudge", "label": "Dormant Contact", "icon": "user-x"},
]

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
