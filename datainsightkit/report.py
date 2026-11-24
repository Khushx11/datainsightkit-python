from .associations import associations
from .distributions import describe, histogram
from .outliers import count_outliers
from .profile import profile
from .quality import quality
from .values import missing, number

def analyse(headers, rows, *, categorical=()):
    overrides = set(categorical)
    unknown = overrides.difference(headers)
    if unknown:
        raise ValueError("Unknown categorical columns: " + ", ".join(sorted(unknown)))
    columns = profile(headers, rows, categorical=overrides)
    numeric = [name for name in headers if columns[name]["kind"] == "numeric"]
    for name in numeric:
        values = [number(row[name]) for row in rows if not missing(row[name])]
        columns[name]["distribution"] = describe(values)
        columns[name]["histogram"] = histogram(values)
        columns[name]["potential_outliers"] = count_outliers(values)
    return {
        "rows": len(rows), "column_count": len(headers),
        "quality": quality(headers, rows, columns), "columns": columns,
        "categorical_overrides": [name for name in headers if name in overrides],
        "associations": associations(numeric, rows),
    }
