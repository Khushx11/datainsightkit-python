from bisect import bisect_right
from statistics import mean, median, quantiles

def describe(values):
    if len(values) < 2:
        q1 = q3 = values[0]
    else:
        q1, _, q3 = quantiles(values, n=4, method="inclusive")
    return {
        "min": min(values), "max": max(values), "mean": mean(values),
        "median": median(values), "q1": q1, "q3": q3,
    }


def histogram(values, bins=10):
    """Count observations in equal-width bins, including the maximum in the last."""
    lo, hi = min(values), max(values)
    if lo == hi:
        return [{"lower": lo, "upper": hi, "count": len(values)}]
    width = hi - lo
    if width == float("inf"):
        edges = [lo * (1 - i / bins) + hi * (i / bins) for i in range(bins + 1)]
    else:
        edges = [lo + width * (i / bins) for i in range(bins + 1)]
    edges[0], edges[-1] = lo, hi
    edges = sorted(set(edges))
    counts = [0] * (len(edges) - 1)
    for value in values:
        index = min(len(counts) - 1, bisect_right(edges, value) - 1)
        counts[index] += 1
    return [
        {"lower": edges[i], "upper": edges[i + 1], "count": count}
        for i, count in enumerate(counts)
    ]
