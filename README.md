# Infinite Connections

This repository contains the teacher-facing code and demo assets for **Infinite Connections**, a single-author STA 561 final project by **Yunxi Kong**.

The project builds and screens NYT Connections-style puzzle boards, then serves a playable web demo backed by a curated puzzle bank.

## What is included

- core generator, validator, solver, and wordplay code in `infinite_connections/`
- runnable scripts for setup, generation, audit, and local serving in `scripts/`
- the playable website in `web/`
- cached reference data and a curated puzzle bank in `data/`
- a small automated test suite in `tests/`

This snapshot intentionally omits local-only draft reports, large intermediate candidate dumps, and review caches that are not needed for grading the code/demo.

## Quick start

### 1. Install dependencies and build the reference cache

```powershell
.\RUN_SETUP.bat
```

### 2. Start the website

```powershell
python scripts\serve.py
```

Then open the local URL printed in the terminal, usually:

```text
http://127.0.0.1:8000/web/
```

### 3. Optional: regenerate a local batch and rebuild the curated bank

```powershell
python scripts\generate_v2_batch.py --count 500 --seed 561 --mode mixed --theme-prob 0.25 --offline-themes --no-rewrite --validate --out data\puzzles\curated_refresh.json
python scripts\audit_puzzle_batch.py --input data\puzzles\curated_100_v2.json --history data\history\unified_reference.json
```

## Main teacher-facing assets

- `web/` — playable interface and review views
- `data/puzzles/curated_100_v2.json` — curated play bank used by the website
- `data/reports/dashboard.json` — cached evaluation summary shown in the review tab
- `data/reports/history_analysis.json` — historical reference summary
- `data/eval/audit_*.json` — audit summaries for the curated bank and 10K batch

## Validation

The snapshot was checked with:

```powershell
python -m unittest discover -s tests
node --check web\app.js
python scripts\serve.py
```
