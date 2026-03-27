# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import csv
import io
import os
import zipfile

import frappe
from frappe import _
from frappe.utils import getdate, nowdate


@frappe.whitelist()
def get_export_preview(
	doc_type: str = "Micro Receipt",
	from_date: str | None = None,
	to_date: str | None = None,
	category: str | None = None,
	only_unexported: int = 0,
) -> dict:
	"""Preview how many documents would be exported with given filters."""
	filters = _build_filters(doc_type, from_date, to_date, category, only_unexported)
	count = frappe.db.count(doc_type, filters)
	return {"doc_type": doc_type, "count": count, "filters": filters}


@frappe.whitelist()
def export_csv(
	doc_type: str = "Micro Receipt",
	from_date: str | None = None,
	to_date: str | None = None,
	category: str | None = None,
	only_unexported: int = 0,
	mark_exported: int = 0,
) -> dict:
	"""Export documents as CSV and optionally mark them as exported."""
	if doc_type == "Micro Receipt":
		return _export_receipts(from_date, to_date, category, only_unexported, mark_exported)
	elif doc_type == "Micro Invoice Draft":
		return _export_invoice_drafts(from_date, to_date, mark_exported)
	else:
		frappe.throw(_("Unsupported document type for export: {0}").format(doc_type))


@frappe.whitelist()
def mark_as_exported(doc_type: str, names: list | str = None) -> dict:
	"""Mark specific documents as exported."""
	if isinstance(names, str):
		import json

		names = json.loads(names)

	if not names:
		frappe.throw(_("No documents specified"))

	if doc_type != "Micro Receipt":
		frappe.throw(_("Export tracking is only supported for Receipts"))

	today = nowdate()
	updated = 0
	for name in names:
		frappe.db.set_value("Micro Receipt", name, {
			"exported": 1,
			"export_date": today,
		})
		updated += 1

	frappe.db.commit()
	return {"updated": updated}


@frappe.whitelist()
def export_zip(
	from_date: str | None = None,
	to_date: str | None = None,
	category: str | None = None,
	only_unexported: int = 0,
	mark_exported: int = 0,
) -> dict:
	"""Export receipts as ZIP containing receipt images + CSV summary.

	Structure:
	  receipts_export_YYYY-MM-DD.zip
	  ├── receipts.csv         (CSV summary)
	  └── images/
	      ├── MR-0001_vendor.jpg
	      └── ...
	"""
	filters = _build_filters("Micro Receipt", from_date, to_date, category, only_unexported)

	receipts = frappe.get_all(
		"Micro Receipt",
		filters=filters,
		fields=[
			"name", "receipt_date", "vendor", "description",
			"category", "amount", "image",
		],
		order_by="receipt_date asc",
	)

	# Build CSV
	csv_output = io.StringIO()
	writer = csv.writer(csv_output, delimiter=";")
	writer.writerow([
		_("Date"), _("Vendor"), _("Description"),
		_("Category"), _("Amount"), _("Receipt ID"), _("Image File"),
	])

	names = []
	image_map = {}  # name -> (file_url, archive_filename)

	for r in receipts:
		archive_filename = ""
		if r.image:
			ext = os.path.splitext(r.image)[1] or ".jpg"
			safe_vendor = (r.vendor or "unknown").replace("/", "_").replace(" ", "_")[:30]
			archive_filename = f"{r.name}_{safe_vendor}{ext}"
			image_map[r.name] = (r.image, archive_filename)

		writer.writerow([
			str(r.receipt_date) if r.receipt_date else "",
			r.vendor or "",
			r.description or "",
			r.category or "",
			f"{float(r.amount or 0):.2f}",
			r.name,
			archive_filename,
		])
		names.append(r.name)

	# Build ZIP in memory
	zip_buffer = io.BytesIO()
	with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
		# Add CSV
		zf.writestr("receipts.csv", csv_output.getvalue())

		# Add images
		for receipt_name, (file_url, archive_name) in image_map.items():
			file_path = _resolve_file_path(file_url)
			if file_path and os.path.exists(file_path):
				zf.write(file_path, f"images/{archive_name}")

	# Mark as exported if requested
	if int(mark_exported) and names:
		today = nowdate()
		for name in names:
			frappe.db.set_value("Micro Receipt", name, {
				"exported": 1,
				"export_date": today,
			})
		frappe.db.commit()

	# Save ZIP as a Frappe File for download
	zip_filename = f"receipts_export_{nowdate()}.zip"
	zip_data = zip_buffer.getvalue()

	file_doc = frappe.get_doc({
		"doctype": "File",
		"file_name": zip_filename,
		"content": zip_data,
		"is_private": 1,
	})
	file_doc.save(ignore_permissions=True)

	return {
		"file_url": file_doc.file_url,
		"filename": zip_filename,
		"count": len(receipts),
		"images_included": len(image_map),
		"marked_exported": int(mark_exported) and len(names) or 0,
	}


def _resolve_file_path(file_url: str) -> str | None:
	"""Resolve a Frappe file URL to an absolute filesystem path."""
	if not file_url:
		return None

	site_path = frappe.get_site_path()
	if file_url.startswith("/private/files/"):
		return os.path.join(site_path, file_url.lstrip("/"))
	if file_url.startswith("/files/"):
		return os.path.join(site_path, "public", file_url.lstrip("/"))

	# Try via File doctype
	file_doc = frappe.db.get_value("File", {"file_url": file_url}, "file_name")
	if file_doc:
		return os.path.join(site_path, "public", "files", file_doc)

	return None


def _build_filters(
	doc_type: str,
	from_date: str | None,
	to_date: str | None,
	category: str | None,
	only_unexported: int,
) -> dict:
	"""Build filter dict from export parameters."""
	filters = {}

	if doc_type == "Micro Receipt":
		date_field = "receipt_date"
		if category:
			filters["category"] = category
		if int(only_unexported):
			filters["exported"] = 0
	else:
		date_field = "date"

	if from_date:
		filters[date_field] = [">=", getdate(from_date)]
	if to_date:
		if date_field in filters:
			filters[date_field] = ["between", [getdate(from_date), getdate(to_date)]]
		else:
			filters[date_field] = ["<=", getdate(to_date)]

	return filters


def _export_receipts(
	from_date: str | None,
	to_date: str | None,
	category: str | None,
	only_unexported: int,
	mark_exported: int,
) -> dict:
	"""Export receipts as CSV for tax advisor."""
	filters = _build_filters("Micro Receipt", from_date, to_date, category, only_unexported)

	receipts = frappe.get_all(
		"Micro Receipt",
		filters=filters,
		fields=[
			"name", "receipt_date", "vendor", "description",
			"category", "amount",
		],
		order_by="receipt_date asc",
	)

	output = io.StringIO()
	writer = csv.writer(output, delimiter=";")
	writer.writerow([
		_("Date"), _("Vendor"), _("Description"),
		_("Category"), _("Amount"), _("Receipt ID"),
	])

	names = []
	for r in receipts:
		writer.writerow([
			str(r.receipt_date) if r.receipt_date else "",
			r.vendor or "",
			r.description or "",
			r.category or "",
			f"{float(r.amount or 0):.2f}",
			r.name,
		])
		names.append(r.name)

	if int(mark_exported) and names:
		today = nowdate()
		for name in names:
			frappe.db.set_value("Micro Receipt", name, {
				"exported": 1,
				"export_date": today,
			})
		frappe.db.commit()

	csv_content = output.getvalue()
	return {
		"csv": csv_content,
		"count": len(receipts),
		"marked_exported": int(mark_exported) and len(names) or 0,
		"filename": f"receipts_export_{nowdate()}.csv",
	}


def _export_invoice_drafts(
	from_date: str | None,
	to_date: str | None,
	mark_exported: int,
) -> dict:
	"""Export invoice drafts as CSV for tax advisor."""
	filters = _build_filters("Micro Invoice Draft", from_date, to_date, None, 0)

	invoices = frappe.get_all(
		"Micro Invoice Draft",
		filters=filters,
		fields=[
			"name", "reference", "date", "contact",
			"title", "total", "status",
		],
		order_by="date asc",
	)

	output = io.StringIO()
	writer = csv.writer(output, delimiter=";")
	writer.writerow([
		_("Date"), _("Reference"), _("Contact"),
		_("Title"), _("Total"), _("Status"),
	])

	for inv in invoices:
		writer.writerow([
			str(inv.date) if inv.date else "",
			inv.reference or "",
			inv.contact or "",
			inv.title or "",
			f"{float(inv.total or 0):.2f}",
			inv.status or "",
		])

	csv_content = output.getvalue()
	return {
		"csv": csv_content,
		"count": len(invoices),
		"filename": f"invoice_drafts_export_{nowdate()}.csv",
	}
