"""
Week 1 - EXTRACT
================
Copy the three NHS GP appointment files into data/raw/, convert the Excel
file to CSV, and write data/raw/manifest.json.

Rules this script follows
  * The raw copy is never edited. The Excel file is converted, but the
    original is also kept untouched in data/raw/original/.
  * Every file gets a SHA-256 checksum and a row count, so any later change
    to the raw data is detectable.
  * Re-running is safe: a file that is already in place with the same
    checksum is skipped; a different one stops the run unless --force.

Usage (from the project root)
    python src/extract.py --source data/source
    python src/extract.py --source /content/drive/MyDrive/LSA_Oct2026/raw   # Colab

Source: NHS England, Appointments in General Practice.
"""
import argparse
import csv
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# The three datasets: name used downstream -> (file-name stem, extension).
# Matching on the stem tolerates names like 'appointments_regional_1.csv' or
# 'national_categories (1).csv' that browsers create when a file is downloaded twice.
DATASETS = {
    "appointments_regional": ("appointments_regional", ".csv"),
    "national_categories": ("national_categories", ".csv"),
    # TRAP 1: despite the name, this is an Excel workbook, not a CSV.
    "actual_duration": ("actual_duration", ".xlsx"),
}

# Row counts the course guide says we must get (used as a sanity check).
EXPECTED_ROWS = {
    "appointments_regional": 596_821,
    "national_categories": 817_394,
    "actual_duration": 137_793,
}


def sha256_of(path: Path) -> str:
    """Checksum a file in 1 MB chunks (so big files don't fill memory)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def count_csv_rows(path: Path) -> int:
    """Count data rows (header excluded) using a real CSV parser.

    'utf-8-sig' swallows the byte-order mark (TRAP 2), and the csv module
    copes with quoted fields containing line breaks, which `wc -l` does not.
    """
    with open(path, newline="", encoding="utf-8-sig") as f:
        return sum(1 for _ in csv.reader(f)) - 1


def has_bom(path: Path) -> bool:
    with open(path, "rb") as f:
        return f.read(3) == b"\xef\xbb\xbf"


def find_source(source: Path, stem: str, ext: str) -> Path:
    """Find the one file in `source` that starts with `stem` and ends with `ext`."""
    hits = sorted(p for p in source.glob(f"{stem}*{ext}") if p.is_file())
    if not hits:
        sys.exit(f"Missing from {source}: a file like {stem}*{ext}")
    if len(hits) > 1:
        sys.exit(f"More than one match for {stem}*{ext} in {source}: "
                 f"{[h.name for h in hits]}. Keep one.")
    return hits[0]


def copy_raw(src: Path, dest: Path, force: bool) -> None:
    """Copy src to dest without ever silently overwriting different data."""
    if dest.exists():
        if sha256_of(dest) == sha256_of(src):
            print(f"  already in place, identical: {dest.name}")
            return
        if not force:
            sys.exit(f"STOP: {dest} exists and differs from the source. "
                     "Raw data is never overwritten; use --force if you are sure.")
    shutil.copyfile(src, dest)   # not copy2: copying metadata can fail on Databricks Volumes


def convert_excel_to_csv(xlsx: Path, csv_path: Path) -> None:
    """TRAP 1: Spark cannot read Excel, so convert it with pandas.

    Codes are read as text so a code such as '07L' keeps its leading zero,
    and dates are written as ISO yyyy-mm-dd so no tool can misread them.
    """
    df = pd.read_excel(
        xlsx,
        dtype={"sub_icb_location_code": str, "sub_icb_location_ons_code": str,
               "icb_ons_code": str, "region_ons_code": str},
    )
    df["appointment_date"] = pd.to_datetime(df["appointment_date"]).dt.strftime("%Y-%m-%d")
    df.to_csv(csv_path, index=False, encoding="utf-8")


def extract(source: Path, raw: Path, force: bool = False) -> dict:
    raw.mkdir(parents=True, exist_ok=True)
    original = raw / "original"
    original.mkdir(exist_ok=True)

    sources = {name: find_source(source, stem, ext) for name, (stem, ext) in DATASETS.items()}

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    files = []
    for name, src in sources.items():
        filename = src.name
        print(f"{name}: {filename}")
        entry = {"dataset": name, "source_file": filename,
                 "source_sha256": sha256_of(src)}

        if src.suffix.lower() == ".xlsx":
            copy_raw(src, original / filename, force)       # untouched original
            raw_file = raw / f"{name}.csv"
            print("  Excel file -> converting to CSV")
            convert_excel_to_csv(src, raw_file)
            entry["converted_from"] = filename
            entry["note"] = "Excel workbook converted to CSV; dates written as yyyy-mm-dd."
        else:
            raw_file = raw / f"{name}.csv"   # always the clean name, whatever the source was called
            copy_raw(src, raw_file, force)
            if has_bom(raw_file):
                entry["note"] = ("Starts with a UTF-8 byte-order mark; strip it "
                                 "from the first column name in transform.")

        rows = count_csv_rows(raw_file)
        entry.update({
            "raw_file": raw_file.as_posix(),
            "size_bytes": raw_file.stat().st_size,
            "sha256": sha256_of(raw_file),
            "row_count": rows,
            "extracted_at_utc": now,
        })
        files.append(entry)
        flag = "OK" if rows == EXPECTED_ROWS[name] else f"MISMATCH (expected {EXPECTED_ROWS[name]:,})"
        print(f"  {rows:,} rows  {flag}")

    manifest = {
        "source": "NHS England, Appointments in General Practice",
        "licence_note": "Check the publication terms page; normally Open Government Licence v3.0.",
        "files": files,
    }
    (raw / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nWrote {raw / 'manifest.json'}")
    return manifest


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Extract the three GP appointment files.")
    ap.add_argument("--source", type=Path, default=Path("data/source"),
                    help="folder holding the three downloaded files")
    ap.add_argument("--raw", type=Path, default=Path("data/raw"))
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    extract(a.source, a.raw, a.force)
