# Configuration

Micro is configured through the **Micro Settings** Single DocType, accessible at `/micro/settings` or via Frappe Desk.

## Settings Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `default_currency` | Data | `EUR` | Default currency for amounts |
| `default_language` | Select | `de` | Language for watermarks and disclaimers |
| `customer_limit` | Int | `100` | Maximum number of customers (community edition) |
| `article_limit` | Int | `50` | Maximum number of articles (community edition) |
| `draft_watermark_text` | Data | `ENTWURF` | Text displayed as draft watermark on documents |
| `draft_disclaimer` | Text | *(auto from language)* | Disclaimer text on draft documents |

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

The community edition enforces soft limits on customers and articles to keep Micro focused on micro businesses:

- **Customers:** Up to 100 (configurable via `customer_limit`)
- **Articles:** Up to 50 (configurable via `article_limit`)

These limits are stored in Micro Settings and checked during document creation.

## Defaults Set on Install

When Micro is first installed, the following defaults are configured:

| Setting | Value |
|---------|-------|
| Currency | EUR |
| Language | de (German) |
| Customer limit | 100 |
| Article limit | 50 |
| Watermark text | ENTWURF |
