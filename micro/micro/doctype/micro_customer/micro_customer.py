# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe import _
from frappe.model.document import Document


class MicroCustomer(Document):
	def before_validate(self):
		self.clear_organization_for_org_type()

	def validate(self):
		self.validate_email()
		self.compute_full_name()

	def before_insert(self):
		self.check_community_limit()
		self.set_default_pipeline_stage()

	def validate_email(self):
		"""Validate email format if provided."""
		if self.email and not frappe.utils.validate_email_address(self.email):
			frappe.throw(_("Invalid email address: {0}").format(self.email))

	def compute_full_name(self):
		"""Auto-compute full_name from name1 + last_name."""
		parts = [self.name1]
		if self.last_name:
			parts.append(self.last_name)
		self.full_name = " ".join(parts)

	def clear_organization_for_org_type(self):
		"""Organization link only valid for Person customers."""
		if self.contact_type == "Organization" and self.organization:
			self.organization = None

	def set_default_pipeline_stage(self):
		"""Set first pipeline stage as default if not specified."""
		if not self.pipeline_stage:
			first_stage = frappe.db.get_value(
				"Micro Pipeline Stage",
				filters={},
				fieldname="name",
				order_by="sort_order asc",
			)
			if first_stage:
				self.pipeline_stage = first_stage

	def check_community_limit(self):
		"""Enforce customer limit for Community edition."""
		settings = frappe.get_single("Micro Settings")
		limit = settings.customer_limit or 100
		if limit > 0:
			count = frappe.db.count("Micro Customer")
			if count >= limit:
				frappe.throw(
					_("Customer limit reached ({0}). Upgrade to Micro Pro for unlimited customers.").format(
						limit
					)
				)
