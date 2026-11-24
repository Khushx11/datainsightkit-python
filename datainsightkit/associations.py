from itertools import combinations
from math import frexp, ldexp
from statistics import StatisticsError, correlation
from .values import missing, number

def scaled(values):
    """Keep Pearson intermediates in range using an exact power-of-two scale."""
    _, exponent = frexp(max(map(abs, values)))
    return [ldexp(value, -exponent) for value in values]


def associations(names, rows):
    results = []
    for left, right in combinations(names, 2):
        pairs = [(number(row[left]), number(row[right])) for row in rows
                 if not missing(row[left]) and not missing(row[right])]
        if len(pairs) < 3:
            continue
        try:
            left_values, right_values = zip(*pairs)
            score = correlation(scaled(left_values), scaled(right_values))
        except StatisticsError:
            continue
        results.append({"left": left, "right": right, "pearson_r": score, "pairs": len(pairs)})
    return sorted(results, key=lambda item: -abs(item["pearson_r"]))
