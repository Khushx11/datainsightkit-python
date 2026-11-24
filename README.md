# DataInsightKit

**Status: experimental Python prototype, not yet a packaged release.**

DataInsightKit explores automated profiling, descriptive analysis, correlation analysis, text processing, and natural-language explanations for tabular datasets. It was developed as a modular Python codebase with pandas-based analysis routines.

## Implemented source modules

| Path | Purpose |
| --- | --- |
| `ingestion/profiler.py` | Column profiling and descriptive statistics |
| `analysis/anomaly_detector.py` | Statistical anomaly-detection methods |
| `analysis/correlation_analyzer.py` | Correlation analysis and structured results |
| `analysis/text_analyzer.py` | Text processing, TF-IDF features and sentiment analysis |
| `nlg/narrative_generator.py` | Experimental generation of natural-language findings |
| `main.py` | A proposed DataInsightKit interface around a pandas DataFrame |
| `config.py` | Environment-based application configuration |

## Development status

The source currently needs a packaging and integration pass before it can be advertised as an installable library:

- Some imports expect a `datainsightkit` package layout that this repository does not yet have.
- Several package initialisers refer to modules that are not present in this snapshot.
- Dependencies are not yet declared in a reproducible project manifest.
- Automated tests and a verified end-to-end example have not yet been added.

The repository is therefore retained as a development snapshot, not a production-ready data analytics package. Installation examples and performance claims will be added only after a clean-environment test.

## Suggested verification priorities

1. Consolidate the code under a proper Python package directory and resolve imports.
2. Remove or implement missing export, formatting and model definitions.
3. Declare and constrain dependencies (including pandas, NumPy, SciPy, scikit-learn, TextBlob, and OpenAI SDK components where used).
4. Add fixtures and unit tests for empty, missing and mixed-type data.
5. Establish a reproducible example from a publicly redistributable dataset.

## Security and privacy

Use environment variables for credentials and do not commit `.env` files, private data, generated artifacts or API credentials. LLM-generated narratives should be treated as hypotheses to validate against the underlying dataset.

## Licence

See [LICENSE](LICENSE) for repository licensing details.
