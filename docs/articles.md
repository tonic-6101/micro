# Article Catalog

The article catalog is your price list — the products and services you offer to clients.

## Micro Article

A **Micro Article** represents a product or service with pricing information.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `article_name` | Data | Article name (required) |
| `article_code` | Data | Short code / SKU |
| `category` | Data | Article category |
| `unit` | Data | Unit of measure (e.g., "Stück", "Stunde", "Pauschal") |
| `selling_price` | Currency | Selling price (VK) |
| `purchase_price` | Currency | Purchase price (EK) |
| `is_active` | Check | Whether the article is currently offered |

### Article Limit

The community edition supports up to 50 articles. This limit is configured in Micro Settings.

### Pricing

Micro tracks two prices per article:

- **Selling price (VK)** — what you charge clients
- **Purchase price (EK)** — what the item costs you

These are simple price fields. Micro does not calculate margins, taxes, or discounts — it is an organizer, not accounting software.

## API

**List articles:**

```
GET /api/method/micro.api.articles.get_articles
```

Parameters:
- `filters` (dict, optional) — Frappe-style filters
- `search` (string, optional) — Search by article name
- `order_by` (string, default: `"modified desc"`) — Sort order
- `limit_start` (int, default: `0`) — Pagination offset
- `limit_page_length` (int, default: `20`) — Page size

Response:
```json
{
  "articles": [
    {
      "name": "ART-001",
      "article_name": "Consulting Hour",
      "article_code": "CONS-01",
      "category": "Services",
      "unit": "Stunde",
      "selling_price": 120.00,
      "purchase_price": 0.00,
      "is_active": 1
    }
  ],
  "total": 15
}
```

**Get single article:**

```
GET /api/method/micro.api.articles.get_article
```

Parameters:
- `article_id` (string, required) — Article document name

Response:
```json
{
  "article": {...}
}
```

## Usage with Drafts

Articles are referenced by offer drafts and invoice drafts. When you add a line item to an offer or invoice draft, you select an article from the catalog. The article's description, unit, and rate can be overridden per line item.
