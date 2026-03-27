# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic


def execute():
	"""No-op: Micro Lead, Pipeline, and Pipeline Stage are now re-introduced per spec.

	Originally removed during an architectural simplification, but the spec
	defines all three as required Zone 1 DocTypes. This patch is retained as
	a no-op so Frappe's patch tracker does not re-run it.
	"""
	pass
