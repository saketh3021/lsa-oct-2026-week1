# Databricks notebook source
# MAGIC %md
# MAGIC # Week 1 - Extract (Databricks Free Edition)
# MAGIC LSA Data Engineering, October 2026 cohort. NHS England, *Appointments in General Practice*.
# MAGIC
# MAGIC **Where things live**
# MAGIC * **Code** is in this Git folder (`src/`), so it is version-controlled and goes on your portfolio.
# MAGIC * **Data** is in a Unity Catalog **Volume**. Never put data in the Git folder (500 MB limit) and never commit it.
# MAGIC
# MAGIC **Free Edition is serverless**, so do NOT use the Colab lines `SparkSession.builder...master("local[*]")`,
# MAGIC `spark.driver.memory` or `spark.sparkContext`. A ready-made `spark` session already exists.
# MAGIC
# MAGIC *Written without a Databricks workspace to test on: if a cell fails, copy the exact error text.*

# COMMAND ----------

# MAGIC %pip install -q openpyxl

# COMMAND ----------

# Where is the Volume? Free Edition normally gives a catalog called "workspace" and a schema "default".
# Check that these match what you see in the Catalog explorer before running.
print("current catalog:", spark.catalog.currentCatalog(), "| schema:", spark.catalog.currentDatabase())

CATALOG, SCHEMA, VOLUME = "workspace", "default", "lsa_oct_2026"
spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.{VOLUME}")

BASE = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"
SOURCE, RAW = f"{BASE}/source", f"{BASE}/raw"

import os
os.makedirs(SOURCE, exist_ok=True)
os.makedirs(RAW, exist_ok=True)
print("Upload the three data files to:", SOURCE)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Upload the data (once, by hand)
# MAGIC 1. Left menu, **Catalog**, then `workspace`, `default`, `lsa_oct_2026`, then the `source` folder.
# MAGIC 2. **Upload to this volume** and add: `appointments_regional.csv`, `national_categories.csv`, `actual_duration_csv.xlsx`.
# MAGIC 3. Run the next cell. You should see three files.

# COMMAND ----------

for f in sorted(os.listdir(SOURCE)):
    print(f"{os.path.getsize(os.path.join(SOURCE, f)) / 1e6:8.1f} MB  {f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Extract: copy, convert the Excel file, write the manifest
# MAGIC Uses the same `src/extract.py` as the local and Colab routes.

# COMMAND ----------

import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath("../src"))   # this notebook lives in notebooks/, code in src/
import extract, profile_data

manifest = extract.extract(Path(SOURCE), Path(RAW))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Profile: writes `docs/data_profile.md` inside the Git folder

# COMMAND ----------

profile_data.main(raw=RAW, out="../docs/data_profile.md")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Check with Spark itself
# MAGIC The manifest was built with plain Python. Here Spark counts the same files independently:
# MAGIC the numbers must agree (596,821 / 817,394 / 137,793).

# COMMAND ----------

from pyspark.sql import functions as F

entries = {f["dataset"]: f for f in manifest["files"]}
for name, e in entries.items():
    df = spark.read.csv(e["raw_file"], header=True)
    n = df.count()
    status = "OK" if n == e["row_count"] else "MISMATCH"
    print(f"{name:24s} spark={n:>8,}  manifest={e['row_count']:>8,}  {status}")

# TRAP 2 in action: how does Spark name the first column of the categories file?
cat = spark.read.csv(entries["national_categories"]["raw_file"], header=True)
print("\nfirst column name:", repr(cat.columns[0]))

# COMMAND ----------

# Spark's total for the regional file: must be 742,804,525
reg = spark.read.csv(entries["appointments_regional"]["raw_file"], header=True, inferSchema=True)
reg.agg(F.sum("count_of_appointments").alias("total_appointments")).show()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Keep the manifest in the repo
# MAGIC The manifest is committed (data is not). Copy it into the Git folder, then use the **Git** button
# MAGIC (top right of the notebook) to commit and push `data/raw/manifest.json` and `docs/data_profile.md`.

# COMMAND ----------

import shutil
os.makedirs("../data/raw", exist_ok=True)
shutil.copyfile(f"{RAW}/manifest.json", "../data/raw/manifest.json")
print("copied manifest into the repo folder")
