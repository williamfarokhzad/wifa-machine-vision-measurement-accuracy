"""Summarize held-out dimensional check readings from a fixed vision setup."""
import argparse
import csv
from collections import defaultdict
from decimal import Decimal, localcontext
from pathlib import Path
import re
import sys

HEADER = ["reference_id", "reference_mm", "zone", "reading_mm"]
ZONES = ("center", "edge")
NUMBER = re.compile(r"[0-9]{1,7}(?:\.[0-9]{1,6})?")
IDENTIFIER = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_-]{0,31}")


def dimension(text):
    """Parse the lab CSV format as decimal millimetres."""
    if not NUMBER.fullmatch(text):
        raise ValueError("dimensions need ordinary decimal millimetres (up to six decimal places)")
    value = Decimal(text)
    if not 0 < value <= 1_000_000:
        raise ValueError("dimensions must be greater than zero and at most 1000000 mm")
    return value


def audit(stream):
    """Return per-cell error statistics and within-artifact field contrasts."""
    reader = csv.reader(stream, strict=True)
    if next(reader, None) != HEADER:
        raise ValueError("expected CSV header: " + ",".join(HEADER))
    references, errors = {}, defaultdict(list)
    with localcontext(prec=40):
        for row in reader:
            try:
                if len(row) != 4:
                    raise ValueError("expected four fields")
                name, reference, zone, reading = (field.strip() for field in row)
                if not IDENTIFIER.fullmatch(name):
                    raise ValueError("invalid reference_id (use letters, digits, underscores or hyphens)")
                if zone not in ZONES:
                    raise ValueError("zone must be center or edge")
                nominal, measured = dimension(reference), dimension(reading)
                if references.setdefault(name, nominal) != nominal:
                    raise ValueError(f"{name} has inconsistent reference_mm")
                errors[name, zone].append(measured - nominal)
            except ValueError as exc:
                raise ValueError(f"CSV line {reader.line_num}: {exc}") from exc
        if not errors:
            raise ValueError("no measurements")
        cells, contrasts = {}, {}
        for name in sorted(references):
            for zone in ZONES:
                values = errors.get((name, zone))
                if not values:
                    continue
                count = len(values)
                bias = sum(values) / count
                scatter = ((sum((v - bias) ** 2 for v in values) / (count - 1)).sqrt()
                           if count > 1 else None)
                cells[name, zone] = (count, bias, scatter, max(map(abs, values)))
            center, edge = (cells.get((name, zone)) for zone in ZONES)
            contrasts[name] = (edge[1] - center[1]
                               if center and edge and min(center[0], edge[0]) >= 2 else None)
    return cells, contrasts


def format_number(value, signed=False):
    if value is None:
        return "insufficient"
    with localcontext(prec=40):
        rounded = value.quantize(Decimal("0.0001"))
    if rounded == 0:
        rounded = abs(rounded)
    return format(rounded, "+.4f" if signed else ".4f")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path, help="held-out dimensional checks in millimetres")
    args = parser.parse_args()
    try:
        with args.csv_file.open(newline="", encoding="utf-8-sig") as stream:
            cells, contrasts = audit(stream)
    except (OSError, ValueError, csv.Error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print("reference zone n bias_mm sample_sd_mm max_abs_error_mm")
    for (name, zone), (n, bias, scatter, worst) in cells.items():
        print(name, zone, n, format_number(bias, signed=True),
              format_number(scatter), format_number(worst))
    print("reference edge_minus_center_bias_mm")
    for name, delta in contrasts.items():
        print(name, format_number(delta, signed=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
