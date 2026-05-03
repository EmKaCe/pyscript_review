#!/usr/bin/env python3
"""Download pure-Python wheels for PyScript compatibility.

Downloads py3-none-any wheels from PyPI to the static/ directory
for offline/local PyScript package loading.

Equivalent to per-package:
    pip download --only-binary=:all: --platform py3-none-any \\
        --python-version 3.13 --dest static/ <package>

Uses only stdlib + PyPI JSON API (no pip subprocess).
"""

import argparse
import json
import re
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
PYPROJECT_TOML = Path(__file__).resolve().parent.parent / "pyproject.toml"

DEFAULT_PACKAGES = [
    "pyyaml",
    "annotated-types",
    "typing-extensions",
    "puepy",
]


def read_version_specs():
    """Parse version specs from pyproject.toml [project] dependencies."""
    if not PYPROJECT_TOML.exists():
        return {}

    with open(PYPROJECT_TOML, "rb") as fh:
        data = tomllib.load(fh)

    specs: dict[str, str] = {}
    for dep in data.get("project", {}).get("dependencies", []):
        m = re.match(
            r"^([a-zA-Z][\w.\-]*(?:[\w]))\s*"
            r"((?:[><=!]+\s*[\w.*]+(?:\s*,\s*[><=!]+\s*[\w.*]+)*))",
            dep,
        )
        if m:
            specs[m.group(1).lower()] = m.group(2).strip()
    return specs


def _fetch_json(url: str) -> dict | None:
    """Fetch JSON from *url*. Returns None on HTTP 404 or network error."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "pyscript_review/2.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        print(f"  HTTP {exc.code} on {url}")
        return None
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
        print(f"  Network error: {exc}")
        return None


def _parts(v: str):
    """Split version string into comparable parts."""
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", v) if p]


def _satisfies(version: str, constraint: str | None) -> bool:
    """Check if version satisfies PEP-440 constraint (>=, <=, >, <, ==, !=)."""
    if not constraint:
        return True

    vp = _parts(version)

    for clause in constraint.split(","):
        clause = clause.strip()
        m = re.match(r"([><=!]+)\s*([\w.*]+)", clause)
        if not m:
            continue
        op, target = m.group(1), m.group(2)
        tp = _parts(target)

        cmp = 0
        for i in range(max(len(vp), len(tp))):
            a = (
                vp[i]
                if i < len(vp)
                else (0 if isinstance(tp[i] if i < len(tp) else 0, int) else "")
            )
            b = tp[i] if i < len(tp) else (0 if isinstance(a, int) else "")
            if a != b:
                cmp = -1 if a < b else 1
                break

        if op in (">=", ">"):
            if cmp < 0 or (op == ">" and cmp == 0):
                return False
        elif op in ("<=", "<"):
            if cmp > 0 or (op == "<" and cmp == 0):
                return False
        elif op == "==" and cmp != 0 or op == "!=" and cmp == 0:
            return False

    return True


def _releases(package: str):
    """Return (releases-dict, info-dict) for package, or (None, None)."""
    data = _fetch_json(f"https://pypi.org/pypi/{package}/json")
    if data is None:
        return None, None
    return data.get("releases", {}), data.get("info", {})


def find_pure_wheel(
    package: str,
    constraint: str | None = None,
) -> dict | None:
    """Find latest py3-none-any wheel matching version constraint."""
    releases, _ = _releases(package)
    if releases is None:
        return None

    sorted_versions = sorted(releases.keys(), key=_parts, reverse=True)

    for version in sorted_versions:
        if constraint and not _satisfies(version, constraint):
            continue
        for entry in releases.get(version, []):
            fn: str = entry.get("filename", "")
            if fn.endswith("py3-none-any.whl"):
                return {
                    "name": package,
                    "version": version,
                    "filename": fn,
                    "url": entry["url"],
                    "size": entry.get("size", 0),
                }
    return None


def _download(url: str, dest: Path) -> bool:
    """Stream url to dest with progress. Returns True on success."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "pyscript_review/2.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            got = 0
            print(f"  Downloading {dest.name} ...", end="", flush=True)
            with open(dest, "wb") as fh:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    fh.write(chunk)
                    got += len(chunk)
                    if total > 0:
                        pct = int(got * 100 / total)
                        print(f"\r  Downloading {dest.name} ... {pct}%", end="", flush=True)
            size_mb = dest.stat().st_size / (1024 * 1024)
            print(f"\r  Downloaded {dest.name} ({size_mb:.1f} MB)")
            return True
    except Exception as exc:
        print(f"\r  Failed: {exc}")
        if dest.exists():
            dest.unlink()
        return False


def cmd_list() -> None:
    """List wheels in static/ with sizes."""
    wheels = sorted(STATIC_DIR.glob("*.whl"))
    if not wheels:
        print(f"No wheel files found in {STATIC_DIR}/")
        return

    print(f"Wheels in {STATIC_DIR}/:")
    print(f"  {'Filename':<55} {'Size':>10}")
    print(f"  {'-' * 55} {'-' * 10}")
    total = 0
    for w in wheels:
        s = w.stat().st_size
        total += s
        label = f"{s / 1024:.0f} KB" if s < 1024**2 else f"{s / (1024 * 1024):.1f} MB"
        print(f"  {w.name:<55} {label:>10}")
    print(f"  {'-' * 55} {'-' * 10}")
    print(f"  {'Total':<55} {total / (1024 * 1024):.1f} MB")


def cmd_download(packages: list[str], dry_run: bool) -> int:
    """Download pure-Python wheels. Returns 0 on success, 1 if any failed."""
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    version_specs = read_version_specs()
    if version_specs:
        print(f"Version specs from {PYPROJECT_TOML.name}:")
        for name, spec in sorted(version_specs.items()):
            print(f"  {name}: {spec}")

    print(f"\nProcessing {len(packages)} package(s) ...")

    downloaded: list[str] = []
    skipped: list[str] = []
    unavailable: list[str] = []
    failed: list[str] = []

    for pkg in packages:
        constraint = version_specs.get(pkg.lower())
        label = constraint or "latest"
        print(f"\n  [{pkg}] (constraint: {label})")

        wheel = find_pure_wheel(pkg, constraint)
        if wheel is None:
            unavailable.append(pkg)
            if constraint:
                print(f"    No py3-none-any wheel satisfies '{constraint}'")
            else:
                print("    No py3-none-any wheel (likely platform-specific)")
            continue

        dest = STATIC_DIR / wheel["filename"]

        if dest.exists():
            skipped.append(pkg)
            print(f"    Already present: {wheel['filename']}")
            continue

        if dry_run:
            skipped.append(pkg)
            print(
                f"    [DRY-RUN] Would download: {wheel['filename']}  "
                f"(v{wheel['version']}, {wheel['size'] / 1024:.0f} KB)"
            )
            continue

        print(f"    Found: {wheel['filename']}")
        ok = _download(wheel["url"], dest)
        if ok:
            downloaded.append(pkg)
        else:
            failed.append(pkg)

    print()
    print("=" * 55)
    print("  SUMMARY")
    print("=" * 55)
    if downloaded:
        print(f"  Downloaded: {', '.join(downloaded)}")
    if skipped:
        print(f"  Skipped (up-to-date / dry-run): {', '.join(skipped)}")
    if unavailable:
        print(f"  No pure-Python wheel: {', '.join(unavailable)}")
    if failed:
        print(f"  FAILED: {', '.join(failed)}")
    if not any([downloaded, skipped, unavailable, failed]):
        print("  Nothing to do.")

    return 1 if failed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download pure-Python (py3-none-any) wheels from PyPI "
        "for PyScript offline/local loading.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be downloaded without actually fetching.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_",
        help="List currently available wheels in static/.",
    )
    parser.add_argument(
        "packages",
        nargs="*",
        help=f"Package(s) to check/download (default: {' '.join(DEFAULT_PACKAGES)}).",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.list_:
        cmd_list()
        return 0

    packages = args.packages or DEFAULT_PACKAGES
    return cmd_download(packages, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
