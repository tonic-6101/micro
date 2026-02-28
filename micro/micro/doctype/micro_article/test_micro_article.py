# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase


class TestMicroArticle(FrappeTestCase):
	def setUp(self):
		super().setUp()
		settings = frappe.get_single("Micro Settings")
		settings.article_limit = 9999
		settings.save(ignore_permissions=True)

	def _make_article(self, **kwargs):
		"""Helper to create a test article."""
		defaults = {
			"doctype": "Micro Article",
			"article_name": "_Test Article",
			"selling_price": 100.00,
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	# --- CRUD ---

	def test_create_article(self):
		article = self._make_article()
		self.assertTrue(article.name)
		self.assertTrue(article.name.startswith("MA-"))

	def test_read_article(self):
		article = self._make_article()
		loaded = frappe.get_doc("Micro Article", article.name)
		self.assertEqual(loaded.article_name, "_Test Article")
		self.assertEqual(loaded.selling_price, 100.00)

	def test_update_article(self):
		article = self._make_article()
		article.selling_price = 200.00
		article.save(ignore_permissions=True)
		loaded = frappe.get_doc("Micro Article", article.name)
		self.assertEqual(loaded.selling_price, 200.00)

	def test_delete_article(self):
		article = self._make_article()
		name = article.name
		frappe.delete_doc("Micro Article", name)
		self.assertFalse(frappe.db.exists("Micro Article", name))

	# --- Autoname ---

	def test_autoname_prefix(self):
		article = self._make_article()
		self.assertRegex(article.name, r"^MA-\d{4}$")

	# --- Fields ---

	def test_default_unit(self):
		article = self._make_article()
		self.assertEqual(article.unit, "Stück")

	def test_default_active(self):
		article = self._make_article()
		self.assertEqual(article.is_active, 1)

	def test_article_code(self):
		article = self._make_article(article_code="ART-001")
		self.assertEqual(article.article_code, "ART-001")

	def test_category(self):
		article = self._make_article(category="Tools")
		self.assertEqual(article.category, "Tools")

	def test_purchase_price(self):
		article = self._make_article(purchase_price=50.00)
		self.assertEqual(article.purchase_price, 50.00)

	def test_description(self):
		article = self._make_article(description="A test article description")
		self.assertEqual(article.description, "A test article description")

	def test_supplier(self):
		article = self._make_article(supplier="Test Supplier GmbH")
		self.assertEqual(article.supplier, "Test Supplier GmbH")

	# --- G3: No tax fields (compliance) ---

	def test_no_tax_fields_on_article(self):
		"""G3: Articles must not have tax-related fields."""
		meta = frappe.get_meta("Micro Article")
		forbidden = ["tax_rate", "vat", "vat_amount", "tax_amount", "tax_category", "tax_template"]
		for field in forbidden:
			self.assertFalse(
				meta.has_field(field),
				f"Article should not have field '{field}' (G3 compliance)",
			)

	# --- Community limit ---

	def test_community_limit_enforcement(self):
		"""Article limit from Micro Settings is enforced."""
		existing_count = frappe.db.count("Micro Article")

		settings = frappe.get_single("Micro Settings")
		settings.article_limit = existing_count + 1
		settings.save(ignore_permissions=True)

		self._make_article(article_name="_Test Limit1")

		with self.assertRaises(frappe.ValidationError):
			self._make_article(article_name="_Test Limit2")

	def test_zero_limit_means_unlimited(self):
		"""Setting limit to 0 means no limit."""
		settings = frappe.get_single("Micro Settings")
		settings.article_limit = 0
		settings.save(ignore_permissions=True)

		article = self._make_article(article_name="_Test Unlimited")
		self.assertTrue(article.name)
