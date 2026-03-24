# Getting Started

## Requirements

- Frappe v16 or later
- Python 3.14+
- MariaDB
- Node.js 24+

## Installation

### Using Frappe Bench

```bash
# Get the app
bench get-app micro

# Install on your site
bench --site your-site.localhost install-app micro

# Run migrations
bench --site your-site.localhost migrate

# Build frontend assets
bench build --app micro
```

### Using Frappe Manager (Docker)

If you use Frappe Manager, run commands inside the container:

```bash
# Enter the container
fm shell your-site.localhost

# Inside the container:
bench --site your-site.localhost install-app micro
bench --site your-site.localhost migrate
bench build --app micro
```

## What Happens on Install

When Micro is installed on a site, it automatically:

1. **Creates roles** — `Micro User` and `Micro Manager`
2. **Sets up defaults** — Micro Settings with EUR currency, German language, 100-customer limit, 50-article limit, and "ENTWURF" watermark

## Accessing Micro

After installation, access the Micro frontend at:

```
https://your-site.localhost/micro
```

The Vue SPA handles all routing under `/micro/*`:

| URL | Page |
|-----|------|
| `/micro` | Dashboard |
| `/micro/customers` | Customer list |
| `/micro/customers/new` | New customer form |
| `/micro/customers/:id` | Customer detail |
| `/micro/tasks` | Task list |
| `/micro/articles` | Article catalog |
| `/micro/offers` | Offer drafts |
| `/micro/offers/:id` | Offer detail |
| `/micro/invoice-drafts` | Invoice draft list |
| `/micro/invoice-drafts/:id` | Invoice draft detail |
| `/micro/receipts` | Receipt list |
| `/micro/export` | Tax advisor export |
| `/micro/settings` | Module settings |

## First Steps

1. **Configure settings** — Go to `/micro/settings` and set your preferred currency and language
2. **Add customers** — Create your first customers at `/micro/customers`
3. **Add articles** — Build your price catalog at `/micro/articles`
4. **Create offers** — Draft your first offer at `/micro/offers`

## Roles and Permissions

| Role | Access |
|------|--------|
| **Micro User** | Full CRUD access to all Micro DocTypes |
| **Micro Manager** | Full CRUD access to all Micro DocTypes |

Assign either role to users who need access to Micro.
