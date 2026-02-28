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
)


class MicroInvoiceDraft(Document):
	def before_insert(self):
		self.generate_reference()

	def validate(self):
		self.enforce_draft_status()
		self.set_watermark()
		self.set_disclaimer()
		self.calculate_totals()
		validate_no_tax_fields(self)

	def generate_reference(self):
		"""G2: Auto-generate non-sequential reference."""
		if not self.reference:
			self.reference = generate_random_reference("INV", "Micro Invoice Draft")

	def enforce_draft_status(self):
		"""G1: Invoice drafts must always be marked as drafts."""
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


@frappe.whitelist()
def create_from_offer(offer_name: str) -> dict:
	"""Create an invoice draft from an accepted offer.

	Copies all line items from the offer to the new invoice draft.
	"""
	frappe.has_permission("Micro Invoice Draft", "create", throw=True)

	offer = frappe.get_doc("Micro Offer Draft", offer_name)

	invoice = frappe.new_doc("Micro Invoice Draft")
	invoice.contact = offer.contact
	invoice.title = offer.title
	invoice.language = offer.language
	invoice.source = "From Offer"
	invoice.offer_draft = offer.name

	for offer_item in offer.items or []:
		invoice.append("items", {
			"article": offer_item.article,
			"description": offer_item.description,
			"quantity": offer_item.quantity,
			"unit": offer_item.unit,
			"rate": offer_item.rate,
		})

	invoice.insert()

	return invoice.as_dict()
