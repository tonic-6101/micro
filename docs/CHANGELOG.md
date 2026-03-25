# Changelog

All notable changes to Micro will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **In-SPA Customer Creation** — New Customer form page (`/micro/customers/new`) in the Vue frontend. Two-column layout with sections for basic info, contact details, address, and notes. Form adapts based on customer type: Person shows first name (required), last name (required), and optional organization; Organization shows company name (required). Replaces the previous redirect to Frappe Desk.
- **`create_customer` API** — New `POST micro.api.customers.create_customer` endpoint for creating customers programmatically. Accepts all customer fields. Validates that `last_name` is required for Person customers.
- **Customer Status Field** — New `status` field on Micro Customer with values: Potential, Active, Inactive. Allows tracking the customer lifecycle directly.

### Changed

- **Micro Contact renamed to Micro Customer** — The CRM entity is now called "Micro Customer" throughout the application. API module renamed from `micro.api.contacts` to `micro.api.customers`. Frontend routes changed from `/micro/contacts/*` to `/micro/customers/*`. Settings field renamed from `contact_limit` to `customer_limit`.
- **Customer form validation** — Last name is now required when creating Person customers (both frontend and backend validation).

### Removed

- **Lead Management** — Micro Lead DocType has been removed. Customer status tracking (Potential/Active/Inactive) replaces the separate lead concept.
- **Pipeline Board** — Micro Pipeline and Micro Pipeline Stage DocTypes have been removed along with the pipeline API (`micro.api.pipeline`) and the pipeline frontend page.

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
