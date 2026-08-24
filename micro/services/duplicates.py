# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Contact duplicate detection — normalize, block, score, band.

The same person arrives twice through four doors: typed by hand, imported from a
scrape, captured as a lead, or adopted from another Dock app. Nothing compared
them until now beyond one exact string match at import time, which cannot see
that `+49 171 1234567` and `0171 1234567` are one phone, or that Müller and
Mueller are one name.

Most duplicates die in normalization, before any similarity measure is involved.
The fuzzy part only has to catch what survives it.

No new dependencies: `difflib` is stdlib and the Cologne phonetic is forty lines.
At Community scale (100 contacts, imports up to a few thousand) that is ample —
reach for rapidfuzz only when a real site measures slow, not before.
"""

import hashlib
import re
from difflib import SequenceMatcher
from functools import lru_cache

import frappe

# Fields every comparison reads. Kept in one place because the live check, the
# full scan and the import path must all judge a contact by the same evidence.
CONTACT_FIELDS = (
	"name",
	"first_name",
	"last_name",
	"full_name",
	"company_name",
	"email_id",
	"phone",
	"mobile_no",
	"micro_contact_type",
	"micro_organization",
	"micro_status",
	"micro_website",
	"micro_address",
	"micro_postal_code",
)

# Score bands. Certain is the only band eligible for "merge all"; nothing is
# ever merged without a human saying so.
CERTAIN = 0.92
LIKELY = 0.75
POSSIBLE = 0.60

# Identity evidence — how much one shared strong identifier is worth on its own.
# Phone sits below the Certain line deliberately: a company switchboard number
# shared by five employees is the classic false positive of every CRM dedupe.
EMAIL_WEIGHT = 0.95
PHONE_WEIGHT = 0.85

# Supporting evidence, summed. An identical name alone reaches Possible, which
# is roughly what an iPhone suggests on — anything less would be noise.
NAME_WEIGHT = 0.45
EXACT_NAME_WEIGHT = 0.10
PHONETIC_WEIGHT = 0.15
ADDRESS_WEIGHT = 0.15
DOMAIN_WEIGHT = 0.10

# Negative evidence. A person and an organization are not the same record even
# when the names line up — "Thomas Müller" is not "Müller GmbH".
TYPE_PENALTY = 0.40
FIRST_NAME_PENALTY = 0.30
DISTINCT_TOKEN_PENALTY = 0.25
POSTCODE_PENALTY = 0.20

# Stripped before names are compared. Titles first, then the German legal forms:
# "Müller Bau GmbH" and "Müller Bau" are one company and must normalize alike.
TITLES = frozenset({"dr", "prof", "dipl", "ing", "med", "jur", "rer", "nat", "hc", "herr", "frau", "mr", "mrs", "ms"})
LEGAL_FORMS = frozenset(
	{
		"gmbh", "mbh", "ug", "haftungsbeschraenkt", "ag", "kg", "kgaa", "ohg", "gbr",
		"ek", "eg", "ev", "se", "gmbhcokg", "co", "und", "and", "ltd", "limited", "inc", "bv", "sa", "srl",
	}
)

# A branch is not a duplicate of its head office. These words appear on one side
# only — "Remotex GmbH" and "Remotex GmbH (NL Kassel)" share a name, a phone and
# a domain, and are two places.
BRANCH_MARKERS = frozenset({"nl", "niederlassung", "filiale", "zweigstelle", "standort"})

# Free mail hosts are not evidence of anything — half a contact list shares them.
GENERIC_DOMAINS = frozenset(
	{
		"gmail.com", "googlemail.com", "web.de", "gmx.de", "gmx.net", "gmx.at", "gmx.ch",
		"t-online.de", "freenet.de", "outlook.com", "outlook.de", "hotmail.com", "hotmail.de",
		"live.com", "live.de", "yahoo.com", "yahoo.de", "icloud.com", "me.com", "aol.com",
		"posteo.de", "mailbox.org", "protonmail.com", "proton.me",
	}
)

UMLAUTS = (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"))

HOUSE_NUMBER = re.compile(r"\b(\d+\s*[a-z]?)\b")
NON_ALNUM = re.compile(r"[^a-z0-9 ]+")
DIGITS = re.compile(r"\D")


# --- normalization ---------------------------------------------------------


@lru_cache(maxsize=8192)
def fold(value: str | None) -> str:
	"""Lowercase and transliterate German characters.

	This single rule is what makes Müller, Mueller and Muller one name, and it
	matters more here than any similarity metric — this is a German-market app.
	"""
	if not value:
		return ""

	text = str(value).strip().lower()
	for umlaut, replacement in UMLAUTS:
		text = text.replace(umlaut, replacement)

	return text


@lru_cache(maxsize=8192)
def normalize_email(value: str | None) -> str:
	"""Lowercase, trimmed, `+tag` removed — the forms one mailbox answers to."""
	text = fold(value)
	if "@" not in text:
		return ""

	local, _, domain = text.partition("@")
	local = local.partition("+")[0]

	return f"{local}@{domain}" if local and domain else ""


@lru_cache(maxsize=8192)
def email_domain(value: str | None) -> str:
	"""The domain of an email, unless everyone has it anyway."""
	domain = normalize_email(value).partition("@")[2]

	return "" if domain in GENERIC_DOMAINS else domain


@lru_cache(maxsize=8192)
def website_domain(value: str | None) -> str:
	"""Bare host of a website — `https://www.x.de/kontakt` is `x.de`."""
	text = fold(value)
	if not text:
		return ""

	text = re.sub(r"^[a-z]+://", "", text).partition("/")[0].partition("?")[0]
	text = text.removeprefix("www.")

	return "" if text in GENERIC_DOMAINS else text


@lru_cache(maxsize=8192)
def phone_key(value: str | None) -> str:
	"""Comparable form of a phone number: its last eight digits.

	`+49 171 1234567`, `0049 171 1234567` and `0171 1234567` all end in the same
	eight digits, so the trailing slice collapses every prefix and separator
	convention at once without needing a parsing library. Numbers shorter than
	eight digits are compared whole.
	"""
	digits = DIGITS.sub("", str(value or ""))
	if len(digits) < 5:
		# Too short to identify anyone — an extension, not a number.
		return ""

	return digits[-8:]


@lru_cache(maxsize=8192)
def normalize_name(value: str | None) -> str:
	"""Folded, punctuation-free, titles removed."""
	text = NON_ALNUM.sub(" ", fold(value))
	tokens = [token for token in text.split() if token and token not in TITLES]

	return " ".join(tokens)


@lru_cache(maxsize=8192)
def normalize_organization(value: str | None) -> str:
	"""A company name without its legal form.

	Falls back to the untouched name when stripping would leave nothing — the
	company actually called "Co" must not normalize to the empty string and
	match every other stripped-to-nothing record.
	"""
	tokens = [token for token in normalize_name(value).split() if token not in LEGAL_FORMS]

	return " ".join(tokens) or normalize_name(value)


def postal_key(record: dict) -> str:
	"""Postcode plus house number — enough to tell two Müllers apart."""
	postcode = DIGITS.sub("", str(record.get("micro_postal_code") or ""))
	if not postcode:
		return ""

	match = HOUSE_NUMBER.search(fold(record.get("micro_address")))

	return f"{postcode}-{match.group(1).replace(' ', '')}" if match else ""


def display_name(record: dict) -> str:
	"""The name to compare on, whichever field the record actually carries."""
	full = record.get("full_name") or " ".join(
		part for part in (record.get("first_name"), record.get("last_name")) if part
	)

	if (record.get("micro_contact_type") or "") == "Organization":
		return normalize_organization(full or record.get("company_name"))

	return normalize_name(full)


# --- Cologne phonetic ------------------------------------------------------


@lru_cache(maxsize=8192)
def cologne_phonetic(word: str | None) -> str:
	"""Kölner Phonetik (Postel, 1969) — Soundex's German counterpart.

	MariaDB ships `SOUNDEX()`, but it is built for English and collapses German
	names wrongly, so the codes are computed here instead. Müller, Mueller and
	Muller all encode to 657.
	"""
	text = "".join(char for char in fold(word) if char.isalpha() and char.isascii()).upper()
	if not text:
		return ""

	codes: list[str] = []
	for index, char in enumerate(text):
		previous = text[index - 1] if index else ""
		following = text[index + 1] if index + 1 < len(text) else ""

		if char in "AEIJOUY":
			code = "0"
		elif char == "B":
			code = "1"
		elif char == "P":
			code = "3" if following == "H" else "1"
		elif char in "DT":
			code = "8" if following in "CSZ" else "2"
		elif char in "FVW":
			code = "3"
		elif char in "GKQ":
			code = "4"
		elif char == "C":
			if not index:
				code = "4" if following in "AHKLOQRUX" else "8"
			else:
				code = "8" if previous in "SZ" else ("4" if following in "AHKOQUX" else "8")
		elif char == "X":
			code = "8" if previous in "CKQ" else "48"
		elif char == "L":
			code = "5"
		elif char in "MN":
			code = "6"
		elif char == "R":
			code = "7"
		elif char in "SZ":
			code = "8"
		else:
			# H carries no code of its own; it only modifies its neighbours.
			continue

		codes.append(code)

	collapsed: list[str] = []
	for digit in "".join(codes):
		if not collapsed or collapsed[-1] != digit:
			collapsed.append(digit)

	if not collapsed:
		# A name of nothing but H — the one letter that carries no code of its own.
		return ""

	# Zero marks a vowel: informative as an initial, noise everywhere else.
	return collapsed[0] + "".join(digit for digit in collapsed[1:] if digit != "0")


def phonetic_key(record: dict) -> str:
	"""Phonetic code of the part of the name that identifies the record."""
	if (record.get("micro_contact_type") or "") == "Organization":
		organization = normalize_organization(record.get("full_name") or record.get("company_name"))

		return cologne_phonetic(organization.split(" ")[0] if organization else "")

	return cologne_phonetic(record.get("last_name") or (display_name(record).split(" ") or [""])[-1])


# --- blocking --------------------------------------------------------------


def blocking_keys(record: dict) -> set[str]:
	"""Keys that make a record worth comparing to another.

	Two contacts are only ever scored when they share at least one of these, so
	the scan stays linear in practice instead of comparing every pair with every
	other pair. A key that identifies nothing is left out rather than becoming a
	bucket that half the database falls into.
	"""
	keys: set[str] = set()

	email = normalize_email(record.get("email_id"))
	if email:
		keys.add(f"e:{email}")

	for field in ("phone", "mobile_no"):
		phone = phone_key(record.get(field))
		if phone:
			keys.add(f"p:{phone}")

	domain = email_domain(record.get("email_id")) or website_domain(record.get("micro_website"))
	if domain:
		keys.add(f"d:{domain}")

	phonetic = phonetic_key(record)
	if phonetic:
		keys.add(f"k:{phonetic}")

	name = display_name(record)
	if name:
		keys.add(f"f:{name}")
	if len(name) >= 4:
		keys.add(f"n:{name[:4]}")

	return keys


# --- scoring ---------------------------------------------------------------


def _similarity(left: str, right: str) -> float:
	"""Order-insensitive string similarity — "Bau Müller" matches "Müller Bau"."""
	if not left or not right:
		return 0.0
	if left == right:
		return 1.0

	sorted_left = " ".join(sorted(left.split()))
	sorted_right = " ".join(sorted(right.split()))

	return max(
		SequenceMatcher(None, left, right).ratio(),
		SequenceMatcher(None, sorted_left, sorted_right).ratio(),
	)


def _distinguishing_tokens(left: str, right: str) -> bool:
	"""Whether both names carry a word the other one genuinely lacks.

	This is what tells a franchise apart from a duplicate. Five branches of
	`hallo.solar` share a head office phone number, a domain and every word of a
	long marketing name; the only thing separating them is the town — Viersen,
	Wiehl, Aachen. Without this they score as one contact on every other signal.

	Tokens that merely *sound* different are not distinguishing: Meier and Maier
	are one surname spelled two ways, and phonetically equal words cancel out
	before the leftovers are counted.
	"""
	def significant(name: str) -> set[str]:
		# Short words carry no meaning of their own — except the branch markers,
		# where the whole signal is two letters long ("NL Kassel").
		return {
			token
			for token in name.split()
			if token not in LEGAL_FORMS and (len(token) >= 3 or token in BRANCH_MARKERS)
		}

	left_tokens = significant(left)
	right_tokens = significant(right)

	left_only = left_tokens - right_tokens
	right_only = right_tokens - left_tokens

	# A branch marker on one side alone is decisive even though nothing sits
	# opposite it, which is exactly the case the rule below would wave through.
	if (left_only | right_only) & BRANCH_MARKERS:
		return True

	if not left_only or not right_only:
		# One name is the other plus extra words — an abbreviation, not a
		# different business.
		return False

	right_sounds = {cologne_phonetic(token) for token in right_only}
	left_only = {token for token in left_only if cologne_phonetic(token) not in right_sounds}

	left_sounds = {cologne_phonetic(token) for token in left_only}
	right_only = {token for token in right_only if cologne_phonetic(token) not in left_sounds}

	return bool(left_only and right_only)


def _belongs_to(person: dict, organization: dict) -> bool:
	"""Whether the first record is a member of the second."""
	link = person.get("micro_organization")

	return bool(link) and link == organization.get("name")


def _phones(record: dict) -> set[str]:
	"""Every number on a record, landline and mobile alike.

	Compared as one set on purpose: the same number is routinely typed into the
	phone field on one record and the mobile field on the other.
	"""
	return {key for key in (phone_key(record.get("phone")), phone_key(record.get("mobile_no"))) if key}


def score_pair(left: dict, right: dict) -> tuple[float, list[str]]:
	"""How strongly two contacts look like one contact, and on what evidence.

	Identity evidence sets a floor; supporting evidence fills the headroom that
	is left (a noisy-OR). Two weak agreements therefore never add up to the
	certainty of one shared email, and one shared email is never dragged below
	the line by a differently spelled name.
	"""
	signals: list[str] = []

	# A person and the organization they belong to share a name, an address, a
	# domain and often a switchboard number. The relation states outright that
	# they are two records on purpose, which beats every signal below it.
	if _belongs_to(left, right) or _belongs_to(right, left):
		return 0.0, ["-same_organization"]

	identity = 0.0
	left_email = normalize_email(left.get("email_id"))
	if left_email and left_email == normalize_email(right.get("email_id")):
		identity = EMAIL_WEIGHT
		signals.append("email")

	if _phones(left) & _phones(right):
		identity = max(identity, PHONE_WEIGHT)
		signals.append("phone")

	support = 0.0
	left_name = display_name(left)
	right_name = display_name(right)
	name_similarity = _similarity(left_name, right_name)
	if name_similarity > 0.5:
		support += NAME_WEIGHT * name_similarity
		signals.append("name")

	# Names that survive normalization *identically* say more than names that
	# merely score high: "Müller Bau GmbH" and "Müller Bau" are one company once
	# the legal form is gone, while "Meier" and "Maier" only look alike.
	if left_name and right_name == left_name and len(left_name) >= 6:
		support += EXACT_NAME_WEIGHT
		signals.append("exact_name")

	left_phonetic = phonetic_key(left)
	if left_phonetic and left_phonetic == phonetic_key(right):
		support += PHONETIC_WEIGHT
		signals.append("phonetic")

	left_postal = postal_key(left)
	if left_postal and left_postal == postal_key(right):
		support += ADDRESS_WEIGHT
		signals.append("address")

	left_domain = email_domain(left.get("email_id")) or website_domain(left.get("micro_website"))
	right_domain = email_domain(right.get("email_id")) or website_domain(right.get("micro_website"))
	if left_domain and left_domain == right_domain:
		support += DOMAIN_WEIGHT
		signals.append("domain")

	score = identity + support * (1 - identity)

	left_type = left.get("micro_contact_type") or ""
	right_type = right.get("micro_contact_type") or ""
	if left_type and right_type and left_type != right_type:
		score -= TYPE_PENALTY
		signals.append("-type")

	if left_type == right_type == "Person":
		left_first = normalize_name(left.get("first_name"))
		right_first = normalize_name(right.get("first_name"))
		if left_first and right_first and _similarity(left_first, right_first) < 0.5:
			score -= FIRST_NAME_PENALTY
			signals.append("-first_name")

	if _distinguishing_tokens(left_name, right_name):
		score -= DISTINCT_TOKEN_PENALTY
		signals.append("-distinct_name")

	# Two postcodes that disagree outweigh a shared switchboard: a head office
	# number says the branches belong to one company, not that they are one
	# record. Names that are *identical* after normalization are exempt — a
	# business that moved, or a record carrying the older address, is a duplicate
	# and not a second company.
	if "exact_name" not in signals:
		left_postcode = DIGITS.sub("", str(left.get("micro_postal_code") or ""))
		right_postcode = DIGITS.sub("", str(right.get("micro_postal_code") or ""))
		if left_postcode and right_postcode and left_postcode != right_postcode:
			score -= POSTCODE_PENALTY
			signals.append("-postcode")

	return max(0.0, min(1.0, score)), signals


def band_for(score: float) -> str | None:
	"""Which review bucket a score falls in, or None when it is not worth asking."""
	if score >= CERTAIN:
		return "Certain"
	if score >= LIKELY:
		return "Likely"
	if score >= POSSIBLE:
		return "Possible"

	return None


def fingerprint(left: dict, right: dict) -> str:
	"""Stable hash of what a pair was judged on.

	A dismissal has to stick — re-suggesting a pair the user already rejected is
	the failure that makes people switch these features off. It sticks until one
	of the two records materially changes, which is exactly what this covers.
	"""
	parts = []
	for record in sorted((left, right), key=lambda item: item.get("name") or ""):
		parts.append(
			"|".join(
				(
					record.get("name") or "",
					display_name(record),
					normalize_email(record.get("email_id")),
					",".join(sorted(_phones(record))),
					postal_key(record),
				)
			)
		)

	return hashlib.sha256("||".join(parts).encode()).hexdigest()


# --- candidate lookup ------------------------------------------------------


class ContactIndex:
	"""Every Micro contact, bucketed by blocking key, held for one scan.

	One query instead of one per row. An import of 3,000 rows used to issue 3,000
	`exists()` calls; now it issues one and adds each new contact to the index as
	it is created, so rows still dedupe against their own file.
	"""

	def __init__(self, records: list[dict] | None = None, micro_only: bool = True):
		self.records: dict[str, dict] = {}
		self.buckets: dict[str, set[str]] = {}

		for record in records if records is not None else load_contacts(micro_only=micro_only):
			self.add(record)

	def add(self, record: dict) -> None:
		name = record.get("name")
		if not name:
			return

		self.records[name] = record
		for key in blocking_keys(record):
			self.buckets.setdefault(key, set()).add(name)

	def candidates(self, record: dict, exclude: str | None = None) -> list[dict]:
		"""Records sharing at least one blocking key with this one."""
		names: set[str] = set()
		for key in blocking_keys(record):
			names |= self.buckets.get(key, set())

		names.discard(exclude)
		names.discard(record.get("name"))

		return [self.records[name] for name in names if name in self.records]

	def matches(self, record: dict, exclude: str | None = None, minimum: float = POSSIBLE) -> list[dict]:
		"""Scored candidates above a threshold, strongest first."""
		results = []
		for candidate in self.candidates(record, exclude=exclude):
			score, signals = score_pair(record, candidate)
			if score >= minimum:
				results.append({"contact": candidate, "score": round(score, 3), "signals": signals})

		results.sort(key=lambda item: item["score"], reverse=True)

		return results


def load_contacts(micro_only: bool = True) -> list[dict]:
	"""Contacts to compare against.

	`micro_only` is the difference between two questions. Suggesting merges is
	Micro's own housekeeping, so the scan stays inside its own customers — the
	Contact doctype is shared with Helo, Orga and the rest, and Micro has no
	business proposing to fuse records it does not own. Deciding whether a
	contact *already exists* is the other question, and there the answer has to
	include every contact on the site: a person another app already entered is
	adopted, not entered a second time.

	`get_all` rather than `get_list`: the caller is permission checked before it
	gets here, and a duplicate the user cannot read is still a duplicate that
	splits their history and skews their health scores.
	"""
	return frappe.get_all(
		"Contact",
		filters={"micro_status": ["is", "set"]} if micro_only else None,
		fields=list(CONTACT_FIELDS),
	)


def find_pairs(index: ContactIndex | None = None) -> list[dict]:
	"""All duplicate pairs in the database, each reported once.

	Pairs are keyed on the sorted contact names so that scoring A against B and
	B against A yields one suggestion, not two mirrored ones.
	"""
	index = index or ContactIndex()
	seen: dict[tuple[str, str], dict] = {}

	for name, record in index.records.items():
		for match in index.matches(record):
			other = match["contact"]["name"]
			key = (name, other) if name < other else (other, name)
			if key in seen:
				continue

			band = band_for(match["score"])
			if not band:
				continue

			seen[key] = {
				"contact_a": key[0],
				"contact_b": key[1],
				"score": match["score"],
				"band": band,
				"signals": match["signals"],
				"fingerprint": fingerprint(index.records[key[0]], index.records[key[1]]),
			}

	return sorted(seen.values(), key=lambda pair: pair["score"], reverse=True)
