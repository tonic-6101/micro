# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe import _
from frappe.model.document import Document

from micro.limits import DEFAULT_PIPELINE_LIMIT, get_limit


def get_pipeline_limit() -> int:
	"""Max number of pipelines. 0 = unlimited. Community default is 1."""
	return get_limit("pipeline_limit", DEFAULT_PIPELINE_LIMIT)


def get_default_pipeline() -> str | None:
	"""Name of the default pipeline, falling back to the first one."""
	return frappe.db.get_value("Micro Pipeline", {"is_default": 1}, "name") or frappe.db.get_value(
		"Micro Pipeline", {}, "name", order_by="sort_order asc, creation asc"
	)


class MicroPipeline(Document):
	def validate(self):
		self._enforce_community_limit()
		self._enforce_single_default()

	def on_trash(self):
		self._block_delete_with_leads()

	def _enforce_community_limit(self):
		"""Community edition: limited number of pipelines (see Micro Settings)."""
		if not self.is_new():
			return

		limit = get_pipeline_limit()
		if limit <= 0:
			return

		if frappe.db.count("Micro Pipeline") >= limit:
			frappe.throw(
				_("Pipeline limit reached ({0}). Upgrade to Micro Pro for unlimited pipelines.").format(
					limit
				)
			)

	def _enforce_single_default(self):
		"""Exactly one default pipeline — no more, no less."""
		if self.is_default:
			frappe.db.sql(
				"UPDATE `tabMicro Pipeline` SET is_default = 0 WHERE name != %s",
				self.name,
			)
			return

		has_other_default = frappe.db.exists(
			"Micro Pipeline", {"is_default": 1, "name": ["!=", self.name]}
		)
		if not has_other_default:
			self.is_default = 1

	def _block_delete_with_leads(self):
		"""A pipeline holding leads must not vanish under them."""
		count = frappe.db.count("Micro Lead", {"pipeline": self.name})
		if count:
			frappe.throw(
				_("Cannot delete pipeline {0} — {1} lead(s) still use it.").format(
					frappe.bold(self.pipeline_name), count
				)
			)
