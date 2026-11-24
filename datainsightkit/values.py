from math import isfinite

MISSING = {"", "na", "n/a", "null", "none"}

def missing(value):
    return value.casefold() in MISSING

def number(value):
    try:
        result = float(value)
    except ValueError:
        return None
    return result if isfinite(result) else None
