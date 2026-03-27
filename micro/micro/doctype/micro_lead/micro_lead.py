# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe import _
from frappe.model.document import Document


class MicroLead(Document):
	def validate(self):
		self._sync_status_from_stage()

	def _sync_status_from_stage(self):
		"""Auto-set Won/Lost status when moved to a win/loss stage."""
		if not self.stage:
			return
		stage = frappe.db.get_value(
			"Micro Pipeline Stage",
			self.stage,
			["is_closed", "stage_name"],
			as_dict=True,
		)
		if not stage:
			return
		if stage.is_closed and self.status == "Open":
			stage_lower = (stage.stage_name or "").lower()
			if "won" in stage_lower:
				self.status = "Won"
			elif "lost" in stage_lower:
				self.status = "Lost"
