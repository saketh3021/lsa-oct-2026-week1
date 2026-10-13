"""Week 2 - TRANSFORM (PySpark). Not started yet.

Plan: read each raw file with an explicit schema, then
  * regional: tidy wait-band labels, standardise 'Other Practice staff',
    add month_start, group by every descriptive column and SUM counts
    (596,821 -> 295,692 rows; total must stay 742,804,525)
  * categories: strip the BOM, to_date(col, 'dd/MM/yyyy'), take the sub-ICB code
    with regexp_extract(name, r' - (\\w+)$', 1)   # codes are not always 3 chars
  * duration: add appointment_month
Write each as Parquet partitioned by appointment_month. See docs/data_profile.md.
"""
