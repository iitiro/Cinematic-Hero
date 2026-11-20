from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ukrainian_workbook_reconciles_and_archetype_shares_sum_to_one():
    module = load_script("ukraine_box_office_analysis_en")
    movies, years, quality = module.load_and_validate(module.DEFAULT_INPUT)
    assert len(movies) == 2844
    assert quality["yearly_gross_reconciliation_max_abs_difference"] == 0
    _, annual, periods = module.build_archetype_tables(movies)
    assert (annual.sum(axis=1).sub(1).abs() < 1e-10).all()
    assert (periods.sum(axis=1).sub(1).abs() < 1e-10).all()


def test_ukrainian_cli_default_input_and_outputs(tmp_path):
    result = subprocess.run([sys.executable, str(ROOT / "ukraine_box_office_analysis_en.py"), "--output", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert len(list(tmp_path.glob("*.png"))) == 9
    assert json.loads((tmp_path / "data_quality.json").read_text())["rows"] == 2844
    assert not pd.read_csv(tmp_path / "table_yearly_metrics.csv").empty


def test_worldwide_cli_with_synthetic_workbook_and_portable_fonts(tmp_path):
    rows = []
    for year in range(1977, 2026):
        for rank in range(1, 22):
            rows.append({"Year": year, "Rank": rank, "Release Group": "Star Wars" if rank == 1 else f"Example {rank}", "Worldwide": 1000000 / rank, "Foreign": 500000 / rank})
    source = tmp_path / "synthetic.xlsx"
    pd.DataFrame(rows).to_excel(source, sheet_name="All Movies", index=False)
    output = tmp_path / "out"
    result = subprocess.run([sys.executable, str(ROOT / "world_box_office_analysis_en.py"), "--input", str(source), "--output", str(output)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert len(list((output / "figures").glob("*.png"))) == 5
    assert len(pd.read_csv(output / "tables" / "richni_pokaznyky.csv")) == 49


def test_worldwide_missing_input_has_actionable_error(tmp_path):
    result = subprocess.run([sys.executable, str(ROOT / "world_box_office_analysis_en.py"), "--input", str(tmp_path / "missing.xlsx")], capture_output=True, text=True)
    assert result.returncode == 2
    assert "Supply the worldwide dataset with --input" in result.stderr
