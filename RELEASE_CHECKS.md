# Release verification

- 4 regression tests passed.
- Full Ukrainian analysis executed on the included 2,844-row workbook: nine figures and analytical tables generated; annual gross reconciliation difference is zero.
- Worldwide analysis executed on a clearly synthetic 1977–2025 fixture: five figures and three tables generated.
- Missing worldwide input produces an actionable command-line error.
- The original worldwide source workbook is not present, so published worldwide findings were not independently regenerated.

## Verification environment

Checked locally on 2026-11-20 with Python 3.14.2 on macOS. Runtime and test dependency versions are recorded in `constraints.txt`. Dependency resolution was also checked for the SPPACEU requirements targeting Python 3.12; the GitHub Actions platform/version matrix has been configured but has not run as part of this local audit.

## Repeat the offline checks

```sh
python -m pip install -r requirements-dev.txt -c constraints.txt
python -m pytest -q
```

No paid API calls were made. Tests use synthetic data and mocked service responses where external inputs are required. No Git commit, release tag, push, or GitHub Release was created by this preparation.
