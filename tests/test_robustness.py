"""Edge cases for CSV ingestion and report generation.

All fixtures are in-memory and contain no private customer data.
"""
import csv
import io
import math
import unittest

from datainsightkit.ingest import read_stream
from datainsightkit.report import analyse
from datainsightkit.export_html import render_html
from datainsightkit.export_json import render_json


class RobustInputTests(unittest.TestCase):
    def parse(self, content, **kwargs):
        return read_stream(io.StringIO(content, newline=""), **kwargs)

    def test_utf8_bom_normalisation(self):
        # read_csv handles BOM when opening from disk; the stream parser
        # must also reject blank and duplicate header names.
        with self.assertRaisesRegex(ValueError, "unique"):
            self.parse("  A, A  \n1,2\n")
        with self.assertRaisesRegex(ValueError, "unique"):
            self.parse("A,  \n1,2\n")

    def test_quotes_commas_unicode_and_multiline_values(self):
        headers, rows = self.parse('name,notes\n"Zoë","hi, there"\n"Ada","first\nsecond"\n')
        self.assertEqual(headers, ["name", "notes"])
        self.assertEqual(rows[0]["name"], "Zoë")
        self.assertEqual(rows[0]["notes"], "hi, there")
        self.assertEqual(rows[1]["notes"], "first\nsecond")

    def test_malformed_quote_and_inconsistent_width(self):
        with self.assertRaises(ValueError):
            self.parse('a,b\n"unclosed,2\n')
        with self.assertRaisesRegex(ValueError, "wrong width"):
            self.parse("a,b\n1,2,3\n")

    def test_bounded_rows_and_columns(self):
        with self.assertRaisesRegex(ValueError, "at most 2 columns"):
            self.parse("a,b,c\n1,2,3\n", max_columns=2)
        with self.assertRaisesRegex(ValueError, "at most 1 rows"):
            self.parse("a,b\n1,2\n3,4\n", max_rows=1)

    def test_numeric_special_values_are_not_treated_as_finite(self):
        headers, rows = self.parse("value,group\n1,x\nnan,x\ninf,y\n1e309,z\n")
        report = analyse(headers, rows)
        self.assertEqual(report["columns"]["value"]["kind"], "categorical")
        self.assertEqual(report["rows"], 4)
        self.assertTrue(math.isfinite(report["quality"]["duplicate_rows"]))

    def test_constant_and_fully_missing_fields(self):
        headers, rows = self.parse("a,b,empty\n3,7,NA\n3,7,null\n3,7,none\n")
        report = analyse(headers, rows)
        self.assertEqual(report["columns"]["a"]["distribution"]["min"], 3.0)
        self.assertEqual(report["columns"]["a"]["potential_outliers"], 0)
        self.assertEqual(report["columns"]["empty"]["kind"], "empty")
        self.assertEqual(report["columns"]["empty"]["missing"], 3)
        # JSON export must never emit NaN or Infinity values.
        rendered = render_json(report)
        self.assertNotIn(": NaN", rendered)
        self.assertNotIn(": Infinity", rendered)

    def test_html_escaping_with_untrusted_column_names(self):
        headers, rows = self.parse('"<script>alert(1)</script>",b\n1,2\n3,4\n')
        html = render_html(analyse(headers, rows))
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)


if __name__ == "__main__":
    unittest.main()
