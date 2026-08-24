# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Shared option lists.

Keep in sync with the `source` Select in `micro_lead.json` — the DocType JSON
cannot import Python, so the list is duplicated there deliberately.
"""

MICRO_SOURCE_OPTIONS = "\n".join(
	[
		"",
		"Manual",
		"Classifieds",
		"Google Ads",
		"Facebook",
		"Instagram",
		"LinkedIn",
		"Email Campaign",
		"Cold Call",
		"Web Form",
		"Organic Search",
		"Referral",
		"Partner",
		"Event",
		"Import",
		"Other",
	]
)

# Keep in sync with the `outcome` Select in `micro_call_attempt.json`.
CALL_OUTCOMES = ("Reached", "No Answer", "Voicemail", "Busy", "Wrong Number")
