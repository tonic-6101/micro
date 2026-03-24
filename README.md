# Micro

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![License](https://img.shields.io/badge/license-AGPL--3.0--or--later-green)
![Frappe](https://img.shields.io/badge/frappe-v16%2B-blue)
![Tests](https://img.shields.io/badge/tests-272%20passing-brightgreen)

**Business organizer for micro businesses.**

Micro manages the complete customer lifecycle: customer tracking with status management, article catalog, offer drafts, invoice drafts, receipt collection, and tax advisor export — all without crossing into regulated invoicing or bookkeeping territory.

Built on [Frappe Framework](https://frappeframework.com) with a Vue 3 frontend.

## Features

- **Customer Management** — CRM with status tracking (Potential/Active/Inactive), tasks, and notes
- **Article Catalog** — Price catalog with selling (VK) and purchase (EK) pricing
- **Offer Drafts** — Client-facing quotes with line items (watermarked, not legally binding)
- **Invoice Drafts** — Preparation documents for your tax advisor, with offer-to-invoice conversion
- **Receipt Collection** — Photo upload, 7 categories, and export tracking
- **Tax Advisor Export** — Semicolon-delimited CSV export with date/category filters
- **Dashboard** — KPI cards, customer status breakdown, recent activity feed, and alerts
- **Compliance Engine** — 6 guardrails ensure drafts stay drafts (G1–G6, 8 languages)
- **Internationalization** — Translated into 7 languages (DE, FR, ES, IT, PT, PL, NL)

## What Micro is NOT

Micro is **not** invoicing software, bookkeeping software, or ERP. It creates **draft documents only** — your tax advisor or bookkeeper handles the rest.

## Quick Start

```bash
bench get-app micro
bench --site your-site.localhost install-app micro
bench --site your-site.localhost migrate
bench build --app micro
```

Then visit `https://your-site.localhost/micro` to access the dashboard.

For detailed setup instructions, see the [Getting Started guide](docs/getting-started.md).

## Screenshots

The Micro frontend provides a clean, modern interface:

- **Dashboard** — KPI overview with customer status breakdown and recent activity
- **Customers** — CRM with status tracking, notes, and tasks
- **Export** — One-click CSV export for your tax advisor

## Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](docs/getting-started.md) | Installation, setup, first steps |
| [User Guide](docs/user-guide.md) | Workflows and day-to-day usage |
| [Customers](docs/customers.md) | CRM, status tracking, notes, tasks |
| [Articles](docs/articles.md) | Price catalog |
| [Drafts](docs/drafts.md) | Offer drafts and invoice drafts |
| [Receipts](docs/receipts.md) | Receipt collection |
| [Export](docs/export.md) | Tax advisor CSV export |
| [Configuration](docs/configuration.md) | Micro Settings |
| [API Reference](docs/api-reference.md) | All API endpoints |
| [Developer Guide](docs/developer-guide.md) | Architecture, testing, contributing |
| [FAQ](docs/faq.md) | Frequently asked questions |
| [Changelog](docs/CHANGELOG.md) | Release history |

## Tech Stack

- **Backend:** Python 3.14+ on Frappe v16
- **Frontend:** Vue 3 + TypeScript + Tailwind CSS + FrappeUI
- **Database:** MariaDB
- **Build:** Vite

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, code conventions, and how to submit changes.

This app uses `pre-commit` for code quality. Install hooks with:

```bash
cd apps/micro
pre-commit install
```

## Security

See [SECURITY.md](SECURITY.md) for our security policy and how to report vulnerabilities.

## License

AGPL-3.0-or-later — see [license.txt](license.txt)
