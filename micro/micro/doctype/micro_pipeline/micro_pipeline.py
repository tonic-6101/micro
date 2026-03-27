# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe import _
from frappe.model.document import Document


class MicroPipeline(Document):
	def validate(self):
		self._enforce_community_limit()
		self._enforce_single_default()

	def _enforce_community_limit(self):
		"""Community edition: max 1 pipeline."""
		if self.is_new():
			count = frappe.db.count("Micro Pipeline")
			if count >= 1:
				frappe.throw(
					_("Community edition supports 1 pipeline. Upgrade to Pro for unlimited pipelines.")
				)

	def _enforce_single_default(self):
		"""Ensure only one default pipeline."""
		if self.is_default:
			frappe.db.sql(
				"UPDATE `tabMicro Pipeline` SET is_default = 0 WHERE name != %s",
				self.name,
			)
