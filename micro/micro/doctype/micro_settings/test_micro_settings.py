# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase


class TestMicroSettings(FrappeTestCase):
	def _get_settings(self):
		return frappe.get_single("Micro Settings")

	# --- Settings exist ---

	def test_settings_exists(self):
		settings = self._get_settings()
		self.assertIsNotNone(settings)

	# --- Default values ---

	def test_default_currency(self):
		settings = self._get_settings()
		self.assertTrue(settings.default_currency)

	def test_default_language(self):
		settings = self._get_settings()
		self.assertTrue(settings.default_language)

	def test_customer_limit(self):
		settings = self._get_settings()
		self.assertIsNotNone(settings.customer_limit)
		self.assertGreater(settings.customer_limit, 0)

	def test_article_limit(self):
		settings = self._get_settings()
		self.assertIsNotNone(settings.article_limit)
		self.assertGreater(settings.article_limit, 0)

	# --- Disclaimer auto-fill ---

	def test_disclaimer_auto_fills(self):
		settings = self._get_settings()
		settings.draft_disclaimer = None
		settings.default_language = "de"
		settings.save(ignore_permissions=True)

		settings.reload()
		self.assertTrue(settings.draft_disclaimer)
		self.assertIn("Entwurf", settings.draft_disclaimer)

	def test_disclaimer_english(self):
		settings = self._get_settings()
		settings.draft_disclaimer = None
		settings.default_language = "en"
		settings.save(ignore_permissions=True)

		settings.reload()
		self.assertTrue(settings.draft_disclaimer)
		self.assertIn("DRAFT", settings.draft_disclaimer)

	# --- Watermark text ---

	def test_watermark_text(self):
		settings = self._get_settings()
		self.assertTrue(settings.draft_watermark_text)
