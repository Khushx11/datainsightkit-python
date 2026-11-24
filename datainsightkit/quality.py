def quality(headers, rows, columns):
    unique = {tuple(row[name] for name in headers) for row in rows}
    return {
        "duplicate_rows": len(rows) - len(unique),
        "columns_at_least_half_missing": [
            name for name, stats in columns.items() if stats["missing"] * 2 >= len(rows)
        ],
    }
