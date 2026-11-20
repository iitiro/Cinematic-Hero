# Cinematic Hero

Explore cinematic hero archetypes, franchise patterns, and box-office change through Ukrainian and worldwide film-market data.

## Research focus

How do commercially successful films reflect changing hero archetypes and recurring narrative worlds? This project examines Ukrainian box-office data for 2005–2025 and provides a separate analysis script for worldwide data for 1977–2025.

## Repository contents

- `ukraine_box_office_analysis_en.py` — market dynamics, concentration, distributors, and title-based archetype coding.
- `world_box_office_analysis_en.py` — worldwide market indicators and dictionary-based coding of serial narrative worlds.
- `boxoffice_ukraine_2005_2025.xlsx` — Ukrainian source workbook.
- CSV tables and `data_quality.json` — included analysis outputs and data-quality indicators.

## Run the Ukrainian analysis

Install the Python dependencies, then run from this repository:

```sh
python3 -m pip install pandas numpy matplotlib openpyxl pillow
python3 ukraine_box_office_analysis_en.py --input boxoffice_ukraine_2005_2025.xlsx --output generated_ukraine_en
```

The explicit input argument points to the included workbook. Outputs include figures, CSV tables, and a data-quality report.

The worldwide workbook is not included. To use the worldwide script, supply the source workbook and update `SOURCE_FILE` and the font paths for your computer.

## Interpretation

Archetype labels are title-based proxies; they do not replace close reading or audience research. Revenue values are nominal. The Ukrainian analysis flags incomplete coverage for 2005 and possible coverage limitations for 2022–2025.

## License

[MIT](LICENSE).
