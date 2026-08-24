# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

import frappe
from frappe import _

from micro.api.leads import attach_stage_names

# What the detail page may write straight onto the contact.
# `email_id`, `phone` and `mobile_no` are deliberately absent: Frappe recomputes
# them from `email_ids` / `phone_nos` on every save, so a direct write is undone
# on the way to the database. They go through the helpers below instead.
EDITABLE_CUSTOMER_FIELDS = {
	"first_name",
	"last_name",
	"company_name",
	"micro_status",
	"micro_contact_type",
	"micro_organization",
	"micro_source",
	"micro_segment",
	"micro_website",
	"micro_address",
	"micro_city",
	"micro_postal_code",
	"micro_country",
	"micro_notes",
}


@frappe.whitelist()
def get_customers(
	filters: dict | None = None,
	fields: list | None = None,
	order_by: str = "modified desc",
	limit_start: int = 0,
	limit_page_length: int = 20,
	search: str | None = None,
	pipeline: str | None = None,
	pipeline_state: str = "",
	segment: str | None = None,
	tag: str | None = None,
	source: str | None = None,
	status: str | None = None,
	contact_type: str | None = None,
) -> dict:
	"""Get contacts that are Micro customers (have micro_status set).

	Every narrowing happens here rather than in the page, so a filter always
	means the whole customer base and not just the rows already fetched.

	`segment` is the one durable category a contact has; `tag` is any of the
	several labels it may carry. `pipeline` + `pipeline_state` pick the audience
	for a campaign: who is already being worked in that pipeline, who has been
	through it before, and who has never been in it at all.
	"""
	frappe.has_permission("Contact", throw=True)

	base_filters = filters or {}
	base_filters["micro_status"] = ["is", "set"]

	if search:
		base_filters["full_name"] = ["like", f"%{search}%"]
	if source:
		base_filters["micro_source"] = source
	if contact_type:
		base_filters["micro_contact_type"] = contact_type
	if status:
		base_filters["micro_status"] = status
	if segment:
		# The chip for contacts nobody has filed yet.
		base_filters["micro_segment"] = ["is", "not set"] if segment == NO_SEGMENT else segment

	if pipeline and pipeline_state:
		_apply_pipeline_filter(base_filters, pipeline, pipeline_state)
	if tag:
		_apply_tag_filter(base_filters, tag)

	default_fields = [
		"name",
		"first_name",
		"last_name",
		"full_name",
		"email_id",
		"phone",
		"micro_contact_type",
		"micro_organization",
		"micro_status",
		"company_name",
		"micro_city",
		"image",
		"micro_pipeline_stage",
		"micro_source",
		"micro_health_score",
		"micro_segment",
		"_user_tags",
	]

	customers = frappe.get_list(
		"Contact",
		filters=base_filters,
		fields=fields or default_fields,
		order_by=order_by,
		start=limit_start,
		page_length=limit_page_length,
	)

	total = frappe.db.count("Contact", filters=base_filters)

	return {"customers": customers, "total": total}


PIPELINE_STATES = ("open", "ever", "never")

# The chip for "filed under nothing yet" — a real audience, not an empty state.
NO_SEGMENT = "__none__"

# Enough for a filter dropdown; a micro business that passes this has a
# labelling problem no list can fix.
TAG_FACET_LIMIT = 50


@frappe.whitelist()
def get_customer_facets() -> dict:
	"""The categories in use and how many contacts each holds.

	Counts are the point: they turn the filter row into an answer to "how big is
	this audience" before a campaign is built on it.
	"""
	frappe.has_permission("Contact", throw=True)

	by_segment = {
		row["segment"]: row["count"]
		for row in frappe.db.sql(
			"""
			SELECT COALESCE(micro_segment, '') AS segment, COUNT(*) AS count
			FROM `tabContact`
			WHERE COALESCE(micro_status, '') != ''
			GROUP BY COALESCE(micro_segment, '')
			""",
			as_dict=True,
		)
	}

	segments = frappe.get_all(
		"Micro Segment",
		filters={"is_active": 1},
		fields=["name", "segment_name", "color", "sort_order"],
		order_by="sort_order asc, segment_name asc",
	)
	for segment in segments:
		segment["count"] = by_segment.get(segment["name"], 0)

	tags = frappe.db.sql(
		"""
		SELECT tl.tag AS tag, COUNT(*) AS count
		FROM `tabTag Link` tl
		INNER JOIN `tabContact` c ON c.name = tl.document_name
		WHERE tl.document_type = 'Contact' AND COALESCE(c.micro_status, '') != ''
		GROUP BY tl.tag
		ORDER BY count DESC, tag ASC
		LIMIT %(limit)s
		""",
		{"limit": TAG_FACET_LIMIT},
		as_dict=True,
	)

	return {
		"total": sum(by_segment.values()),
		"segments": segments,
		"unsegmented": by_segment.get("", 0),
		"tags": tags,
	}


def _apply_tag_filter(base_filters: dict, tag: str) -> None:
	"""Narrow to one tag via `Tag Link` — the indexed side of Frappe's tagging.

	`_user_tags` is the display copy: a comma-joined string that only matches
	with a LIKE, which would also match "Altbau" inside "Altbausanierung".
	"""
	tagged = frappe.get_all(
		"Tag Link",
		filters={"document_type": "Contact", "tag": tag},
		pluck="document_name",
	)
	_restrict_by_name(base_filters, allow=set(tagged))


def _restrict_by_name(
	base_filters: dict, allow: set[str] | None = None, deny: set[str] | None = None
) -> None:
	"""Add a contact-id restriction on top of any already in the filters.

	Two filters can both narrow by id — a tag and a pipeline state, say. Writing
	`name` twice would let the second quietly replace the first, so they are
	intersected here instead.
	"""
	current = base_filters.get("name")
	allowed = set(current[1]) if current and current[0] == "in" else None
	denied = set(current[1]) if current and current[0] == "not in" else set()

	if allow is not None:
		allowed = allow if allowed is None else allowed & allow
	if deny:
		denied |= deny

	if allowed is not None:
		# IN () is not valid SQL — a sentinel keeps "nobody" meaning nobody.
		base_filters["name"] = ["in", list(allowed - denied) or [""]]
	elif denied:
		base_filters["name"] = ["not in", list(denied)]


def _apply_pipeline_filter(base_filters: dict, pipeline: str, state: str) -> None:
	"""Narrow a customer list by what it has done in one pipeline.

	The contact ids are collected first rather than joined: a Micro site holds
	hundreds of contacts, not millions, and the readable filter is worth more
	here than a join would save.
	"""
	if state not in PIPELINE_STATES:
		frappe.throw(_("Unknown pipeline filter: {0}").format(state))

	lead_filters: dict = {"pipeline": pipeline}
	if state == "open":
		lead_filters["status"] = "Open"

	contacts = {
		name
		for name in frappe.get_all("Micro Lead", filters=lead_filters, pluck="contact")
		if name
	}

	if state == "never":
		_restrict_by_name(base_filters, deny=contacts)
	else:
		_restrict_by_name(base_filters, allow=contacts)


@frappe.whitelist()
def get_customer(customer_id: str) -> dict:
	"""Get a single contact (Micro customer) with unified notes timeline."""
	frappe.has_permission("Contact", throw=True)

	customer = frappe.get_doc("Contact", customer_id).as_dict()

	# CRM-structured notes (Call, Meeting, Email Summary, Note)
	micro_notes = frappe.get_list(
		"Micro Note",
		filters={"contact": customer_id},
		fields=["name", "subject", "note_type", "date", "content", "modified"],
		order_by="date desc",
		limit_page_length=50,
	)

	# Dock Notes linked to this contact (quick notes + any context-linked notes)
	dock_notes = []
	if frappe.db.exists("DocType", "Dock Note"):
		dock_notes = frappe.get_list(
			"Dock Note",
			filters={
				"reference_doctype": "Contact",
				"reference_name": customer_id,
				"deleted_at": ["is", "not set"],
			},
			fields=["name", "content", "pinned", "color", "owner", "creation", "modified"],
			order_by="creation desc",
			limit_page_length=50,
		)

	# Build unified timeline sorted by date descending
	timeline = []
	for n in micro_notes:
		timeline.append({
			"name": n.name,
			"source": "micro",
			"note_type": n.note_type,
			"subject": n.subject,
			"content": n.content,
			"date": str(n.date),
			"modified": str(n.modified),
		})
	for n in dock_notes:
		timeline.append({
			"name": n.name,
			"source": "dock",
			"note_type": "Quick Note",
			"subject": None,
			"content": n.content,
			"date": str(n.creation),
			"modified": str(n.modified),
			"pinned": n.pinned,
			"color": n.color,
		})

	timeline.sort(key=lambda x: x["date"], reverse=True)

	return {
		"customer": customer,
		"notes": timeline,
		"leads": get_customer_leads(customer_id),
		"tags": _customer_tags(customer_id),
		# Whichever side of the relation this contact sits on: a person carries
		# one organization, an organization carries the people who belong to it.
		"organization": _organization_card(customer.get("micro_organization")),
		"members": get_organization_members(customer_id)["members"]
		if customer.get("micro_contact_type") == "Organization"
		else [],
	}


def _organization_card(organization: str | None) -> dict | None:
	"""The linked organization, named rather than left as a bare docname."""
	if not organization:
		return None

	values = frappe.db.get_value(
		"Contact",
		organization,
		["name", "full_name", "company_name", "email_id", "phone", "micro_city"],
		as_dict=True,
	)

	return dict(values) if values else None


def get_customer_leads(customer_id: str) -> list[dict]:
	"""Every lead this contact has ever been in, open ones first.

	A contact can be open in several pipelines at once and can go through the
	same pipeline more than once over the years, so this is a history, not a
	single field. `Contact.micro_pipeline_stage` only mirrors the most recent
	open one — it cannot answer "what happened last time we called them".
	"""
	leads = frappe.get_list(
		"Micro Lead",
		filters={"contact": customer_id},
		fields=[
			"name",
			"lead_name",
			"status",
			"pipeline",
			"stage",
			"priority",
			"expected_value",
			"next_follow_up",
			"lost_reason",
			"creation",
			"modified",
		],
		order_by="modified desc",
		limit_page_length=50,
	)
	if not leads:
		return []

	attach_stage_names(leads)

	pipeline_names = {lead["pipeline"] for lead in leads if lead.get("pipeline")}
	pipelines = {}
	if pipeline_names:
		pipelines = {
			row["name"]: row["pipeline_name"]
			for row in frappe.get_all(
				"Micro Pipeline",
				filters={"name": ["in", list(pipeline_names)]},
				fields=["name", "pipeline_name"],
			)
		}

	for lead in leads:
		lead["pipeline_name"] = pipelines.get(lead.get("pipeline"))
		lead["is_open"] = lead["status"] == "Open"

	# Open first — that is what today's work is — then the closed ones as history.
	leads.sort(key=lambda lead: 0 if lead["is_open"] else 1)

	return leads


@frappe.whitelist()
def create_customer(
	first_name: str,
	contact_type: str = "Person",
	status: str = "Potential",
	last_name: str | None = None,
	email: str | None = None,
	phone: str | None = None,
	mobile: str | None = None,
	website: str | None = None,
	organization: str | None = None,
	organization_contact: str | None = None,
	source: str | None = None,
	pipeline_stage: str | None = None,
	address: str | None = None,
	city: str | None = None,
	postal_code: str | None = None,
	country: str | None = None,
	notes: str | None = None,
) -> dict:
	"""Create a new Contact with Micro CRM fields."""
	frappe.has_permission("Contact", "create", throw=True)

	if contact_type == "Person" and not last_name:
		frappe.throw(_("Last name is required for Person customers"))

	contact = frappe.new_doc("Contact")
	contact.first_name = first_name
	if last_name:
		contact.last_name = last_name
	if email:
		contact.email_id = email
		contact.append("email_ids", {"email_id": email, "is_primary": 1})
	if phone:
		contact.phone = phone
		contact.append("phone_nos", {"phone": phone, "is_primary_phone": 1})
	if mobile:
		contact.mobile_no = mobile
		contact.append("phone_nos", {"phone": mobile, "is_primary_mobile_no": 1})
	if organization:
		contact.company_name = organization
	if organization_contact:
		# Validation mirrors the organization's name into `company_name`, so the
		# free-text value above is only ever a fallback for contacts that have
		# no organization record of their own.
		contact.micro_organization = organization_contact

	# Micro CRM custom fields
	contact.micro_status = status
	contact.micro_contact_type = contact_type
	if source:
		contact.micro_source = source
	if pipeline_stage:
		contact.micro_pipeline_stage = pipeline_stage
	if website:
		contact.micro_website = website
	if notes:
		contact.micro_notes = notes
	if address:
		contact.micro_address = address
	if city:
		contact.micro_city = city
	if postal_code:
		contact.micro_postal_code = postal_code
	if country:
		contact.micro_country = country

	contact.insert()

	return {"customer": contact.as_dict()}


@frappe.whitelist()
def update_customer(customer_id: str, **values) -> dict:
	"""Update a customer's own fields from the detail page.

	Everything the detail page shows can be changed here. Anything not listed
	stays with Desk — the health score and the pipeline stage mirror are
	derived, not typed.
	"""
	frappe.has_permission("Contact", "write", throw=True)

	contact = frappe.get_doc("Contact", customer_id)

	for fieldname, value in values.items():
		if fieldname in EDITABLE_CUSTOMER_FIELDS:
			contact.set(fieldname, value)
		elif fieldname == "email_id":
			_set_primary_email(contact, value)
		elif fieldname in ("phone", "mobile_no"):
			_set_primary_phone(contact, fieldname, value)

	contact.save()

	return {"customer": contact.as_dict()}


def _set_primary_email(contact, email: str | None) -> None:
	"""Write the email through the row that carries it."""
	email = (email or "").strip()
	primary = next((row for row in contact.email_ids if row.is_primary), None)

	if not email:
		if primary:
			contact.remove(primary)
		return

	if primary:
		primary.email_id = email
	else:
		contact.append("email_ids", {"email_id": email, "is_primary": 1})


def _set_primary_phone(contact, fieldname: str, number: str | None) -> None:
	"""Same for the phone numbers — two flags over one child table."""
	flag = "is_primary_phone" if fieldname == "phone" else "is_primary_mobile_no"
	other = "is_primary_mobile_no" if fieldname == "phone" else "is_primary_phone"
	number = (number or "").strip()
	primary = next((row for row in contact.phone_nos if row.get(flag)), None)

	if not number:
		if primary:
			# One row can hold both numbers — then only drop our claim on it.
			if primary.get(other):
				primary.set(flag, 0)
			else:
				contact.remove(primary)
		return

	if primary and primary.get(other):
		# The two numbers part ways: this one moves to a row of its own.
		primary.set(flag, 0)
		primary = None

	if primary:
		primary.phone = number
	else:
		contact.append("phone_nos", {"phone": number, flag: 1})


@frappe.whitelist()
def add_customer_tag(customer_id: str, tag: str) -> dict:
	"""Put one more label on a contact.

	Tagging is Frappe's, not Micro's — `Tag`, `Tag Link` and `_user_tags` are
	core tables that every app can read. Micro only owns the permission check
	and the one durable category (`micro_segment`).
	"""
	from frappe.desk.doctype.tag.tag import DocTags

	frappe.has_permission("Contact", "write", throw=True)

	tag = (tag or "").strip()
	if not tag:
		frappe.throw(_("Enter a tag."))

	DocTags("Contact").add(customer_id, tag)

	return {"tags": _customer_tags(customer_id)}


@frappe.whitelist()
def remove_customer_tag(customer_id: str, tag: str) -> dict:
	"""Take one label off a contact. The tag itself survives for other records."""
	from frappe.desk.doctype.tag.tag import DocTags

	frappe.has_permission("Contact", "write", throw=True)

	DocTags("Contact").remove(customer_id, tag)

	return {"tags": _customer_tags(customer_id)}


def _customer_tags(customer_id: str) -> list[str]:
	raw = frappe.db.get_value("Contact", customer_id, "_user_tags") or ""
	return [tag for tag in raw.split(",") if tag]


@frappe.whitelist()
def update_intelligence(customer_id: str, **kwargs) -> dict:
	"""Update intelligence card fields on a customer contact."""
	frappe.has_permission("Contact", "write", throw=True)

	allowed_fields = {
		"micro_client_loves",
		"micro_client_avoid",
		"micro_communication_style",
		"micro_personal_notes",
		"micro_opportunities",
		"micro_last_contact_date",
		"micro_last_contact_topic",
	}

	contact = frappe.get_doc("Contact", customer_id)
	updated = False
	for field in allowed_fields:
		if field in kwargs:
			contact.set(field, kwargs[field])
			updated = True

	if updated:
		contact.save()

	return {"customer": contact.as_dict()}


# --- organizations ------------------------------------------------------------

# What a member row shows. Enough to call the person without opening their page.
MEMBER_FIELDS = (
	"name",
	"first_name",
	"last_name",
	"full_name",
	"designation",
	"email_id",
	"phone",
	"mobile_no",
	"micro_status",
	"image",
)


@frappe.whitelist()
def get_organization_members(customer_id: str) -> dict:
	"""The people who belong to this organization.

	The question free text could never answer: "who do I know at Müller Bau?"
	"""
	frappe.has_permission("Contact", throw=True)

	members = frappe.get_all(
		"Contact",
		filters={"micro_organization": customer_id},
		fields=list(MEMBER_FIELDS),
		order_by="full_name asc",
	)

	return {"members": members, "total": len(members)}


@frappe.whitelist()
def set_customer_organization(customer_id: str, organization: str | None = None) -> dict:
	"""Attach a person to an organization, or detach them from one.

	Detaching leaves `company_name` alone: the employer was true when it was
	written, and dropping a relation is not a claim that the person never worked
	there.
	"""
	frappe.has_permission("Contact", "write", throw=True)

	contact = frappe.get_doc("Contact", customer_id)
	contact.micro_organization = organization or None
	contact.save()

	return {"customer": contact.as_dict()}


# --- removal -----------------------------------------------------------------

# Documents carrying a retention obligation. A receipt is a Beleg from the moment
# it exists; a draft becomes one once it has left the house. While any of these
# refer to a contact it cannot be erased — an orphaned financial record is a
# worse outcome than a refused delete.
RETENTION_DOCUMENTS = {
	"Micro Receipt": None,
	"Micro Offer Draft": ("Sent", "Accepted", "Declined", "Expired"),
	"Micro Invoice Draft": ("Sent to Tax Advisor", "Archived"),
}

# Micro's own working records: they belong to the CRM and go when it goes.
MICRO_OWNED_DOCUMENTS = ("Micro Lead", "Micro Note", "Micro Task", "Micro Call Attempt")

# Drafts that never went anywhere. They hold a link to the contact, so erasing
# without removing them first fails on that link — and a draft addressed to
# somebody being erased has nobody left to send it to.
UNSENT_DRAFTS = {"Micro Offer Draft": "Draft", "Micro Invoice Draft": "Draft"}

# Micro's own doctypes, so that the search for *other* apps' links skips them.
MICRO_DOCTYPES = (
	set(MICRO_OWNED_DOCUMENTS)
	| set(RETENTION_DOCUMENTS)
	| {"Micro Duplicate Pair", "Micro Customer"}
)

# What makes a Contact a Micro customer. Clearing `micro_status` is what removal
# means; the CRM detail is left in place, so re-adopting the contact later brings
# its history back instead of starting from nothing.
MICRO_MEMBERSHIP_FIELDS = ("micro_status", "micro_pipeline_stage")


def _retention_blockers(customer_id: str) -> list[dict]:
	"""Documents whose retention obligation outranks a delete request."""
	blockers = []

	for doctype, states in RETENTION_DOCUMENTS.items():
		filters = {"contact": customer_id}
		if states:
			filters["status"] = ["in", states]

		count = frappe.db.count(doctype, filters=filters)
		if count:
			blockers.append({"doctype": doctype, "count": count})

	return blockers


def _removable_documents(customer_id: str) -> dict:
	"""Micro records that an erase would take with it."""
	counts = {}

	for doctype in MICRO_OWNED_DOCUMENTS:
		count = frappe.db.count(doctype, filters={"contact": customer_id})
		if count:
			counts[doctype] = count

	for doctype, state in UNSENT_DRAFTS.items():
		count = frappe.db.count(doctype, filters={"contact": customer_id, "status": state})
		if count:
			counts[doctype] = counts.get(doctype, 0) + count

	return counts


def _foreign_links(customer_id: str) -> list[dict]:
	"""Other apps still pointing at this contact.

	`Contact` is Frappe core, shared with Helo, Orga and the rest. Erasing one
	from Micro reaches into their data, so what they hold is reported up front
	rather than discovered as a link error halfway through the delete.
	"""
	from frappe.model.rename_doc import get_link_fields

	found: dict[str, int] = {}

	for field in get_link_fields("Contact"):
		doctype = field["parent"]
		if field.get("issingle") or doctype in MICRO_DOCTYPES or doctype == "Contact":
			continue

		try:
			count = frappe.db.count(doctype, filters={field["fieldname"]: customer_id})
		except Exception:
			# A doctype whose table is missing must not sink the preview.
			continue

		if count:
			found[doctype] = found.get(doctype, 0) + count

	return [{"doctype": doctype, "count": count} for doctype, count in sorted(found.items())]


@frappe.whitelist()
def get_delete_preview(customer_id: str) -> dict:
	"""What removing this customer would cost, before anything is removed."""
	frappe.has_permission("Contact", "delete", throw=True)

	if not frappe.db.exists("Contact", customer_id):
		frappe.throw(_("Customer not found"))

	blockers = _retention_blockers(customer_id)
	foreign = _foreign_links(customer_id)

	return {
		"customer": customer_id,
		"deletes": _removable_documents(customer_id),
		"retention_blockers": blockers,
		"foreign_links": foreign,
		"can_erase": not blockers and not foreign,
	}


@frappe.whitelist()
def delete_customer(customer_id: str, mode: str = "remove") -> dict:
	"""Take a customer out of Micro, or erase the contact entirely.

	Two different requests wear the same word. "I no longer work with them" is
	`remove`: the contact stops being a Micro customer and frees a slot under the
	Community limit, while every document that refers to it stays exactly where
	it is — including documents belonging to the other apps that share this
	Contact. "Erase every trace of this person" is `erase`, and that is only
	available while nothing holds a retention obligation over the record.
	"""
	frappe.has_permission("Contact", "delete", throw=True)

	if mode not in ("remove", "erase"):
		frappe.throw(_("Unknown delete mode: {0}").format(mode))

	if not frappe.db.exists("Contact", customer_id):
		frappe.throw(_("Customer not found"))

	if mode == "remove":
		contact = frappe.get_doc("Contact", customer_id)
		for field in MICRO_MEMBERSHIP_FIELDS:
			if contact.meta.has_field(field):
				contact.set(field, None)
		contact.save(ignore_permissions=True)

		_close_duplicate_pairs(customer_id)

		return {"customer": customer_id, "mode": mode, "erased": False}

	blockers = _retention_blockers(customer_id)
	if blockers:
		frappe.throw(
			_(
				"{0} cannot be erased: {1} refer to it and have to be kept. "
				"Remove the customer from Micro instead."
			).format(
				frappe.bold(customer_id),
				", ".join(f"{item['count']} × {_(item['doctype'])}" for item in blockers),
			)
		)

	foreign = _foreign_links(customer_id)
	if foreign:
		frappe.throw(
			_("{0} is still in use by {1}. This contact is shared between apps.").format(
				frappe.bold(customer_id),
				", ".join(f"{item['count']} × {_(item['doctype'])}" for item in foreign),
			)
		)

	# Micro's own records go first: Frappe refuses to delete a contact anything
	# still links to, and these are the links.
	for doctype in MICRO_OWNED_DOCUMENTS:
		for name in frappe.get_all(doctype, filters={"contact": customer_id}, pluck="name"):
			frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)

	for doctype, state in UNSENT_DRAFTS.items():
		for name in frappe.get_all(doctype, filters={"contact": customer_id, "status": state}, pluck="name"):
			frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)

	_close_duplicate_pairs(customer_id, delete=True)

	# People do not disappear with their employer. The relation is dropped so the
	# organization can go, and `company_name` is left standing — it was true when
	# it was written.
	for member in frappe.get_all("Contact", filters={"micro_organization": customer_id}, pluck="name"):
		frappe.db.set_value("Contact", member, "micro_organization", None, update_modified=False)

	frappe.delete_doc("Contact", customer_id, ignore_permissions=True)

	return {"customer": customer_id, "mode": mode, "erased": True}


@frappe.whitelist()
def bulk_delete_customers(customer_ids: list | str, mode: str = "remove") -> dict:
	"""Remove or erase several customers in one request.

	Each customer goes through the same rules as a single delete. A retention
	blocker on one erase does not stop the rest of the batch — it is reported
	back instead, next to whichever customers went through.
	"""
	if isinstance(customer_ids, str):
		customer_ids = frappe.parse_json(customer_ids)

	if not customer_ids:
		frappe.throw(_("No customers specified"))

	if mode not in ("remove", "erase"):
		frappe.throw(_("Unknown delete mode: {0}").format(mode))

	succeeded = []
	failed = []

	for customer_id in customer_ids:
		try:
			delete_customer(customer_id, mode=mode)
			succeeded.append(customer_id)
		except frappe.ValidationError as e:
			failed.append({"customer": customer_id, "error": str(e)})

	return {"mode": mode, "succeeded": succeeded, "failed": failed}


def _close_duplicate_pairs(customer_id: str, delete: bool = False) -> None:
	"""Suggestions about a contact that is leaving are not worth keeping open.

	On an erase they are deleted rather than closed, whatever their status: a
	resolved pair still holds a Link to the contact, and one forgotten row is
	enough to make the delete fail.
	"""
	if not frappe.db.exists("DocType", "Micro Duplicate Pair"):
		return

	names = frappe.get_all(
		"Micro Duplicate Pair",
		filters={} if delete else {"status": "Open"},
		or_filters={"contact_a": customer_id, "contact_b": customer_id},
		pluck="name",
	)

	for name in names:
		if delete:
			frappe.delete_doc("Micro Duplicate Pair", name, ignore_permissions=True, force=True)
		else:
			frappe.db.set_value("Micro Duplicate Pair", name, "status", "Dismissed")
