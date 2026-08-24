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
| `organization` | Data | Employer as free text, stored in `company_name` (shown for Person customers) |
| `micro_organization` | Link | The organization Contact a person belongs to (see People and organizations below) |
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

### People and organizations

A person's employer used to be free text only: "Müller Bau GmbH" typed on Thomas
and the organization record called "Müller Bau GmbH" were unrelated strings, so
neither "who do I know at Müller Bau?" nor "who does Thomas work for?" could be
answered.

`micro_organization` links the two. Both directions show on the customer page:
a person gets a card naming their organization, an organization gets the list of
its people. On a person's page the card is editable — pick an organization to
attach, clear the field and save to detach.

The rules that keep the link honest, enforced on the Contact itself so they hold
however the record is written:

- A contact cannot belong to itself.
- An organization cannot belong to another organization; only people are members.
- The target must exist and must be an organization, not a person.
- Attaching mirrors the organization's name into the person's `company_name`.
  Frappe core, the kanban cards, the contact picker and the print formats all
  read `company_name`, and a link that left them showing a different employer
  than the relation says would be worse than no link at all.
- Detaching leaves `company_name` alone, and so does erasing the organization:
  people do not disappear with their employer, and the name was true when it was
  written.

The duplicate detector knows about the relation. A person and the organization
they belong to share a name, an address, a domain and often a switchboard number
— normally strong evidence of a duplicate. The link states outright that they are
two records on purpose, so the pair is never suggested for merging.

Existing contacts can be linked in bulk by the
`link_people_to_organizations` patch, which joins a person to an organization
whenever the normalized employer name matches exactly one organization record.
Ambiguous names are left alone: a wrong employer is worse than a missing one.

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


## Deleting a Customer

"Delete" is two different requests, and Micro keeps them apart. Both live behind
the **Delete** button on the customer detail page.

### Remove from Micro

The everyday one: this contact is no longer a customer.

- Stops being a Micro customer and frees a slot under the Community limit
- **Every document stays** — leads, notes, offers, invoices, receipts keep their
  recipient
- The `Contact` record survives, so Helo, Orga and the other apps are untouched
- Reversible: give them a status again and their whole history is back

### Delete permanently

Erases the contact record itself. Micro's own working records for that contact —
leads, notes, tasks, and any *unsent* offer or invoice draft — are deleted with
it. This cannot be undone.

It is **refused** while anything holds a retention obligation over the record:

| Blocker | Why |
|---------|-----|
| Any **receipt** | A Beleg from the moment it exists |
| An **offer draft** past `Draft` | It has left the house |
| An **invoice draft** sent to the tax advisor or archived | Same |
| A link from **another app** | The `Contact` is shared — erase it there first |

The dialog names the blockers before you decide, and offers *Remove from Micro*
instead. An orphaned financial document is a worse outcome than a refused delete.

> **On erasure requests.** Where GoBD retention and a GDPR Art. 17 request
> collide, retention wins and this deliberately refuses. Resolving that properly
> means anonymizing the contact while leaving the documents intact — Micro does
> not do that yet.

## Duplicate Detection

Micro checks new contacts against the ones you already have and suggests merging
the pairs that look like one customer — while you type, and again in a daily
background scan. Nothing is merged automatically.

See [duplicates.md](duplicates.md).
