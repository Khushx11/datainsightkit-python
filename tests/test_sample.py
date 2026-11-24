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
