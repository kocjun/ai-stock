# Repository Guidelines

## Project Structure & Module Organization
Core analytics live in `core/`, split into `agents/` (CrewAI entrypoints), `modules/` (analysis logic), `tools/` (Crew tools), and `utils/` (shared helpers). The `paper_trading/` package drives the live dashboard, execution engine, and performance reporter. Automation lives in `scripts/`, docs in `docs/`, and infrastructure in `docker/`. Persisted artifacts (`logs/`, `reports/`, `postgres-data/`, `n8n-data/`) stay untracked.

## Build, Test, and Development Commands
- `python3 -m venv .venv && source .venv/bin/activate` prepares an isolated Python 3.11 environment.
- `pip install -r requirements.txt` installs required Python packages.
- `cd docker && docker-compose up -d` boots PostgreSQL and n8n; use `docker-compose logs -f` for diagnostics.
- `python core/agents/integrated_crew.py` runs the end-to-end investment workflow; individual agents can be launched from `core/agents/`.
- `./scripts/run_daily_collection.sh` and `./scripts/run_weekly_analysis.sh` mirror the cron pipelines for local drills.
- `./test_all_workflows.sh` sequentially exercises every Crew-based workflow for smoke validation.

## Coding Style & Naming Conventions
Favor PEP 8: four-space indentation, snake_case modules, and explicit type hints on public functions. Keep module docstrings explaining each agent or tool. Name scripts with verbs (`run_*`, `setup_*`) and keep env vars uppercase (`N8N_WEBHOOK_URL`). Route dashboards and analytics artifacts to their domain folders instead of `core/`.

## Testing Guidelines
Unit-style checks live in `tests/`; export `PYTHONPATH=core/modules:core/tools` and ensure the database is reachable. Run `pytest tests` for fast feedback, then `python test_workflows.py` to validate n8n integration. Finish with `./test_all_workflows.sh` to confirm sequencing and archive output in `reports/`. Update `tests/TEST_CHECKLIST.md` when coverage changes and add fixtures before hitting live feeds.

## Commit & Pull Request Guidelines
Git metadata is not bundled here, so follow Conventional Commits (e.g., `feat(core): add risk alert thresholds`) with imperative subjects under 72 characters. Document rationale, data sources, and follow-ups in the body. Pull requests need a summary, command logs or screenshots (notably for `paper_trading/dashboard.py`), linked issues, and rollback notes. Flag schema or scheduler changes up front and tag affected owners.

## Environment & Security Notes
Copy `.env.example` to `.env`, populate secrets, and keep credentials out of version control. Stateful services write to `postgres-data/`, `n8n-data/`, and `logs/`, so scrub sensitive rows before sharing. Prototype agents under `core/agents/experiments/` or a feature branch, and purge transient data before merging.
