# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe import _
from frappe.model.document import Document


class MicroDuplicatePair(Document):
	def validate(self):
		if self.contact_a == self.contact_b:
			frappe.throw(_("A contact cannot be a duplicate of itself"))

		# Stored in one canonical order so that scoring A against B and B against
		# A can never leave two mirrored rows describing the same suggestion.
		if self.contact_b < self.contact_a:
			self.contact_a, self.contact_b = self.contact_b, self.contact_a
