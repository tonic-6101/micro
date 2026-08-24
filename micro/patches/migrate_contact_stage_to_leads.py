# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Turn the pipeline stage parked on each Contact into a real Micro Lead.

Until now the Kanban board read `Contact.micro_pipeline_stage`, which allowed a
contact exactly one stage in exactly one process. The board now reads Micro Lead,
so every contact that carried a stage gets a lead representing that open deal.
The contact field survives as a read-only mirror.
"""

import frappe


def execute():
	for doctype in ("Micro Pipeline", "Micro Pipeline Stage", "Micro Lead"):
		if not frappe.db.exists("DocType", doctype):
			return

	_backfill_pipeline_defaults()
	_create_leads_from_contact_stages()


def _backfill_pipeline_defaults():
	"""Existing pipelines predate is_active/sort_order."""
	for name in frappe.get_all("Micro Pipeline", pluck="name"):
		frappe.db.set_value("Micro Pipeline", name, "is_active", 1, update_modified=False)

	if not frappe.db.exists("Micro Pipeline", {"is_default": 1}):
		first = frappe.db.get_value("Micro Pipeline", {}, "name", order_by="creation asc")
		if first:
			frappe.db.set_value("Micro Pipeline", first, "is_default", 1, update_modified=False)

	frappe.db.commit()


def _create_leads_from_contact_stages():
	contacts = frappe.get_all(
		"Contact",
		filters={"micro_pipeline_stage": ["is", "set"]},
		fields=["name", "first_name", "last_name", "company_name", "micro_pipeline_stage", "micro_source"],
	)
	if not contacts:
		return

	stage_pipelines = {
		row["name"]: row["pipeline"]
		for row in frappe.get_all("Micro Pipeline Stage", fields=["name", "pipeline"])
	}

	created = 0
	for contact in contacts:
		if frappe.db.exists("Micro Lead", {"contact": contact["name"]}):
			continue

		pipeline = stage_pipelines.get(contact["micro_pipeline_stage"])
		if not pipeline:
			continue

		lead = frappe.new_doc("Micro Lead")
		lead.lead_name = _display_name(contact)
		lead.contact = contact["name"]
		lead.pipeline = pipeline
		lead.stage = contact["micro_pipeline_stage"]
		lead.priority = "Medium"
		if contact.get("micro_source"):
			lead.source = contact["micro_source"]
		# A migrated lead in a loss stage has no recorded reason.
		lead.lost_reason = lead.lost_reason or "Migrated from contact stage"
		lead.insert(ignore_permissions=True)
		created += 1

	frappe.db.commit()
	print(f"micro: created {created} lead(s) from contact pipeline stages")


def _display_name(contact: dict) -> str:
	parts = [contact.get("first_name"), contact.get("last_name")]
	name = " ".join(part for part in parts if part).strip()
	return name or contact.get("company_name") or contact["name"]
