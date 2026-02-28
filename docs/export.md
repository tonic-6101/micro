# Tax Advisor Export

Micro's export feature generates CSV files for your tax advisor (Steuerberater). This is the bridge between your business organizer and your accounting professional.

## Supported Document Types

You can export two types of documents:

- **Receipts** — expense records for bookkeeping
- **Invoice Drafts** — draft billing documents for final invoice creation

## API

### Preview Export

Check how many documents match your export filters before generating the CSV.

```
GET /api/method/micro.api.export.get_export_preview
```

Parameters:
- `doc_type` (string, default: `"Micro Receipt"`) — `"Micro Receipt"` or `"Micro Invoice Draft"`
- `from_date` (string, optional) — Start date (YYYY-MM-DD)
- `to_date` (string, optional) — End date (YYYY-MM-DD)
- `category` (string, optional) — Receipt category filter (receipts only)
- `only_unexported` (int, default: `0`) — Set to `1` to exclude already-exported receipts

Response:
```json
{
  "doc_type": "Micro Receipt",
  "count": 15,
  "filters": {"receipt_date": ["between", ["2026-01-01", "2026-03-31"]]}
}
```

### Export CSV

Generate and download a CSV file.

```
POST /api/method/micro.api.export.export_csv
```

Parameters:
- `doc_type` (string, default: `"Micro Receipt"`)
- `from_date` (string, optional)
- `to_date` (string, optional)
- `category` (string, optional) — receipts only
- `only_unexported` (int, default: `0`) — receipts only
- `mark_exported` (int, default: `0`) — Set to `1` to mark exported receipts

Response:
```json
{
  "csv": "Date;Vendor;Description;Category;Amount;Receipt ID\n2026-03-01;Office Depot;...",
  "count": 15,
  "marked_exported": 15,
  "filename": "receipts_export_2026-03-15.csv"
}
```

### Mark as Exported

Manually mark specific receipts as exported (without generating a CSV).

```
POST /api/method/micro.api.export.mark_as_exported
```

Parameters:
- `doc_type` (string) — currently only `"Micro Receipt"` supported
- `names` (list) — list of document names to mark

Response:
```json
{
  "updated": 5
}
```

## CSV Format

### Receipt Export

Semicolon-delimited CSV with these columns:

| Column | Description |
|--------|-------------|
| Date | Receipt date |
| Vendor | Vendor name |
| Description | What was purchased |
| Category | Expense category |
| Amount | Amount (two decimal places) |
| Receipt ID | Micro document ID |

### Invoice Draft Export

| Column | Description |
|--------|-------------|
| Date | Draft date |
| Reference | Random reference code |
| Customer | Customer name |
| Title | Draft title |
| Total | Total amount (two decimal places) |
| Status | Draft status |

## Workflow

1. Go to the **Export** page in the Micro frontend
2. Select the document type (Receipts or Invoice Drafts)
3. Set date range and optional filters
4. Preview the export count
5. Download the CSV
6. Send the CSV to your tax advisor
7. Optionally mark documents as exported for tracking
