# Receipt Collection

Micro helps you collect and organize business receipts for your tax advisor.

## Micro Receipt

A **Micro Receipt** records an expense — a purchase you made for your business.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `receipt_date` | Date | Date of the expense |
| `vendor` | Data | Vendor / supplier name |
| `description` | Data | What was purchased |
| `amount` | Currency | Receipt amount |
| `category` | Select | Expense category |
| `image` | Attach Image | Photo of the receipt |
| `customer` | Link | Associated Micro Customer (optional) |
| `exported` | Check | Whether this receipt has been exported to tax advisor |
| `export_date` | Date | Date when the receipt was exported |

### Categories

Receipts can be categorized as:

- **Materials** — Raw materials and supplies
- **Travel** — Transportation, accommodation, mileage
- **Office** — Office supplies and equipment
- **Food** — Meals and catering
- **Software** — Software licenses and subscriptions
- **Services** — Professional services
- **Other** — Everything else

### Export Tracking

Receipts have built-in export tracking. When you export receipts to your tax advisor (via CSV), Micro can mark them as exported and record the export date. This helps you track which receipts have already been sent.

## API

**List receipts:**

```
GET /api/method/micro.api.receipts.get_receipts
```

Parameters:
- `filters` (dict, optional) — Frappe-style filters
- `search` (string, optional) — Search by vendor name
- `category` (string, optional) — Filter by category
- `order_by` (string, default: `"receipt_date desc"`) — Sort order
- `limit_start` (int, default: `0`) — Pagination offset
- `limit_page_length` (int, default: `20`) — Page size

Response:
```json
{
  "receipts": [
    {
      "name": "REC-001",
      "receipt_date": "2026-03-01",
      "vendor": "Office Depot",
      "amount": 45.99,
      "category": "Office",
      "description": "Printer paper",
      "exported": 0,
      "export_date": null
    }
  ],
  "total": 28
}
```

**Get single receipt:**

```
GET /api/method/micro.api.receipts.get_receipt
```

Parameters:
- `receipt_id` (string, required)

## Workflow

1. Photograph a receipt and upload the image
2. Fill in vendor, amount, date, and category
3. When ready, export to your tax advisor (see [Export](export.md))
4. Exported receipts are marked so you know what has been sent
