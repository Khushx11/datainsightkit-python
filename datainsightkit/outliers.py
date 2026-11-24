from .distributions import describe

def count_outliers(values):
    if len(values) < 4:
        return None
    summary = describe(values)
    q1, q3 = summary["q1"], summary["q3"]
    spread = q3 - q1
    return sum(v < q1 - 1.5 * spread or v > q3 + 1.5 * spread for v in values)
