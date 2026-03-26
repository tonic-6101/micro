# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

"""Create 10 example Micro customers for demo/development.

Usage:
    bench --site dock16.localhost execute micro.demo.create_demo_customers.execute
"""

import frappe


DEMO_CUSTOMERS = [
	{
		"first_name": "Anna",
		"last_name": "Bergmann",
		"contact_type": "Person",
		"status": "Active",
		"email": "anna.bergmann@designstudio.de",
		"phone": "+49 30 1234567",
		"source": "Referral",
		"website": "https://designstudio-bergmann.de",
		"city": "Berlin",
		"postal_code": "10115",
		"country": "Germany",
		"address": "Kastanienallee 12",
	},
	{
		"first_name": "Thomas",
		"last_name": "Müller",
		"contact_type": "Person",
		"status": "Potential",
		"email": "t.mueller@architektur-mueller.de",
		"phone": "+49 89 9876543",
		"source": "Google Ads",
		"city": "München",
		"postal_code": "80331",
		"country": "Germany",
		"address": "Marienplatz 8",
	},
	{
		"first_name": "Kreativwerk",
		"last_name": "",
		"contact_type": "Organization",
		"status": "Active",
		"email": "info@kreativwerk.de",
		"phone": "+49 40 5551234",
		"source": "Cold Call",
		"website": "https://kreativwerk.de",
		"city": "Hamburg",
		"postal_code": "20095",
		"country": "Germany",
		"address": "Jungfernstieg 44",
	},
	{
		"first_name": "Sarah",
		"last_name": "Chen",
		"contact_type": "Person",
		"status": "Active",
		"email": "sarah@chendigital.com",
		"phone": "+49 69 4445566",
		"mobile": "+49 170 9998877",
		"source": "LinkedIn",
		"website": "https://chendigital.com",
		"city": "Frankfurt",
		"postal_code": "60311",
		"country": "Germany",
	},
	{
		"first_name": "Marco",
		"last_name": "Rossi",
		"contact_type": "Person",
		"status": "Potential",
		"email": "marco.rossi@tradeworks.it",
		"phone": "+39 02 3344556",
		"source": "Partner",
		"city": "Milano",
		"postal_code": "20121",
		"country": "Italy",
	},
	{
		"first_name": "Stadtwerke Freiburg",
		"last_name": "",
		"contact_type": "Organization",
		"status": "Active",
		"email": "auftrag@stadtwerke-freiburg.de",
		"phone": "+49 761 2082000",
		"source": "Web Form",
		"city": "Freiburg",
		"postal_code": "79098",
		"country": "Germany",
		"address": "Habsburgerstr. 9",
	},
	{
		"first_name": "Lena",
		"last_name": "Winkler",
		"contact_type": "Person",
		"status": "Inactive",
		"email": "lena@winkler-beratung.de",
		"phone": "+49 711 8899001",
		"source": "Referral",
		"city": "Stuttgart",
		"postal_code": "70173",
		"country": "Germany",
	},
	{
		"first_name": "Pixel & Code",
		"last_name": "",
		"contact_type": "Organization",
		"status": "Potential",
		"email": "hello@pixelundcode.de",
		"phone": "+49 221 3344556",
		"source": "Organic Search",
		"website": "https://pixelundcode.de",
		"city": "Köln",
		"postal_code": "50667",
		"country": "Germany",
		"address": "Ehrenstr. 71",
	},
	{
		"first_name": "Jonas",
		"last_name": "Fischer",
		"contact_type": "Person",
		"status": "Active",
		"email": "jonas@fischer-consulting.ch",
		"phone": "+41 44 5556677",
		"source": "Event",
		"website": "https://fischer-consulting.ch",
		"city": "Zürich",
		"postal_code": "8001",
		"country": "Switzerland",
	},
	{
		"first_name": "Marie",
		"last_name": "Dupont",
		"contact_type": "Person",
		"status": "Potential",
		"email": "marie.dupont@agence-lumiere.fr",
		"phone": "+33 1 42568899",
		"source": "Instagram",
		"city": "Paris",
		"postal_code": "75001",
		"country": "France",
		"address": "14 Rue de Rivoli",
	},
]


def execute():
	"""Create demo customers — works with both old and new schema."""
	# Raise limit for demo
	try:
		settings = frappe.get_single("Micro Settings")
		if settings.customer_limit and settings.customer_limit < 200:
			settings.customer_limit = 200
			settings.save(ignore_permissions=True)
	except Exception:
		pass

	use_contact = _has_micro_fields_on_contact()
	created = 0

	for data in DEMO_CUSTOMERS:
		if use_contact:
			name = _create_as_contact(data)
		else:
			name = _create_as_micro_customer(data)

		if name:
			created += 1
			print(f"  Created: {data['first_name']} {data.get('last_name', '')} → {name}")

	frappe.db.commit()
	print(f"\nDone — {created} demo customers created.")


def _has_micro_fields_on_contact() -> bool:
	"""Check if micro_status custom field exists on Contact (post-migration)."""
	try:
		result = frappe.db.sql(
			"SHOW COLUMNS FROM `tabContact` LIKE 'micro_status'"
		)
		return bool(result)
	except Exception:
		return False


def _create_as_contact(data: dict) -> str | None:
	"""Create a Frappe Contact with micro_* CRM fields (post-migration)."""
	email = data.get("email", "")
	if email and frappe.db.exists("Contact", {"email_id": email}):
		print(f"  Skipped (exists): {email}")
		return None

	try:
		doc = frappe.new_doc("Contact")
		doc.first_name = data["first_name"]
		doc.last_name = data.get("last_name") or ""
		doc.email_id = email
		doc.phone = data.get("phone", "")
		doc.mobile_no = data.get("mobile", "")
		doc.company_name = data["first_name"] if data["contact_type"] == "Organization" else ""
		doc.micro_status = data.get("status", "Potential")
		doc.micro_contact_type = data.get("contact_type", "Person")
		doc.micro_source = data.get("source", "")
		doc.micro_website = data.get("website", "")
		doc.micro_address = data.get("address", "")
		doc.micro_city = data.get("city", "")
		doc.micro_postal_code = data.get("postal_code", "")
		doc.micro_country = data.get("country", "")

		if email:
			doc.append("email_ids", {"email_id": email, "is_primary": 1})
		if data.get("phone"):
			doc.append("phone_nos", {"phone": data["phone"], "is_primary_phone": 1})
		if data.get("mobile"):
			doc.append("phone_nos", {"phone": data["mobile"], "is_primary_mobile_no": 1})

		doc.flags.ignore_permissions = True
		doc.insert()
		return doc.name
	except Exception as e:
		print(f"  Error: {e}")
		return None


def _create_as_micro_customer(data: dict) -> str | None:
	"""Create a Micro Customer record (pre-migration)."""
	email = data.get("email", "")
	if email and frappe.db.exists("Micro Customer", {"email": email}):
		print(f"  Skipped (exists): {email}")
		return None

	try:
		doc = frappe.new_doc("Micro Customer")
		doc.name1 = data["first_name"]
		doc.last_name = data.get("last_name") or ""
		doc.contact_type = data.get("contact_type", "Person")
		doc.status = data.get("status", "Potential")
		doc.email = email
		doc.phone = data.get("phone", "")
		doc.mobile = data.get("mobile", "")
		doc.source = data.get("source", "")
		doc.website = data.get("website", "")
		doc.address = data.get("address", "")
		doc.city = data.get("city", "")
		doc.postal_code = data.get("postal_code", "")
		doc.country = data.get("country", "")

		doc.flags.ignore_permissions = True
		doc.insert()
		return doc.name
	except Exception as e:
		print(f"  Error: {e}")
		return None
