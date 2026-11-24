import csv
from pathlib import Path

def read_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        headers = [value.strip() for value in next(reader, [])]
        if not headers or "" in headers or len(headers) != len(set(headers)):
            raise ValueError("CSV needs unique, non-empty column names")
        rows = []
        for row in reader:
            if not row:
                continue
            if len(row) != len(headers):
                raise ValueError(f"CSV row ending at line {reader.line_num} has the wrong width")
            rows.append(dict(zip(headers, (value.strip() for value in row))))
    if not rows:
        raise ValueError("CSV has no data rows")
    return headers, rows
