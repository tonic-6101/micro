# API Reference

All Micro API endpoints are Frappe whitelisted methods, accessible via `/api/method/micro.api.<module>.<function>`.

Authentication is handled by Frappe's session system. All endpoints require the user to have the appropriate Micro permissions.

## Customers — `micro.api.customers`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `get_customers` | List customers with filters, search, pagination |
| GET | `get_customer` | Get single customer with related notes, tasks |
| POST | `create_customer` | Create a new customer |

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

**Returns:** `{ customer: {...}, notes: [...], tasks: [...] }`

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
| `organization` | string | No | Organization name (Person customers only) |
| `source` | string | No | Customer source (`Manual`, `Google Ads`, `Facebook`, `Instagram`, `LinkedIn`, `Email Campaign`, `Cold Call`, `Web Form`, `Organic Search`, `Referral`, `Partner`, `Event`, `Import`, `Other`) |
| `pipeline_stage` | string | No | Pipeline stage document name |
| `address` | string | No | Street address |
| `city` | string | No | City |
| `postal_code` | string | No | Postal code |
| `country` | string | No | Country |
| `notes` | string | No | Free-text notes |

**Returns:** `{ customer: {...} }`

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
  "tasks": { "open": 5 },
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
