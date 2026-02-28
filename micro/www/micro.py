# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe


def get_context(context):
	csrf_token = frappe.sessions.get_csrf_token()
	context.csrf_token = csrf_token
