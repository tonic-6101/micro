# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

from frappe import _


def get_data():
	return [
		{
			"module_name": "Micro",
			"type": "module",
			"label": _("Micro"),
			"color": "#4F46E5",
			"icon": "octicon octicon-briefcase",
			"description": _("Business organizer for micro businesses"),
		}
	]
