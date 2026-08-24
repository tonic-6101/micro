# Micro — Repository Guidelines

Micro is a business organizer for micro businesses in the Tonic ecosystem (Layer 2). It depends on Dock (Layer 1) for ecosystem integration.

```
Layer 0  Frappe Core
Layer 1  Dock          ← required dependency
Layer 2  Micro         ← this app
```

## Stack

- **Backend:** Frappe v16+, Python 3.14+, MariaDB
- **Frontend:** Vue 3 SPA + TypeScript + Tailwind CSS + FrappeUI

## Dependencies

- `frappe` (framework)
- `dock` (coordination layer — required)

## Build & Development Commands

```bash
# Frontend development (HMR, instant feedback)
cd frontend && npm install && npm run dev

# Production build (only before pushing)
bench build --app micro

# Backend
bench --site <site> migrate
bench run-tests --app micro
bench --site <site> clear-cache
```

**During development, always use `npm run dev`.** Only run `bench build` when preparing to push.

## Coding Style

### TypeScript (mandatory for frontend)

All new code in `frontend/src/` must be TypeScript (`.ts` or `<script lang="ts">`).

### License Headers

```python
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic
```

```typescript
// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic
```

```vue
<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
```

Exceptions: JSON, Markdown, config files, auto-generated files.

### Field Help — Every Label Explains Itself

Ecosystem rule (`spec/design/unified-design.md`). No labelled point ships as bare
text: fields, table headers, filters and status badges all explain themselves on
hover.

```vue
<FieldLabel field="expected_value" :label="__('Expected Value')" />
```

- Wording lives in `frontend/src/glossary.ts`, keyed by fieldname — written once,
  reused everywhere. No entry yet? Write one; don't drop the label.
- The label is the hover target. No `?` badge, no `ⓘ` icon — a mark on every row
  is clutter, and `cursor: help` says it already.
- Say what the field does for the user, not what it is: "The board sums these per
  column" beats "the expected value".
- Where the DocType field carries a `description` in `hooks.py`, repeat it
  verbatim so the Desk and the app agree.
- Never `title="..."` for an explanation — slow, unstyleable, unreachable by
  keyboard. It stays fine for text that merely overflows.
- Hint strings are translated like any other string.

### Translation (i18n)

All user-facing strings must be wrapped for translation:

```typescript
import { __ } from '@/composables/useTranslate'
```

```python
from frappe import _
```

After adding strings, update all CSV files in `micro/translations/`.

## Dock Integration

Micro registers with Dock's app switcher, search, and notifications via hook declarations in `hooks.py`. No direct import of Dock code — use the hook system only.

## Commit Guidelines

```
feat(scope): description
fix(scope): description
docs(scope): description
refactor(scope): description
```

## Git Workflow

- Remote: `upstream` | Default branch: `develop`
- **Always** specify remote and branch: `git push upstream develop`
- **Always** pull before push: `git pull upstream develop --rebase`
- **Never** force push unless explicitly requested

### Preparing a Push

```bash
bench build --app micro                    # 1. Build frontend (if changed)
bench --site <site> clear-cache            # 2. Clear cache
python3 bump_version.py patch              # 3. Bump version
git add -A && git commit -m "feat: ..."    # 4. Commit
git pull upstream develop --rebase         # 5. Pull
git push upstream develop                  # 6. Push
```

### Version Files

`bump_version.py` updates all — never edit just one:

| File | Controls |
|------|----------|
| `VERSION` | Canonical source |
| `micro/__init__.py` | `__version__` |
| `pyproject.toml` | `version` |
| `frontend/package.json` | `"version"` |

## Frappe v16 — Known Issues

- Single DocType `issingle` flag may not sync during migrate — fix via SQL
- Default sort order is `creation` (not `modified`) — always specify sort explicitly
- `has_permission` hooks must return explicit `True`
- State-changing methods require POST (not GET)

## Multi-Agent Safety

- Do **not** create/apply/drop `git stash` entries unless explicitly requested
- Do **not** switch branches unless explicitly requested
- When you see unrecognized files, focus on your changes and leave others untouched

## Dependency Safety

- Exact versions for patched dependencies (no `^` or `~`)
- Patching dependencies requires explicit maintainer approval

## Bug Investigation

- Read source code of relevant dependencies before concluding
- Aim for high-confidence root cause, not surface-level fixes
