# Duplicate Detection

The same customer arrives twice more often than anyone expects: typed by hand on
Monday, imported from a supplier list on Friday, captured again through a web
form. Micro looks for those pairs and suggests merging them.

**Micro suggests, you decide.** Nothing is ever merged automatically, not even
on an identical email address.

## Where duplicates surface

| Surface | When |
|---------|------|
| **While creating a customer** | A card appears above the form as soon as the name, email or phone matches an existing contact. It never blocks the save — "Create anyway" dismisses it. |
| **Banner on the customer list** | *"3 possible duplicates found"* links to the review screen whenever open suggestions exist. |
| **Review screen** | `/micro/customers/duplicates` — one card per pair, with **Merge**, **Not a duplicate**, and a **Scan now** button. |
| **Import** | Rows are checked against existing contacts before they are created, using the key chosen in the import wizard. |

A background scan re-checks every contact once a day.

## What counts as a duplicate

Two contacts are compared only when they share something worth comparing — an
email, a phone number, a domain, a surname that sounds alike, or the start of a
company name. Everything is compared in normalized form:

| Written as | Compared as |
|------------|-------------|
| `Info@Müller-Bau.de`, `info+crm@mueller-bau.de` | `info@mueller-bau.de` |
| `+49 171 1234567`, `0049 171 1234567`, `(0171) 123 45 67` | the same last eight digits |
| `Müller`, `Mueller`, `Muller` | one name (Kölner Phonetik) |
| `Müller Bau GmbH`, `Müller Bau UG (haftungsbeschränkt)` | `müller bau` |

Matches are then scored and sorted into three bands:

| Band | Meaning |
|------|---------|
| **Certain** | A shared email or phone plus a matching name. |
| **Likely** | Strong agreement, worth a look. |
| **Possible** | Same name and little else — roughly what an iPhone suggests on. |

### What is deliberately *not* a duplicate

- **A shared switchboard.** Five employees on one company number are five people.
- **Franchise branches.** `hallo.solar Viersen` and `hallo.solar Wiehl` share a
  head-office number, a domain and every other word — the town separates them.
- **Branch offices.** `Remotex GmbH` and `Remotex GmbH (NL Kassel)` are two places.
- **A person and their company.** `Thomas Müller` is not `Müller GmbH`.
- **A shared free mail host.** Half a contact list is on gmx.de.

Spelling variants are *not* treated as differences: Meier and Maier are one
surname spelled two ways.

## Merging

Choose which record survives — the default is whichever carries more history.
The surviving contact keeps its own name; everything else is combined:

- Blank fields are filled from the other record. **Nothing already filled in is
  overwritten.**
- Conflicting emails and phone numbers are *both kept*, as additional entries.
- Notes are appended, with a line marking where they came from.
- Every linked lead, note, task, offer, invoice draft and receipt is repointed
  to the surviving contact.

Merging frees a slot under the Community customer limit.

> **Documents that have already been sent.** Offer and invoice drafts render the
> recipient live from the contact record. If the record being merged away is
> referenced by a document you have already sent, that document will show the
> surviving contact's details afterwards. The review screen warns you and gives
> the count before you merge.

### Undo

A merge can be undone for 30 days. Micro keeps a copy of the record it removed,
together with the list of documents it moved, and puts both back. Documents
linked to the surviving contact *after* the merge stay where they are.

## "Not a duplicate" sticks

Dismissing a suggestion stores a fingerprint of what the two records looked like.
The pair only comes back if one of them actually changes — editing an address or
adding a phone number can make Micro ask again, but a daily scan on its own
never will.

## Settings and scheduling

The daily scan runs as part of Micro's scheduled tasks
(`micro.api.duplicates.scan_for_duplicates`). It only ever looks at Micro's own
customers. The live check while typing is wider: it searches every contact on
the site, so a person another app already entered is found and adopted rather
than entered twice.

See [api-reference.md](api-reference.md) for the endpoints.
