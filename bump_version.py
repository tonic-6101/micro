#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Version bump script — updates all version references in a single command.
Also audits platform requirements (Frappe, Python, Node, MariaDB) across
all docs and code to catch stale references after a platform migration.

Usage:
    python3 bump_version.py 0.4.0          # explicit version
    python3 bump_version.py patch          # 0.3.0 → 0.3.1
    python3 bump_version.py minor          # 0.3.0 → 0.4.0
    python3 bump_version.py major          # 0.3.0 → 1.0.0
    python3 bump_version.py --from-changelog
    python3 bump_version.py 0.4.0 --dry-run
    python3 bump_version.py --check-platform          # audit only
    python3 bump_version.py 0.4.0 --check-platform    # bump + audit
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def detect_app_name() -> str:
    for child in ROOT.iterdir():
        if child.is_dir() and (child / "hooks.py").exists():
            return child.name
    return ROOT.name


def read_current_version() -> str:
    version_file = ROOT / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()
    return "0.0.0"


def parse_semver(v: str) -> tuple[int, int, int]:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", v)
    if not match:
        raise ValueError(f"Invalid semver: {v}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def bump_level(current: str, level: str) -> str:
    major, minor, patch = parse_semver(current)
    if level == "patch":
        return f"{major}.{minor}.{patch + 1}"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    if level == "major":
        return f"{major + 1}.0.0"
    raise ValueError(f"Unknown level: {level}")


def get_changelog_version() -> str | None:
    changelog = ROOT / "docs" / "CHANGELOG.md"
    if not changelog.exists():
        return None
    match = re.search(r"##\s*\[(\d+\.\d+\.\d+)\]", changelog.read_text())
    return match.group(1) if match else None


def validate_version(v: str) -> bool:
    return bool(re.match(r"^\d+\.\d+\.\d+(-[\w.]+)?$", v))


def update_file(path: Path, pattern: str, replacement: str, label: str, dry_run: bool) -> bool:
    if not path.exists():
        print(f"  SKIP  {label} (not found)")
        return False
    content = path.read_text()
    new_content, count = re.subn(pattern, replacement, content, count=1)
    if count == 0:
        print(f"  SKIP  {label} (pattern not matched)")
        return False
    if dry_run:
        print(f"  OK    {label} (dry-run)")
        return True
    path.write_text(new_content)
    print(f"  OK    {label}")
    return True


def read_platform() -> dict[str, str]:
    """Read canonical platform requirements from platform.json."""
    platform_file = ROOT / "platform.json"
    if not platform_file.exists():
        return {}
    return json.loads(platform_file.read_text())


# Patterns that match stale platform references in docs/code.
# Each entry: (key in platform.json, regex that captures the version part, description)
PLATFORM_PATTERNS: list[tuple[str, str, str]] = [
    ("frappe", r"[Ff]rappe[\s_-]*v(\d+)", "Frappe version"),
    ("frappe", r"frappe-v(\d+)\+", "Frappe badge"),
    ("python", r"Python\s+(\d+\.\d+)", "Python version"),
    ("node", r"Node(?:\.?js)?\s+(\d+)", "Node version"),
    ("mariadb", r"MariaDB\s+(\d+\.\d+)", "MariaDB version"),
]


def audit_platform(dry_run: bool = True) -> int:
    """Scan all .md files and README for stale platform references.

    Returns the number of stale references found.
    """
    platform = read_platform()
    if not platform:
        print("  SKIP  platform audit (no platform.json)")
        return 0

    stale_count = 0
    scan_globs = ["*.md", "docs/*.md", "docs/**/*.md"]
    files: set[Path] = set()
    for g in scan_globs:
        files.update(ROOT.glob(g))

    for fpath in sorted(files):
        content = fpath.read_text()
        rel = fpath.relative_to(ROOT)
        for key, pattern, desc in PLATFORM_PATTERNS:
            expected = platform.get(key)
            if not expected:
                continue
            for m in re.finditer(pattern, content):
                found = m.group(1)
                if found != expected:
                    stale_count += 1
                    action = "WOULD FIX" if dry_run else "FIX"
                    print(f"  {action}  {rel}: {desc} {found} → {expected}")
                    if not dry_run:
                        content = content[:m.start(1)] + expected + content[m.end(1):]
        if not dry_run:
            fpath.write_text(content)

    if stale_count == 0:
        print("  OK    All platform references match platform.json")
    return stale_count


def update_json(path: Path, key: str, version: str, label: str, dry_run: bool) -> bool:
    if not path.exists():
        print(f"  SKIP  {label} (not found)")
        return False
    data = json.loads(path.read_text())
    old = data.get(key)
    data[key] = version
    if dry_run:
        print(f"  OK    {label}  {old} → {version} (dry-run)")
        return True
    path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"  OK    {label}  {old} → {version}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Bump version across all app files")
    parser.add_argument("version", nargs="?",
                        help="New version (e.g. 0.4.0) or level (patch/minor/major)")
    parser.add_argument("--from-changelog", action="store_true",
                        help="Read version from latest CHANGELOG.md entry")
    parser.add_argument("--check-platform", action="store_true",
                        help="Audit docs for stale platform requirements (from platform.json)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without writing")
    args = parser.parse_args()

    # Platform-only audit (no version bump needed)
    if args.check_platform and not args.version and not args.from_changelog:
        print("\nPlatform requirements audit\n")
        stale = audit_platform(dry_run=args.dry_run)
        sys.exit(1 if stale and args.dry_run else 0)

    app_name = detect_app_name()
    current = read_current_version()

    # Determine target version
    if args.from_changelog:
        new_version = get_changelog_version()
        if not new_version:
            print("Error: no version found in docs/CHANGELOG.md")
            sys.exit(1)
    elif args.version in ("patch", "minor", "major"):
        new_version = bump_level(current, args.version)
    elif args.version:
        new_version = args.version
    else:
        parser.print_help()
        sys.exit(1)

    if not validate_version(new_version):
        print(f"Error: '{new_version}' is not valid semver")
        sys.exit(1)

    if new_version == current and not args.dry_run:
        print(f"Already at {current}")
        sys.exit(0)

    mode = " (dry-run)" if args.dry_run else ""
    print(f"\n{app_name}: {current} → {new_version}{mode}\n")

    results = []

    # 1. VERSION
    results.append(update_file(
        ROOT / "VERSION",
        r"^\d+\.\d+\.\d+\S*",
        new_version,
        "VERSION", args.dry_run,
    ))

    # 2. __init__.py
    results.append(update_file(
        ROOT / app_name / "__init__.py",
        r'__version__\s*=\s*"[^"]+"',
        f'__version__ = "{new_version}"',
        f"{app_name}/__init__.py", args.dry_run,
    ))

    # 3. frontend/package.json
    results.append(update_json(
        ROOT / "frontend" / "package.json",
        "version", new_version,
        "frontend/package.json", args.dry_run,
    ))

    # 4. README.md — version badge (handles both blue and green badge styles)
    results.append(update_file(
        ROOT / "README.md",
        r'version-[\d.]+-(?:blue|green)\.svg("?\s*alt="Version:\s*[\d.]+")?',
        f'version-{new_version}-blue.svg',
        "README.md badge", args.dry_run,
    ))

    # 5. README.md — alt text (if present, e.g. Watch style)
    readme = ROOT / "README.md"
    if readme.exists() and 'alt="Version:' in readme.read_text():
        results.append(update_file(
            readme,
            r'alt="Version:\s*[^"]*"',
            f'alt="Version: {new_version}"',
            "README.md alt text", args.dry_run,
        ))

    # 6. setup.py (legacy, if present)
    setup_py = ROOT / "setup.py"
    if setup_py.exists():
        results.append(update_file(
            setup_py,
            r'version\s*=\s*"[^"]+"',
            f'version="{new_version}"',
            "setup.py", args.dry_run,
        ))

    ok = sum(1 for r in results if r)
    total = len(results)
    print(f"\n{'[dry-run] ' if args.dry_run else ''}Updated {ok}/{total} targets to {new_version}")

    # Always audit platform requirements during a bump
    if read_platform():
        print("\nPlatform requirements audit\n")
        audit_platform(dry_run=args.dry_run)

    if not args.dry_run:
        print(f"\n  git add -p && git commit -m 'chore: bump version to {new_version}'")


if __name__ == "__main__":
    main()
