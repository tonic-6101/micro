# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability in Micro, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, email security concerns to: **tonic@example.com**

Include:

- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

We aim to acknowledge reports within 48 hours and provide a fix or mitigation within 7 days for critical issues.

## Security Considerations

### Authentication & Authorization

Micro relies on Frappe's built-in authentication and permission system. All API endpoints are decorated with `@frappe.whitelist()` and check user permissions via `frappe.has_permission()`.

### Data Handling

- Micro stores contacts, leads, and draft documents — no passwords, payment credentials, or sensitive financial data
- Receipt images are stored via Frappe's file system with standard access controls
- CSV exports are generated server-side and delivered to authenticated users only

### Compliance Architecture

Micro is designed as a business organizer, not invoicing or bookkeeping software. The compliance engine enforces guardrails that prevent Micro from being used as a regulated financial system:

- No sequential invoice numbering
- No tax/VAT calculations
- No payment tracking
- All financial documents are clearly marked as drafts

### Dependencies

Micro depends only on Frappe (v15+). Frontend dependencies are managed via yarn with a lock file. We recommend keeping Frappe and all dependencies up to date.
