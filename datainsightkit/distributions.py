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
