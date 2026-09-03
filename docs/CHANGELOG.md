# Changelog

All notable changes to Micro will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.5] - 2026-08-25

### Added

- **Lead distance on board cards** — each Kanban card shows how far the lead is from its follow-up date, so an overdue deal is visible without opening it.

### Fixed

- `company_name` now has a real default (`My Business`), so **Micro Settings** can actually be created during install instead of failing on a required empty field.
- CI: fetch required apps before installing Micro, install frontend npm dependencies before `bench build`, skip the asset build inside `get-app`, match Python and Node to `platform.json`, and install an unversioned `mariadb-client`.
- Two tests that only passed on an already-seeded site now pass on a fresh one.

## [0.1.4] - 2026-08-24

The customer-lifecycle release. CRM data now lives on Frappe **Contact**; `Micro Customer` is retained only as a legacy DocType.

### Added

- **Segments and organizations** — contacts get a durable `Micro Segment` (a target group, independent of any single deal's pipeline stage) and an `micro_organization` link, so a person and the company they write under stay related without merging their identities.
- **Remove vs. erase** — deleting a customer is split in two: *remove* clears Micro membership and leaves every document in place; *erase* destroys the record and is **refused while a retention obligation still points at it**. Both offer a preview of what would happen, plus a bulk variant for acting on several customers from the list view.
- **Call attempts** — `Micro Call Attempt` logs when a contact was called and whether it landed (Reached / No Answer / Voicemail / Busy / Wrong Number). Attempts hang off the contact, not one lead, so a pattern of when somebody actually answers builds up across every deal. A "best time to reach" hint appears once enough attempts exist.
- **Configurable pipelines** — pipelines and stages move from a fixed default to something the user configures: reorderable stages, per-stage won/lost outcomes, and a Pipeline Manager dialog that avoids the Desk entirely. `pipeline_limit` joins the Community-edition caps.
- **Kanban board rework** — drag-to-reorder and richer cards (`KanbanCard` / `KanbanColumn`).
- **Lead lifecycle and trash** — `Micro Lead` becomes a real record separate from the contact it is about, with archive / restore / delete. An archived lead is the app's trash: kept whole and restorable rather than gone.
- **Call list** — surfaces whoever is due a follow-up today.
- **Duplicate detection and merge review** — a daily scan scores likely-duplicate contact pairs on name, email, phone and address signals, storing them as `Micro Duplicate Pair` banded Certain / Likely / Possible. The Duplicates page reviews each pair side by side and shows how much history (leads, notes, offers, invoices, receipts) hangs off each side, so the survivor is chosen with the stakes visible. Merges can be undone.
- **CSV contact import** — paste or upload a CSV, map columns to contact fields, then import. Rows are inserted server-side with deduplication against existing contacts; a failing row is reported individually instead of failing the batch.
- **Field help everywhere** — `FieldLabel` + a shared glossary explain each labelled field on hover; `InlineField` allows one-click inline edits.
- **Server-booted limits** — a shared limits module sends the current caps (max expected value, article limit) to the frontend instead of hardcoding them per page.

### Fixed

- Dashboard KPIs, the annual wrapped summary, and the health-score recalculation trigger still queried the removed `Micro Customer` DocType; they now read `Contact` + `micro_status`.
- Health-score recalculation is skipped during bulk import. A CSV import saves thousands of contacts in a row, and one queued job per row exceeded Frappe's pending-job ceiling, which started failing the inserts themselves. The nightly scheduler recalculates every score anyway.

## [0.1.3] - 2026-04-15

### Added

- **Moments** — emotional-design milestones: offer-accepted celebration, first-offer-sent acknowledgement, and an annual "wrapped" summary, each dismissible.
- **Article categories** — `Micro Article Category` DocType with a category picker.
- **Creation flows in the SPA** — new pages for creating articles (`ArticleNew`, `ArticleDetail`) and offers (`OfferNew`).
- **`micro.api.jana_briefing`** — exposes Micro's daily numbers to the Jana assistant and to Dock's briefing panel via the `jana_briefing_source` hook.

## [0.1.2] - 2026-03-27

### Added

- **Micro Task, Micro Lead and Micro Pipeline re-introduced.** These had been removed in 0.1.1; the spec requires them as Zone 1 features, so they are back — see *Corrections* below.
  - `Micro Task` — simple to-dos linked to contacts and leads
  - `Micro Lead` — pipeline deals with expected value and follow-up tracking
  - `Micro Pipeline` — parent container for stages (Community limit: 1)
  - `Micro Pipeline Stage` — gains a pipeline link plus `is_win_stage` / `is_loss_stage`
- **Capacity widget** — workload visualisation on the dashboard, backed by `micro.api.capacity`.
- **Guardrail G5** — blocks forbidden invoice terminology in document titles.
- **Guardrail G6** — blocks payment-based statuses (Paid / Bezahlt and equivalents).

### Changed

- **Contact migration** — Micro Customer fields move to a Frappe Contact link (`contact_type` → `micro_contact_type`; email and phone become linked fields). Pipeline, customer and offer pages follow the Contact-based model.

### Corrections

> An earlier draft of this changelog stated that Lead Management and the Pipeline Board had
> been **removed** and that customer status tracking replaced them. That was true only
> between 0.1.1 and 0.1.2. Both were re-introduced in 0.1.2 and have been expanded
> substantially since — configurable pipelines, a Kanban board, lead archiving and a call
> list all shipped in 0.1.4. `Micro Lead`, `Micro Pipeline` and `Micro Pipeline Stage` are
> current, supported DocTypes.

## [0.1.1] - 2026-03-25

### Added

- **Dock integration** — app-level design tokens and a settings bridge, so Micro renders inside the ecosystem shell.

### Removed

- **Micro Task** — moved to Orga. (Reversed in 0.1.2, which brought the DocType back.)

### Changed

- README rewritten to match the ecosystem app format.

## [0.1.0] - 2026-02-27

First public release of Micro — a business organizer for micro businesses.

### Added

- **Customer Management** — Micro Customer DocType with person/organization support, status tracking (Potential/Active/Inactive), full name auto-computation, email validation, phone, mobile, website, address, city, postal code, country, notes, source, and image fields. Paginated list, detail, and create API endpoints with search. Community limit: 100 customers.
- **Notes** — Micro Note DocType for context notes and correspondence records linked to customers.
- **Article Catalog** — Micro Article DocType with article name, code, category, unit, selling price (VK), and purchase price (EK). Paginated list and detail API with search. Community limit: 50 articles.
- **Offer Drafts** — Micro Offer Draft DocType with line items (Micro Offer Item), random reference codes (non-sequential), customer linking, status tracking (Draft, Sent, Accepted, Declined, Expired), date and validity tracking. Watermarked PDF print format.
- **Invoice Drafts** — Micro Invoice Draft DocType with line items (Micro Invoice Item), random reference codes, customer linking, and status tracking. Create-from-offer flow copies items automatically. Watermarked PDF print format.
- **Receipt Collection** — Micro Receipt DocType with vendor, amount, category (Materials, Travel, Office, Food, Software, Services, Other), image upload, receipt date, export tracking, and customer linking.
- **Tax Advisor Export** — CSV export for receipts and invoice drafts with semicolon delimiter. Supports date range filtering, category filtering, unexported-only filtering. Mark-as-exported functionality with export date tracking.
- **Dashboard** — Aggregated KPI endpoint with customer count by status, offer/invoice status breakdown, receipt stats (total, unexported, by category, total amount), and recent activity feed.
- **Compliance Engine** — Zone 2 guardrail enforcement service with 6 guardrails: G1 (draft watermark in 8 languages), G2 (random reference codes), G3 (no tax/VAT fields), G4 (disclaimer footer in 8 languages), G5 (safe terminology), G6 (no payment tracking).
- **Settings** — Micro Settings (Single DocType) for module configuration: default currency, language, customer/article limits, watermark text, disclaimer text.
- **Print Formats** — Watermarked PDF print formats for offer drafts and invoice drafts with ENTWURF/DRAFT overlay and disclaimer footer.
- **Roles** — Micro User and Micro Manager roles created on install.
- **Vue Frontend** — Vue 3 SPA with TypeScript: Dashboard (KPIs, recent activity, alerts), Customers (list + new + detail), Tasks, Articles, Offers (list + detail), Invoice Drafts (list + detail), Receipts, Export wizard, Settings. Grouped sidebar navigation (CRM, Documents, Tools).
- **Internationalization** — 7 language translations: German, French, Spanish, Italian, Portuguese, Polish, Dutch. Translation infrastructure with `useTranslate` composable for frontend and `frappe._()` for backend.
- **Post-Install Setup** — Automatic role creation and settings defaults (EUR, German).
- **Test Suite** — Tests covering all DocTypes, API endpoints, compliance guardrails, and business logic.
- **Documentation** — Getting started guide, user guide, API reference, developer guide, and FAQ.
