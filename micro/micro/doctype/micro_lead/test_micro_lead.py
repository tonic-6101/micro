# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe.tests import IntegrationTestCase


class TestMicroLead(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.db.set_single_value("Micro Settings", "pipeline_limit", 0)
		frappe.db.set_single_value("Micro Settings", "customer_limit", 9999)

	def _make_pipeline(self, **kwargs):
		defaults = {
			"doctype": "Micro Pipeline",
			"pipeline_name": frappe.generate_hash("_Test Pipeline", 8),
			"is_active": 1,
		}
		defaults.update(kwargs)
		return frappe.get_doc(defaults).insert(ignore_permissions=True)

	def _make_stage(self, pipeline, **kwargs):
		defaults = {
			"doctype": "Micro Pipeline Stage",
			"stage_name": "_Test Stage",
			"pipeline": pipeline,
			"sort_order": 10,
		}
		defaults.update(kwargs)
		return frappe.get_doc(defaults).insert(ignore_permissions=True)

	def _make_lead(self, **kwargs):
		defaults = {"doctype": "Micro Lead", "lead_name": "_Test Lead"}
		defaults.update(kwargs)
		return frappe.get_doc(defaults).insert(ignore_permissions=True)

	def _make_contact(self, **kwargs):
		defaults = {
			"doctype": "Contact",
			"first_name": "_Test Lead Contact",
			"micro_status": "Potential",
		}
		defaults.update(kwargs)
		return frappe.get_doc(defaults).insert(ignore_permissions=True)

	# --- basics ---

	def test_create_lead(self):
		pipeline = self._make_pipeline()
		stage = self._make_stage(pipeline.name)
		lead = self._make_lead(
			lead_name="_Test Website Project", pipeline=pipeline.name, stage=stage.name
		)

		self.assertEqual(lead.status, "Open")
		self.assertTrue(lead.name.startswith("ML-"))

	def test_lead_defaults(self):
		pipeline = self._make_pipeline()
		self._make_stage(pipeline.name)
		lead = self._make_lead(pipeline=pipeline.name)

		self.assertEqual(lead.priority, "Medium")

	def test_stage_defaults_to_first_open_stage_of_its_pipeline(self):
		pipeline = self._make_pipeline()
		first = self._make_stage(pipeline.name, stage_name="_Test First", sort_order=10)
		self._make_stage(pipeline.name, stage_name="_Test Second", sort_order=20)

		lead = self._make_lead(pipeline=pipeline.name)
		self.assertEqual(lead.stage, first.name)

	# --- pipeline integrity ---

	def test_stage_from_another_pipeline_is_rejected(self):
		pipeline_a = self._make_pipeline()
		pipeline_b = self._make_pipeline()
		self._make_stage(pipeline_a.name, stage_name="_Test A")
		foreign = self._make_stage(pipeline_b.name, stage_name="_Test B")

		with self.assertRaises(frappe.ValidationError):
			self._make_lead(pipeline=pipeline_a.name, stage=foreign.name)

	# --- win/loss by flag, not by stage name ---

	def test_win_stage_sets_status_won_regardless_of_stage_name(self):
		pipeline = self._make_pipeline()
		self._make_stage(pipeline.name, stage_name="_Test Erstkontakt", sort_order=10)
		won = self._make_stage(
			pipeline.name, stage_name="_Test Beauftragt", sort_order=50, is_win_stage=1
		)

		lead = self._make_lead(pipeline=pipeline.name)
		lead.stage = won.name
		lead.save()

		self.assertEqual(lead.status, "Won")

	def test_loss_stage_requires_a_reason(self):
		pipeline = self._make_pipeline()
		self._make_stage(pipeline.name, stage_name="_Test Open", sort_order=10)
		lost = self._make_stage(
			pipeline.name, stage_name="_Test Abgesagt", sort_order=60, is_loss_stage=1
		)

		lead = self._make_lead(pipeline=pipeline.name)
		lead.stage = lost.name
		with self.assertRaises(frappe.ValidationError):
			lead.save()

		lead.reload()
		lead.stage = lost.name
		lead.lost_reason = "Too expensive"
		lead.save()
		self.assertEqual(lead.status, "Lost")

	def test_moving_back_out_of_a_closing_stage_reopens_the_lead(self):
		pipeline = self._make_pipeline()
		open_stage = self._make_stage(pipeline.name, stage_name="_Test Open", sort_order=10)
		won = self._make_stage(pipeline.name, stage_name="_Test Won", sort_order=50, is_win_stage=1)

		lead = self._make_lead(pipeline=pipeline.name, stage=won.name)
		self.assertEqual(lead.status, "Won")

		lead.stage = open_stage.name
		lead.save()
		self.assertEqual(lead.status, "Open")

	# --- contact side effects ---

	def test_lead_tags_its_contact_with_the_pipeline_segment(self):
		segment = frappe.get_doc(
			{"doctype": "Micro Segment", "segment_name": frappe.generate_hash("_Test Seg", 8)}
		).insert(ignore_permissions=True)
		pipeline = self._make_pipeline(segment=segment.name)
		self._make_stage(pipeline.name)
		contact = self._make_contact(first_name="_Test Segment")

		self._make_lead(pipeline=pipeline.name, contact=contact.name)

		self.assertEqual(frappe.db.get_value("Contact", contact.name, "micro_segment"), segment.name)

	def test_lead_mirrors_its_stage_onto_the_contact(self):
		pipeline = self._make_pipeline()
		stage = self._make_stage(pipeline.name)
		contact = self._make_contact(first_name="_Test Mirror")

		self._make_lead(pipeline=pipeline.name, stage=stage.name, contact=contact.name)

		self.assertEqual(
			frappe.db.get_value("Contact", contact.name, "micro_pipeline_stage"), stage.name
		)

	# --- expected value bounds ---

	def test_expected_value_rejects_a_negative_amount(self):
		pipeline = self._make_pipeline()
		stage = self._make_stage(pipeline.name)

		with self.assertRaises(frappe.ValidationError):
			self._make_lead(pipeline=pipeline.name, stage=stage.name, expected_value=-1)

	def test_expected_value_rejects_a_slipped_zero(self):
		"""The ceiling is a typo guard, so the amount above it must not save."""
		pipeline = self._make_pipeline()
		stage = self._make_stage(pipeline.name)
		frappe.db.set_single_value("Micro Settings", "max_expected_value", 1000)

		with self.assertRaises(frappe.ValidationError):
			self._make_lead(pipeline=pipeline.name, stage=stage.name, expected_value=10000)

	def test_expected_value_accepts_the_ceiling_itself(self):
		pipeline = self._make_pipeline()
		stage = self._make_stage(pipeline.name)
		frappe.db.set_single_value("Micro Settings", "max_expected_value", 1000)

		lead = self._make_lead(pipeline=pipeline.name, stage=stage.name, expected_value=1000)
		self.assertEqual(lead.expected_value, 1000)

	def test_expected_value_ceiling_of_zero_means_no_ceiling(self):
		"""0 switches the limit off, as it does for every other Micro Settings limit."""
		pipeline = self._make_pipeline()
		stage = self._make_stage(pipeline.name)
		frappe.db.set_single_value("Micro Settings", "max_expected_value", 0)

		lead = self._make_lead(
			pipeline=pipeline.name, stage=stage.name, expected_value=50_000_000
		)
		self.assertEqual(lead.expected_value, 50_000_000)

	def test_expected_value_may_stay_empty(self):
		"""Not knowing the amount yet is normal — it must not block the save."""
		pipeline = self._make_pipeline()
		stage = self._make_stage(pipeline.name)

		lead = self._make_lead(pipeline=pipeline.name, stage=stage.name)
		self.assertFalse(lead.expected_value)
