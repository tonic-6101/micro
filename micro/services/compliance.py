# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

"""
Compliance Engine — Zone 2 Guardrail Enforcement

This module implements the 6 universal guardrails for Zone 2 (Financial Draft Layer):
  G1: Draft watermark (ENTWURF/DRAFT) on all documents
  G2: No sequential numbering (random reference codes only)
  G3: No tax/VAT fields
  G4: Disclaimer footer (language-aware)
  G5: Safe terminology
  G6: No payment tracking
"""

import random
import string
from datetime import date

import frappe
from frappe import _


# G4: Language-aware disclaimer texts
DISCLAIMERS = {
	"de": "Entwurf — keine rechtsgültige Rechnung. Erstellung der endgültigen Rechnung durch Ihren Steuerberater.",
	"en": "DRAFT — not a legally binding invoice. Final invoice to be created by your tax advisor.",
	"fr": "BROUILLON — pas une facture juridiquement contraignante. La facture finale sera établie par votre conseiller fiscal.",
	"es": "BORRADOR — no es una factura legalmente vinculante. La factura final será creada por su asesor fiscal.",
	"it": "BOZZA — non è una fattura legalmente vincolante. La fattura finale sarà creata dal vostro consulente fiscale.",
	"pt": "RASCUNHO — não é uma fatura legalmente vinculativa. A fatura final será criada pelo seu consultor fiscal.",
	"pl": "PROJEKT — nie jest prawnie wiążącą fakturą. Ostateczna faktura zostanie wystawiona przez Twojego doradcę podatkowego.",
	"nl": "CONCEPT — geen juridisch bindende factuur. De definitieve factuur wordt opgesteld door uw belastingadviseur.",
}

# G1: Language-aware watermark texts
WATERMARKS = {
	"de": "ENTWURF",
	"en": "DRAFT",
	"fr": "BROUILLON",
	"es": "BORRADOR",
	"it": "BOZZA",
	"pt": "RASCUNHO",
	"pl": "PROJEKT",
	"nl": "CONCEPT",
}


def generate_random_reference(prefix: str, doctype: str | None = None) -> str:
	"""G2: Generate a non-sequential reference code.

	Format: {PREFIX}-{YYYYMMDD}-{RANDOM4}
	Example: OFF-20260315-X7K2

	References must NEVER be sequential (G2 guardrail).
	"""
	today = date.today().strftime("%Y%m%d")
	random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
	ref = f"{prefix}-{today}-{random_part}"

	# Ensure uniqueness — retry on collision (only if doctype is known)
	if doctype:
		attempts = 0
		while frappe.db.exists(doctype, {"reference": ref}) and attempts < 10:
			random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
			ref = f"{prefix}-{today}-{random_part}"
			attempts += 1

	return ref


def get_watermark_text(language: str = None) -> str:
	"""G1: Get draft watermark text, language-aware.

	Falls back to settings default, then to 'ENTWURF'.
	"""
	if language and language in WATERMARKS:
		return WATERMARKS[language]

	try:
		settings = frappe.get_single("Micro Settings")
		return settings.draft_watermark_text or "ENTWURF"
	except Exception:
		return "ENTWURF"


def get_disclaimer_text(language: str = None) -> str:
	"""G4: Get disclaimer footer text, language-aware.

	Falls back to settings default, then to German disclaimer.
	"""
	if language and language in DISCLAIMERS:
		return DISCLAIMERS[language]

	try:
		settings = frappe.get_single("Micro Settings")
		lang = settings.default_language or "de"
		return settings.draft_disclaimer or DISCLAIMERS.get(lang, DISCLAIMERS["de"])
	except Exception:
		return DISCLAIMERS["de"]


def validate_no_tax_fields(doc) -> None:
	"""G3: Ensure no tax/VAT fields exist on Zone 2 documents.

	Raises ValidationError if tax-related fields are found with values.
	"""
	forbidden_fields = ["tax_rate", "vat", "vat_amount", "tax_amount", "tax_category", "tax_template"]

	for field in forbidden_fields:
		if hasattr(doc, field) and getattr(doc, field):
			frappe.throw(_("Tax fields are not allowed on draft documents (compliance guardrail G3)"))

	# Check child table items if present
	items = getattr(doc, "items", None)
	if isinstance(items, (list, tuple)):
		for item in items:
			for field in forbidden_fields:
				if hasattr(item, field) and getattr(item, field):
					frappe.throw(_("Tax fields are not allowed on draft line items (compliance guardrail G3)"))


# G5: Safe terminology — forbidden terms that would classify Micro as a billing system
FORBIDDEN_TERMS = {
	"de": ["Rechnung", "Rechnungsnummer", "Rechnungsliste", "Rechnung senden"],
	"en": ["Invoice", "Invoice Number", "Invoice List", "Send Invoice"],
	"es": ["Factura", "Número de factura"],
	"fr": ["Facture", "Numéro de facture"],
	"it": ["Fattura", "Numero fattura"],
	"pt": ["Fatura", "Número da fatura"],
	"pl": ["Faktura", "Numer faktury"],
	"nl": ["Factuur", "Factuurnummer"],
}


def validate_safe_terminology(doc) -> None:
	"""G5: Ensure Zone 2 documents never use forbidden invoice terminology.

	Checks the title field for terms that would classify Micro as a billing system.
	Only validates user-editable fields — internal field names are not checked.
	"""
	fields_to_check = ["title"]
	for field in fields_to_check:
		value = getattr(doc, field, None)
		if not value:
			continue
		value_lower = value.lower()
		for lang, terms in FORBIDDEN_TERMS.items():
			for term in terms:
				if term.lower() == value_lower:
					frappe.throw(
						_(
							'The term "{0}" is not allowed in draft documents. '
							"Use draft-safe terminology instead (compliance guardrail G5)."
						).format(term)
					)


# G6: No payment tracking — forbidden status values
FORBIDDEN_STATUSES = [
	"Paid", "Unpaid", "Partially Paid", "Overdue",
	"Bezahlt", "Unbezahlt", "Teilweise bezahlt", "Überfällig",
	"Payé", "Impayé", "Pagado", "Impagado",
]


def validate_no_payment_tracking(doc) -> None:
	"""G6: Ensure Zone 2 documents never track payment status.

	Document statuses must be workflow-based (Draft/Sent/Accepted),
	never payment-based (Paid/Unpaid/Overdue).
	"""
	status = getattr(doc, "status", None)
	if status and status in FORBIDDEN_STATUSES:
		frappe.throw(
			_(
				'Payment status "{0}" is not allowed. Micro tracks document workflow, '
				"not payment status (compliance guardrail G6)."
			).format(status)
		)
