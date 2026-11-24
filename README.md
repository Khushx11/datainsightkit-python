# DataInsightKit

A local CSV profiler for the first pass over unfamiliar tabular data. It answers four questions before modelling. Which fields are incomplete? Are rows repeated? What do the numeric distributions look like? Which fields move together?

## Browser interface

After installing the package with `python -m pip install .`, start it with:

```sh
python -m datainsightkit.web
```

Open http://127.0.0.1:8000. Open or paste a CSV, review the quality summary, filter columns, and download the JSON profile. The interface includes the real Palmer Penguins dataset as a worked example. Select a column name to inspect its distribution or most frequent values. The server listens only on your computer.

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

## Browser example data

Palmer Penguins contains 344 observations and eight columns. Allison Horst, Alison Hill and Kristen Gorman packaged the data collected by Kristen Gorman and Palmer Station LTER. The included CSV is the unmodified [CC0 source file](https://github.com/allisonhorst/palmerpenguins/blob/8957207b78d6ccd1b4654a9dd9c9041b657478ab/inst/extdata/penguins.csv). The profiler was checked against pandas for missing counts, duplicates, quartiles and complete-pair correlations on this exact file.
