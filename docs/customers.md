# Customer Management

Micro provides a built-in CRM for managing the people and organizations you work with.

## Customers

A **Micro Customer** represents a person or organization in your business network.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `name1` | Data | First name or company name (required) |
| `last_name` | Data | Last name (required for Person customers) |
| `full_name` | Data | Auto-computed from first + last name |
| `contact_type` | Select | `Person` or `Organization` |
| `status` | Select | `Potential`, `Active`, or `Inactive` |
| `pipeline_stage` | Link | Pipeline stage for Kanban view (see Pipeline below) |
| `email` | Data | Email address (validated) |
| `phone` | Data | Phone number |
| `mobile` | Data | Mobile number |
| `website` | Data | Website URL |
| `organization` | Link | Associated organization (shown for Person customers) |
| `source` | Select | How the customer was acquired (see Source Tracking below) |
| `address` | Small Text | Street address |
| `city` | Data | City |
| `postal_code` | Data | Postal code |
| `country` | Link | Country |
| `notes` | Text | Free-text notes |
| `image` | Attach Image | Customer photo |

### Customer Types

- **Person** — An individual. Requires both first name and last name. Can optionally be linked to an organization.
- **Organization** — A company or entity. Requires a company name (stored in `name1`). Last name and organization fields are hidden.

### Customer Status

Each customer has a `status` field that tracks their lifecycle:

- **Potential** — A prospective customer who has not yet done business with you.
- **Active** — A customer you are currently working with.
- **Inactive** — A customer you are no longer actively engaged with.

### Source Tracking

The `source` field tracks how a customer was acquired. Available options:

| Source | Description |
|--------|-------------|
| Manual | Manually entered |
| Google Ads | Google advertising |
| Facebook | Facebook marketing |
| Instagram | Instagram marketing |
| LinkedIn | LinkedIn outreach |
| Email Campaign | Email marketing |
| Cold Call | Cold calling |
| Web Form | Website contact form |
| Organic Search | Found via search engine |
| Referral | Referred by someone |
| Partner | Business partner referral |
| Event | Met at an event |
| Import | Imported from external system |
| Other | Other source |

The dashboard includes a **Customers by Source** widget showing the distribution of customers across acquisition channels. The Customers list page also includes a source filter dropdown for quick filtering.

### Customer Limit

The community edition supports up to 100 customers. This limit is configured in Micro Settings.

### API

**List customers:**

```
GET /api/method/micro.api.customers.get_customers
```

Parameters:
- `filters` (dict, optional) — Frappe-style filters
- `search` (string, optional) — Search by full name
- `order_by` (string, default: `"modified desc"`) — Sort order
- `limit_start` (int, default: `0`) — Pagination offset
- `limit_page_length` (int, default: `20`) — Page size

Response:
```json
{
  "customers": [...],
  "total": 42
}
```

**Get single customer:**

```
GET /api/method/micro.api.customers.get_customer
```

Parameters:
- `customer_id` (string, required) — The customer document name

Response includes the customer with related notes:
```json
{
  "customer": {...},
  "notes": [...]
}
```

**Create a customer:**

```
POST /api/method/micro.api.customers.create_customer
```

Parameters:
- `name1` (string, required) — First name (Person) or company name (Organization)
- `contact_type` (string, default: `"Person"`) — `"Person"` or `"Organization"`
- `last_name` (string) — Required for Person customers
- `status` (string, default: `"Potential"`) — `"Potential"`, `"Active"`, or `"Inactive"`
- `email` (string, optional) — Email address
- `phone` (string, optional) — Phone number
- `mobile` (string, optional) — Mobile number
- `website` (string, optional) — Website URL
- `organization` (string, optional) — Organization name (Person customers only)
- `source` (string, optional) — How the customer was acquired
- `address` (string, optional) — Street address
- `city` (string, optional) — City
- `postal_code` (string, optional) — Postal code
- `country` (string, optional) — Country
- `notes` (string, optional) — Free-text notes

Response:
```json
{
  "customer": {...}
}
```

### Frontend

Customers can be created directly in the Vue frontend at `/micro/customers/new`. The form adapts based on customer type:

- **Person** — Shows first name, last name (both required), and optional organization
- **Organization** — Shows company name (required); last name and organization fields are hidden

## Pipeline

The **Pipeline** page provides a visual Kanban board where customers are displayed as draggable cards grouped by customizable stages.

### Pipeline Stages

A **Micro Pipeline Stage** defines a column on the Kanban board.

| Field | Type | Description |
|-------|------|-------------|
| `stage_name` | Data | Display name (e.g., "New", "Contacted") |
| `sort_order` | Int | Column order (lower = further left) |
| `color` | Select | Column header color (Gray, Blue, Green, Yellow, Orange, Red, Purple, Pink) |
| `is_closed` | Check | Whether the stage is a closed/terminal stage (e.g., Won, Lost) |

Default stages (created on install): **New** → **Contacted** → **Offer Sent** → **Negotiating** → **Won** → **Lost**

Stages can be customized via the Frappe Desk (`/app/micro-pipeline-stage`).

### Status vs. Pipeline Stage

These are separate fields with distinct purposes:

- **Status** (`Potential` / `Active` / `Inactive`) — The customer's business lifecycle state. Set manually or programmatically.
- **Pipeline Stage** — Where the customer is in your sales/engagement process. Updated by dragging cards on the Kanban board.

A customer can be in any pipeline stage regardless of their status. For example, an "Active" customer could be at the "Negotiating" stage for a new project.

### Pipeline API

See [API Reference](api-reference.md) for full details on the pipeline endpoints (`get_pipeline`, `move_customer`, `get_stages`).

---

## Notes

A **Micro Note** stores context about interactions with a customer — meeting notes, call summaries, correspondence records.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `subject` | Data | Note title |
| `customer` | Link | Associated Micro Customer |
| `note_type` | Select | Type of note |
| `date` | Date | Date of the interaction |
| `content` | Text | Note body |

