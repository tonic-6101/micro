# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase


class TestPipelineAPI(FrappeTestCase):
	def setUp(self):
		super().setUp()
		# Ensure customer limit is high enough for tests
		settings = frappe.get_single("Micro Settings")
		settings.customer_limit = 9999
		settings.save(ignore_permissions=True)

	def _make_stage(self, **kwargs):
		defaults = {
			"doctype": "Micro Pipeline Stage",
			"stage_name": "_Test Stage",
			"sort_order": 10,
			"color": "Blue",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def _make_customer(self, **kwargs):
		defaults = {
			"doctype": "Contact",
			"first_name": "_Test Pipeline",
			"last_name": "Customer",
			"micro_contact_type": "Person",
			"micro_status": "Potential",
			"email_id": "pipeline@example.com",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		if defaults.get("email_id"):
			doc.append("email_ids", {"email_id": defaults["email_id"], "is_primary": 1})
		doc.insert(ignore_permissions=True)
		return doc

	def test_get_pipeline_returns_stages(self):
		"""get_pipeline returns stages with customers."""
		from micro.api.pipeline import get_pipeline

		stage = self._make_stage(stage_name="_Test Pipeline Stage")
		customer = self._make_customer(
			micro_pipeline_stage=stage.name,
			email_id="pstage@example.com",
		)

		result = get_pipeline(show_closed=True)
		self.assertIn("stages", result)
		self.assertIn("unassigned", result)
		self.assertIsInstance(result["stages"], list)

		# Find our stage
		found = False
		for col in result["stages"]:
			if col["stage"]["name"] == stage.name:
				found = True
				customer_names = [c["name"] for c in col["customers"]]
				self.assertIn(customer.name, customer_names)
		self.assertTrue(found)

	def test_get_pipeline_hides_closed(self):
		"""get_pipeline hides closed stages by default."""
		from micro.api.pipeline import get_pipeline

		open_stage = self._make_stage(
			stage_name="_Test Open", sort_order=10, is_closed=0
		)
		closed_stage = self._make_stage(
			stage_name="_Test Closed", sort_order=20, is_closed=1
		)

		result = get_pipeline(show_closed=False)
		stage_names = [col["stage"]["name"] for col in result["stages"]]
		self.assertIn(open_stage.name, stage_names)
		self.assertNotIn(closed_stage.name, stage_names)

	def test_get_pipeline_shows_closed(self):
		"""get_pipeline shows closed stages when requested."""
		from micro.api.pipeline import get_pipeline

		closed_stage = self._make_stage(
			stage_name="_Test Show Closed", sort_order=99, is_closed=1
		)

		result = get_pipeline(show_closed=True)
		stage_names = [col["stage"]["name"] for col in result["stages"]]
		self.assertIn(closed_stage.name, stage_names)

	def test_move_customer(self):
		"""move_customer updates the contact's pipeline stage."""
		from micro.api.pipeline import move_customer

		stage1 = self._make_stage(stage_name="_Test From", sort_order=10)
		stage2 = self._make_stage(stage_name="_Test To", sort_order=20)
		customer = self._make_customer(
			micro_pipeline_stage=stage1.name,
			email_id="move@example.com",
		)

		result = move_customer(customer.name, stage2.name)
		self.assertTrue(result["success"])

		loaded = frappe.get_doc("Contact", customer.name)
		self.assertEqual(loaded.micro_pipeline_stage, stage2.name)

	def test_move_customer_invalid_customer(self):
		"""move_customer throws for invalid customer."""
		from micro.api.pipeline import move_customer

		stage = self._make_stage(stage_name="_Test Move Invalid")
		with self.assertRaises(frappe.ValidationError):
			move_customer("NONEXISTENT", stage.name)

	def test_move_customer_invalid_stage(self):
		"""move_customer throws for invalid stage."""
		from micro.api.pipeline import move_customer

		customer = self._make_customer(email_id="moveinv@example.com")
		with self.assertRaises(frappe.ValidationError):
			move_customer(customer.name, "NONEXISTENT")

	def test_get_stages(self):
		"""get_stages returns all stages in order."""
		from micro.api.pipeline import get_stages

		s1 = self._make_stage(stage_name="_Test S1", sort_order=10)
		s2 = self._make_stage(stage_name="_Test S2", sort_order=20)

		result = get_stages()
		self.assertIn("stages", result)
		self.assertIsInstance(result["stages"], list)

		# Check order — s1 should come before s2
		names = [s["name"] for s in result["stages"]]
		if s1.name in names and s2.name in names:
			self.assertLess(names.index(s1.name), names.index(s2.name))

	def test_unassigned_customers(self):
		"""Contacts with micro_status but no pipeline_stage appear in unassigned."""
		from micro.api.pipeline import get_pipeline

		customer = self._make_customer(
			email_id="unassigned@example.com",
		)
		# Clear the auto-assigned pipeline stage
		frappe.db.set_value("Contact", customer.name, "micro_pipeline_stage", None)

		result = get_pipeline()
		unassigned_names = [c["name"] for c in result["unassigned"]]
		self.assertIn(customer.name, unassigned_names)
