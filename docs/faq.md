# FAQ

## General

### What is Micro?

Micro is a business organizer for micro businesses. It manages the complete customer lifecycle: customer management, article catalog, offer drafts, invoice drafts, receipt collection, and tax advisor export.

### Is Micro invoicing software?

No. Micro creates **draft documents only** — preparation documents for your tax advisor. All drafts are watermarked and carry a disclaimer. Your tax advisor creates the actual, legally binding invoices.

### Is Micro bookkeeping software?

No. Micro does not do double-entry bookkeeping, profit/loss statements, balance sheets, or any regulated accounting functions. It is a business organizer that helps you collect and export data for your accountant or tax advisor.

### Does Micro handle taxes?

No. Micro does not calculate VAT, sales tax, or any tax amounts. Tax fields are intentionally excluded from all documents (compliance guardrail G3). Your tax advisor handles all tax-related work.

### Does Micro require ERPNext?

No. Micro depends only on Frappe (v15+). It is completely independent of ERPNext.

## Customers

### How many customers can I have?

The community edition supports up to 100 customers by default. This limit is configurable in Micro Settings.

### How many articles can I have?

The community edition supports up to 50 articles by default. This limit is configurable in Micro Settings.

### Can I import customers from a CSV?

Micro uses Frappe's standard data import functionality. You can import customers via the Frappe Desk import tool.

### What do the customer statuses mean?

Each customer has a status field with three values:

- **Potential** — A prospective customer you have not yet done business with
- **Active** — A customer you are currently working with
- **Inactive** — A customer you are no longer actively engaged with

## Drafts & Documents

### Why are my documents watermarked?

All offer drafts and invoice drafts display a draft watermark (e.g., "ENTWURF" or "DRAFT") to clearly indicate they are not legally binding documents. This is a compliance requirement and cannot be disabled.

### Why don't documents have sequential numbers?

Sequential numbering could make draft documents appear to be real invoices. Micro uses random reference codes (e.g., `OFF-20260315-X7K2`) to prevent this confusion. This is a compliance requirement.

### Can I create real invoices with Micro?

No. Micro only creates draft documents. For real invoicing, use dedicated invoicing software or have your tax advisor create invoices based on your Micro exports.

### What languages are supported for watermarks?

Draft watermarks and disclaimer footers are available in 8 languages: German, English, French, Spanish, Italian, Portuguese, Polish, and Dutch.

## Export

### What format does the export use?

Micro exports semicolon-delimited CSV files, compatible with common spreadsheet applications and accounting tools.

### Can I export to tax authorities directly?

No. Micro exports are designed for your tax advisor only. Direct submission to tax authorities is not supported and is outside Micro's scope.

### How do I track what I've already exported?

When exporting receipts, enable the "Mark as exported" option. Micro records the export date on each receipt. Next time, you can filter to show only unexported receipts.

## Technical

### How do I run Micro in development mode?

```bash
# Enter the container (if using Frappe Manager)
fm shell your-site.localhost

# Start the frontend dev server
cd apps/micro/frontend
npm install
npm run dev
```

### How do I run tests?

```bash
# Inside the Docker container
bench run-tests --app micro
```

### How do I clear the cache?

```bash
bench --site your-site.localhost clear-cache
```
