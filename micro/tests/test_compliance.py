# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase

from micro.services.compliance import (
	DISCLAIMERS,
	WATERMARKS,
	generate_random_reference,
	get_disclaimer_text,
	get_watermark_text,
	validate_no_tax_fields,
)


class TestComplianceService(FrappeTestCase):
	# --- G2: Random reference generation ---

	def test_reference_format(self):
		ref = generate_random_reference("OFF")
		self.assertRegex(ref, r"^OFF-\d{8}-[A-Z0-9]{4}$")

	def test_reference_prefix_inv(self):
		ref = generate_random_reference("INV")
		self.assertTrue(ref.startswith("INV-"))

	def test_reference_uniqueness(self):
		refs = {generate_random_reference("TEST") for _ in range(20)}
		self.assertEqual(len(refs), 20)

	def test_reference_date_component(self):
		ref = generate_random_reference("OFF")
		date_part = ref.split("-")[1]
		self.assertEqual(len(date_part), 8)
		self.assertTrue(date_part.isdigit())

	# --- G1: Watermark text ---

	def test_watermark_german(self):
		self.assertEqual(get_watermark_text("de"), "ENTWURF")

	def test_watermark_english(self):
		self.assertEqual(get_watermark_text("en"), "DRAFT")

	def test_watermark_french(self):
		self.assertEqual(get_watermark_text("fr"), "BROUILLON")

	def test_watermark_spanish(self):
		self.assertEqual(get_watermark_text("es"), "BORRADOR")

	def test_watermark_italian(self):
		self.assertEqual(get_watermark_text("it"), "BOZZA")

	def test_watermark_portuguese(self):
		self.assertEqual(get_watermark_text("pt"), "RASCUNHO")

	def test_watermark_polish(self):
		self.assertEqual(get_watermark_text("pl"), "PROJEKT")

	def test_watermark_dutch(self):
		self.assertEqual(get_watermark_text("nl"), "CONCEPT")

	def test_watermark_fallback(self):
		text = get_watermark_text("xx")
		self.assertTrue(text)

	def test_watermark_none_language(self):
		text = get_watermark_text(None)
		self.assertTrue(text)

	# --- G4: Disclaimer text ---

	def test_disclaimer_german(self):
		text = get_disclaimer_text("de")
		self.assertIn("Entwurf", text)
		self.assertIn("Steuerberater", text)

	def test_disclaimer_english(self):
		text = get_disclaimer_text("en")
		self.assertIn("DRAFT", text)
		self.assertIn("tax advisor", text)

	def test_disclaimer_all_languages(self):
		for lang in DISCLAIMERS:
			text = get_disclaimer_text(lang)
			self.assertTrue(text, f"Disclaimer missing for language: {lang}")
			self.assertGreater(len(text), 20, f"Disclaimer too short for language: {lang}")

	def test_disclaimer_fallback(self):
		text = get_disclaimer_text("xx")
		self.assertTrue(text)

	def test_disclaimer_none_language(self):
		text = get_disclaimer_text(None)
		self.assertTrue(text)

	# --- G3: No tax fields ---

	def test_no_tax_fields_clean_doc(self):
		doc = frappe._dict({})
		validate_no_tax_fields(doc)

	def test_no_tax_fields_with_tax_rate(self):
		doc = frappe._dict({"tax_rate": 19.0})
		with self.assertRaises(frappe.ValidationError):
			validate_no_tax_fields(doc)

	def test_no_tax_fields_with_vat(self):
		doc = frappe._dict({"vat": 19.0})
		with self.assertRaises(frappe.ValidationError):
			validate_no_tax_fields(doc)

	def test_no_tax_fields_with_vat_amount(self):
		doc = frappe._dict({"vat_amount": 100})
		with self.assertRaises(frappe.ValidationError):
			validate_no_tax_fields(doc)

	def test_no_tax_fields_child_items(self):
		"""Error when child items have tax fields."""
		# Use a simple namespace to avoid frappe._dict.items conflict
		class MockDoc:
			pass
		doc = MockDoc()
		item = frappe._dict({"tax_rate": 7.0})
		doc.items = [item]
		with self.assertRaises(frappe.ValidationError):
			validate_no_tax_fields(doc)

	# --- Watermark/Disclaimer dictionaries ---

	def test_all_8_watermark_languages(self):
		self.assertEqual(len(WATERMARKS), 8)
		for lang in ["de", "en", "fr", "es", "it", "pt", "pl", "nl"]:
			self.assertIn(lang, WATERMARKS)

	def test_all_8_disclaimer_languages(self):
		self.assertEqual(len(DISCLAIMERS), 8)
		for lang in ["de", "en", "fr", "es", "it", "pt", "pl", "nl"]:
			self.assertIn(lang, DISCLAIMERS)
