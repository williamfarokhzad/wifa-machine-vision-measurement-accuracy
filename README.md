# Machine vision measurement accuracy: a center and edge audit

This offline lab compares repeated width readings from a fixed vision setup with independent dimensional references. It separates signed bias, within-cell scatter, and the change in bias when the same reference is moved from image center to edge. The supplied readings are synthetic. The project does not acquire images, calibrate a camera, or approve an inspection station.

[Read the full WIFA lesson](https://wifarobotics.com/learn/machine-vision-measurement-accuracy/).

## Start with a clean folder

1. Install Python 3.10 or newer from [python.org](https://www.python.org/downloads/). On Windows, use the Python launcher and replace each `python3` command below with `py -3`.
2. In GitHub, choose **Code → Download ZIP**, extract it and open a terminal in the extracted folder. If Git is already installed, use:

```sh
git clone https://github.com/williamfarokhzad/wifa-machine-vision-measurement-accuracy.git
cd wifa-machine-vision-measurement-accuracy
```

3. Confirm the version and run the examples. No pip installs, images, camera, or network connection are needed after downloading.

```sh
python3 --version
python3 vision_audit.py examples/field-offset.csv
python3 vision_audit.py examples/noisy-center.csv
python3 vision_audit.py examples/missing-coverage.csv
python3 vision_audit.py examples/inconsistent-reference.csv
python3 -m unittest discover -s tests -v
```

| File | Check |
| --- | --- |
| `field-offset.csv` | B30 at the edge has bias +0.2400 mm, sample SD 0.0100 mm, maximum absolute observed error 0.2500 mm. Its edge minus center bias is +0.2400 mm. |
| `noisy-center.csv` | Center bias is +0.0000 mm for both references. Center sample SD is 0.0800 mm, while edge sample SD is 0.0100 mm. |
| `missing-coverage.csv` | No B30 center row is reported. A10 edge has just one reading, so its sample SD and both zone contrasts are marked `insufficient`. |
| `inconsistent-reference.csv` | Line 3 changes the reference value for A10. The command exits with code 2 and writes the error to stderr. |

## Bring your own data

Keep the exact header `reference_id,reference_mm,zone,reading_mm`. Give each artifact a stable ID using letters, digits, underscores or hyphens, and repeat its assigned width consistently. Enter positive decimal values in millimetres (up to six decimal places). A row is one repeated acquisition of that same reference at the specified zone: `center` or `edge`. Record missing detections separately; replacing one with zero would turn a coverage problem into a false dimension. The CLI rounds display to four decimals, not to a claim about instrument resolution.

If both cells have at least two readings, compare their means for that same artifact. The difference is descriptive, even for complete data. It is not a significance test, a full uncertainty budget, or evidence that a lens caused the difference. Do not infer production capability from these synthetic examples or tune the calibration with the same references used to validate it.

## Troubleshooting

- If Python cannot open the script, switch to the folder that contains `vision_audit.py`. Confirm with `ls` on macOS/Linux or `dir` on Windows.
- If the header is rejected, export a comma separated UTF-8 file using decimal points, without unit suffixes or an added index column.
- If the result says `insufficient`, check whether the reference was measured twice in each zone. Keep failed attempts in a separate log and report them alongside the audit.
- If the center is steady but the edge moves, repeat after confirming the same working plane, orientation, focus, lighting and region of interest. Changing all settings at once hides the source of error.

The editable figures are in `diagrams/`. If you want to regenerate the figures after editing the examples, install Inkscape and Pillow and run `python3 diagrams/render.py`. The analyzer does not use either dependency.
