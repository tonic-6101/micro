# Bundled data

## `plz_centroids.csv`

One row per German postal code: `PLZ,latitude,longitude` (WGS84), 10,813 rows.

Used by `micro/services/distance.py` to answer "how far away is this lead"
without sending a single customer address to a third party. See that module
for why the lookup is offline rather than a geocoding API.

Where a PLZ appears several times in the source (large-volume postal codes are
listed once per assigned organisation), the rows are averaged into one centroid.
Coordinates are rounded to four decimals — roughly 11 m, far finer than the
postal-code granularity itself justifies.

### Source and licence

Derived from the [GeoNames](https://www.geonames.org/) postal code export
(`DE.zip`), which is published under the
[Creative Commons Attribution 4.0 licence](https://creativecommons.org/licenses/by/4.0/).
Attribution to GeoNames is required and is carried in the app's about page.

Regenerate with:

```bash
curl -sSLO https://download.geonames.org/export/zip/DE.zip && unzip -o DE.zip
python3 - <<'PY'
import collections, csv
acc = collections.defaultdict(list)
for row in csv.reader(open("DE.txt", encoding="utf-8"), delimiter="\t"):
    if len(row) < 11:
        continue
    plz, lat, lon = row[1].strip(), row[9].strip(), row[10].strip()
    if plz.isdigit() and len(plz) == 5 and lat and lon:
        acc[plz].append((float(lat), float(lon)))
with open("plz_centroids.csv", "w", encoding="utf-8", newline="") as out:
    w = csv.writer(out)
    for plz in sorted(acc):
        pts = acc[plz]
        w.writerow([plz, round(sum(p[0] for p in pts) / len(pts), 4),
                         round(sum(p[1] for p in pts) / len(pts), 4)])
PY
```

**Do not** regenerate this file from the Google Geocoding API. Google's terms
allow caching latitude/longitude for 30 days only, which rules out shipping
them in a repository — this is also why the widely mirrored `plz_geocoord`
dataset, despite its Apache-2.0 label, is not used here.
