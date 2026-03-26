# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

"""Migrate Micro Customer records to Frappe Contact with micro_* custom fields.

This patch:
1. Creates custom fields on Contact if they don't exist yet
2. For each Micro Customer, finds or creates a matching Frappe Contact
3. Updates all Link fields in Micro Note, Offer Draft, Invoice Draft, and Receipt
4. Drops the Micro Customer DocType after migration

References: OWNERSHIP.md M1, Architecture Decision D1
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


MICRO_CUSTOM_FIELDS = {
	"Contact": [
		{
			"fieldname": "micro_crm_section",
			"fieldtype": "Section Break",
			"label": "CRM (Micro)",
			"insert_after": "image",
			"collapsible": 1,
		},
		{
			"fieldname": "micro_status",
			"fieldtype": "Select",
			"label": "CRM Status",
			"options": "\nPotential\nActive\nInactive",
			"insert_after": "micro_crm_section",
			"in_standard_filter": 1,
		},
		{
			"fieldname": "micro_pipeline_stage",
			"fieldtype": "Link",
			"label": "Pipeline Stage",
			"options": "Micro Pipeline Stage",
			"insert_after": "micro_status",
		},
		{
			"fieldname": "micro_source",
			"fieldtype": "Select",
			"label": "Acquisition Source",
			"options": "\nManual\nGoogle Ads\nFacebook\nInstagram\nLinkedIn\nEmail Campaign\nCold Call\nWeb Form\nOrganic Search\nReferral\nPartner\nEvent\nImport\nOther",
			"insert_after": "micro_pipeline_stage",
		},
		{
			"fieldname": "micro_crm_column",
			"fieldtype": "Column Break",
			"insert_after": "micro_source",
		},
		{
			"fieldname": "micro_contact_type",
			"fieldtype": "Select",
			"label": "Contact Type",
			"options": "\nPerson\nOrganization",
			"insert_after": "micro_crm_column",
		},
		{
			"fieldname": "micro_website",
			"fieldtype": "Data",
			"label": "Website",
			"insert_after": "micro_contact_type",
		},
		{
			"fieldname": "micro_notes",
			"fieldtype": "Text",
			"label": "Notes",
			"insert_after": "micro_website",
		},
		{
			"fieldname": "micro_address_section",
			"fieldtype": "Section Break",
			"label": "Address (Micro)",
			"insert_after": "micro_notes",
			"collapsible": 1,
		},
		{
			"fieldname": "micro_address",
			"fieldtype": "Small Text",
			"label": "Street Address",
			"insert_after": "micro_address_section",
		},
		{
			"fieldname": "micro_city",
			"fieldtype": "Data",
			"label": "City",
			"insert_after": "micro_address",
		},
		{
			"fieldname": "micro_address_column",
			"fieldtype": "Column Break",
			"insert_after": "micro_city",
		},
		{
			"fieldname": "micro_postal_code",
			"fieldtype": "Data",
			"label": "Postal Code",
			"insert_after": "micro_address_column",
		},
		{
			"fieldname": "micro_country",
			"fieldtype": "Link",
			"label": "Country",
			"options": "Country",
			"insert_after": "micro_postal_code",
		},
	],
}


def execute():
	"""Run the Micro Customer → Contact migration."""
	if not frappe.db.table_exists("tabMicro Customer"):
		return

	# Step 1: Ensure custom fields exist on Contact
	create_custom_fields(MICRO_CUSTOM_FIELDS, update=True)

	# Step 2: Migrate each Micro Customer to a Contact
	customers = frappe.db.sql(
		"SELECT * FROM `tabMicro Customer`",
		as_dict=True,
	)

	if not customers:
		_cleanup()
		return

	# Build mapping: old Micro Customer name → new Contact name
	name_map = {}

	for cust in customers:
		contact_name = _find_or_create_contact(cust)
		if contact_name:
			name_map[cust.name] = contact_name

	# Step 3: Update all Link fields in child DocTypes
	_update_links(name_map)

	# Step 4: Clean up
	_cleanup()

	frappe.db.commit()


def _find_or_create_contact(cust: dict) -> str | None:
	"""Find an existing Contact by email match or create a new one."""
	contact_name = None

	# Try to find by email match
	if cust.get("email"):
		contact_name = frappe.db.get_value(
			"Contact",
			{"email_id": cust.email},
			"name",
		)

	if contact_name:
		# Update existing contact with CRM fields
		frappe.db.set_value(
			"Contact",
			contact_name,
			{
				"micro_status": cust.get("status") or "Active",
				"micro_pipeline_stage": cust.get("pipeline_stage") or "",
				"micro_source": cust.get("source") or "",
				"micro_contact_type": cust.get("contact_type") or "Person",
				"micro_website": cust.get("website") or "",
				"micro_notes": cust.get("notes") or "",
				"micro_address": cust.get("address") or "",
				"micro_city": cust.get("city") or "",
				"micro_postal_code": cust.get("postal_code") or "",
				"micro_country": cust.get("country") or "",
			},
			update_modified=False,
		)
		return contact_name

	# Create new Contact
	try:
		contact = frappe.new_doc("Contact")
		contact.first_name = cust.get("name1") or "Unknown"
		contact.last_name = cust.get("last_name") or ""
		contact.email_id = cust.get("email") or ""
		contact.phone = cust.get("phone") or ""
		contact.mobile_no = cust.get("mobile") or ""
		contact.company_name = cust.get("organization") or ""
		contact.image = cust.get("image") or ""

		# Add email to child table if present
		if cust.get("email"):
			contact.append("email_ids", {
				"email_id": cust.email,
				"is_primary": 1,
			})

		# Add phone to child table if present
		if cust.get("phone"):
			contact.append("phone_nos", {
				"phone": cust.phone,
				"is_primary_phone": 1,
			})

		if cust.get("mobile"):
			contact.append("phone_nos", {
				"phone": cust.mobile,
				"is_primary_mobile_no": 1,
			})

		# CRM custom fields
		contact.micro_status = cust.get("status") or "Active"
		contact.micro_pipeline_stage = cust.get("pipeline_stage") or ""
		contact.micro_source = cust.get("source") or ""
		contact.micro_contact_type = cust.get("contact_type") or "Person"
		contact.micro_website = cust.get("website") or ""
		contact.micro_notes = cust.get("notes") or ""
		contact.micro_address = cust.get("address") or ""
		contact.micro_city = cust.get("city") or ""
		contact.micro_postal_code = cust.get("postal_code") or ""
		contact.micro_country = cust.get("country") or ""

		contact.flags.ignore_permissions = True
		contact.flags.ignore_mandatory = True
		contact.insert()

		return contact.name
	except Exception:
		frappe.log_error(
			f"Failed to migrate Micro Customer {cust.get('name')} to Contact"
		)
		return None


def _update_links(name_map: dict):
	"""Update contact Link fields in all Micro DocTypes."""
	doctypes_with_contact = [
		"Micro Note",
		"Micro Offer Draft",
		"Micro Invoice Draft",
		"Micro Receipt",
	]

	for doctype in doctypes_with_contact:
		table = f"tab{doctype}"
		if not frappe.db.table_exists(table):
			continue

		for old_name, new_name in name_map.items():
			frappe.db.sql(
				f"UPDATE `{table}` SET `contact` = %s WHERE `contact` = %s",
				(new_name, old_name),
			)


def _cleanup():
	"""Remove the Micro Customer DocType after migration."""
	try:
		# Drop the table
		if frappe.db.table_exists("tabMicro Customer"):
			frappe.db.sql("DROP TABLE IF EXISTS `tabMicro Customer`")

		# Remove DocType record
		if frappe.db.exists("DocType", "Micro Customer"):
			frappe.delete_doc("DocType", "Micro Customer", force=True, ignore_permissions=True)
	except Exception:
		frappe.log_error("Failed to clean up Micro Customer DocType")
