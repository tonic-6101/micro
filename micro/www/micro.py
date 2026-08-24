# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe.translate import get_messages_for_boot

from micro.limits import DEFAULT_MAX_EXPECTED_VALUE, get_limit

no_cache = 1


def get_context():
	context = frappe._dict()
	context.site_name = frappe.local.site
	context.title = "Micro"

	csrf_token = frappe.sessions.get_csrf_token()
	frappe.db.commit()
	context.boot = get_boot()
	context.boot.csrf_token = csrf_token
	context.csrf_token = csrf_token

	return context


def _get_dock_boot():
	"""Return dock boot info if dock is installed, else None."""
	if "dock" not in frappe.get_installed_apps():
		return None
	try:
		from dock.boot import get_boot as dock_get_boot
		return dock_get_boot()
	except Exception:
		return {"installed": True}


def get_boot():
	"""Build boot data for Vue SPA including user session info."""
	user = frappe.session.user
	user_info = frappe.get_doc("User", user)

	return frappe._dict(
		{
			"frappe": {
				"boot": {
					"user": {
						"name": user,
						"email": user_info.email or "",
						"full_name": user_info.full_name or user,
						"user_image": user_info.user_image or "",
					},
					"user_roles": frappe.get_roles(user),
					"dock": _get_dock_boot(),
				},
				"csrf_token": frappe.sessions.get_csrf_token(),
			},
			"frappe_version": frappe.__version__,
			"default_route": "/micro",
			"site_name": frappe.local.site,
			"read_only_mode": frappe.flags.read_only,
			"lang": frappe.local.lang,
			# The bounds the forms have to obey. They ride along with the page
			# so no screen needs a round trip just to learn what it may accept.
			"micro_limits": {
				"max_expected_value": get_limit("max_expected_value", DEFAULT_MAX_EXPECTED_VALUE),
			},
			"__messages": get_messages_for_boot(),
		}
	)
