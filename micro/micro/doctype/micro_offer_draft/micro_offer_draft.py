# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe import _
from frappe.model.document import Document

from micro.services.compliance import (
	generate_random_reference,
	get_disclaimer_text,
	get_watermark_text,
	validate_no_tax_fields,
	validate_safe_terminology,
	validate_no_payment_tracking,
)


class MicroOfferDraft(Document):
	def before_insert(self):
		self.generate_reference()

	def validate(self):
		self.enforce_draft_status()
		self.set_watermark()
		self.set_disclaimer()
		self.calculate_totals()
		validate_no_tax_fields(self)
		validate_safe_terminology(self)
		validate_no_payment_tracking(self)

	def generate_reference(self):
		"""G2: Auto-generate non-sequential reference."""
		if not self.reference:
			self.reference = generate_random_reference("OFF", "Micro Offer Draft")

	def enforce_draft_status(self):
		"""G1: Offer documents must always be marked as drafts."""
		self.is_draft = 1

	def set_watermark(self):
		"""G1: Set language-aware watermark text."""
		lang = self.language or None
		self.watermark_text = get_watermark_text(lang)

	def set_disclaimer(self):
		"""G4: Set language-aware disclaimer footer."""
		lang = self.language or None
		self.disclaimer = get_disclaimer_text(lang)

	def calculate_totals(self):
		"""Compute item amounts and document total."""
		total = 0
		for item in self.items or []:
			item.amount = (item.quantity or 0) * (item.rate or 0)
			total += item.amount
		self.total = total
