# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Community-edition limits, read one way.

There were two readings of the same setting and they disagreed. `settings.x or
default` treats a deliberate 0 as unset, so a site that had switched a limit off
— 0 means unlimited, as the field descriptions say — silently got the Community
cap back. Pipelines read theirs correctly; contacts and articles did not.
"""

import frappe

DEFAULT_CUSTOMER_LIMIT = 100
DEFAULT_ARTICLE_LIMIT = 50
DEFAULT_PIPELINE_LIMIT = 1

# Not an edition cap but a typo guard. A micro business does not close a million
# euro deal, while one extra zero quietly distorts every column total on the
# board and every forecast built on them. Raise it in Micro Settings, or set 0
# to switch it off.
DEFAULT_MAX_EXPECTED_VALUE = 1_000_000


def get_limit(fieldname: str, default: int) -> int:
	"""A Micro Settings limit, where 0 means unlimited.

	Only a genuinely unset field falls back to `default` — 0 is an answer, not
	the absence of one.
	"""
	try:
		value = frappe.get_single("Micro Settings").get(fieldname)
	except Exception:
		return default

	if value is None or value == "":
		return default

	return int(value)
