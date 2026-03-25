# Micro

**Business Organizer for Micro Businesses**

[![Version](https://img.shields.io/badge/version-0.1.1-blue.svg)](https://github.com/tonic-6101/micro/releases)
[![Frappe](https://img.shields.io/badge/frappe-v16+-green.svg)](https://frappeframework.com)
[![License](https://img.shields.io/badge/license-AGPL--3.0-orange.svg)](LICENSE)

Micro manages the complete customer lifecycle for micro businesses: customer tracking with status management, article catalog, offer drafts, invoice drafts, receipt collection, and tax advisor export — all without crossing into regulated invoicing or bookkeeping territory.

---

## Features

### Customer Management

Track your customers from first contact to long-term relationship with a simple, effective CRM.

- Customer profiles with contact details and notes
- Status tracking through lifecycle stages (Potential, Active, Inactive)
- Customer detail view with linked offers, invoices, and receipts
- Quick-add for new customers

### Article Catalog

Maintain a price catalog for the products and services you offer.

- Selling price (VK) and purchase price (EK) per article
- Reusable across offers and invoice drafts
- Simple list management

### Offer Drafts

Create client-facing quotes to share with potential customers — watermarked and clearly marked as non-binding.

- Line items pulled from the article catalog
- Watermarked output to signal draft status
- Not legally binding — preparation documents only

### Invoice Drafts

Prepare invoice documents for your tax advisor or bookkeeper. Micro handles the draft; your professional handles the rest.

- Offer-to-invoice conversion with one click
- Line items with quantities and pricing
- Compliance guardrails ensure drafts stay drafts (G1–G6)
- Clearly labeled as preparation documents

### Receipt Collection

Photograph and organize your business receipts for easy handoff at tax time.

- Photo upload from camera or file
- Seven receipt categories for organization
- Export tracking to know what's been sent
- Date and category filtering

### Tax Advisor Export

Export your data as semicolon-delimited CSV files ready for your tax advisor's workflow.

- One-click CSV export
- Date and category filters
- Structured format for professional handoff

### Dashboard

See your business at a glance with KPI cards, charts, and activity feeds.

- KPI cards for key metrics
- Customer status breakdown
- Recent activity feed
- Alerts for items needing attention

### Compliance Engine

Six built-in guardrails ensure Micro stays in its lane — draft documents only, no regulated invoicing.

- Guardrails G1–G6 enforced automatically
- Translated compliance messages in 8 languages
- Clear separation between drafts and legal documents

### Internationalization

Use Micro in your language.

- Translated into 7 languages: German, French, Spanish, Italian, Portuguese, Polish, Dutch
- Compliance messages available in 8 languages

### Dock Integration

When [Dock](https://github.com/tonic-6101/dock) is installed, Micro integrates into the ecosystem navigation and settings.

- App registered in the Dock app switcher
- Settings accessible from Dock settings panel

---

## What Micro is NOT

Micro is **not** invoicing software, bookkeeping software, or ERP. It creates **draft documents only** — your tax advisor or bookkeeper handles the rest.

---

## Installation

### Prerequisites

- Frappe Framework v16 or higher
- Python 3.14+
- Node.js 24+
- MariaDB 10.6+
- [Dock](https://github.com/tonic-6101/dock) (required dependency)

### Install via Bench

```bash
# Get the app
bench get-app micro https://github.com/tonic-6101/micro.git

# Install on your site
bench --site your-site.localhost install-app micro

# Run migrations
bench --site your-site.localhost migrate

# Build assets
bench build --app micro
```

### Access the Application

After installation, access Micro at: `https://your-site.localhost/micro`

---

## Quick Start

1. **Add Customers**: Create your first customer profiles
2. **Build Your Catalog**: Add articles with selling and purchase prices
3. **Create an Offer**: Draft a quote for a customer
4. **Convert to Invoice Draft**: Turn accepted offers into invoice preparation documents
5. **Collect Receipts**: Photograph and categorize your business receipts
6. **Export**: Send CSV exports to your tax advisor

---

## Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](docs/getting-started.md) | Installation, setup, first steps |
| [User Guide](docs/user-guide.md) | Workflows and day-to-day usage |
| [Customers](docs/customers.md) | CRM, status tracking, notes |
| [API Reference](docs/api-reference.md) | All API endpoints |
| [Developer Guide](docs/developer-guide.md) | Architecture, testing, contributing |
| [Changelog](docs/CHANGELOG.md) | Release history |

---

## Technology Stack

- **Backend**: Frappe Framework, Python 3.14+
- **Frontend**: Vue 3, TypeScript, Tailwind CSS
- **UI Components**: FrappeUI
- **Database**: MariaDB
- **Build**: Vite

---

## Contributing

Contributions are welcome! This project uses `pre-commit` for code formatting and linting:

```bash
cd apps/micro
pre-commit install
```

Pre-commit runs the following tools automatically:

- **ruff** — Python linting and formatting
- **eslint** — TypeScript/JavaScript linting
- **prettier** — Code formatting
- **pyupgrade** — Python syntax modernization

---

## Support

- **Issues**: [GitHub Issues](https://github.com/tonic-6101/micro/issues)
- **Discussions**: [GitHub Discussions](https://github.com/tonic-6101/micro/discussions)

---

## License

GNU Affero General Public License v3.0 (AGPL-3.0)

See [LICENSE](LICENSE) for details.

```
SPDX-License-Identifier: AGPL-3.0-or-later
Copyright (C) 2024-2026 Tonic
```

---

## Acknowledgments

Built with [Frappe Framework](https://frappeframework.com) and [FrappeUI](https://github.com/frappe/frappe-ui).
