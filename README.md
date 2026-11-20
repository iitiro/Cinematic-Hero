# Cinematic Hero

Explore cinematic hero archetypes, franchise patterns, and box-office change through Ukrainian and worldwide film-market data.

## Research materials

- `ukraine_box_office_analysis_en.py` — Ukrainian market dynamics, concentration, distributors, and title-based archetype coding.
- `world_box_office_analysis_en.py` — worldwide market indicators and dictionary-based coding of serial narrative worlds.
- `boxoffice_ukraine_2005_2025.xlsx` — the included Ukrainian workbook (2,844 records, 2005–2025).
- CSV tables and `data_quality.json` — previously exported research results. Worldwide exports can be inspected without the original worldwide workbook.

## Setup

Python 3.12 or newer is recommended. Run these commands from the repository directory:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -c constraints.txt
```

On Windows, activate the environment with `.venv\Scripts\activate`.
`constraints.txt` records the dependency versions used for the local release checks.

## Run the Ukrainian analysis

```sh
python ukraine_box_office_analysis_en.py
```

The default input is the workbook alongside the script. Figures, tables, and a quality report are written to `generated_ukraine_en/`. To choose paths explicitly:

```sh
python ukraine_box_office_analysis_en.py --input boxoffice_ukraine_2005_2025.xlsx --output outputs/ukraine
```

## Run the worldwide analysis

The worldwide source workbook is **not included**. Supply your own workbook with an `All Movies` sheet and the columns `Year`, `Rank`, `Release Group`, `Worldwide`, and `Foreign`:

```sh
python world_box_office_analysis_en.py --input /path/to/boxoffice_world_1977_2025.xlsx --output outputs/world
```

The script expects years within 1977–2025 and positive 2019 revenue for its reference index. It creates `figures/` and `tables/` under the output directory. Fonts are selected from bundled DejaVu assets on macOS, Linux, and Windows. Use `--help` on either script for options.

## Interpretation and data quality

Archetype labels are title-based proxies, not a substitute for close reading or audience research. Values are nominal and are not adjusted for inflation. The Ukrainian workbook contains incomplete 2005 coverage, possible coverage limitations for 2022–2025, three duplicate year/title pairs, and missing distributor, theatre, and genre fields. The quality report retains these indicators rather than silently deleting records. Yearly gross totals reconcile with the supplied summary sheet.

## Offline checks

```sh
python -m pip install -r requirements-dev.txt -c constraints.txt
python -m pytest -q
```

The test suite does not require API credentials. GitHub Actions is configured to repeat these checks on Python 3.12, 3.13, and 3.14 after push.

## License

[MIT](LICENSE).
