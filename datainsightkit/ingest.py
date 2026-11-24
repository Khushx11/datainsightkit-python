import csv
from pathlib import Path

def read_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return read_stream(stream)

def read_stream(stream, *, max_rows=None, max_columns=None):
    try:
        reader = csv.reader(stream, strict=True)
        headers = [value.strip() for value in next(reader, [])]
        if not headers or "" in headers or len(headers) != len(set(headers)):
            raise ValueError("CSV needs unique, non-empty column names")
        if max_columns is not None and len(headers) > max_columns:
            raise ValueError(f"CSV must have at most {max_columns:,} columns")
        rows = []
        for row in reader:
            if not row:
                continue
            if len(row) != len(headers):
                raise ValueError(f"CSV row ending at line {reader.line_num} has the wrong width")
            rows.append(dict(zip(headers, (value.strip() for value in row))))
            if max_rows is not None and len(rows) > max_rows:
                raise ValueError(f"CSV must have at most {max_rows:,} rows")
        if not rows:
            raise ValueError("CSV has no data rows")
        return headers, rows
    except csv.Error as error:
        raise ValueError(f"Invalid CSV: {error}") from error
