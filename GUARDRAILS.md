# SmartSQLQuery — Guardrails

**Open this file before you start a task and again before you merge.**  
Architecture: [PHASEDOWN.md](PHASEDOWN.md). Task list: [ROADMAP.md](ROADMAP.md). This file is **how work is executed**: git, GitHub, pytest, ignore rules, secrets, safety, and definition of done.

If a later idea conflicts with this file, **this file wins** unless PHASEDOWN is explicitly updated first.

---

## 1. Why these guardrails exist

* Every [ROADMAP.md](ROADMAP.md) task must be **finishable in isolation** on a branch, with **green tests** on GitHub before merge.
* LLM-generated SQL is untrusted. After Phase 2 exists, **no execute path may skip** `safe_execute`.
* Sample databases, gold files, and docs are source; secrets, caches, and local DBs-journal files are not.
* Status in ROADMAP must match git reality (`Done` only after CI green and merge).

---

## 2. Documents and which one to follow

| Question | File |
|---|---|
| What are we building and what is out of scope? | PHASEDOWN.md |
| What is the next module and which files? | ROADMAP.md |
| How do I run a task end-to-end (branch, tests, PR)? | **This file** |
| How do I run the app? | README.md (from T-4.14) |

Do not add LangChain, extra LLM vendors, voice, or Spider as “while I’m here” work. That is a PHASEDOWN change, not a task bonus.

---

## 3. Task execution workflow (do this every time)

Copy this sequence. A task is not complete if any step is skipped.

```
1.  Pick        → lowest Not-started task whose dependencies are Done
2.  Branch      → from up-to-date main, named per §4
2.5 Env         → create or activate .venv; install deps (§5-venv)
3.  Status      → ROADMAP: that task → In progress
4.  Build       → only files listed for that task (plus tests)
5.  Tests       → add/update pytest for the task’s “Done when”
6.  Local green → pytest command for this phase (§6) exits 0
7.  Guard check → §8 safety, §9 gitignore, §10 secrets
8.  Commit      → message references task id (T-1.04)
9.  Push + PR   → GitHub Actions must be green (§7)
10. Merge       → squash or merge as repo default; delete branch
11. Status      → ROADMAP + master board: Done
```

### 3.1 Pick (step 1)

* Do not start Phase *N+1* implementation that **executes user/LLM SQL** until Phase 2 `T-2.10` is Done.
* You **may** start T-3.01–T-3.02 (settings, fake provider) in parallel with late Phase 2 only if they do not call the database with model output.
* Blocked = dependency not Done, or missing API key that a **required** live test needs. Prefer fakes so CI never needs keys.

### 3.2 Build (step 4)

* Stay inside the **Files involved** column for that task. Touching unrelated packages needs a sentence in the PR (“needed because …”).
* New Python modules: tests in the matching `tests/` path the same PR.
* Do not commit `__pycache__`, `.env`, `.chroma/`, or regenerated junk (§9).

### 3.3 “Done when” (step 5–6)

ROADMAP’s **Done when** is the acceptance test. Translate it into pytest names, not a manual click-only demo (UI tasks: pytest for the backend path **plus** a short PR checklist for the browser).

### 3.4 After merge (step 11)

* Update **both** the phase table and the master status board in ROADMAP.md (same commit as the task or a tiny follow-up on `main` is OK if you forgot—do not leave `In progress` on merged work).

---

## 4. Git and GitHub

### 4.1 `main` is always releasable-for-that-phase

* `main` must be green on CI.
* Do not push commits directly to `main` once the remote exists. Use PRs.

### 4.2 Branch naming

```
task/<task-id>-<short-kebab>

Examples:
  task/T-1.04-schema-inspector
  task/T-2.07-limit-rewrite
  task/T-3.11-streamlit-shell
```

* One ROADMAP task per branch. If a task is huge, still one branch; do not invent `T-1.04a` without adding a row to ROADMAP.
* `fix/` and `chore/` only for CI/docs/gitignore that are not a numbered task (`chore/gitignore`, `fix/ci-sqlite-path`).

### 4.3 Commits

```
T-1.04: extract FK graph in schema inspector

T-2.11: add stacked-query fixtures
```

* Imperative, **why** in the body if the diff is non-obvious.
* Never `--no-verify` unless the hook is broken and the PR describes the bypass.

### 4.4 Pull requests

**Title:** `T-1.04: Schema inspector (tables, columns, keys)`

**Body template:**

```markdown
## Task
- ID: T-x.xx
- ROADMAP: Done when = …

## Changes
- …

## Tests
- Commands run: `pytest …`
- New/updated files: `tests/…`

## Guardrails
- [ ] No secrets committed
- [ ] LLM/user SQL goes through `safe_execute` (if this PR executes SQL)
- [ ] ROADMAP status will be set to Done after merge

## Manual (UI tasks only)
- [ ] streamlit: pick university → ask … → see SQL + table
```

* **Require CI green** before merge (GitHub branch protection when the remote exists: `main` requires the `test` workflow).
* Reviewer or you: do not merge with failing or skipped-all tests.

### 4.5 Tags / releases (optional)

* `v0.1.0-phase1` after T-1.13. Not required for task completion.

---

## 5. Virtual environment (venv)

Every task is built and tested inside `.venv/`. The directory is already gitignored (`.gitignore` line `.venv/`). Follow these steps once per clone and once per new task branch.

### 5.1 Create (once per clone)

```bash
# Windows PowerShell
python -m venv .venv

# macOS / Linux
python3 -m venv .venv
```

### 5.2 Activate (every shell session / task)

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows CMD
.venv\Scripts\activate.bat

# macOS / Linux
source .venv/bin/activate
```

Your prompt will show `(.venv)` when active.

### 5.3 Install dependencies

```bash
# After activate — install runtime deps
pip install -r requirements.txt

# Once pyproject.toml exists (from T-1.01) — editable install
pip install -e .

# Install test runner (always required)
pip install pytest
```

### 5.4 Rules

* **Never run `pytest` outside the venv.** If `which python` (or `where python` on Windows) does not point inside `.venv/`, activate first.
* **Never commit `.venv/`.** It is machine-specific and already gitignored.
* **Never `pip install` globally** for this project. All dependencies live in `.venv/`.
* Each fresh branch: re-activate (the venv itself does not change, only activation is needed).
* If `requirements.txt` changes in a PR, run `pip install -r requirements.txt` again after pulling.

### 5.5 GitHub Actions

GitHub Actions uses `actions/setup-python` which provides a clean, isolated Python environment equivalent to a venv. An explicit `python -m venv` step is therefore **not needed in CI** — the `pip install -r requirements.txt` step installs directly into the Actions runner's managed environment. Developers working locally always need the venv.

---

## 6. Definition of done (every task)

A task may be marked **Done** only if **all** of the following are true:

1. ROADMAP **Done when** is satisfied.
2. **pytest is green** for the required selection (§6) locally **and** on the GitHub Actions run for that PR.
3. New behavior has tests (or an explicit exception in the PR: “T-4.15 Docker cannot be asserted in pytest; compose file added, manual note in PR”).
4. No new files that belong in `.gitignore`.
5. No API keys, DSNs with passwords, or `.env`.
6. After Phase 2: any execution of non-gold, non-inspector SQL uses `smartsql.safety.pipeline.safe_execute` (or successor name).
7. PR merged to `main`.
8. ROADMAP status updated to `Done`.

**Not done:** “works on my machine,” Streamlit screenshot without tests for the Python path, commented-out failing tests, `pytest.mark.skip` on the task’s own acceptance test.

---

## 7. Pytest policy (green on every task branch)

### 7.1 Tooling

* **pytest** is the only required runner. Put config in `pytest.ini` or `[tool.pytest.ini_options]` in `pyproject.toml` (add in T-1.01 / T-1.13).
* Default CI: Python **3.11**, Ubuntu, SQLite only.
* Live network/LLM/MySQL/Ollama tests **must** be marked and **skipped** when the resource is absent so CI stays green.

**Required markers** (register in pytest config):

| Marker | Use |
|---|---|
| `mysql` | Needs `MYSQL_DSN` |
| `llm` | Needs cloud API key |
| `ollama` | Needs local Ollama |
| `slow` | Full gold EX with a real model (Phase 4 eval); not default CI |
| `security` | AST fixture pack |

Default `pytest` (no extra flags) **must not** require keys or MySQL.

### 7.2 What must pass on GitHub for a PR

Always:

```bash
pytest -q --tb=short
```

That command must exit **0**. It includes unit tests and SQLite integration tests. It excludes `mysql`, `llm`, `ollama`, `slow` via default `addopts` or by not collecting them unless you use `-m`.

Recommended `pytest.ini`:

```ini
[pytest]
testpaths = tests
pythonpath = .
markers =
    mysql: needs MySQL
    llm: needs cloud LLM key
    ollama: needs Ollama daemon
    slow: long eval / live generation
    security: adversarial SQL fixtures
addopts = -q --strict-markers
filterwarnings = ignore::DeprecationWarning
```

If you use `addopts = -m "not mysql and not llm and not ollama and not slow"`, CI stays green; developers run extra marks locally.

### 7.3 Per-phase required tests (map to tasks)

When you finish a task, **at least** the tests listed for that task (and all earlier tasks in the phase) must be in the default pytest path and passing.

| Task(s) | Must be green (default pytest) |
|---|---|
| T-1.01 | Import `smartsql` (smoke test OK) |
| T-1.02 | Unknown profile errors; SQLite healthcheck |
| T-1.03 | Parameterized SELECT + `elapsed_ms` + row cap |
| T-1.04 | Inspector FK fixture |
| T-1.05 | Comment merge from YAML |
| T-1.06 | Sampler includes low-card, skips high-card |
| T-1.07 | Hash stable; DDL contains FK |
| T-1.08–T-1.10 | Inspector sees seeded tables (can be one test per DB) |
| T-1.11 | Gold loader validation |
| T-1.12–T-1.13 | **All gold SQL execute** on SQLite via execute helper |
| T-2.01–T-2.09 | Unit tests per module (parse, walker, limits, …) |
| T-2.10 | Pipeline: gold allow, `DELETE` deny |
| T-2.11 | `tests/security/` parametrize, all `reject` fail closed |
| T-2.12 | All gold SQL through `safe_execute` |
| T-3.02–T-3.10 | Fake provider: rewrite (≥5), retry, ambiguity, explainer, `ask()` smoke |
| T-3.12 | `safe_execute("DROP …")` denied (no UI required in CI) |
| T-3.14 | Full agent suite without `llm` mark |
| T-4.02 | Bad glossary fragment rejected |
| T-4.05–T-4.07 | Retrieve/few-shot/grounding unit tests (fixture index, no big model download if possible; pin a tiny embedding or mock embeddings in CI) |
| T-4.09 | Chart heuristic shapes |
| T-4.11 | Eval runner with **fake** provider writes JSON |
| T-4.12 | Cache hit test with fake provider |
| T-4.13 | Recall test on **frozen fixture index** (no live LLM) |

**CI must stay green without downloading a 400MB embedding model** if that would make Actions flaky. Mock the embedding function in unit tests; optional workflow `embeddings` can run nightly.

### 7.4 Local commands (cheat sheet)

```bash
# Activate venv first (every session — see §5.2)
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\Activate.ps1       # Windows PowerShell

# Same as GitHub (must pass before push)
pytest -q --tb=short -m "not mysql and not llm and not ollama and not slow"

# Security pack
pytest -q -m security

# Live LLM (your machine, never required for merge)
pytest -q -m llm

# MySQL optional
pytest -q -m mysql
```

### 7.5 Coverage (optional, not a merge blocker until T-4.13)

* Do not fail CI on coverage % in early phases.
* Prefer **security + gold + retry** tests over chasing 85% line coverage.

### 7.6 Flakes

* No `time.sleep` for LLM. Fake providers are deterministic.
* Do not depend on row order unless the test sorts or uses `ORDER BY`.
* Gold EX compares **bags of rows** (sort all columns) unless the gold question is order-sensitive.

---

## 8. GitHub Actions (required once the repo is on GitHub)

Create `.github/workflows/test.yml` no later than **T-1.13**. Until then, local pytest is the bar; the first PR that adds tests should add this workflow.

> **venv in CI:** GitHub Actions uses `actions/setup-python` which creates an isolated managed environment — a dedicated `python -m venv` step is not required. The `pip install -r requirements.txt` run installs into that environment directly. Local developers must always activate `.venv/` (§5) before running pytest.

```yaml
name: test

on:
  push:
    branches: [main]
  pull_request:

jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Test
        run: pytest -q --tb=short -m "not mysql and not llm and not ollama and not slow"
        env:
          # SQLite paths only; never put real keys here
          SMARTSQL_ENV: test
```

**Rules:**

* Do **not** add GitHub Secrets for LLM keys just to make CI “smarter.” Default CI is fake/SQLite.
* `main` branch protection: require workflow `test` / job `pytest`.
* A red X on the PR means the task is not Done. Fix or revert; do not merge and “fix later.”

Optional later workflow: `eval.yml` `workflow_dispatch` with a secret key for T-4.11 live runs.

---

## 9. Product and safety guardrails (code)

These apply from the first line of Phase 2 onward. Phase 1 may run gold SQL through `execute_select` only inside tests.

1. **Fail closed.** Parse errors, unknown profiles, missing DBs → error objects, not empty DataFrames that look like success.
2. **sqlglot is the security parser.** Regex prefilter is optional and never sufficient.
3. **Read-only execution connection** plus AST. Tests must prove `DELETE` fails on the execution engine (T-2.08).
4. **LIMIT** only on row-returning queries; do not wrap pure `AVG`/`COUNT`.
5. **Glossary/OKF SQL fragments** go through the same AST gate (T-4.02) before prompt injection.
6. **No silent ambiguity.** Two interpretations → clarify, do not execute.
7. **Retries ≤ 3.** No unbounded LLM loops.
8. **Show SQL** in the UI beside results (Phase 3).
9. **RAG collections are per `profile_id` + `schema_hash`.** No cross-DB retrieval.
10. **Cache keys** include `profile_id` and `schema_hash`. Never cache results across profiles.
11. Human-edited SQL in Streamlit still uses `safe_execute`.

If a task makes any of these weaker, it is a defect, not an optimization.

---

## 10. Gitignore (canonical list)

Maintain a root `.gitignore` (create in T-1.01). The committed file must include **at least** the following. Do not “force add” these files.

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
env/
*.egg-info/
.eggs/
dist/
build/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
.tox/

# Secrets and local env
.env
.env.*
!.env.example
*.pem
credentials.json
service-account*.json

# OS / editor
.DS_Store
Thumbs.db
.idea/
.vscode/
*.swp

# SQLite junk (keep seeded *.db if you choose to commit them)
*.db-journal
*.db-wal
*.db-shm

# Vector store / caches
.chroma/
*.chroma/
.cache/
__cache__/

# Eval outputs (commit fixtures, not machine-specific last runs if they contain SQL from live LLMs)
data/eval/last_run.json
data/eval/*.local.json

# Streamlit
.streamlit/secrets.toml

# Docker
# (do not ignore Dockerfile)

# Logs
*.log
logs/
```

### 10.1 What **should** be committed

* `data/university.db`, `data/ecommerce.db`, `data/hr_analytics.db` **or** only `data/seeds/*.sql` plus a seed script (pick one in T-1.08; if DBs are large/binary-noisy, prefer seeds + `scripts/seed_all.py` and gitignore `data/*.db` except in CI generate-from-seed).
* `data/gold/*.yaml`, `data/schema_comments/*.yaml`, `data/knowledge/**`
* `.env.example` with **empty** placeholders
* `tests/security/fixtures.yaml`

**Recommendation:** commit **seed SQL + a seeder**, generate `.db` locally and in CI. If you commit `.db` files, they must not contain personal data.

### 10.2 Never commit

* API keys, MySQL passwords, production DSNs
* `.chroma/` indexes (rebuild in T-4.04)
* User-uploaded CSV/Parquet (if T-4.16 happens)

---

## 11. Secrets and configuration

* All secrets via environment / `.env` (never read in code from a committed file).
* `.env.example` lists names only: `GEMINI_API_KEY=`, `GROQ_API_KEY=`, `MYSQL_DSN=`.
* Streamlit: use env or `st.secrets` locally; **commit no `secrets.toml`**.
* GitHub: no keys in workflow YAML, logs, or PR screenshots.
* If a key is leaked: rotate immediately; do not “rewrite git history” unless you know the process; assume the key is burned.

Named profiles only (T-1.02). No “paste any connection string” in v1 UI.

---

## 12. Code and repo conventions

* Package name: `smartsql`. App entry: `app/streamlit_app.py`.
* Python 3.11+, type hints on public functions, small modules matching ROADMAP paths.
* No wildcard `import *`.
* SQL in tests: prefer fixtures under `tests/fixtures/` or inline strings; adversarial SQL lives in `tests/security/fixtures.yaml`.
* Do not add dependencies outside the PHASEDOWN stack table without a ROADMAP/PHASEDOWN note.
* Format: unformatted PRs are allowed in v1 unless you add `ruff`; if `ruff` is added, CI must run it.

---

## 13. Data and gold files

* Gold `gold_sql` must remain valid **SELECT**s that pass Phase 2 once T-2.12 exists.
* Changing seed data requires re-checking `expected_row_count` / EX.
* Jargon/ambiguous tags must stay consistent with PHASEDOWN (clarification vs execute).

---

## 14. LLM and cost guardrails

* Default tests: **Fake provider**.
* Do not call live APIs in GitHub Actions on every push.
* Retry cap 3 (T-3.08). No recursive tools.
* Prompts and gold questions may be committed; **responses from live models** in `last_run.json` should stay gitignored if they are bulky or environment-specific.

---

## 15. UI / Streamlit guardrails (Phase 3+)

* Browser checks are **in addition to** pytest, not a replacement (user rule: verify UI when you change it).
* CI cannot click Streamlit; keep `ask()` and `safe_execute` fully tested without the UI.
* PR manual checklist for T-3.11–T-3.13 and T-4.10.

---

## 16. Pre-push checklist (print this)

```
[ ] Branch is task/T-x.xx-…
[ ] .venv activated: `python --version` shows 3.11+ and path is inside .venv/
[ ] ROADMAP Done when implemented
[ ] pytest -m "not mysql and not llm and not ollama and not slow"  → 0  (run inside .venv)
[ ] New tests added for this task
[ ] No .env, keys, .chroma, __pycache__, .venv/ committed
[ ] After T-2.10: execute paths use safe_execute
[ ] PR title has task id
[ ] CI green on GitHub
[ ] After merge: ROADMAP status Done (phase table + master board)
```

---

## 17. Phase completion gates

You may announce a **phase complete** only when:

| Phase | Gate |
|---|---|
| 1 | T-1.13 Done, default pytest green, gold SQL all execute |
| 2 | T-2.11 + T-2.12 Done, security fixtures green, gold through `safe_execute` |
| 3 | T-3.14 Done, fake-provider agent tests green, UI PR checklist done |
| 4 / v1 | T-4.13, T-4.14, T-4.15 Done; T-4.12/T-4.16 optional |

---

## 18. Exceptions

The only valid reasons to merge with a skip:

* Upstream GitHub Actions outage (merge with local green + note; re-run CI after).
* Marked `llm`/`mysql` tests—these must **not** be in the default job.

“I will add tests in the next task” is **not** a valid exception.

---

## 19. Quick file index (copy into the repo when the task says so)

| Path | When | Notes |
|---|---|---|
| `.venv/` | T-1.01 — `python -m venv .venv` | gitignored; never commit |
| `.gitignore` | T-1.01 (contents = §10) | must include `.venv/` |
| `pytest.ini` | T-1.01 / T-1.13 (contents = §7.3) | |
| `.github/workflows/test.yml` | T-1.13 (contents = §8) | no venv step needed in CI |
| `.env.example` | T-1.02 / T-3.01 | |
| `GUARDRAILS.md` | this file — keep updated if workflow changes | |
