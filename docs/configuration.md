# Configuration

Micro is configured through the **Micro Settings** Single DocType, accessible at `/micro/settings` or via Frappe Desk.

## Settings Fields

### Company

Your own business details. These appear on offer and invoice drafts.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `company_name` | Data | `My Business` | Your business name. Required — Micro Settings cannot be created without it |
| `company_email` | Data | — | Contact email printed on documents |
| `company_phone` | Data | — | Contact phone printed on documents |
| `company_address` | Small Text | — | Street address |
| `company_postal_code` | Data | — | Postal code |
| `company_city` | Data | — | City |
| `company_logo` | Attach Image | — | Logo used on print formats |

### Defaults and limits

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `default_currency` | Link | `EUR` | Default currency for amounts |
| `default_language` | Link | `de` | Language for watermarks and disclaimers |
| `customer_limit` | Int | `100` | Maximum customers (Community edition) |
| `article_limit` | Int | `50` | Maximum articles (Community edition) |
| `pipeline_limit` | Int | `1` | Maximum pipelines (Community edition) |
| `monthly_capacity_hours` | Int | `100` | Hours per month the capacity indicator measures against |
| `max_expected_value` | Currency | `1000000` | Upper bound accepted for a lead's expected value |

These caps are sent to the frontend at boot rather than hardcoded per page, so raising one
takes effect everywhere at once.

### Compliance

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `draft_watermark_text` | Data | `ENTWURF` | Draft watermark on documents (guardrail G1) |
| `draft_disclaimer` | Small Text | *(auto from language)* | Disclaimer footer on drafts (guardrail G4) |

### Tax advisor

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `tax_advisor_name` | Data | — | Name shown in the export wizard |
| `tax_advisor_email` | Data | — | Address the export is prepared for |

### Integration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enable_orga_integration` | Check | `0` | Turn on the Orga bridge |

### Milestone flags (internal)

Written by the app, not meant for manual editing. `micro.api.moments.reset_milestones`
clears both so the moments can be triggered again.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `first_offer_sent_seen` | Check | `0` | The First Offer Sent milestone has been shown |
| `annual_wrapped_year` | Int | `0` | Last year whose Annual Wrapped was dismissed |

## Language Support

The `default_language` setting controls the language used for draft watermarks (G1) and disclaimer footers (G4). Supported languages:

| Code | Watermark | Language |
|------|-----------|----------|
| `de` | ENTWURF | German |
| `en` | DRAFT | English |
| `fr` | BROUILLON | French |
| `es` | BORRADOR | Spanish |
| `it` | BOZZA | Italian |
| `pt` | RASCUNHO | Portuguese |
| `pl` | PROJEKT | Polish |
| `nl` | CONCEPT | Dutch |

## Community Edition Limits

The community edition enforces soft limits to keep Micro focused on micro businesses:

- **Customers:** Up to 100 (configurable via `customer_limit`)
- **Articles:** Up to 50 (configurable via `article_limit`)
- **Pipelines:** 1 (configurable via `pipeline_limit`)

These limits are stored in Micro Settings and checked during document creation.

## Defaults Set on Install

When Micro is first installed, the following defaults are configured:

| Setting | Value |
|---------|-------|
| Currency | EUR |
| Language | de (German) |
| Customer limit | 100 |
| Article limit | 50 |
| Pipeline limit | 1 |
| Watermark text | ENTWURF |
