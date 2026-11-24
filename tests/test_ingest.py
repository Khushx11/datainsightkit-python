import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from datainsightkit.ingest import read_csv

class IngestTests(unittest.TestCase):
    def test_invalid_csv(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv"
            for data in ["a,a\n1,2\n", "a,b\n1\n", "a,b\n"]:
                with self.subTest(data=data), self.assertRaises(ValueError):
                    path.write_text(data)
                    read_csv(path)
