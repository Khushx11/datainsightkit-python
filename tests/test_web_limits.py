import unittest

from datainsightkit.web import MAX_ROWS, profile_csv


class WebInputTests(unittest.TestCase):
    def test_browser_api_rejects_excess_columns(self):
        names = ",".join(f"c{i}" for i in range(41))
        values = ",".join("1" for _ in range(41))
        with self.assertRaisesRegex(ValueError, "at most 40 columns"):
            profile_csv(names + "\n" + values + "\n")

    def test_browser_api_rejects_excess_rows(self):
        data = "x,y\n" + "1,2\n" * (MAX_ROWS + 1)
        with self.assertRaisesRegex(ValueError, "at most"):
            profile_csv(data)

    def test_browser_api_reports_duplicate_rows_without_rewriting(self):
        report = profile_csv("x,category\n1,A\n1,A\n2,B\n")
        self.assertEqual(report["quality"]["duplicate_rows"], 1)
        self.assertEqual(report["rows"], 3)
        self.assertEqual(report["columns"]["category"]["kind"], "categorical")

    def test_browser_api_handles_non_ascii_categories(self):
        report = profile_csv("region,amount\nMünchen,10\nSão Paulo,20\n")
        self.assertEqual(report["rows"], 2)
        self.assertEqual(report["columns"]["region"]["distinct"], 2)


if __name__ == "__main__":
    unittest.main()
