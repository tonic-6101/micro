# Developer Guide

This guide covers Micro's architecture, extension points, and conventions for contributors.

## Architecture

Micro is a **Frappe-level app** — it depends only on Frappe, not on ERPNext or any other app.

```
Browser → Vue 3 SPA → Frappe REST API → Micro API → MariaDB
```

### Backend Structure

```
micro/
├── api/              # Whitelisted API endpoints (6 modules)
├── config/           # Frappe desk configuration
├── micro/
│   ├── doctype/      # 10 DocTypes (schemas + controllers)
│   └── print_format/ # PDF print formats
├── services/         # Business logic (compliance engine)
├── tests/            # API + DocType tests
├── hooks.py          # App configuration
└── install.py        # Post-install setup
```

### Frontend Structure

```
frontend/src/
├── pages/            # Page components (Vue 3 + TypeScript)
├── components/       # Reusable components (customers/, drafts/)
├── composables/      # Vue composition hooks (useTranslate)
├── types/            # TypeScript interfaces
├── utils/            # Utility functions
├── router.ts         # Vue Router configuration
├── main.ts           # Entry point
└── App.vue           # Root component
```

## DocTypes

Micro uses 9 DocTypes organized in two zones:

### Zone 1: The Organizer (no financial data)

| DocType | Controller | Description |
|---------|------------|-------------|
| Micro Customer | `micro_customer.py` | CRM customers |
| Micro Note | `micro_note.py` | Correspondence notes |

### Zone 2: Financial Draft Layer (guardrails enforced)

| DocType | Controller | Description |
|---------|------------|-------------|
| Micro Article | `micro_article.py` | Price catalog items |
| Micro Offer Draft | `micro_offer_draft.py` | Client-facing quotes |
| Micro Offer Item | *(child table)* | Offer line items |
| Micro Invoice Draft | `micro_invoice_draft.py` | Billing preparation docs |
| Micro Invoice Item | *(child table)* | Invoice line items |
| Micro Receipt | `micro_receipt.py` | Expense records |
| Micro Settings | `micro_settings.py` | Module configuration |

## Compliance Engine

The compliance engine (`micro/services/compliance.py`) enforces Zone 2 guardrails. All Zone 2 DocType controllers call these functions during validation:

```python
from micro.services.compliance import (
    generate_random_reference,   # G2: Non-sequential references
    get_watermark_text,          # G1: Draft watermark
    get_disclaimer_text,         # G4: Disclaimer footer
    validate_no_tax_fields,      # G3: No tax/VAT fields
)
```

### Reference Code Format

```
{PREFIX}-{YYYYMMDD}-{RANDOM4}
```

Examples: `OFF-20260315-X7K2`, `INV-20260315-M3P9`

References are checked for uniqueness and regenerated on collision (up to 10 attempts).

## API Conventions

All API endpoints follow these patterns:

- Defined in `micro/api/<module>.py`
- Decorated with `@frappe.whitelist()`
- Permission-checked via `frappe.has_permission()`
- Return dicts (Frappe serializes to JSON)
- List endpoints accept: `filters`, `search`, `order_by`, `limit_start`, `limit_page_length`
- List endpoints return: `{ <plural_name>: [...], total: int }`

## Hooks

Micro registers these hooks in `hooks.py`:

| Hook | Value | Description |
|------|-------|-------------|
| `after_install` | `micro.install.after_install` | Creates roles and settings defaults |
| `website_route_rules` | `/micro/<path:app_path>` → `micro` | SPA routing for Vue frontend |
| `add_to_apps_screen` | Micro entry | Shows Micro in Frappe's app switcher |

## Roles

| Role | Purpose |
|------|---------|
| Micro User | Standard access to all Micro DocTypes |
| Micro Manager | Extended access (same as User in v0.1.0) |

## Frontend Conventions

- All components use `<script setup lang="ts">` (TypeScript required)
- Translation: wrap strings with `__()` from `@/composables/useTranslate`
- Routing defined in `src/router.ts`
- Type definitions in `src/types/micro.ts`
- Built with Vite, styled with Tailwind CSS
- Uses FrappeUI component library

## Testing

Tests are located in `micro/tests/` and follow Frappe's test patterns:

```bash
# Run all Micro tests (inside Docker container)
bench run-tests --app micro

# Run a specific test module
bench run-tests --app micro --module micro.tests.test_api_customers
```

### Test Coverage

- **API tests** (`test_api_*.py`) — integration tests for all API modules
- **DocType tests** (`test_micro_*.py`) — unit tests for all DocTypes with logic
- **Compliance tests** (`test_compliance.py`) — guardrail enforcement validation

## Contributing

1. Fork the repository
2. Install pre-commit hooks: `cd apps/micro && pre-commit install`
3. Make your changes (Python: Ruff formatting, Frontend: ESLint + Prettier)
4. Run tests: `bench run-tests --app micro`
5. Submit a pull request

### Code Quality Tools

| Tool | Scope | Configuration |
|------|-------|---------------|
| Ruff | Python linting + formatting | `pyproject.toml` |
| ESLint | TypeScript/Vue linting | `.eslintrc` |
| Prettier | Code formatting | `.prettierrc` |
| pyupgrade | Python syntax modernization | pre-commit |

## License

Micro is licensed under [AGPL-3.0-or-later](../license.txt). All source files must include the SPDX license header:

```python
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic
```
