from itertools import combinations
from statistics import StatisticsError, correlation
from .values import missing, number

def associations(names, rows):
    results = []
    for left, right in combinations(names, 2):
        pairs = [(number(row[left]), number(row[right])) for row in rows
                 if not missing(row[left]) and not missing(row[right])]
        if len(pairs) < 3:
            continue
        try:
            score = correlation(*zip(*pairs))
        except StatisticsError:
            continue
        results.append({"left": left, "right": right, "pearson_r": score, "pairs": len(pairs)})
    return sorted(results, key=lambda item: -abs(item["pearson_r"]))
