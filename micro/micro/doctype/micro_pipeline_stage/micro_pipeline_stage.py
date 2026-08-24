# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe import _
from frappe.model.document import Document

from micro.micro.doctype.micro_pipeline.micro_pipeline import get_default_pipeline


class MicroPipelineStage(Document):
	def validate(self):
		self._set_default_pipeline()
		self._validate_outcome_flags()

	def on_trash(self):
		self._block_delete_with_leads()

	def _set_default_pipeline(self):
		if not self.pipeline:
			self.pipeline = get_default_pipeline()

	def _validate_outcome_flags(self):
		"""A stage is either a win or a loss — never both — and either one closes the lead."""
		if self.is_win_stage and self.is_loss_stage:
			frappe.throw(_("A stage cannot be both a win stage and a loss stage."))

		if self.is_win_stage or self.is_loss_stage:
			self.is_closed = 1

	def _block_delete_with_leads(self):
		count = frappe.db.count("Micro Lead", {"stage": self.name})
		if count:
			frappe.throw(
				_("Cannot delete stage {0} — {1} lead(s) are still in it.").format(
					frappe.bold(self.stage_name), count
				)
			)
