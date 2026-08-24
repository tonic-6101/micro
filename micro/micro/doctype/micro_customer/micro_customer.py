# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe import _
from frappe.model.document import Document

from micro.limits import DEFAULT_CUSTOMER_LIMIT, get_limit


class MicroCustomer(Document):
	"""Micro's standalone CRM record.

	Micro Customer is Micro's own entity. The `linked_contact` field
	bridges to Frappe's shared Contact DocType for Dock People Hub
	integration. When a Micro Customer is created, a Frappe Contact
	is auto-created (or linked) so that Dock, Watch, and other
	ecosystem apps can reference the same person.
	"""

	def before_validate(self):
		self.clear_organization_for_org_type()

	def validate(self):
		self.validate_email()
		self.compute_full_name()

	def before_insert(self):
		self.check_community_limit()
		self.set_default_pipeline_stage()

	def after_insert(self):
		self._ensure_linked_contact()

	def on_update(self):
		self._sync_linked_contact()

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
		"""Enforce customer limit for Community edition. 0 = unlimited."""
		limit = get_limit("customer_limit", DEFAULT_CUSTOMER_LIMIT)
		if limit > 0:
			count = frappe.db.count("Micro Customer")
			if count >= limit:
				frappe.throw(
					_("Customer limit reached ({0}). Upgrade to Micro Pro for unlimited customers.").format(
						limit
					)
				)

	def _ensure_linked_contact(self):
		"""Auto-create a Frappe Contact if not already linked."""
		if self.linked_contact:
			return

		contact = frappe.new_doc("Contact")
		contact.first_name = self.name1
		contact.last_name = self.last_name or ""
		if self.email:
			contact.append("email_ids", {"email_id": self.email, "is_primary": 1})
		if self.phone:
			contact.append("phone_nos", {"phone": self.phone, "is_primary_phone": 1})
		if self.mobile:
			contact.append("phone_nos", {"phone": self.mobile, "is_primary_mobile_no": 1})

		# Set Micro CRM custom fields
		contact.micro_status = self.status
		contact.micro_pipeline_stage = self.pipeline_stage
		contact.micro_source = self.source
		contact.micro_contact_type = self.contact_type

		contact.insert(ignore_permissions=True)

		self.db_set("linked_contact", contact.name)

	def _sync_linked_contact(self):
		"""Keep the Frappe Contact in sync with Micro Customer changes."""
		if not self.linked_contact:
			return
		if not frappe.db.exists("Contact", self.linked_contact):
			return

		frappe.db.set_value("Contact", self.linked_contact, {
			"first_name": self.name1,
			"last_name": self.last_name or "",
			"micro_status": self.status,
			"micro_pipeline_stage": self.pipeline_stage,
			"micro_source": self.source,
			"micro_contact_type": self.contact_type,
		})
