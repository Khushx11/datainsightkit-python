"""Reproducible single-machine CSV profiling benchmark.

Measurements are local to the machine running this script, not SLA claims.
Does not require external datasets or services.
"""
import argparse
import csv
import json
import platform
import random
import statistics
import time
import tracemalloc
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from datainsightkit.cli import main as profile_csv
from datainsightkit.report import analyse


def fixture(row_count: int, seed: int = 42):
    if row_count < 1:
        raise ValueError("rows must be positive")
    rng = random.Random(seed)
    names = [f"metric_{i}" for i in range(6)] + ["category", "region"]
    rows = []
    for index in range(row_count):
        row = {}
        for j in range(6):
            value = round(index * 0.01 + j + rng.uniform(-3, 3), 5)
            row[f"metric_{j}"] = "NA" if index % (13 + j) == 0 else str(value)
        row["category"] = ("basic", "pro", "enterprise")[index % 3]
        row["region"] = ("AU", "NZ", "IN", "UK")[index % 4]
        rows.append(row)
    return names, rows


def measure(row_count: int, repeats: int = 3):
    if repeats < 1:
        raise ValueError("repeats must be positive")
    headers, rows = fixture(row_count)
    analyse(headers, rows)  # Warm up imports and cache effects.
    durations = []
    peaks = []
    for _ in range(repeats):
        tracemalloc.start()
        t0 = time.perf_counter()
        report = analyse(headers, rows)
        durations.append(time.perf_counter() - t0)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peaks.append(peak)
        assert report["rows"] == row_count
        assert report["column_count"] == len(headers)
    median_s = statistics.median(durations)
    return {
        "rows": row_count,
        "columns": len(headers),
        "repeats": repeats,
        "median_seconds": round(median_s, 6),
        "rows_per_second": round(row_count / median_s, 2),
        "peak_traced_mib": round(max(peaks) / (1024 * 1024), 2),
        "durations_seconds": [round(d, 6) for d in durations],
    }


def measure_csv_to_json(row_count: int, repeats: int = 3):
    """Measure the CLI entry point in-process with tracing disabled for timing."""
    if repeats < 1:
        raise ValueError("repeats must be positive")
    headers, rows = fixture(row_count)
    with TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "input.csv"
        with source.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
        del rows
        output = root / "profile.json"

        def profile():
            with redirect_stdout(StringIO()):
                profile_csv([str(source), "--output", str(output)])

        def validate():
            report = json.loads(output.read_text(encoding="utf-8"))
            assert report["rows"] == row_count
            assert report["column_count"] == len(headers)
            output.unlink()

        profile()
        validate()
        durations = []
        for _ in range(repeats):
            started = time.perf_counter()
            profile()
            durations.append(time.perf_counter() - started)
            validate()

        tracemalloc.start()
        try:
            profile()
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        validate()
        input_bytes = source.stat().st_size

    median_s = statistics.median(durations)
    return {
        "rows": row_count,
        "columns": len(headers),
        "input_bytes": input_bytes,
        "repeats": repeats,
        "median_seconds": round(median_s, 6),
        "rows_per_second": round(row_count / median_s, 2),
        "peak_traced_mib": round(peak / (1024 * 1024), 2),
        "durations_seconds": [round(duration, 6) for duration in durations],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", nargs="+", type=int, default=[1000, 5000])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "measurement": "time.perf_counter + tracemalloc",
        "dataset": "deterministic generated 6 numeric + 2 categorical columns",
        "cases": [measure(n, args.repeats) for n in args.rows],
        "csv_to_json_measurement": "in-process CLI; timing without tracing; one separate traced run",
        "csv_to_json_cases": [measure_csv_to_json(n, args.repeats) for n in args.rows],
    }
    content = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    print(content, end="")


if __name__ == "__main__":
    main()
