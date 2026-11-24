import unittest
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
