# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""How far away a lead sits, in kilometres.

The answer has to appear on every card of a board that may hold thousands of
them, so it is worked out from a postal code against a table shipped with the
app — no geocoding request, no API key, no rate limit, and no customer address
leaving the installation. That last point is the deciding one: a tradesperson's
contact list is personal data, and handing 7,000 German addresses to a
geocoding service to learn a rough distance is not a trade worth making.

The rejected alternatives, for the next person who wonders:

- **Nominatim** caps at one request per second and asks that long-running bulk
  jobs stay under four per minute. A first pass over an imported list would run
  for hours, and it still ships every address to a third party.
- **Google Geocoding** permits caching coordinates for 30 days, then requires
  deleting them — so the distances would silently expire, and the widely
  mirrored `plz_geocoord` dataset built from it cannot be redistributed either.

What this buys in exchange for the compromise below: distances resolve
instantly, offline, for the 98% of contacts that carry a German postal code.

**This is straight-line distance** — Luftlinie, not driving distance. Roads are
longer than the crow flies, typically by a fifth to a third, and more in the
hills. It answers "is this lead nearby or across the country", which is the
question a board is asking; it does not answer "how long is the drive".
Anything better needs a routing engine and a request per pair, which is exactly
what a board full of cards cannot afford.
"""

import csv
import math
import os
from functools import lru_cache

import frappe

# Mean Earth radius (IUGG). The error against a proper ellipsoidal calculation
# is well under a kilometre at German distances — far below the precision a
# postal-code centroid can honestly claim anyway.
EARTH_RADIUS_KM = 6371.0088

_CENTROID_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "plz_centroids.csv")


@lru_cache(maxsize=1)
def _centroids() -> dict[str, tuple[float, float]]:
	"""The postal-code table, read once per process.

	Roughly 10,800 rows. Small enough to hold in memory, and cheap enough that
	caching it anywhere more elaborate would cost more than it saves.
	"""
	table: dict[str, tuple[float, float]] = {}

	try:
		with open(_CENTROID_FILE, encoding="utf-8", newline="") as handle:
			for row in csv.reader(handle):
				if len(row) != 3:
					continue
				try:
					table[row[0]] = (float(row[1]), float(row[2]))
				except ValueError:
					continue
	except OSError:
		# A missing data file must not take the board down with it — every
		# distance simply goes unknown.
		frappe.log_error("Micro: postal code centroids missing", _CENTROID_FILE)

	return table


def _postal_code(value: str | None) -> str | None:
	"""A German postal code, or nothing.

	Five digits is what the table holds. A four-digit code is Austrian or Swiss
	and `micro_country` is unset on nearly every imported contact, so there is
	no way to tell 8032 Zürich from 8032 anywhere else — those stay unknown
	rather than being answered wrongly.
	"""
	code = (value or "").strip()

	return code if len(code) == 5 and code.isdigit() else None


def centroid(postal_code: str | None) -> tuple[float, float] | None:
	"""Where a postal code sits, as (latitude, longitude)."""
	code = _postal_code(postal_code)

	return _centroids().get(code) if code else None


def haversine_km(origin: tuple[float, float], target: tuple[float, float]) -> float:
	"""Great-circle distance between two (latitude, longitude) pairs."""
	lat1, lon1 = math.radians(origin[0]), math.radians(origin[1])
	lat2, lon2 = math.radians(target[0]), math.radians(target[1])

	inner = (
		math.sin((lat2 - lat1) / 2) ** 2
		+ math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
	)

	return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(inner))


def origin_centroid() -> tuple[float, float] | None:
	"""Where the business itself sits — the point everything is measured from.

	Absent until somebody fills in the company postal code under Micro Settings,
	and every distance stays unknown until they do.
	"""
	return centroid(frappe.db.get_single_value("Micro Settings", "company_postal_code"))


def distance_km(postal_code: str | None, origin: tuple[float, float] | None = None) -> int | None:
	"""Straight-line kilometres from the business to a postal code.

	Whole kilometres: a postal code covers a town, so a decimal place would be
	claiming a precision the input never had. Pass `origin` when annotating a
	batch, so the settings lookup happens once rather than per row.
	"""
	origin = origin if origin is not None else origin_centroid()
	if not origin:
		return None

	target = centroid(postal_code)
	if not target:
		return None

	return round(haversine_km(origin, target))


def attach_distance(
	rows: list[dict],
	postal_field: str = "micro_postal_code",
	target_field: str = "distance_km",
) -> None:
	"""Annotate rows in place with their distance from the business.

	One settings lookup for the whole batch, then a dict lookup and a little
	arithmetic per row — cheap enough to run on every board fetch.
	"""
	if not rows:
		return

	origin = origin_centroid()

	for row in rows:
		if row is None:
			continue
		row[target_field] = distance_km(row.get(postal_field), origin) if origin else None
