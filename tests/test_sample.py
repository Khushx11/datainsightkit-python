import unittest

from datainsightkit.distributions import histogram
from datainsightkit.web import profile_csv, sample_report


class BrowserDataTests(unittest.TestCase):
    def test_uci_case_preserves_schema_and_observations(self):
        result = sample_report()
        self.assertEqual((result["rows"], result["column_count"]), (12330, 18))
        self.assertEqual(result["case_study"]["purchases"], 1908)
        self.assertEqual(sum(row["sessions"] for row in result["case_study"]["segments"]), 12330)
        self.assertEqual(result["columns"]["Browser"]["kind"], "categorical")
        self.assertTrue(all("Browser" not in (p["left"], p["right"]) for p in result["associations"]))

    def test_numeric_bins_reconcile_and_upload_has_no_sample_metadata(self):
        counts = histogram([0, 0, 1, 2], bins=2)
        self.assertEqual([part["count"] for part in counts], [2, 2])
        result = profile_csv("Browser,Revenue\n1,TRUE\n2,FALSE\n")
        self.assertEqual(result["columns"]["Browser"]["kind"], "numeric")
        self.assertNotIn("case_study", result)

    def test_histogram_counts_follow_the_reported_edges(self):
        values = [0, 0.3, 0.4, 1]
        bins = histogram(values)
        for index, part in enumerate(bins):
            expected = sum(
                part["lower"] <= value < part["upper"]
                or (index == len(bins) - 1 and value == part["upper"])
                for value in values
            )
            self.assertEqual(part["count"], expected)

    def test_uploaded_category_override_changes_analysis(self):
        body = "Browser,Revenue\n1,12\n2,18\n3,25\n"
        inferred = profile_csv(body)
        self.assertEqual(len(inferred["associations"]), 1)
        result = profile_csv(body, categorical=["Browser"])
        self.assertEqual(result["categorical_overrides"], ["Browser"])
        self.assertEqual(result["columns"]["Browser"]["kind"], "categorical")
        self.assertEqual(result["associations"], [])
        with self.assertRaisesRegex(ValueError, "Unknown categorical columns"):
            profile_csv(body, categorical=["Unrecognised"])
