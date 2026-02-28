# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase

from micro.api.articles import get_article, get_articles


class TestArticleAPI(FrappeTestCase):
	def setUp(self):
		super().setUp()
		settings = frappe.get_single("Micro Settings")
		settings.article_limit = 9999
		settings.save(ignore_permissions=True)

	def _make_article(self, **kwargs):
		defaults = {
			"doctype": "Micro Article",
			"article_name": "_Test API Article",
			"selling_price": 75.00,
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	# --- get_articles ---

	def test_get_articles_returns_dict(self):
		self._make_article()
		result = get_articles()
		self.assertIsInstance(result, dict)
		self.assertIn("articles", result)
		self.assertIn("total", result)

	def test_get_articles_list(self):
		self._make_article()
		result = get_articles()
		self.assertGreaterEqual(len(result["articles"]), 1)

	def test_get_articles_pagination(self):
		for i in range(3):
			self._make_article(article_name=f"_Test Page Art {i}", selling_price=10.00 + i)

		result = get_articles(limit_page_length=2)
		self.assertLessEqual(len(result["articles"]), 2)
		self.assertGreaterEqual(result["total"], 3)

	def test_get_articles_search(self):
		self._make_article(article_name="_Test Searchable Widget")
		result = get_articles(search="_Test Searchable Widget")
		self.assertGreaterEqual(len(result["articles"]), 1)
		self.assertTrue(
			any("Searchable Widget" in a["article_name"] for a in result["articles"])
		)

	def test_get_articles_fields(self):
		self._make_article()
		result = get_articles()
		article = result["articles"][0]
		for field in ["name", "article_name", "selling_price", "is_active"]:
			self.assertIn(field, article)

	# --- get_article ---

	def test_get_article_detail(self):
		article = self._make_article()
		result = get_article(article.name)
		self.assertIsInstance(result, dict)
		self.assertIn("article", result)
		self.assertEqual(result["article"]["article_name"], "_Test API Article")

	def test_get_article_not_found(self):
		with self.assertRaises(frappe.DoesNotExistError):
			get_article("NONEXISTENT-ARTICLE")
