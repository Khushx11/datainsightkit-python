import json
import unittest

from datainsightkit.export_json import render_json
from datainsightkit.report import analyse

class ProfileTests(unittest.TestCase):
    def test_quality_and_pairwise_analysis(self):
        rows = [{"x": str(n), "y": str(2*n)} for n in range(3)]
        rows += [rows[0], {"x": "3", "y": "NA"}]
        report = analyse(["x", "y"], rows)
        self.assertEqual(report["columns"]["y"]["missing"], 1)
        self.assertEqual(report["quality"]["duplicate_rows"], 1)
        self.assertEqual(report["associations"][0]["pairs"], 4)
        self.assertAlmostEqual(report["associations"][0]["pearson_r"], 1)
        self.assertEqual(report["columns"]["x"]["distribution"]["median"], 1)

    def test_pearson_is_finite_for_extreme_numeric_scales(self):
        rows = [{"large": f"{i}e200", "small": f"{5-i}e-200"} for i in range(1, 5)]
        result = json.loads(render_json(analyse(["large", "small"], rows)))
        self.assertEqual(len(result["associations"]), 1)
        self.assertAlmostEqual(result["associations"][0]["pearson_r"], -1.0)
