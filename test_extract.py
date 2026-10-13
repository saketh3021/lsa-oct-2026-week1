"""Checks on the Week 1 extract. Run `python src/extract.py` first, then `pytest`."""
import hashlib
import json
from pathlib import Path

import pytest

RAW = Path("data/raw")
EXPECTED = {"appointments_regional": 596_821,
            "national_categories": 817_394,
            "actual_duration": 137_793}


@pytest.fixture(scope="module")
def manifest():
    path = RAW / "manifest.json"
    if not path.exists():
        pytest.skip("run src/extract.py first")
    return {f["dataset"]: f for f in json.loads(path.read_text())["files"]}


def test_all_three_datasets_listed(manifest):
    assert set(manifest) == set(EXPECTED)


@pytest.mark.parametrize("name,rows", EXPECTED.items())
def test_row_counts(manifest, name, rows):
    assert manifest[name]["row_count"] == rows


@pytest.mark.parametrize("name", EXPECTED)
def test_checksum_matches_file(manifest, name):
    """If anyone edits a raw file, its checksum no longer matches the manifest."""
    path = Path(manifest[name]["raw_file"])
    assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest[name]["sha256"]


def test_csv_files_are_byte_identical_to_source(manifest):
    """Raw copies of the two CSVs must be untouched (BOM and all)."""
    for name in ("appointments_regional", "national_categories"):
        assert manifest[name]["sha256"] == manifest[name]["source_sha256"]


def test_excel_original_kept_and_converted_csv_exists(manifest):
    assert (RAW / "original" / "actual_duration_csv.xlsx").exists()
    assert manifest["actual_duration"]["raw_file"].endswith(".csv")
    assert manifest["actual_duration"]["converted_from"].endswith(".xlsx")


def test_duration_dates_are_iso(manifest):
    with open(manifest["actual_duration"]["raw_file"], encoding="utf-8") as f:
        header = f.readline().strip().split(",")
        first = f.readline().strip().split(",")
    d = first[header.index("appointment_date")]
    assert len(d) == 10 and d[4] == "-" and d[7] == "-"


def test_codes_keep_leading_zeros(manifest):
    with open(manifest["actual_duration"]["raw_file"], encoding="utf-8") as f:
        header = f.readline().strip().split(",")
        first = f.readline().strip().split(",")
    assert first[header.index("sub_icb_location_code")] == "00L"
