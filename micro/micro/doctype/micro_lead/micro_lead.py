# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from micro.limits import DEFAULT_MAX_EXPECTED_VALUE, get_limit
from micro.micro.doctype.micro_pipeline.micro_pipeline import get_default_pipeline


class DuplicateOpenLeadError(frappe.ValidationError):
	"""The contact is already open in this pipeline — callers may want to skip."""


class MicroLead(Document):
	def validate(self):
		self._set_default_pipeline()
		self._set_default_stage()
		self._validate_stage_belongs_to_pipeline()
		self._sync_status_from_stage()
		self._no_second_open_lead()
		self._require_lost_reason()
		self._validate_expected_value()

	def on_update(self):
		self._tag_contact_segment()
		self._mirror_stage_to_contact()

	def on_trash(self):
		self._mirror_stage_to_contact(removing=True)

	def _set_default_pipeline(self):
		if not self.pipeline:
			self.pipeline = get_default_pipeline()

	def _set_default_stage(self):
		"""New leads start in the first open stage of their own pipeline."""
		if self.stage or not self.pipeline:
			return

		self.stage = frappe.db.get_value(
			"Micro Pipeline Stage",
			{"pipeline": self.pipeline, "is_closed": 0},
			"name",
			order_by="sort_order asc",
		)

	def _validate_stage_belongs_to_pipeline(self):
		"""A lead can only sit in a stage of its own pipeline."""
		if not self.stage or not self.pipeline:
			return

		stage_pipeline = frappe.db.get_value("Micro Pipeline Stage", self.stage, "pipeline")
		if stage_pipeline and stage_pipeline != self.pipeline:
			frappe.throw(
				_("Stage {0} belongs to pipeline {1}, not to {2}.").format(
					frappe.bold(self.stage),
					frappe.bold(stage_pipeline),
					frappe.bold(self.pipeline),
				)
			)

	def _sync_status_from_stage(self):
		"""Win/loss stages drive the status — never the stage name."""
		if not self.stage:
			return

		# Archiving is an explicit act on the lead itself; the stage it happens
		# to be parked in does not get to undo it.
		if self.status == "Archived":
			return

		stage = frappe.db.get_value(
			"Micro Pipeline Stage",
			self.stage,
			["is_win_stage", "is_loss_stage"],
			as_dict=True,
		)
		if not stage:
			return

		if stage.is_win_stage:
			self.status = "Won"
		elif stage.is_loss_stage:
			self.status = "Lost"
		elif self.status in ("Won", "Lost"):
			# Dragged back out of a closing stage — the deal is live again.
			self.status = "Open"

	def _no_second_open_lead(self):
		"""One open lead per contact per pipeline.

		Pipelines are separate conversations, so the same contact may be open in
		several of them at once — a customer being sold a website is also a
		candidate for the maintenance retainer. Twice in the *same* pipeline at
		the same time is not a second deal though; it is one deal entered twice,
		which is what a re-import or a forgotten first attempt produces.

		Closed leads never block. Coming back to a contact months after a Lost is
		the whole point of the follow-up queue, and each attempt keeps its own row
		so the history reads: lost in March, won in September.
		"""
		if self.status != "Open" or not self.contact or not self.pipeline:
			return

		existing = frappe.db.get_value(
			"Micro Lead",
			{
				"contact": self.contact,
				"pipeline": self.pipeline,
				"status": "Open",
				"name": ["!=", self.name or ""],
			},
			["name", "lead_name"],
			as_dict=True,
		)
		if not existing:
			return

		frappe.throw(
			_("{0} already has an open lead in this pipeline: {1}. Close that one first, or work it instead.").format(
				frappe.bold(frappe.db.get_value("Contact", self.contact, "full_name") or self.contact),
				frappe.bold(existing.lead_name or existing.name),
			),
			title=_("Already in this pipeline"),
			exc=DuplicateOpenLeadError,
		)

	def _require_lost_reason(self):
		if self.status == "Lost" and not self.lost_reason:
			frappe.throw(_("Please record why this lead was lost."))

	def _validate_expected_value(self):
		"""Between nothing and the ceiling in Micro Settings.

		A deal is never worth less than nothing, and the upper bound is there to
		catch a slipped zero rather than to police ambition — the board sums
		these values per column, so one wrong figure moves every total.
		"""
		if self.expected_value is None or self.expected_value == "":
			return

		value = flt(self.expected_value)

		if value < 0:
			frappe.throw(
				_("Expected value cannot be negative — a deal is worth nothing at worst."),
				title=_("Check the amount"),
			)

		maximum = get_limit("max_expected_value", DEFAULT_MAX_EXPECTED_VALUE)
		if maximum and value > maximum:
			frappe.throw(
				_("Expected value must be between {0} and {1}. Raise the ceiling in Micro Settings if this deal really is that big.").format(
					frappe.format_value(0, {"fieldtype": "Currency"}),
					frappe.format_value(maximum, {"fieldtype": "Currency"}),
				),
				title=_("Check the amount"),
			)

	def _tag_contact_segment(self):
		"""Carry the pipeline's segment over to the contact if it has none yet."""
		if not self.contact or not self.pipeline:
			return

		segment = frappe.db.get_value("Micro Pipeline", self.pipeline, "segment")
		if not segment:
			return

		if not frappe.db.get_value("Contact", self.contact, "micro_segment"):
			frappe.db.set_value(
				"Contact", self.contact, "micro_segment", segment, update_modified=False
			)

	def _mirror_stage_to_contact(self, removing: bool = False):
		"""Keep the legacy Contact.micro_pipeline_stage mirror in step.

		The board reads Micro Lead; the contact field only exists so Dock and
		the contact list can show a stage at a glance.
		"""
		if not self.contact:
			return

		filters = {"contact": self.contact, "status": "Open"}
		if removing:
			filters["name"] = ["!=", self.name]

		stage = frappe.db.get_value("Micro Lead", filters, "stage", order_by="modified desc")
		frappe.db.set_value(
			"Contact", self.contact, "micro_pipeline_stage", stage, update_modified=False
		)
