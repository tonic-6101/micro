# API Reference

All Micro API endpoints are Frappe whitelisted methods, accessible via `/api/method/micro.api.<module>.<function>`.

Authentication is handled by Frappe's session system. All endpoints require the user to have the appropriate Micro permissions.

## Customers — `micro.api.customers`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `get_customers` | List customers with filters, search, pagination |
| GET | `get_customer` | Get single customer with related notes |
| POST | `create_customer` | Create a new customer |
| GET | `get_delete_preview` | What deleting this customer would cost |
| POST | `delete_customer` | Remove from Micro, or erase the contact |

### `get_customers`

```
GET /api/method/micro.api.customers.get_customers
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `filters` | dict | `None` | Frappe-style filters |
| `fields` | list | `None` | Fields to return (uses defaults if omitted) |
| `search` | string | `None` | Search by full name |
| `order_by` | string | `"modified desc"` | Sort order |
| `limit_start` | int | `0` | Pagination offset |
| `limit_page_length` | int | `20` | Page size |

**Default fields:** `name`, `name1`, `last_name`, `full_name`, `email`, `phone`, `contact_type`, `status`, `organization`, `city`, `image`, `pipeline_stage`

**Returns:** `{ customers: [...], total: int }`

### `get_customer`

```
GET /api/method/micro.api.customers.get_customer
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_id` | string | Yes | Customer document name |

**Returns:** `{ customer: {...}, notes: [...], tags: [...], leads: [...], organization: {...} | null, members: [...] }`

`organization` is the organization a person belongs to, carrying its name rather
than a bare docname. `members` is the people who belong to this organization,
and is empty for a person. Only one of the two is ever populated.

### `create_customer`

```
POST /api/method/micro.api.customers.create_customer
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name1` | string | Yes | First name (Person) or company name (Organization) |
| `contact_type` | string | No | `"Person"` (default) or `"Organization"` |
| `last_name` | string | Person: Yes | Last name (required for Person customers) |
| `status` | string | No | `"Potential"` (default), `"Active"`, or `"Inactive"` |
| `email` | string | No | Email address |
| `phone` | string | No | Phone number |
| `mobile` | string | No | Mobile number |
| `website` | string | No | Website URL |
| `organization` | string | No | Employer as free text (Person customers only). A fallback for contacts with no organization record |
| `organization_contact` | string | No | Docname of the organization Contact to link the person to. Takes precedence over `organization`, whose value it overwrites |
| `source` | string | No | Customer source (`Manual`, `Google Ads`, `Facebook`, `Instagram`, `LinkedIn`, `Email Campaign`, `Cold Call`, `Web Form`, `Organic Search`, `Referral`, `Partner`, `Event`, `Import`, `Other`) |
| `pipeline_stage` | string | No | Pipeline stage document name |
| `address` | string | No | Street address |
| `city` | string | No | City |
| `postal_code` | string | No | Postal code |
| `country` | string | No | Country |
| `notes` | string | No | Free-text notes |

**Returns:** `{ customer: {...} }`

### `get_organization_members`

```
GET /api/method/micro.api.customers.get_organization_members
```

The people who belong to an organization — "who do I know at Müller Bau?"

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_id` | string | Yes | Docname of the organization Contact |

**Returns:** `{ members: [...], total: 0 }`, ordered by full name.

### `set_customer_organization`

```
POST /api/method/micro.api.customers.set_customer_organization
```

Attaches a person to an organization, or detaches them from one.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_id` | string | Yes | Docname of the person |
| `organization` | string | No | Docname of the organization. Omit or pass `null` to detach |

Attaching mirrors the organization's name into the person's `company_name`.
Detaching leaves `company_name` standing: the employer was true when it was
written, and dropping a relation is not a claim that the person never worked
there.

**Returns:** `{ customer: {...} }`

### `get_delete_preview`

```
GET /api/method/micro.api.customers.get_delete_preview
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_id` | string | Yes | Contact document name |

**Returns:** `{ customer, deletes: {doctype: count}, retention_blockers: [...], foreign_links: [...], can_erase: bool }`

### `delete_customer`

```
POST /api/method/micro.api.customers.delete_customer
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `customer_id` | string | — | Contact document name |
| `mode` | string | `"remove"` | `remove` or `erase` |

`remove` clears the contact's Micro membership and keeps every document.
`erase` deletes the Contact along with Micro's leads, notes, tasks and unsent
drafts for it, and is refused while a receipt, a sent draft or another app still
refers to the record. Requires `delete` on Contact.

**Returns:** `{ customer, mode, erased: bool }`

### `get_customer_facets`

```
GET /api/method/micro.api.customers.get_customer_facets
```

No parameters. **Returns:** the categories in use and how many contacts each holds — used to build the list filters.

### `update_customer`

```
POST /api/method/micro.api.customers.update_customer
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_id` | string | Yes | Contact document name |

Remaining fields are passed as keyword arguments. Only whitelisted fields are written:
`first_name`, `last_name`, `company_name`, `micro_status`, `micro_contact_type`,
`micro_organization`, `micro_source`, `micro_segment`, `micro_website`, `micro_address`,
`micro_city`, `micro_postal_code` and the other `micro_*` CRM fields.

> `email_id`, `phone` and `mobile_no` are **not** directly writable. Frappe recomputes them
> from `email_ids` / `phone_nos` on every save, so a direct write is undone on the way to the
> database. They go through the child-table helpers instead.

### `add_customer_tag` / `remove_customer_tag`

```
POST /api/method/micro.api.customers.add_customer_tag
POST /api/method/micro.api.customers.remove_customer_tag
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_id` | string | Yes | Contact document name |
| `tag` | string | Yes | Label to add or remove |

Removing a tag from one contact leaves the tag itself intact for other records.

### `update_intelligence`

```
POST /api/method/micro.api.customers.update_intelligence
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_id` | string | Yes | Contact document name |

Writes the Client Intelligence Card fields: `micro_client_loves`, `micro_client_avoid`,
`micro_communication_style`, `micro_personal_notes`, `micro_opportunities`,
`micro_last_contact_date`, `micro_last_contact_topic`, `micro_referred_by`.

### `bulk_delete_customers`

```
POST /api/method/micro.api.customers.bulk_delete_customers
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `customer_ids` | list \| JSON string | *(required)* | Contacts to act on |
| `mode` | string | `remove` | `remove` or `erase` — see below |

**`remove` vs `erase`:**

| Mode | Effect |
|------|--------|
| `remove` | Clears Micro membership (`micro_status`, `micro_pipeline_stage`). Every document stays; re-adopting the contact later brings its history back |
| `erase` | Destroys the record. **Refused while a retention obligation still points at it** — sent offers, invoices and receipts outrank a delete request |

Use `get_delete_preview` first to show what each mode would do.

---

## Articles — `micro.api.articles`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `get_articles` | List articles with filters, search, pagination |
| GET | `get_article` | Get single article |

### `get_articles`

```
GET /api/method/micro.api.articles.get_articles
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `filters` | dict | `None` | Frappe-style filters |
| `search` | string | `None` | Search by article name |
| `order_by` | string | `"modified desc"` | Sort order |
| `limit_start` | int | `0` | Pagination offset |
| `limit_page_length` | int | `20` | Page size |

**Default fields:** `name`, `article_name`, `article_code`, `category`, `unit`, `selling_price`, `purchase_price`, `is_active`

**Returns:** `{ articles: [...], total: int }`

### `get_article`

```
GET /api/method/micro.api.articles.get_article
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `article_id` | string | Yes | Article document name |

**Returns:** `{ article: {...} }`

### `create_article`

```
POST /api/method/micro.api.articles.create_article
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `article_name` | string | *(required)* | Display name |
| `selling_price` | float | `0` | VK |
| `purchase_price` | float | `0` | EK |
| `article_code` | string | `None` | Internal code |
| `barcode` | string | `None` | Barcode |
| `category` | string | `None` | Link to Micro Article Category |
| `unit` | string | `Stück` | Unit of measure |
| `is_active` | bool | `True` | Show in pickers |
| `description` | string | `None` | Long text |
| `supplier` | string | `None` | Supplier name |
| `notes` | string | `None` | Internal notes |

Subject to `article_limit` (Community default: 50).

### `update_article`

```
POST /api/method/micro.api.articles.update_article
```

Takes `article_id` plus any of the `create_article` fields. Omitted fields are left untouched.

### `get_categories` / `create_category`

```
GET  /api/method/micro.api.articles.get_categories
POST /api/method/micro.api.articles.create_category
```

`get_categories` takes no parameters and returns the list for dropdowns. `create_category`
takes `category_name` and exists so a category can be added inline from the article form.

---

## Offers — `micro.api.offers`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `get_offers` | List offer drafts with filters, search, pagination |
| GET | `get_offer` | Get single offer draft with items |
| POST | `create_offer` | Create new offer draft |

### `get_offers`

```
GET /api/method/micro.api.offers.get_offers
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `filters` | dict | `None` | Frappe-style filters |
| `search` | string | `None` | Search by reference |
| `order_by` | string | `"modified desc"` | Sort order |
| `limit_start` | int | `0` | Pagination offset |
| `limit_page_length` | int | `20` | Page size |

**Default fields:** `name`, `reference`, `title`, `customer`, `date`, `valid_until`, `status`, `total`

**Returns:** `{ offers: [...], total: int }`

### `get_offer`

```
GET /api/method/micro.api.offers.get_offer
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `offer_id` | string | Yes | Offer draft document name |

**Returns:** `{ offer: {...} }` (includes `items` child table)

### `create_offer`

```
POST /api/method/micro.api.offers.create_offer
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer` | string | Yes | Customer document name |
| `title` | string | No | Offer title |
| `items` | list | No | Line items (see below) |

**Item format:** `{ article: string, description: string, quantity: float, rate: float, unit: string }`

**Returns:** `{ offer: {...} }`

### `update_offer`

```
POST /api/method/micro.api.offers.update_offer
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `offer_id` | string | Offer draft document name *(required)* |
| `title` | string | Offer title — checked against guardrail G5 (forbidden invoice terminology) |
| `contact` | string | Contact the offer is addressed to |
| `valid_until` | date | Validity date |
| `status` | string | `Draft`, `Sent`, `Accepted`, `Declined`, `Expired` — guardrail G6 blocks payment-based statuses |
| `items` | list | Replacement line items |
| `notes` | string | Notes printed on the document |
| `internal_notes` | string | Never printed |

Omitted fields are left untouched.

---

## Invoice Drafts — `micro.api.invoices`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `get_invoices` | List invoice drafts with filters, search, pagination |
| GET | `get_invoice` | Get single invoice draft with items |
| POST | `create_invoice` | Create new invoice draft |

### `get_invoices`

```
GET /api/method/micro.api.invoices.get_invoices
```

Same parameters as `get_offers`.

**Default fields:** `name`, `reference`, `title`, `customer`, `date`, `status`, `source`, `total`

**Returns:** `{ invoices: [...], total: int }`

### `get_invoice`

```
GET /api/method/micro.api.invoices.get_invoice
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `invoice_id` | string | Yes | Invoice draft document name |

**Returns:** `{ invoice: {...} }` (includes `items` child table)

### `create_invoice`

```
POST /api/method/micro.api.invoices.create_invoice
```

Same parameters as `create_offer`: `customer` (required), `title`, `items`.

**Returns:** `{ invoice: {...} }`

---

## Receipts — `micro.api.receipts`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `get_receipts` | List receipts with filters, search, pagination |
| GET | `get_receipt` | Get single receipt |

### `get_receipts`

```
GET /api/method/micro.api.receipts.get_receipts
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `filters` | dict | `None` | Frappe-style filters |
| `search` | string | `None` | Search by vendor |
| `category` | string | `None` | Filter by receipt category |
| `order_by` | string | `"receipt_date desc"` | Sort order |
| `limit_start` | int | `0` | Pagination offset |
| `limit_page_length` | int | `20` | Page size |

**Default fields:** `name`, `receipt_date`, `vendor`, `amount`, `category`, `description`, `exported`, `export_date`

**Returns:** `{ receipts: [...], total: int }`

### `get_receipt`

```
GET /api/method/micro.api.receipts.get_receipt
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `receipt_id` | string | Yes | Receipt document name |

**Returns:** `{ receipt: {...} }`

---

## Duplicates — `micro.api.duplicates`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `get_duplicate_summary` | Open suggestion counts, for the banner |
| GET | `get_duplicate_pairs` | Open suggestions with both records attached |
| GET | `check_duplicates` | Live check for a contact that is not saved yet |
| GET | `get_merge_preview` | What a merge would carry over and touch |
| POST | `scan_for_duplicates` | Re-scan every contact (also runs daily) |
| POST | `merge_contacts` | Fold one contact into another |
| POST | `dismiss_pair` | Mark a suggestion as "not a duplicate" |
| POST | `undo_merge` | Restore a merged-away contact within 30 days |

### `get_duplicate_summary`

```
GET /api/method/micro.api.duplicates.get_duplicate_summary
```

**Returns:** `{ open: int, certain: int }`

### `get_duplicate_pairs`

```
GET /api/method/micro.api.duplicates.get_duplicate_pairs
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit_start` | int | `0` | Pagination offset |
| `limit_page_length` | int | `20` | Page size |
| `band` | string | `None` | `Certain`, `Likely` or `Possible` |

**Returns:** `{ pairs: [{ name, score, band, signals, reasons, contact_a, contact_b, documents_a, documents_b }], total: int }`

`reasons` is the translated, human-readable form of `signals` — what the review
screen shows as the explanation for a suggestion.

### `check_duplicates`

```
GET /api/method/micro.api.duplicates.check_duplicates
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `first_name`, `last_name` | string | No | Name being typed |
| `email`, `phone`, `mobile` | string | No | Contact details being typed |
| `organization` | string | No | Company name |
| `contact_type` | string | No | `Person` (default) or `Organization` |
| `postal_code`, `address`, `website` | string | No | Further evidence |
| `exclude` | string | No | Contact to leave out — itself, when editing |

Writes nothing. Searches every contact on the site, not only Micro's customers,
so a person another app already entered is found rather than duplicated.

**Returns:** `{ matches: [{ contact, score, band, reasons }] }` — at most five.

### `merge_contacts`

```
POST /api/method/micro.api.duplicates.merge_contacts
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `winner` | string | Yes | Contact that survives |
| `loser` | string | Yes | Contact folded into it |
| `pair` | string | No | Suggestion this resolves |

Fills blanks on the survivor, keeps conflicting emails and phone numbers side by
side, repoints every linked document, then deletes the loser. Requires `write`
and `delete` on Contact.

**Returns:** `{ winner, merged, pair, undo_days }`

### `undo_merge`

```
POST /api/method/micro.api.duplicates.undo_merge
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pair` | string | Yes | The merged suggestion to reverse |

**Returns:** `{ restored: string, documents_moved: int }`

---

## Pipeline — `micro.api.pipeline`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `get_pipelines` | List active pipelines, for the board switcher |
| GET | `get_pipeline` | Get Kanban board data (stages with grouped leads) |
| POST | `move_lead` | Move a lead to another stage of its own pipeline |
| GET | `get_stages` | List pipeline stages |
| GET | `get_segments` | List active segments, for filter dropdowns |

> **The cards on the board are leads, not customers.** One contact can run through
> several pipelines at once, which is exactly why the two are kept apart. Pipeline
> endpoints therefore take `lead_id`, not `customer_id`.

### `get_pipelines`

```
GET /api/method/micro.api.pipeline.get_pipelines
```

No parameters.

**Returns:** `{ pipelines: [{ name, pipeline_name, segment, is_default, sort_order, description, open_leads }] }`

### `get_pipeline`

```
GET /api/method/micro.api.pipeline.get_pipeline
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pipeline` | string | *(default pipeline)* | Pipeline to render |
| `show_closed` | bool | `False` | Include closed stages (Won, Lost) |
| `segment` | string | `None` | Filter by segment |
| `source` | string | `None` | Filter by acquisition source |
| `priority` | string | `None` | Filter by priority |
| `due_only` | bool | `False` | Only leads with a follow-up due |
| `search` | string | `None` | Search term |
| `leads_per_stage` | int | `0` | Cap the cards per stage (`0` = no cap) |

**Returns:** stages with their leads, grouped for the board.

### `move_lead`

```
POST /api/method/micro.api.pipeline.move_lead
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lead_id` | string | Yes | Lead document name |
| `stage_id` | string | Yes | Target stage — must belong to the lead's own pipeline |

**Returns:** `{ success: true, status, stage }`

### `get_stages`

```
GET /api/method/micro.api.pipeline.get_stages
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pipeline` | string | `None` | Restrict to one pipeline; omit for all |

**Returns:** `{ stages: [{ name, stage_name, pipeline, sort_order, color, is_closed, is_win_stage, is_loss_stage }] }`

### `get_segments`

```
GET /api/method/micro.api.pipeline.get_segments
```

No parameters.

**Returns:** `{ segments: [{ name, segment_name, color, sort_order }] }`

## Dashboard — `micro.api.dashboard`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `get_dashboard_kpis` | Aggregated KPIs for the dashboard |

### `get_dashboard_kpis`

```
GET /api/method/micro.api.dashboard.get_dashboard_kpis
```

No parameters.

**Returns:**
```json
{
  "customers": {
    "total": 42,
    "by_status": { "Potential": 15, "Active": 22, "Inactive": 5 },
    "by_source": { "Referral": 12, "Google Ads": 10, "Web Form": 8, "Manual": 7, "Unknown": 5 }
  },
  "offers": { "total": 15, "by_status": { "Draft": 5, "Sent": 7, "Accepted": 3 } },
  "invoices": { "total": 10, "by_status": { "Draft": 8, "Sent": 2 } },
  "receipts": {
    "total": 28,
    "unexported": 12,
    "by_category": { "Office": 10, "Travel": 8, "Software": 5, "Other": 5 },
    "total_amount": 3456.78
  },
  "recent_activity": [
    {
      "doctype": "Contact",
      "name": "CUST-001",
      "label": "Max Mustermann",
      "modified": "2026-03-15 14:30:00"
    }
  ]
}
```

---

## Export — `micro.api.export`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `get_export_preview` | Preview export count |
| POST | `export_csv` | Generate CSV export |
| POST | `mark_as_exported` | Mark documents as exported |
| POST | `export_zip` | Download the export as a ZIP (CSV plus receipt images) |

See [Export documentation](export.md) for full details.

---

## Leads — `micro.api.leads`

Leads are the cards on the pipeline board. A lead is a **deal**, kept separate from the
contact it is about — one contact can run through several pipelines at once.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `get_leads` | List leads with filters, pagination, search |
| GET | `get_lead` | One lead, contact and stage resolved to names |
| POST | `create_lead` | Create a lead |
| POST | `update_lead` | Update editable fields (call list, detail page) |
| POST | `move_lead` | Move a lead to another stage |
| POST | `archive_lead` | Soft delete — off every board, still recoverable |
| POST | `restore_lead` | Take a lead back out of the archive |
| POST | `delete_lead` | Hard delete — Micro Manager only, gone for good |
| GET | `get_archived_leads` | The archive view (Micro's trash), newest first |
| POST | `snooze_lead` | Push the follow-up date out — the "not today" button |
| GET | `get_call_list` | Today's queue: open leads that are due, most urgent first |

### `get_leads`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `filters` | dict | `None` | Frappe filter dict |
| `order_by` | string | `modified desc` | Sort order |
| `limit_start` | int | `0` | Pagination offset |
| `limit_page_length` | int | `20` | Page size |
| `search` | string | `None` | Search term |
| `include_archived` | bool | `False` | Include archived leads |

### `create_lead`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lead_name` | string | Yes | Deal name |
| `pipeline` | string | No | Defaults to the board it is created from |
| `stage` | string | No | Defaults to the pipeline's first stage |
| `contact` | string | No | Contact the deal is about |
| `priority` | string | No | `Low`, `Medium` (default), `High` |
| `source` | string | No | Acquisition source |
| `expected_value` | float | No | Capped by `max_expected_value` in settings |
| `next_follow_up` | date | No | Drives the call list |
| `notes` | string | No | Rich text |

### `snooze_lead`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `lead_id` | string | *(required)* | Lead document name |
| `days` | int | `7` | Days to push the follow-up date out |

### `get_call_list`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pipeline` | string | `None` | Restrict to one pipeline |
| `segment` | string | `None` | Restrict to one segment |
| `include_undated` | bool | `False` | Include leads with no follow-up date |
| `limit` | int | `50` | Max entries |

---

## Call Attempts — `micro.api.call_attempts`

A lightweight log of phone attempts. Attempts hang off the **contact**, not one lead, so the
pattern of when somebody actually picks up builds up across every deal.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `log_call_attempt` | Record one attempt to reach a contact |
| GET | `get_call_attempts` | Recent attempts for a contact, newest first |
| GET | `get_best_time_to_call` | When the logged attempts say they tend to answer |

### `log_call_attempt`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `contact` | string | Yes | Contact document name |
| `outcome` | string | Yes | `Reached`, `No Answer`, `Voicemail`, `Busy`, `Wrong Number` |
| `lead` | string | No | Lead the call was about |
| `attempted_at` | datetime | No | Defaults to now |
| `notes` | string | No | Free text |

---

## Pipeline Administration — `micro.api.pipeline_admin`

Backs the Pipeline Manager dialog, so pipelines and stages are configured without touching
the Frappe Desk. Community edition allows `pipeline_limit` pipelines (default 1).

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `get_pipeline_setup` | Everything the dialog needs, including what blocks deletion |
| POST | `create_pipeline` | Create a pipeline, with starter stages by default |
| POST | `update_pipeline` | Update a pipeline; a changed name is a real rename |
| POST | `delete_pipeline` | Delete with its stages — **refused while leads still live in it** |
| POST | `reorder_pipelines` | Persist the tab order |
| POST | `create_stage` | Append a stage |
| POST | `update_stage` | Rename, recolour, or change what the stage means for the deal |
| POST | `delete_stage` | Delete a stage, optionally moving its leads elsewhere first |
| POST | `reorder_stages` | Persist one pipeline's column order |
| POST | `create_segment` | Create a segment without leaving the dialog |

### `create_pipeline`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pipeline_name` | string | *(required)* | Display name |
| `segment` | string | `None` | Segment this pipeline serves |
| `description` | string | `None` | Free text |
| `with_starter_stages` | bool | `True` | Seed stages so the board is never born empty |

### `delete_stage`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `stage` | string | *(required)* | Stage document name |
| `move_leads_to` | string | `None` | Move the stage's leads here before deleting |

---

## Import — `micro.api.imports`

CSV contact import. The frontend parses and maps columns client-side; this module does the
row-by-row insert. **A failing row is reported individually — it never fails the batch.**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `get_import_setup` | Target fields plus remaining room under the customer limit |
| GET | `get_capacity` | How many more contacts fit before the Community limit bites |
| POST | `import_contacts` | Import one batch; returns an outcome per row |

### `import_contacts`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rows` | list \| JSON string | *(required)* | Parsed CSV rows |
| `mapping` | dict \| JSON string | *(required)* | Column → contact field |
| `contact_type` | string | `Organization` | `Person` or `Organization` |
| `status` | string | `Potential` | Initial `micro_status` |
| `source` | string | `Import` | Acquisition source |
| `dedupe_by` | string | `phone` | Field used to detect existing contacts |
| `on_duplicate` | string | `skip` | What to do on a match |
| `create_leads` | bool | `False` | Also create a lead per imported contact |
| `pipeline` | string | `None` | Pipeline for created leads |
| `stage` | string | `None` | Stage for created leads |

**Returns:** an outcome per row, never a bare count.

> Health-score recalculation is skipped during import. A large import would otherwise queue
> one job per row and exceed Frappe's pending-job ceiling; the nightly scheduler recalculates
> every score anyway.

---

## Tasks — `micro.api.tasks`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `get_tasks` | List tasks with filters, pagination, search |
| GET | `get_task` | One task |

Tasks are created and edited through the Frappe Desk; the SPA is read-only here.

---

## Capacity — `micro.api.capacity`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `get_capacity_data` | Capacity indicator data for the current month |

Compares committed work against `monthly_capacity_hours` in Micro Settings.

---

## Client Health — `micro.api.health`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `get_client_portfolio` | All Micro contacts ranked by health score, with portfolio insights |
| POST | `recalculate_score` | Recalculate one contact's score on demand |

Scores are stored on `Contact.micro_health_score` and refreshed nightly by the scheduler.

---

## Intelligence — `micro.api.intelligence`

Read-only analysis over existing records. No new data is stored.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `get_nudges` | Unanswered offers, dormant contacts, upcoming follow-ups |
| GET | `get_win_rate` | Win rate intelligence |
| GET | `get_revenue_runway` | Revenue runway |
| GET | `get_weekly_briefing` | Weekly business briefing |

---

## Moments — `micro.api.moments`

Emotional-design milestones. Every moment is dismissible and remembers that it was seen.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `get_offer_accepted_data` | Context for the Offer Accepted celebration card |
| GET | `get_first_offer_sent_status` | Whether to show the First Offer Sent overlay |
| POST | `dismiss_first_offer_sent` | Mark that milestone as seen |
| GET | `get_annual_wrapped` | Aggregated business summary for a year |
| POST | `dismiss_annual_wrapped` | Mark the year's wrapped as seen |
| POST | `reset_milestones` | Reset all milestone flags so moments re-trigger |

`get_first_offer_sent_status` and `get_annual_wrapped` accept `force` to bypass the seen flag.

---

## Assistant Briefing — `micro.api.jana_briefing`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `get_briefing` | Micro's daily sales-intelligence summary |

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `date` | string | *(today)* | `YYYY-MM-DD` |

Registered through the `jana_briefing_source` hook, so this feeds both the Jana assistant and
Dock's briefing panel. See Dock's `docs/hooks.md` for the hook contract.
