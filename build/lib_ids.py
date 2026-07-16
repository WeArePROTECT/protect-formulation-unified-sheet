"""
lib_ids.py — canonical ID + small IO helpers for the formulation unified-sheet build.

The one job that has to be right everywhere: turn the messy ASMA identifiers found across
files (`ASMA_ID` / `ASMA_id` / `ASMA-ID`, trailing spaces, `_priming` suffixes, zero-padding,
reporter/pathogen tokens leaked into member columns) into ONE canonical form: `ASMA-<int>`,
matching the stock list of record (`SYK/ASMA_list.xlsx`, which uses `ASMA-1`, `ASMA-2`, …).

Stdlib + openpyxl only (no pandas — NumPy ABI noise on this host). Parquet via pyarrow.
"""
import csv
import re

# Substrings that mark a value as a reporter/pathogen token, NOT an ASMA isolate.
# (e.g. 'PA14_KEH108_Reporter', 'PAO1', 'PA14_FA' leaked into a member column.)
_NON_ASMA_HINTS = ("reporter", "pa14", "pao1", "keh", "_fa", "blank")
_NULLISH = {"", "na", "nan", "none", "null", "blank", "0"}
_ASMA_RE = re.compile(r"^\s*asma[\s_-]*0*(\d+)")


def normalize_asma_id(value):
    """Return canonical 'ASMA-<int>' or None if the value is not an ASMA isolate.

    None covers: blanks/NA/0, reporter/pathogen tokens, and anything that doesn't
    parse to an ASMA number. Callers should drop None member values (strain omitted).
    """
    if value is None:
        return None
    s = str(value).strip()
    low = s.lower()
    if low in _NULLISH:
        return None
    if any(h in low for h in _NON_ASMA_HINTS):
        return None
    m = _ASMA_RE.match(low)
    if not m:
        return None
    return f"ASMA-{int(m.group(1))}"


def is_asma_id(value):
    return normalize_asma_id(value) is not None


def read_xlsx_sheet(path, sheet=None):
    """Yield rows of an .xlsx sheet as dicts keyed by the (stripped) header row.

    sheet=None uses the active sheet; otherwise pass a sheet title.
    """
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet] if sheet else wb.active
    rows = ws.iter_rows(values_only=True)
    header = [str(c).strip() if c is not None else "" for c in next(rows)]
    for r in rows:
        yield {header[i]: r[i] for i in range(min(len(header), len(r)))}
    wb.close()


def read_delimited(path, delimiter="\t"):
    """Yield rows of a CSV/TSV as dicts keyed by the header row."""
    import csv
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh, delimiter=delimiter):
            yield row


def parse_gtdb_lineage(classification):
    """GTDB lineage string -> (genus, species).

    e.g. 'd__Bacteria;...;g__Staphylococcus;s__Staphylococcus aureus'
         -> ('Staphylococcus', 'Staphylococcus aureus'). Missing ranks -> None.
    """
    if not classification:
        return (None, None)
    genus = species = None
    for part in str(classification).split(";"):
        part = part.strip()
        if part.startswith("g__"):
            genus = part[3:] or None
        elif part.startswith("s__"):
            species = part[3:] or None
    return (genus, species)


def write_table(rows, columns, out_stem):
    """Write a list-of-dicts to <out_stem>.csv and (if pyarrow present) <out_stem>.parquet.

    `columns` fixes column order. Returns the number of rows written.
    """
    csv_path = f"{out_stem}.csv"
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
        table = pa.table({c: [row.get(c) for row in rows] for c in columns})
        pq.write_table(table, f"{out_stem}.parquet")
    except Exception as e:  # parquet is a bonus; CSV is the guaranteed output
        print(f"  (parquet skipped: {e})")
    return len(rows)
