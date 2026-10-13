# GP Appointments Pipeline (LSA Data Engineering, October 2026)

An end-to-end data pipeline for NHS England's **Appointments in General Practice**
statistics, built with free and open tools (Python, PySpark, DuckDB, pytest).

**The question it answers:** an NHS primary care manager asks, *"How is GP appointment
capacity being used, and where is it being lost?"*

> Status: **Week 1 (Extract) complete.** Transform, load and the dashboard are built in weeks 2-4.

## What is in the data

| Dataset | One row is | Rows | Period |
|---|---|---|---|
| `appointments_regional` | ICB x month x status x staff type x mode x booking wait | 596,821 | Jan 2020 - Jun 2022 |
| `national_categories` | sub-ICB x day x service setting x national category | 817,394 | Aug 2021 - Jun 2022 |
| `actual_duration` | sub-ICB x day x consultation-length band | 137,793 | Dec 2021 - Jun 2022 |

Full details, plus five data traps found by profiling, are in
[`docs/data_profile.md`](docs/data_profile.md).

## How to run (Week 1)

1. Put the three source files in `data/source/` (they are not stored in this repo):
   `appointments_regional.csv`, `national_categories.csv`, `actual_duration_csv.xlsx`.
   Names like `appointments_regional_1.csv` are fine too; extract matches on the start of the name.
2. Set up Python 3.10+ in a virtual environment and install the requirements:
   ```bash
   python -m venv .venv
   source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt    # PySpark builds from source: a few quiet minutes
   ```
   Only pandas, openpyxl and pytest are needed for Week 1.
3. Run the pipeline so far (extract, then profile):
   ```bash
   python run_pipeline.py --source data/source
   ```
   Or each stage on its own: `python src/extract.py --source data/source`
   then `python src/profile_data.py`.
4. Check the result: `pytest`

On Google Colab, point `--source` at the Drive folder, for example
`python src/extract.py --source /content/drive/MyDrive/LSA_Oct2026/raw`.

## Running on Databricks Free Edition

1. Push this repo to GitHub, then in Databricks: **Workspace, Create, Git folder**, paste the repo URL.
2. Open `notebooks/week1_databricks.py` and run it top to bottom. It creates a Volume,
   tells you where to upload the three source files, then runs extract, the profile and a Spark check.
3. Data lives in the Volume (`/Volumes/workspace/default/lsa_oct_2026/`), code lives in the Git folder.
4. Free Edition is serverless: do not set `master`, `spark.driver.memory` or use `spark.sparkContext`.

## What Week 1 produces

| File | What it is |
|---|---|
| `data/raw/*.csv`, `data/raw/original/` | Raw copies. Never edited. Not committed. |
| `data/raw/manifest.json` | File name, size, SHA-256, row count and time for every file. **Committed.** |
| `docs/data_profile.md` | Columns, types, nulls, distinct values, date range, grain, five traps. |

The Excel file `actual_duration_csv.xlsx` is converted to CSV because Spark cannot read Excel;
the untouched original is kept alongside.

## Project layout

```
README.md  requirements.txt  run_pipeline.py
data/source/   the files you download (not committed)
data/raw/      raw copies + manifest.json (manifest committed, data not)
data/clean/    Parquet from the transform (week 2, not committed)
warehouse/     DuckDB star schema (week 3, not committed)
notebooks/     week1_databricks.py
src/           extract.py  profile_data.py  transform.py  load.py  checks.py
tests/         pytest checks
docs/          data profile, decision log, quality report
app/           Streamlit dashboard (week 4)
```

## Data source and licence

Source: NHS England, *Appointments in General Practice* (digital.nhs.uk).
UK public sector statistics are normally published under the Open Government Licence v3.0;
check the publication's terms page. The data is aggregated counts with no patient-level records.
This project is not an official NHS product and does not use NHS logos.
