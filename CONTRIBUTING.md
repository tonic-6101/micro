# Contributing to Micro

Thank you for considering a contribution to Micro. This guide explains how to set up your development environment and submit changes.

## Code of Conduct

Be respectful, constructive, and inclusive. We follow the [Contributor Covenant](https://www.contributor-covenant.org/) code of conduct.

## Getting Started

### Prerequisites

- Frappe v15 or later
- Python 3.10+
- Node.js 18+
- MariaDB

### Development Setup

1. **Fork and clone** the repository
2. **Install on a Frappe bench site:**
   ```bash
   bench get-app micro /path/to/your/fork
   bench --site your-site.localhost install-app micro
   ```
3. **Install pre-commit hooks:**
   ```bash
   cd apps/micro
   pre-commit install
   ```
4. **Run the frontend dev server:**
   ```bash
   cd apps/micro/frontend
   yarn install
   yarn dev
   ```

### Using Frappe Manager (Docker)

If you use Frappe Manager, all bench/npm commands must run inside the container:

```bash
fm shell your-site.localhost
# Then run commands inside the container
```

## Making Changes

### Branch Naming

- `feat/<short-description>` — new features
- `fix/<short-description>` — bug fixes
- `docs/<short-description>` — documentation updates
- `refactor/<short-description>` — code refactoring

### Commit Messages

Use the format: `type(scope): description`

```
feat(zone-1): add contact search by city
fix(zone-2): correct offer total calculation
docs(api): update export endpoint parameters
refactor(frontend): extract shared currency formatter
```

### Code Quality

Pre-commit hooks enforce these tools automatically:

| Tool | Scope | Configuration |
|------|-------|---------------|
| Ruff | Python linting + formatting | `pyproject.toml` |
| ESLint | TypeScript/Vue linting | `.eslintrc` |
| Prettier | Code formatting | `.prettierrc` |
| pyupgrade | Python syntax modernization | pre-commit |

### TypeScript Requirement

All frontend code must use TypeScript. Vue components require `<script setup lang="ts">`.

### Translation

All user-facing strings must be wrapped for translation:

- **Frontend:** `__('String')` from `@/composables/useTranslate`
- **Backend:** `_('String')` from `frappe`

### License Headers

All source files must include the AGPL-3.0 SPDX header:

**Python:**
```python
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic
```

**TypeScript:**
```typescript
// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Tonic
```

**Vue:**
```vue
<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
```

## Compliance

Micro has a two-zone architecture. Before implementing features that involve financial data (Zone 2), review the compliance guardrails:

- **G1:** Draft watermark on all financial documents
- **G2:** No sequential numbering (random reference codes only)
- **G3:** No tax/VAT fields
- **G4:** Disclaimer footer on all financial documents
- **G5:** Safe terminology ("Draft", never "Invoice" alone)
- **G6:** No payment tracking

Zone 2 features require extra care. If unsure whether your change affects compliance, open an issue to discuss before submitting a PR.

## Testing

Run the full test suite before submitting:

```bash
bench run-tests --app micro
```

Run a specific test module:

```bash
bench run-tests --app micro --module micro.tests.test_api_contacts
```

Current test count: 267 tests.

## Submitting Changes

1. Push your branch to your fork
2. Open a pull request against `main`
3. Describe what your change does and why
4. Reference any related issues
5. Ensure all tests pass

## Reporting Issues

Use [GitHub Issues](https://github.com/AgeneLabs/micro/issues) to report bugs or request features. Include:

- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Frappe version and Python version
- Browser and OS (for frontend issues)

## Questions

For general questions about Micro's architecture or conventions, see the [Developer Guide](docs/developer-guide.md).
