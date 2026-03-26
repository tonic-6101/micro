# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe import _
from frappe.contacts.doctype.contact.contact import Contact


class MicroContact(Contact):
	"""Extends Frappe Contact with Micro CRM pipeline fields.

	Adds micro_pipeline_stage, micro_source, and micro_status as CRM
	metadata on the shared Contact DocType. Only active when Micro is installed.
	"""

	def validate(self):
		super().validate()
		if self.micro_status or self.micro_pipeline_stage or self.micro_source:
			self._validate_micro_email()

	def before_insert(self):
		if hasattr(super(), "before_insert"):
			super().before_insert()
		if self.micro_status:
			self._check_community_limit()
			self._set_default_pipeline_stage()

	def _validate_micro_email(self):
		"""Validate primary email format if set."""
		if self.email_id and not frappe.utils.validate_email_address(self.email_id):
			frappe.throw(_("Invalid email address: {0}").format(self.email_id))

	def _set_default_pipeline_stage(self):
		"""Set first pipeline stage as default if not specified."""
		if not self.micro_pipeline_stage:
			first_stage = frappe.db.get_value(
				"Micro Pipeline Stage",
				filters={},
				fieldname="name",
				order_by="sort_order asc",
			)
			if first_stage:
				self.micro_pipeline_stage = first_stage

	def _check_community_limit(self):
		"""Enforce customer limit for Community edition."""
		try:
			settings = frappe.get_single("Micro Settings")
			limit = settings.customer_limit or 100
		except Exception:
			limit = 100

		if limit > 0:
			count = frappe.db.count(
				"Contact",
				filters={"micro_status": ["is", "set"]},
			)
			if count >= limit:
				frappe.throw(
					_(
						"Customer limit reached ({0}). Upgrade to Micro Pro for unlimited customers."
					).format(limit)
				)
