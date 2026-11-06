import csv
from decimal import Decimal as D
from io import StringIO
from pathlib import Path
import subprocess
import sys
import unittest

from vision_audit import audit

ROOT = Path(__file__).resolve().parents[1]
HEADER = "reference_id,reference_mm,zone,reading_mm\n"


def fixture(name):
    with (ROOT / "examples" / name).open(newline="") as stream:
        return audit(stream)


class VisionAuditTest(unittest.TestCase):
    def test_field_errors_match_hand_calculation(self):
        cells, delta = fixture("field-offset.csv")
        # B30 edge errors are 0.23, 0.24 and 0.25; variance is 0.0001.
        self.assertEqual(cells["B30", "edge"], (3, D(".24"), D(".01"), D(".25")))
        self.assertEqual(delta, {"A10": D(".08"), "B30": D(".24")})

    def test_zero_bias_can_hide_scatter(self):
        cells, delta = fixture("noisy-center.csv")
        self.assertEqual(delta["A10"], D("0"))
        self.assertEqual(cells["A10", "center"], (3, D("0"), D(".08"), D(".08")))
        self.assertEqual(cells["A10", "edge"][2], D(".01"))

    def test_missing_cell_and_singleton_are_distinct(self):
        cells, delta = fixture("missing-coverage.csv")
        self.assertNotIn(("B30", "center"), cells)
        self.assertEqual(cells["A10", "edge"], (1, D(".12"), None, D(".12")))
        self.assertEqual(delta, {"A10": None, "B30": None})

    def test_uneven_replicates_use_per_cell_means_and_n_minus_one(self):
        rows = "R,10,center,9\nR,10,center,11\nR,10,edge,11\nR,10,edge,12\nR,10,edge,13\n"
        cells, delta = audit(StringIO(HEADER + rows))
        self.assertAlmostEqual(float(cells["R", "center"][2]), 1.4142135623730951)
        self.assertEqual(cells["R", "edge"], (3, D(2), D(1), D(3)))
        self.assertEqual(delta["R"], D(2))

    def test_permutation_and_common_shift(self):
        rows = ["R,10,center,9.8", "R,10,center,10", "R,10,edge,9.4", "R,10,edge,9.6"]
        run = lambda lines: audit(StringIO(HEADER + "\n".join(lines)))
        original = run(rows)
        self.assertEqual(original, run(rows[::-1]))
        self.assertEqual(original[1]["R"], D("-.4"))
        shifted = []
        for name, nominal, zone, reading in csv.reader(rows):
            shifted.append(f"{name},{nominal},{zone},{D(reading)+D('.3')}")
        cells, delta = run(shifted)
        self.assertEqual(delta, original[1])
        self.assertEqual(cells["R", "edge"][2], original[0]["R", "edge"][2])
        self.assertEqual(cells["R", "edge"][1], D("-.2"))

    def test_rejects_bad_units_nonfinite_wrong_zone_and_missing_field(self):
        for row in ("R,10,edge,NaN", "R,10,edge,10mm", "R,10,left,10", "R,10,center",
                    "R,0,center,10", "R,10,edge,0", "R,10,edge,10.0000001"):
            with self.subTest(row=row), self.assertRaisesRegex(ValueError, "CSV line 2"):
                audit(StringIO(HEADER + row))

    def test_rejects_empty_csv_and_wrong_header(self):
        for raw, message in [(HEADER, "no measurements"), ("sample,mm\n", "expected CSV header")]:
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, message):
                audit(StringIO(raw))

    def test_cli_rejects_changed_reference_without_partial_report(self):
        result = subprocess.run(
            [sys.executable, "vision_audit.py", "examples/inconsistent-reference.csv"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("CSV line 3: A10 has inconsistent reference_mm", result.stderr)


if __name__ == "__main__":
    unittest.main()
