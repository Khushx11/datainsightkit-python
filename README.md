# DataInsightKit

A local CSV profiler for the first pass over unfamiliar tabular data. It answers four questions before modelling. Which fields are incomplete? Are rows repeated? What do the numeric distributions look like? Which fields move together?

## Browser interface

After installing the package with `python -m pip install .`, start it with:

```sh
python -m datainsightkit.web
```

Open http://127.0.0.1:8000. Open or paste a CSV, review the quality summary, filter columns, and download the JSON profile. The interface starts with the UCI Online Shoppers dataset. Select a column name to inspect its distribution or most frequent values. Upload or paste a different CSV to analyse your own data. In the column details, choose “Treat as categorical” for numeric codes such as browser IDs. Clear the checkbox to restore inference. JSON exports include the applied overrides. The server listens only on your computer.

## Try it

Requires Python 3.10 or later. Run from the repository root.

```sh
python -m pip install .
datainsightkit examples/weekly_orders.csv --output reports/orders.html
datainsightkit examples/weekly_orders.csv --output reports/orders.json
python -m unittest discover -s tests -v
```

Open the HTML file in a browser. The bundled CSV is a small synthetic example of weekly retail orders with a duplicate, a missing refund count and a large order week. The tool runs locally without a network connection or API key.

The report includes column types, missing counts, category frequencies, numeric quartiles, Tukey outlier counts and pairwise Pearson correlations with their usable sample sizes. A correlation can flag fields worth reviewing before fitting a model. It does not establish causation. A flagged outlier can be a real event and needs context before removal.

The profiler handles a single in-memory UTF-8 CSV with a header. It infers a numeric type only when every non-missing value parses as a finite number. Use caution with number-like IDs and with the missing markers `NA`, `N/A`, `null` and `none`, which some datasets use as categories. Reports can contain frequent source values, so review them before sharing.

Khush Bhavin Maru · Adelaide University MAAIM portfolio. Codex assisted with implementation and documentation.

## E-commerce case study

The browser demo profiles **12,330 observed shopping sessions** across 17 features and a purchase outcome. It reports **1,908 purchases (15.5%)**, including **24.9% of 1,694 new visitors** and **13.9% of 10,551 returning visitors**. These are descriptive rates. The **125 identical rows** are repeated observed feature-and-outcome vectors. They do not establish duplicate customers or sessions.

The sample uses the publisher’s categorical schema, so numeric identifiers such as browser and traffic type are excluded from Pearson correlations. Uploaded CSVs use type inference unless you mark a column as categorical in the browser or pass `--categorical COLUMN` to the CLI. Repeat the flag for multiple columns. The dashboard does not fit a purchase prediction model.

Source: Sakar, C. and Kastro, Y. (2018), *Online Shoppers Purchasing Intention Dataset*, UCI Machine Learning Repository, [DOI 10.24432/C5F88Q](https://doi.org/10.24432/C5F88Q), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The bundled CSV preserves the upstream records and headers with normalised line endings. The profiler’s key results were independently checked against pandas.

## Profiling benchmark

The reproducible benchmark uses a fixed-seed synthetic dataset with six numeric and two categorical fields. It warms up the analyser, repeats each case three times, records median elapsed seconds, throughput in rows/second and Python traced peak allocations. These measurements are **machine- and workload-specific**, not a production service-level guarantee.

```sh
python benchmarks/profile_throughput.py --rows 1000 5000 --repeats 3 --output benchmarks/local.json
```

Every pull request also executes the benchmark in GitHub Actions and uploads a JSON benchmark artifact. Use the generated JSON alongside the runner type and Python version when comparing performance across revisions. Memory reflects Python-tracked allocations through `tracemalloc`, **not** full operating-system resident memory.

### Data-handling verification

Regression tests cover malformed CSV quoting, duplicate and blank headers, inconsistent row widths, quoted multiline values, Unicode, maximum browser row/column limits, numerical edge cases, fully missing columns, browser sample profiling and escaping untrusted field names in HTML exports.

The browser remains local-only by design; it is **not** an authenticated or audited multi-user analytics service. CSV profiling is in-memory and pairwise correlations scale with the number of numeric columns, so large datasets should be processed with explicit resource limits or a distributed backend.
