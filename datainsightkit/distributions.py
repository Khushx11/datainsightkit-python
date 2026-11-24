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
    # Scale before subtracting so values close to float limits still have finite bins.
    scale = max(abs(lo), abs(hi))
    low, high = lo / scale, hi / scale
    width = (high - low) / bins
    if width == 0:
        return [{"lower": lo, "upper": hi, "count": len(values)}]
    counts = [0] * bins
    for value in values:
        index = max(0, min(bins - 1, int((value / scale - low) / width)))
        counts[index] += 1
    edges = [lo] + [(low + width * i) * scale for i in range(1, bins)] + [hi]
    return [
        {"lower": edges[i], "upper": edges[i + 1], "count": count}
        for i, count in enumerate(counts)
    ]
