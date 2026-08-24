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
| GET | `get_pipeline` | Get Kanban board data (stages with grouped customers) |
| POST | `move_customer` | Move a customer to a different pipeline stage |
| GET | `get_stages` | List all pipeline stages |

### `get_pipeline`

```
GET /api/method/micro.api.pipeline.get_pipeline
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `show_closed` | bool | `False` | Include closed stages (Won, Lost) |

**Returns:**
```json
{
  "stages": [
    {
      "stage": { "name": "MPS-0001", "stage_name": "New", "sort_order": 10, "color": "Blue", "is_closed": false },
      "customers": [{ "name": "MC-0001", "full_name": "Max Mustermann", ... }]
    }
  ],
  "unassigned": [{ "name": "MC-0005", "full_name": "Jane Doe", ... }]
}
```

### `move_customer`

```
POST /api/method/micro.api.pipeline.move_customer
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_id` | string | Yes | Customer document name |
| `stage_id` | string | Yes | Target pipeline stage document name |

**Returns:** `{ success: true }`

### `get_stages`

```
GET /api/method/micro.api.pipeline.get_stages
```

No parameters.

**Returns:** `{ stages: [...] }`

---

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
      "doctype": "Micro Customer",
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

See [Export documentation](export.md) for full details.
