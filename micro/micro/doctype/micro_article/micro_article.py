# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe import _
from frappe.model.document import Document

from micro.services.compliance import validate_no_tax_fields


class MicroArticle(Document):
	def validate(self):
		validate_no_tax_fields(self)

	def before_insert(self):
		self.check_community_limit()

	def check_community_limit(self):
		"""Enforce article limit for Community edition."""
		settings = frappe.get_single("Micro Settings")
		limit = settings.article_limit or 50
		if limit > 0:
			count = frappe.db.count("Micro Article")
			if count >= limit:
				frappe.throw(
					_("Article limit reached ({0}). Upgrade to Micro Pro for unlimited articles.").format(
						limit
					)
				)
