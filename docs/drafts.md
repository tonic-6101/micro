# Offer Drafts & Invoice Drafts

Micro creates **draft documents only** — preparation documents for your tax advisor. These are not legally binding invoices or quotes.

All draft documents are watermarked and carry a disclaimer footer to clearly indicate their non-binding status.

## Offer Drafts

A **Micro Offer Draft** is a client-facing quote that you can share as a proposal.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `reference` | Data | Auto-generated random reference (e.g., `OFF-20260315-X7K2`) |
| `title` | Data | Offer title |
| `customer` | Link | Associated Micro Customer |
| `date` | Date | Offer date |
| `valid_until` | Date | Expiry date |
| `status` | Select | `Draft`, `Sent`, `Accepted`, `Declined`, `Expired` |
| `total` | Currency | Computed total from line items |
| `items` | Table | Child table of Micro Offer Item |

### Line Items (Micro Offer Item)

| Field | Type | Description |
|-------|------|-------------|
| `article` | Link | Reference to Micro Article |
| `description` | Data | Item description (can override article name) |
| `quantity` | Float | Quantity |
| `rate` | Currency | Unit price |
| `unit` | Data | Unit of measure |
| `amount` | Currency | Computed: quantity x rate |

### Status Workflow

```
Draft → Sent → Accepted / Declined / Expired
```

### API

**List offer drafts:**

```
GET /api/method/micro.api.offers.get_offers
```

Parameters: `filters`, `search`, `order_by`, `limit_start`, `limit_page_length` (same pattern as other list endpoints).

**Get single offer draft:**

```
GET /api/method/micro.api.offers.get_offer
```

Parameters:
- `offer_id` (string, required)

**Create offer draft:**

```
POST /api/method/micro.api.offers.create_offer
```

Parameters:
- `customer` (string, required) — Customer document name
- `title` (string, optional) — Offer title
- `items` (list, optional) — Line items, each with: `article`, `description`, `quantity`, `rate`, `unit`

Example:
```json
{
  "customer": "CUST-001",
  "title": "Website Redesign",
  "items": [
    {"article": "ART-001", "description": "Design", "quantity": 10, "rate": 120, "unit": "Stunde"},
    {"article": "ART-002", "description": "Hosting Setup", "quantity": 1, "rate": 250, "unit": "Pauschal"}
  ]
}
```

## Invoice Drafts

A **Micro Invoice Draft** is a preparation document — it gathers the information your tax advisor needs to create the actual invoice.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `reference` | Data | Auto-generated random reference (e.g., `INV-20260315-M3P9`) |
| `title` | Data | Draft title |
| `customer` | Link | Associated Micro Customer |
| `date` | Date | Draft date |
| `status` | Select | Draft status |
| `source` | Data | Origin of the draft (e.g., manual, from offer) |
| `total` | Currency | Computed total from line items |
| `items` | Table | Child table of Micro Invoice Item |

### Line Items (Micro Invoice Item)

Same structure as Micro Offer Item: `article`, `description`, `quantity`, `rate`, `unit`, `amount`.

### API

**List invoice drafts:**

```
GET /api/method/micro.api.invoices.get_invoices
```

**Get single invoice draft:**

```
GET /api/method/micro.api.invoices.get_invoice
```

Parameters:
- `invoice_id` (string, required)

**Create invoice draft:**

```
POST /api/method/micro.api.invoices.create_invoice
```

Parameters:
- `customer` (string, required)
- `title` (string, optional)
- `items` (list, optional) — same format as offer items

## Compliance Guardrails

All draft documents enforce the following guardrails:

| Guardrail | What It Does |
|-----------|-------------|
| **G1: Draft Watermark** | Every document displays "ENTWURF" / "DRAFT" prominently (8 languages supported) |
| **G2: No Sequential Numbering** | References are random codes (e.g., `OFF-20260315-X7K2`), never sequential |
| **G3: No Tax/VAT Fields** | Tax-related fields are rejected at validation |
| **G4: Disclaimer Footer** | Every document includes "Entwurf — keine rechtsgültige Rechnung" (8 languages) |
| **G5: Safe Terminology** | UI uses "Draft" / "Entwurf", never "Invoice" / "Rechnung" for these documents |
| **G6: No Payment Tracking** | No payment status, payment date, or payment method fields |

### Supported Languages

Watermarks and disclaimers are available in: German (de), English (en), French (fr), Spanish (es), Italian (it), Portuguese (pt), Polish (pl), Dutch (nl).
