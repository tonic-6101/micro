# User Guide

Micro is a business organizer for micro businesses. This guide walks through the key workflows.

## Dashboard

The dashboard (`/micro`) shows a summary of your business at a glance:

- **Customer count** — total customers in your CRM, broken down by status
- **Open tasks** — to-do items needing attention
- **Offer stats** — offer drafts by status
- **Invoice draft stats** — invoice drafts by status
- **Receipt stats** — total receipts, unexported count, total amount, by category
- **Recent activity** — latest changes across all document types

## Managing Customers

### Adding a Customer

1. Go to **Customers** (`/micro/customers`)
2. Click **New Customer** — this opens the in-app customer form at `/micro/customers/new`
3. Choose **customer type**: **Person** or **Organization**
4. For **Person**: fill in first name (required) and last name (required), plus optional organization
5. For **Organization**: fill in company name (required)
6. Set the **status**: Potential (default), Active, or Inactive
7. Add contact details: email, phone, mobile, website
8. Add address: street, postal code, city, country
9. Add any notes
10. Click **Save Customer**

### Customer Detail

Click any customer to see their full profile, including:
- **Notes** — meeting notes, call logs, correspondence
- **Tasks** — to-do items for this customer

### Customer Status

Track where each customer is in their lifecycle:

- **Potential** — A prospective customer you have not yet worked with
- **Active** — A customer you are currently doing business with
- **Inactive** — A customer you are no longer actively engaged with

## Building Your Price Catalog

### Adding Articles

1. Go to **Articles** (`/micro/articles`)
2. Click **New Article**
3. Enter article name, code, category, and unit
4. Set selling price (VK) and purchase price (EK)
5. Save

Articles appear as options when you add line items to offer or invoice drafts.

## Creating Offer Drafts

Offer drafts are client-facing proposals. They are **not** legally binding — they carry a draft watermark and disclaimer.

### Creating an Offer

1. Go to **Offers** (`/micro/offers`)
2. Click **New Offer**
3. Select a **customer**
4. Add a **title** describing the offer
5. Add **line items** — select an article, set quantity and rate
6. Save

A random reference code is generated automatically (e.g., `OFF-20260315-X7K2`).

### Offer Statuses

- **Draft** — still being prepared
- **Sent** — shared with the client
- **Accepted** — client agreed
- **Declined** — client declined
- **Expired** — past the validity date

## Creating Invoice Drafts

Invoice drafts are preparation documents for your tax advisor. They gather the billing details; your tax advisor creates the actual, legally binding invoice.

### Creating an Invoice Draft

1. Go to **Invoice Drafts** (`/micro/invoice-drafts`)
2. Click **New Draft**
3. Select a **customer**
4. Add line items
5. Save

All invoice drafts display a prominent watermark ("ENTWURF" / "DRAFT") and a disclaimer footer.

## Collecting Receipts

### Adding a Receipt

1. Go to **Receipts** (`/micro/receipts`)
2. Click **New Receipt**
3. Upload a **photo** of the receipt
4. Enter vendor, amount, date, and category
5. Save

### Categories

Organize receipts by category: Materials, Travel, Office, Food, Software, Services, or Other.

## Exporting to Your Tax Advisor

### Generating a CSV Export

1. Go to **Export** (`/micro/export`)
2. Choose document type: **Receipts** or **Invoice Drafts**
3. Set a date range (optional)
4. For receipts: filter by category or unexported-only
5. Preview the count
6. Download the CSV file
7. Send the CSV to your tax advisor

### Tracking Exports

When exporting receipts, you can mark them as exported. This records the export date and helps you track which receipts have already been sent to your tax advisor.

## Settings

Go to **Settings** (`/micro/settings`) to configure:

- **Default currency** — used across all documents
- **Default language** — controls watermark and disclaimer language
- **Customer limit** — maximum customers (community edition: 100)
- **Article limit** — maximum articles (community edition: 50)
- **Watermark text** — customizable draft watermark
