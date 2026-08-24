# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe import _
from frappe.contacts.doctype.contact.contact import Contact

from micro.limits import DEFAULT_CUSTOMER_LIMIT, get_limit


class MicroContact(Contact):
	"""Extends Frappe Contact with Micro CRM metadata.

	Adds micro_status, micro_source and micro_segment to the shared Contact
	DocType. Pipeline position lives on Micro Lead, not here — a contact can
	run through several pipelines at once. `micro_pipeline_stage` is only a
	read-only mirror maintained by the lead controller.
	"""

	def validate(self):
		super().validate()
		if self.micro_status or self.micro_pipeline_stage or self.micro_source:
			self._validate_micro_email()
		self._validate_organization()

	def _validate_organization(self):
		"""Keep the person-to-organization link pointing at an organization.

		`company_name` is kept as a mirror of the linked record's name rather
		than a second place to type one. Frappe core, the kanban cards, the
		contact picker and the print formats all read `company_name`, and a link
		that leaves them showing a different employer than the relation says
		would be worse than no link at all.
		"""
		if not self.get("micro_organization"):
			return

		if self.micro_organization == self.name:
			frappe.throw(_("A contact cannot belong to itself"))

		if self.micro_contact_type == "Organization":
			frappe.throw(_("An organization cannot belong to another organization"))

		organization = frappe.db.get_value(
			"Contact",
			self.micro_organization,
			["micro_contact_type", "company_name", "first_name"],
			as_dict=True,
		)
		if not organization:
			frappe.throw(_("Organization {0} does not exist").format(self.micro_organization))

		if organization.micro_contact_type != "Organization":
			frappe.throw(
				_("{0} is a person, not an organization").format(frappe.bold(self.micro_organization))
			)

		self.company_name = organization.company_name or organization.first_name

	def before_insert(self):
		if hasattr(super(), "before_insert"):
			super().before_insert()
		if self.micro_status:
			self._check_community_limit()

	def _validate_micro_email(self):
		"""Validate primary email format if set."""
		if self.email_id and not frappe.utils.validate_email_address(self.email_id):
			frappe.throw(_("Invalid email address: {0}").format(self.email_id))

	def _check_community_limit(self):
		"""Enforce customer limit for Community edition. 0 = unlimited."""
		limit = get_limit("customer_limit", DEFAULT_CUSTOMER_LIMIT)

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
