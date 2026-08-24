# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe.tests.utils import FrappeTestCase


class TestPipelineAdminAPI(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.db.set_single_value("Micro Settings", "pipeline_limit", 0)

	def _name(self, prefix="_Test Admin"):
		return frappe.generate_hash(prefix, 10)

	def _make_pipeline(self, **kwargs):
		from micro.api.pipeline_admin import create_pipeline

		result = create_pipeline(pipeline_name=self._name(), **kwargs)
		return result["pipeline"]

	# --- create ---

	def test_create_pipeline_seeds_starter_stages(self):
		from micro.api.pipeline_admin import STARTER_STAGES, get_pipeline_setup

		pipeline = self._make_pipeline()
		setup = get_pipeline_setup(pipeline)

		self.assertEqual(len(setup["stages"]), len(STARTER_STAGES))
		self.assertEqual(setup["stages"][0]["stage_name"], "New")
		self.assertEqual(setup["stages"][-1]["outcome"], "loss")

	def test_create_pipeline_without_stages(self):
		from micro.api.pipeline_admin import get_pipeline_setup

		pipeline = self._make_pipeline(with_starter_stages=False)
		self.assertEqual(get_pipeline_setup(pipeline)["stages"], [])

	def test_duplicate_pipeline_name_is_rejected(self):
		from micro.api.pipeline_admin import create_pipeline

		name = self._name()
		create_pipeline(pipeline_name=name)
		with self.assertRaises(frappe.ValidationError):
			create_pipeline(pipeline_name=name)

	# --- rename ---

	def test_rename_pipeline_keeps_its_stages(self):
		from micro.api.pipeline_admin import get_pipeline_setup, update_pipeline

		pipeline = self._make_pipeline()
		new_name = self._name("_Test Renamed")

		result = update_pipeline(pipeline=pipeline, pipeline_name=new_name)

		self.assertTrue(result["renamed"])
		self.assertEqual(result["pipeline"], new_name)
		self.assertEqual(len(get_pipeline_setup(new_name)["stages"]), 5)
		self.assertEqual(frappe.db.count("Micro Pipeline Stage", {"pipeline": pipeline}), 0)

	def test_rename_pipeline_relinks_its_leads(self):
		from micro.api.pipeline_admin import get_pipeline_setup, update_pipeline

		pipeline = self._make_pipeline()
		stage = get_pipeline_setup(pipeline)["stages"][0]["name"]
		lead = frappe.get_doc(
			{
				"doctype": "Micro Lead",
				"lead_name": "_Test Relink",
				"pipeline": pipeline,
				"stage": stage,
			}
		).insert(ignore_permissions=True)

		new_name = self._name("_Test Relinked")
		update_pipeline(pipeline=pipeline, pipeline_name=new_name)

		self.assertEqual(frappe.db.get_value("Micro Lead", lead.name, "pipeline"), new_name)

	def test_rename_onto_an_existing_name_is_rejected(self):
		from micro.api.pipeline_admin import update_pipeline

		first = self._make_pipeline()
		second = self._make_pipeline()

		with self.assertRaises(frappe.ValidationError):
			update_pipeline(pipeline=second, pipeline_name=first)

	# --- delete ---

	def test_delete_pipeline_removes_its_stages(self):
		from micro.api.pipeline_admin import delete_pipeline

		pipeline = self._make_pipeline()
		delete_pipeline(pipeline)

		self.assertFalse(frappe.db.exists("Micro Pipeline", pipeline))
		self.assertEqual(frappe.db.count("Micro Pipeline Stage", {"pipeline": pipeline}), 0)

	def test_delete_pipeline_with_leads_is_refused(self):
		from micro.api.pipeline_admin import delete_pipeline, get_pipeline_setup

		pipeline = self._make_pipeline()
		stage = get_pipeline_setup(pipeline)["stages"][0]["name"]
		frappe.get_doc(
			{
				"doctype": "Micro Lead",
				"lead_name": "_Test Blocker",
				"pipeline": pipeline,
				"stage": stage,
			}
		).insert(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			delete_pipeline(pipeline)

	# --- stages ---

	def test_stage_outcome_maps_onto_the_flags(self):
		from micro.api.pipeline_admin import create_stage, update_stage

		pipeline = self._make_pipeline(with_starter_stages=False)
		stage = create_stage(pipeline=pipeline, stage_name="_Test Outcome")["stage"]

		update_stage(stage=stage, outcome="win")
		row = frappe.db.get_value(
			"Micro Pipeline Stage", stage, ["is_win_stage", "is_loss_stage", "is_closed"], as_dict=True
		)
		self.assertTrue(row.is_win_stage)
		self.assertFalse(row.is_loss_stage)
		self.assertTrue(row.is_closed)

		update_stage(stage=stage, outcome="open")
		row = frappe.db.get_value(
			"Micro Pipeline Stage", stage, ["is_win_stage", "is_loss_stage", "is_closed"], as_dict=True
		)
		self.assertFalse(row.is_win_stage)
		self.assertFalse(row.is_closed)

	def test_unknown_outcome_is_rejected(self):
		from micro.api.pipeline_admin import create_stage

		pipeline = self._make_pipeline(with_starter_stages=False)
		with self.assertRaises(frappe.ValidationError):
			create_stage(pipeline=pipeline, stage_name="_Test Bad", outcome="maybe")

	def test_reorder_stages(self):
		from micro.api.pipeline_admin import get_pipeline_setup, reorder_stages

		pipeline = self._make_pipeline()
		stages = get_pipeline_setup(pipeline)["stages"]
		reversed_ids = [s["name"] for s in reversed(stages)]

		reorder_stages(pipeline=pipeline, stage_ids=reversed_ids)

		after = [s["name"] for s in get_pipeline_setup(pipeline)["stages"]]
		self.assertEqual(after, reversed_ids)

	def test_reorder_rejects_a_foreign_stage(self):
		from micro.api.pipeline_admin import get_pipeline_setup, reorder_stages

		pipeline_a = self._make_pipeline()
		pipeline_b = self._make_pipeline()
		foreign = get_pipeline_setup(pipeline_b)["stages"][0]["name"]

		with self.assertRaises(frappe.ValidationError):
			reorder_stages(pipeline=pipeline_a, stage_ids=[foreign])

	def test_delete_stage_moves_its_leads(self):
		from micro.api.pipeline_admin import delete_stage, get_pipeline_setup

		pipeline = self._make_pipeline()
		stages = get_pipeline_setup(pipeline)["stages"]
		source, target = stages[0]["name"], stages[1]["name"]

		lead = frappe.get_doc(
			{
				"doctype": "Micro Lead",
				"lead_name": "_Test Moved",
				"pipeline": pipeline,
				"stage": source,
			}
		).insert(ignore_permissions=True)

		result = delete_stage(stage=source, move_leads_to=target)

		self.assertEqual(result["moved"], 1)
		self.assertEqual(frappe.db.get_value("Micro Lead", lead.name, "stage"), target)
		self.assertFalse(frappe.db.exists("Micro Pipeline Stage", source))

	def test_delete_stage_with_leads_needs_a_target(self):
		from micro.api.pipeline_admin import delete_stage, get_pipeline_setup

		pipeline = self._make_pipeline()
		stage = get_pipeline_setup(pipeline)["stages"][0]["name"]
		frappe.get_doc(
			{
				"doctype": "Micro Lead",
				"lead_name": "_Test Stuck",
				"pipeline": pipeline,
				"stage": stage,
			}
		).insert(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			delete_stage(stage=stage)

	def test_leads_cannot_be_moved_into_another_pipeline(self):
		from micro.api.pipeline_admin import delete_stage, get_pipeline_setup

		pipeline_a = self._make_pipeline()
		pipeline_b = self._make_pipeline()
		stage_a = get_pipeline_setup(pipeline_a)["stages"][0]["name"]
		stage_b = get_pipeline_setup(pipeline_b)["stages"][0]["name"]

		frappe.get_doc(
			{
				"doctype": "Micro Lead",
				"lead_name": "_Test Cross",
				"pipeline": pipeline_a,
				"stage": stage_a,
			}
		).insert(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			delete_stage(stage=stage_a, move_leads_to=stage_b)

	# --- segments ---

	def test_create_segment_is_idempotent(self):
		from micro.api.pipeline_admin import create_segment

		name = self._name("_Test Seg")
		self.assertTrue(create_segment(segment_name=name)["created"])
		self.assertFalse(create_segment(segment_name=name)["created"])
