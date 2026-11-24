from collections import Counter
from .values import missing, number

def profile(headers, rows, *, categorical=()):
    columns = {}
    for name in headers:
        values = [row[name] for row in rows if not missing(row[name])]
        numeric = name not in categorical and bool(values) and all(number(v) is not None for v in values)
        columns[name] = {
            "kind": "numeric" if numeric else "categorical" if values else "empty",
            "missing": len(rows) - len(values),
            "distinct": len(set(values)),
            "top_values": [] if numeric else Counter(values).most_common(5),
        }
    return columns
