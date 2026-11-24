import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from datainsightkit.cli import main

class CliTests(unittest.TestCase):
    def test_end_to_end(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            csv = root / "input.csv"
            csv.write_text("<script>,n\nhello,1\n")
            html, data = root / "report.html", root / "report.json"
            main([str(csv), "--output", str(html)])
            main([str(csv), "--output", str(data)])
            self.assertNotIn("<script>", html.read_text())
            self.assertEqual(json.loads(data.read_text())["rows"], 1)
            with self.assertRaises(SystemExit):
                main([str(csv), "--output", str(data)])
