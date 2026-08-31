# SmartSQLQuery — Task Roadmap

Work-breakdown for implementing [PHASEDOWN.md](PHASEDOWN.md). This file is the **checklist**: what to build, in what order, which files to touch, and whether it is done. Before starting or merging a task, follow [GUARDRAILS.md](GUARDRAILS.md) (branch, pytest green on GitHub, gitignore, definition of done).

**Status values:** `Not started` · `In progress` · `Blocked` · `Done`

**Dependency column:** task IDs that must be **Done** (or at least mergeable) before this task can finish. `—` means no prior task.

**How to use:** complete Phase *N* tables before starting Phase *N+1* except where a dependency says otherwise. Do not skip Phase 2 before any LLM execute path.

---

# Phase 1 — Data plane, schema inspector, and gold sets

**Goal:** named SQLite databases, a working inspector, gold NL↔SQL files, and tests that run **hand-written** SELECTs. No LLM. No Streamlit.

---

### T-1.01 — Repository skeleton and Python package

Create the installable layout so later tasks have a home. Add `smartsql/` as a package, `tests/`, `data/`, `requirements.txt` (or `pyproject.toml`) with Python 3.11+, SQLAlchemy, Pandas, pytest. Add `.gitignore` (`.venv/`, `venv/`, `__pycache__`, `.env`, `*.db-journal`). **Create the project virtual environment** (`python -m venv .venv`) and document the activate commands for Windows and macOS/Linux. Install deps via `pip install -r requirements.txt` inside the venv. Do **not** add Streamlit, sqlglot, or LLM SDKs yet unless they are listed as comments for later phases.

**Done when:** `python -c "import smartsql"` works from the repo root (or via editable install) **inside `.venv/`**. Empty `__init__.py` files exist for `smartsql`, `smartsql.db`. `.venv/` is present locally, is gitignored, and `pip install -r requirements.txt` inside it succeeds.

---

### T-1.02 — Named profile registry and connection manager

Implement a registry of **named** database profiles (`university`, `ecommerce`, `hr`, optional `mysql`). Each profile has dialect (`sqlite` / `mysql`), path or DSN from environment, pool/timeout settings. `get_engine(profile_id)` returns a SQLAlchemy engine. `healthcheck(profile_id)` runs a trivial `SELECT 1`. Fail clearly if the file is missing. No UI connection-string box.

**Done when:** connecting to a throwaway SQLite file succeeds; unknown profile raises a typed error.

---

### T-1.03 — Read helper: parameterized SELECT, timing, client row cap

A single function `execute_select(engine, sql, params=None, max_rows=1000)` that:

* Accepts only caller-supplied SQL in this phase (tests/gold), still using bound parameters where the test provides them.
* Records wall-clock milliseconds.
* Truncates the fetched result to `max_rows`.
* Returns a Pandas DataFrame plus a small metadata dict (`row_count`, `elapsed_ms`, `truncated`).

This is **not** the safety layer. It exists so inspector tests and gold SQL have one execution path. Phase 2 will wrap it.

**Done when:** a parameterized `SELECT` test returns expected rows and a non-zero `elapsed_ms`.

---

### T-1.04 — Schema inspector (tables, columns, keys)

Introspect a live engine into a canonical Python/JSON structure:

* Tables: name, comment/description if the dialect exposes it.
* Columns: name, SQL type, nullable, default, comment.
* Primary keys and foreign keys (column pairs, on-delete if available).
* Derived **join-path list**: undirected edges from FKs (table A.col → table B.col).

SQLite often lacks comments in `PRAGMA`; that is handled in T-1.05. Inspector must still work with empty comments.

**Done when:** inspector on a fixture DB with two tables and one FK returns both tables, all columns, PK, and the FK edge.

---

### T-1.05 — Schema comments sidecar

If SQLite has no native comments, load `data/schema_comments/<profile>.yaml` (table and column descriptions) and merge them into the inspector snapshot. Missing sidecar = empty comments, not a crash. This text is what RAG and the LLM will use later.

**Done when:** a YAML comment for `students.name` appears in inspector JSON after merge.

---

### T-1.06 — Low-cardinality value sampler

For each column, if distinct count is below a threshold (default 50) and the type is string/enum-like, store a sample of distinct values on the snapshot. Skip high-cardinality columns (emails, UUIDs, free text). Cap work with `LIMIT` in the sampling query. Never sample BLOBs.

**Done when:** a `department` column with 5 values is listed; a unique `email` column is not.

---

### T-1.07 — Snapshot serializers and schema hash

From the canonical snapshot, emit:

1. JSON (canonical, stable key order for hashing).
2. Dialect DDL string suitable for an LLM prompt.
3. Markdown summary (tables as headings, columns as lists) for a future UI explorer.

Compute `schema_hash` (SHA-256 of canonical JSON). Store hash on the snapshot object. Phase 4 uses it to invalidate vector indexes.

**Done when:** two inspect calls on an unchanged DB produce the same hash; adding a column changes the hash. DDL string contains the FK.

---

### T-1.08 — Sample database: `university.db`

Build `data/university.db` with FKs, seed rows, and at least one concept that is **not** a column name (e.g. “high performer”). Suggested tables: Students, Courses, Enrollments, Instructors, Departments, Grades. Include a department code vs name so later value-grounding has something to map. Provide a SQL seed script (`data/seeds/university.sql`) so the DB is reproducible (`sqlite3` or a Python seeder).

**Done when:** inspector lists all tables and FKs; a manual join query returns rows.

---

### T-1.09 — Sample database: `ecommerce.db`

Same standard as T-1.08: Customers, Orders, OrderItems, Products, Categories, Payments. Include dates, money, statuses (`paid` / `refunded`) and a jargon gap (e.g. “churned customer” not a column). Seed script + reproducible DB file.

**Done when:** inspector + a revenue-by-category gold-style join works.

---

### T-1.10 — Sample database: `hr_analytics.db`

Employees, Departments, Salaries, PerformanceReviews, Projects (and a link table if needed). Include “active employee” or similar as a non-column metric. Seed script + DB file.

**Done when:** inspector + an average-salary-by-department query works.

---

### T-1.11 — Gold file format and loader

Define `data/gold/<profile>.yaml` schema:

* `id` (stable string)
* `question`
* `gold_sql`
* `required_tables` (list)
* `tags` (`filter`, `join`, `aggregate`, `ambiguous`, `jargon`, …)
* optional `expected_row_count`

Loader: `load_gold(profile_id) -> list[GoldItem]`. Validate required keys. Reject empty SQL.

**Done when:** a 3-item fixture YAML loads; a missing-key file raises.

---

### T-1.12 — Gold questions: fill 50–80 across three DBs

Author the actual questions. Mix easy filters, 2–3 table joins, `GROUP BY`, and **at least 5** `ambiguous` and **at least 5** `jargon` tags (jargon can wait for glossary in Phase 4 but the questions must exist). Every `gold_sql` must execute successfully via T-1.03 on the matching DB.

Split roughly evenly across university / ecommerce / hr.

**Done when:** a pytest loop executes all gold SQL; zero operational errors; count is in 50–80.

---

### T-1.13 — Phase 1 test suite

Tests for: unknown profile; SQLite healthcheck; inspector FK graph on all three DBs; hash stability; sampler threshold; gold loader; gold SQL execution. MySQL tests marked `@pytest.mark.mysql` and skipped without `MYSQL_DSN`.

**Done when:** `pytest tests/phase1` (or `tests/db`) is green on a clean machine with only SQLite **run from inside `.venv/`** (see GUARDRAILS.md §5).

---

## Phase 1 — task table

| Task num | Plan dependency | Status | Files involved |
|---|---|---|---|
| T-1.01 | — | Not started | `pyproject.toml` or `requirements.txt`, `.gitignore`, `.venv/` (local only — gitignored), `smartsql/__init__.py`, `smartsql/db/__init__.py`, `tests/__init__.py` |
| T-1.02 | T-1.01 | Not started | `smartsql/db/profiles.py`, `smartsql/db/connection.py`, `.env.example` (SQLite paths only) |
| T-1.03 | T-1.02 | Not started | `smartsql/db/execute.py`, `tests/db/test_execute.py` |
| T-1.04 | T-1.02 | Not started | `smartsql/db/inspector.py`, `smartsql/db/models.py`, `tests/db/test_inspector.py` |
| T-1.05 | T-1.04 | Not started | `smartsql/db/comments.py`, `data/schema_comments/university.yaml`, `data/schema_comments/ecommerce.yaml`, `data/schema_comments/hr.yaml`, `tests/db/test_comments.py` |
| T-1.06 | T-1.04 | Not started | `smartsql/db/sampler.py`, `tests/db/test_sampler.py` |
| T-1.07 | T-1.04, T-1.05, T-1.06 | Not started | `smartsql/db/serialize.py`, `smartsql/db/hashing.py`, `tests/db/test_serialize.py` |
| T-1.08 | T-1.02 | Not started | `data/seeds/university.sql`, `data/university.db`, `scripts/seed_university.py` (optional) |
| T-1.09 | T-1.02 | Not started | `data/seeds/ecommerce.sql`, `data/ecommerce.db` |
| T-1.10 | T-1.02 | Not started | `data/seeds/hr_analytics.sql`, `data/hr_analytics.db` |
| T-1.11 | T-1.01 | Not started | `smartsql/eval/gold.py`, `data/gold/schema.md` (optional), `tests/eval/test_gold_loader.py` |
| T-1.12 | T-1.08, T-1.09, T-1.10, T-1.11, T-1.03 | Not started | `data/gold/university.yaml`, `data/gold/ecommerce.yaml`, `data/gold/hr.yaml` |
| T-1.13 | T-1.03 … T-1.12 | Not started | `tests/db/`, `tests/eval/test_gold_executes.py`, `pytest.ini` |

**Phase 1 complete when:** T-1.13 is Done and PHASEDOWN §1.4 exit criteria hold.

---

# Phase 2 — AST safety, read-only execution, LIMIT policy

**Goal:** nothing reaches the database except validated, rewritten, read-only SELECTs. Gold SQL from Phase 1 still runs.

---

### T-2.01 — Error types and validation result object

Define `SecurityViolationError`, `SqlParseError`, `SchemaMismatchError`, `LimitRewriteError`. Define `ValidationResult`: `ok`, `sql_original`, `sql_final`, `violations[]`, `warnings[]`. All later safety modules return this shape (or raise). Keep messages specific (`blocked: DROP`) so Phase 3 retries have signal.

**Done when:** unit tests construct and serialize the result object.

---

### T-2.02 — Optional regex pre-filter (non-authoritative)

Cheap scan for obvious `DROP`/`DELETE`/`INSERT`/`UPDATE`/`ALTER`/`TRUNCATE`/`CREATE`/`GRANT` as a fast reject. Document that this is **not** security. Must not be the only check. Comments like `SELECT 1 -- DROP` should still be decided by the AST (T-2.03), not this regex.

**Done when:** obvious `DROP TABLE t` fails here; a benign `SELECT department FROM students` passes.

---

### T-2.03 — sqlglot parse and dialect binding

Parse SQL with sqlglot using the profile dialect (`sqlite` / `mysql`). Fail **closed** on parse error (`SqlParseError`). Expose the AST to later walkers. No execute.

**Done when:** valid SELECT parses; `SELEC FROM` raises parse error; dialect is passed through (MySQL vs SQLite backtick/quote tests if cheap).

---

### T-2.04 — Mutation and admin AST walker

Walk the AST; reject DML (`INSERT`, `UPDATE`, `DELETE`, `MERGE`), DDL (`DROP`, `ALTER`, `TRUNCATE`, `CREATE`), admin (`GRANT`, `REVOKE`, `EXEC`/`EXECUTE`), destructive `PRAGMA`, `INTO OUTFILE` / `COPY`-style, attach-database patterns that sqlglot exposes. Recurse into CTEs and subqueries.

**Done when:** each forbidden class has at least one fixture that raises `SecurityViolationError`; a normal SELECT with CTE passes.

---

### T-2.05 — Multi-statement / stacked-query blocker

Reject more than one statement (`SELECT 1; DROP TABLE x`). Reject empty statements. Decide policy on trailing semicolon (usually allow **one** statement with optional trailing `;`).

**Done when:** stacked query fixtures fail; single SELECT with trailing `;` passes.

---

### T-2.06 — Static schema identifier check

Using the Phase 1 snapshot, verify every table and column referenced in the AST exists (with reasonable alias handling). Unknown table/column → `SchemaMismatchError` (retryable in Phase 3). Do not allow `SELECT *` to skip column checks on other clauses (`WHERE` still checked).

**Done when:** `SELECT nope FROM students` fails; gold SQL identifiers all pass on the matching snapshot.

---

### T-2.07 — LIMIT policy rewriter

On **row-returning** SELECT trees: if no LIMIT, inject default (100); if LIMIT > max (1000), cap it. Handle `UNION`/`UNION ALL` branches. Preserve `ORDER BY`. **Do not** inject LIMIT on pure aggregate queries (`COUNT`, `SUM`, `AVG`, `MIN`, `MAX` without extra non-aggregated row dump). Document the heuristic (no GROUP BY + only aggregate expressions in SELECT list, etc.).

**Done when:** tests cover unbounded SELECT, capped LIMIT, UNION, ORDER BY, and `SELECT AVG(salary) FROM employees` unchanged.

---

### T-2.08 — Read-only engine wrapper

For SQLite: open URI/`mode=ro` or equivalent query-only connection for **execution** (inspector in Phase 1 may still need a normal connection at seed time). For MySQL: document a read-only user; set session read-only when the server allows it. Application profiles in v1 must not point at a writable DSN for query execution.

**Done when:** a test that bypasses AST and issues `DELETE` against the **execution** engine fails at the driver/DB.

---

### T-2.09 — Statement timeout and fetch guards

Apply engine/driver timeouts. Keep T-1.03 max_rows. Optionally cap fetched bytes if cheap. Timeouts must be configurable (env).

**Done when:** a test can set a very low timeout (or mock) and see a controlled failure, not a hang.

---

### T-2.10 — Safe execute pipeline

Single entry `safe_execute(profile_id, sql)`:

1. Load snapshot (inspect or cache from T-1.07).
2. Regex pre-filter (optional).
3. Parse → mutation walk → multi-statement → schema check → LIMIT rewrite.
4. Execute on read-only engine via T-1.03.
5. Return DataFrame + metadata + `sql_final`.

Nothing in Phase 3/4 should call `execute_select` on user or LLM SQL except through this function.

**Done when:** gold SQL all succeed through `safe_execute`; a `DELETE` does not.

---

### T-2.11 — Security fixture pack (living)

Create `tests/security/fixtures.yaml` (50+ cases): comments, stacked queries, CTE wrappers, `UPDATE` in subquery if applicable, `PRAGMA`, case tricks. Each case: `sql`, `expect` (`reject` | `rewrite` | `allow`). Any future bypass is added here.

**Done when:** pytest parametrize runs the pack; all `reject` cases fail closed.

---

### T-2.12 — Phase 2 regression: gold still valid

Re-run all Phase 1 gold SQL through `safe_execute`. No false rejects on legitimate JOIN/GROUP BY/UNION if gold contains them.

**Done when:** gold execution test is green under the safety pipeline.

---

## Phase 2 — task table

| Task num | Plan dependency | Status | Files involved |
|---|---|---|---|
| T-2.01 | T-1.01 | Not started | `smartsql/safety/errors.py`, `smartsql/safety/result.py`, `tests/safety/test_errors.py` |
| T-2.02 | T-2.01 | Not started | `smartsql/safety/prefilter.py`, `tests/safety/test_prefilter.py` |
| T-2.03 | T-2.01 | Not started | `smartsql/safety/parse.py`, `requirements.txt` (add `sqlglot`), `tests/safety/test_parse.py` |
| T-2.04 | T-2.03 | Not started | `smartsql/safety/walker.py`, `tests/safety/test_walker.py` |
| T-2.05 | T-2.03 | Not started | `smartsql/safety/statements.py`, `tests/safety/test_statements.py` |
| T-2.06 | T-2.03, T-1.07 | Not started | `smartsql/safety/schema_check.py`, `tests/safety/test_schema_check.py` |
| T-2.07 | T-2.03 | Not started | `smartsql/safety/limits.py`, `tests/safety/test_limits.py` |
| T-2.08 | T-1.02 | Not started | `smartsql/db/readonly.py`, `tests/db/test_readonly.py` |
| T-2.09 | T-1.03, T-2.08 | Not started | `smartsql/db/execute.py`, `smartsql/db/connection.py`, `tests/db/test_timeout.py` |
| T-2.10 | T-2.02 … T-2.09 | Not started | `smartsql/safety/pipeline.py`, `tests/safety/test_pipeline.py` |
| T-2.11 | T-2.10 | Not started | `tests/security/fixtures.yaml`, `tests/security/test_fixtures.py` |
| T-2.12 | T-2.10, T-1.12 | Not started | `tests/eval/test_gold_safe_execute.py` |

**Phase 2 complete when:** T-2.11 and T-2.12 are Done and PHASEDOWN §2.4 exit criteria hold.

---

# Phase 3 — Agent loop, explanation, and thin UI

**Goal:** a person can pick a sample DB, ask a question, see SQL + explanation + table. Retries and follow-ups work. RAG is not required.

---

### T-3.01 — Settings and secrets

Load `.env` via python-dotenv: provider name, API keys, Ollama base URL, retry limit (default 3), default/max LIMIT (from Phase 2). Never commit `.env`. Expand `.env.example` with placeholder keys.

**Done when:** missing key produces a clear error at provider init, not a stack trace in the UI later.

---

### T-3.02 — LLM provider interface

`LLMProvider.generate(prompt: str) -> str` plus optional `generate_sql(...)`. No LangChain. Fake/scripted provider for tests (`EchoProvider` or recorded fixtures).

**Done when:** a unit test injects a fake provider and gets a string back.

---

### T-3.03 — Cloud adapter (Gemini **or** Groq)

Implement **one** hosted adapter chosen for the project. Map API errors to a small `ProviderError`. Keep SQL extraction robust (strip markdown fences).

**Done when:** a manual or marked integration test returns SQL-like text with a live key; CI skips without key.

---

### T-3.04 — Ollama adapter (optional local)

Same interface as T-3.03 against local Ollama (e.g. a coder model). Skip in CI if daemon is down.

**Done when:** documented `ollama pull` + one successful generate on a developer machine, or skip-marked test.

---

### T-3.05 — Dialect-aware prompt assembler (full schema)

Build the system/user prompt from: dialect notes, full T-1.07 DDL + join hints + comments, SELECT-only instructions, the (possibly rewritten) question. Return the prompt string for logging. No Chroma.

**Done when:** snapshot fixture → prompt contains table names and the user question.

---

### T-3.06 — Follow-up question rewriter

Given `history: list[{question, sql}]` and `new_utterance`, produce a **standalone** question. Use the LLM with a tight prompt, or rules for trivial cases (“only IT”). Do not dump raw chat into the SQL generator without this step. If history is empty, pass the utterance through.

**Done when:** at least five scripted dialogues in tests (fake LLM or snapshot) match expected standalone questions, including the salary/IT example from PHASEDOWN.

---

### T-3.07 — Ambiguity gate

Before execute: detect “need clarification” from (a) model JSON flag, or (b) heuristic (question matches two tables equally, gold `ambiguous` pattern). Return `clarifying_question` and **do not** call `safe_execute`. UI must render that text.

**Done when:** a fixture question returns clarification and zero DB execute calls (mock).

---

### T-3.08 — Self-correction loop (N ≤ 3)

Orchestrator:

1. Assemble prompt (include last error if retry).
2. Generate SQL.
3. `safe_execute`.
4. On parse/security/schema/DB error: append error + failed SQL + **relevant schema slice** (not the whole catalog if the error names a table/column). Retry until N.
5. On success: stop.
6. On exhaustion: return last SQL + user-facing error.

Log `attempts`, `llm_ms`, `db_ms`.

**Done when:** tests with a fake LLM that first returns a bad column, then a good query, succeed in ≤ 2 retries; a perpetual-bad fake stops at 3.

---

### T-3.09 — Deterministic SQL explainer

Walk sqlglot AST of `sql_final` into sections: tables, filters, joins, aggregations, sort/limit. Template English from the tree. **No invented predicates.** Optional later LLM polish is out of this task.

**Done when:** explainer on `SELECT AVG(salary) FROM employees WHERE department = 'IT'` mentions average, employees, IT, and not a fake JOIN.

---

### T-3.10 — Agent facade `ask()`

Public function used by UI and tests: `ask(profile_id, question, history=None, auto_execute=True) -> AgentResult` wiring T-3.06 → T-3.07 → T-3.05 → T-3.08 → T-3.09. If `auto_execute` is false, return SQL + explanation without execute (still run AST validate so DROP cannot sit in the editor as “valid”).

**Done when:** integration test with fake provider + university DB answers one gold `filter` question with a matching result table (or EX-style compare).

---

### T-3.11 — Streamlit shell: profile picker and question

`app/streamlit_app.py`: sidebar DB picker (three samples), text area, submit. Session state for history. Call `ask()`. Display errors from Phase 2 in plain language.

**Done when:** local `streamlit run` shows picker and can submit with a fake or live provider.

---

### T-3.12 — SQL panel: highlight, edit, human-in-the-loop run

Show `sql_final` in a text area (or streamlit-ace if you accept the extra dependency; otherwise `st.text_area`). Buttons: **Run edited SQL** (always `safe_execute`), toggle **Preview only / Auto-execute**. Edited SQL never bypasses Phase 2.

**Done when:** pasting `DROP TABLE students` from the editor is blocked in the UI with a security message.

---

### T-3.13 — Results, explanation, and diagnostics panels

DataFrame table; explanation sections from T-3.09; diagnostics: retries, `llm_ms`, `db_ms`, `schema_hash`, `sql_final` vs original. Clarification-only responses hide the table.

**Done when:** a successful join query shows all three panels; a clarification shows no table.

---

### T-3.14 — Phase 3 tests

Fake-provider tests for rewrite (5 dialogues), retry, ambiguity, explainer, `ask()` smoke, and “editor DROP” via `safe_execute`. Mark live-API tests so CI stays green.

**Done when:** `pytest` without keys is green; PHASEDOWN §3.4 is satisfied on a dev machine with one provider.

---

## Phase 3 — task table

| Task num | Plan dependency | Status | Files involved |
|---|---|---|---|
| T-3.01 | T-1.01 | Not started | `smartsql/settings.py`, `.env.example`, `requirements.txt` (`python-dotenv`) |
| T-3.02 | T-3.01 | Not started | `smartsql/agent/providers/base.py`, `smartsql/agent/providers/fake.py`, `tests/agent/test_providers.py` |
| T-3.03 | T-3.02 | Not started | `smartsql/agent/providers/gemini.py` **or** `groq.py`, `requirements.txt` (one SDK) |
| T-3.04 | T-3.02 | Not started | `smartsql/agent/providers/ollama.py` |
| T-3.05 | T-1.07, T-3.02 | Not started | `smartsql/agent/prompt.py`, `tests/agent/test_prompt.py` |
| T-3.06 | T-3.02, T-3.05 | Not started | `smartsql/agent/rewrite.py`, `tests/agent/test_rewrite.py` |
| T-3.07 | T-3.02 | Not started | `smartsql/agent/ambiguity.py`, `tests/agent/test_ambiguity.py` |
| T-3.08 | T-2.10, T-3.05 | Not started | `smartsql/agent/retry.py`, `tests/agent/test_retry.py` |
| T-3.09 | T-2.03 | Not started | `smartsql/agent/explain.py`, `tests/agent/test_explain.py` |
| T-3.10 | T-3.06, T-3.07, T-3.08, T-3.09 | Not started | `smartsql/agent/ask.py`, `smartsql/agent/result.py`, `tests/agent/test_ask.py` |
| T-3.11 | T-3.10 | Not started | `app/streamlit_app.py`, `requirements.txt` (`streamlit`) |
| T-3.12 | T-3.11, T-2.10 | Not started | `app/streamlit_app.py`, `app/components/sql_editor.py` |
| T-3.13 | T-3.11, T-3.09 | Not started | `app/streamlit_app.py`, `app/components/results.py` |
| T-3.14 | T-3.10 … T-3.13 | Not started | `tests/agent/`, `tests/app/` (optional) |

**Phase 3 complete when:** T-3.14 is Done and a human can finish the university join/aggregate flow in the browser.

---

# Phase 4 — Knowledge, visualization, eval, and packaging

**Goal:** jargon and large-schema retrieval, simple charts, honest gold EX, Docker demo. RAG default-off for small DBs, with a force flag.

---

### T-4.01 — Knowledge format decision and loader

Implement **OKF bundles** (preferred): `data/knowledge/<profile>/*.md` with YAML frontmatter (`type`, `title`, `description`). Types: `Table`, `Metric`, `Playbook`, `Term`. Alternative: `business_glossary.yaml` **named semantic layer** if OKF is too heavy—pick one and document in README.

Loader returns concept objects including optional `sql_fragment`.

**Done when:** university “high performer” concept loads with a fragment `grade >= 85` (or equivalent).

---

### T-4.02 — AST-gate knowledge fragments

Any `sql_fragment` from T-4.01 is parsed with sqlglot and must be an expression/predicate, not a mutation. Reject fragments that fail T-2.04. Only then inject into prompts or compose into SQL.

**Done when:** a fragment `1=1; DROP TABLE x` is rejected; `grade >= 85` is accepted.

---

### T-4.03 — Table embedding documents

From inspector snapshot, build one text document per table: metadata, column comments, FKs, low-cardinality samples. Used as Chroma documents.

**Done when:** university `students` document contains `student_id` and a sample department value if sampled.

---

### T-4.04 — Chroma index per database + hash invalidation

Collection name includes `profile_id` and `schema_hash` (or metadata filter). Embed with sentence-transformers (local) or an embedding API. On hash change, drop and rebuild. Persist under `.chroma/` (gitignore).

**Done when:** inspect → index → retrieve a table by a keyword from its comment; changing schema comments rebuilds (hash change).

---

### T-4.05 — Hybrid retriever (BM25 + dense) top-K

Retrieve top-K tables (default 5–8). Combine BM25 over document text with vector similarity. Return scores. If max score is below threshold: widen K, or fall back to full schema when table count is small, or signal “low confidence” to T-3.07.

**Done when:** gold items with `required_tables` of size 2 retrieve both in top-5 on a fixture index for at least a majority of a labeled subset (full Recall@5 gate is T-4.13).

---

### T-4.06 — Few-shot playbook retrieval

Index gold `(question, sql)` and OKF `Playbook` concepts. Retrieve top-3 similar questions for the prompt. Never retrieve playbooks from a **different** `profile_id`.

**Done when:** a question similar to a gold join pulls that gold SQL into prompt extras.

---

### T-4.07 — Categorical value grounding

Fuzzy-match entity spans in the question against T-1.06 samples only. RapidFuzz; threshold configurable. Emit mappings (`"CSE" → departments.code = 'CSE'`) into the prompt. No full table scans.

**Done when:** “computer science department” maps to the seeded code/name if present in samples.

---

### T-4.08 — Wire retrieval into `ask()` behind flags

Config: `rag_mode = off | auto | force`. `off`: Phase 3 full schema (default for sample DBs). `force`: top-K only (demo). `auto`: full schema if table count ≤ N (e.g. 15), else RAG. Inject glossary hits from T-4.01/T-4.02.

**Done when:** `force` prompt omits irrelevant tables on a toy snapshot with 20 fake tables (test fixture).

---

### T-4.09 — Plotly heuristic visualizer

From result DataFrame: bar (1 cat + 1 num), line (1 datetime + 1 num), KPI (1 scalar). Else table only. No crash on empty frames. Return a figure or `None`.

**Done when:** unit tests for the three shapes plus a “too messy → None” case.

---

### T-4.10 — UI chart switcher and CSV export

Streamlit: Table / Bar / Line (Bar/Line disabled if heuristic says no). Download CSV of the result. Excel/JSON optional, not required.

**Done when:** user can download CSV after a successful ask; chart toggle does not break the table.

---

### T-4.11 — Gold evaluation harness (EX, taxonomy, latency)

CLI or `python -m smartsql.eval.run --profile university`: generate via `ask()` (real or recorded), compare result bags to gold SQL results. Metrics: EX, error tags, p50/p95 `llm_ms`/`db_ms`. Write `data/eval/last_run.json`. Ablation flag `--no-glossary` for jargon subset.

**Done when:** a dry run on fake provider writes a JSON log with the expected keys.

---

### T-4.12 — Optional SQL cache (SQL only)

Key: `profile_id + schema_hash + normalized_question`. Store SQL string. Disable on follow-up until rewrite is standalone. No cross-profile hits. Skip result-set cache unless documented as sample-DB-only.

**Done when:** second identical question with fake provider does not call generate (or cache hit is logged).

---

### T-4.13 — Retrieval and viz tests; Recall@5 report

Parametrize gold `required_tables` through T-4.05; compute Recall@5; fail CI if below 0.9 on the committed fixture index **or** record the number in eval log if the first index is still tuning (prefer fail-the-build once fixtures are frozen). Chart tests from T-4.09.

**Done when:** recall number is in the eval log; chart tests green.

---

### T-4.14 — README and architecture notes

How to run, env vars, three DBs, safety guarantees, OKF vs glossary choice, alignment with SmartQuery11 / Additions / PHASEDOWN. One architecture diagram (text is enough). Do not claim Spider or voice.

**Done when:** a new clone can follow README without reading PHASEDOWN.

---

### T-4.15 — Docker Compose demo

`Dockerfile` + `docker-compose.yml`: app + sample DBs + env template. `docker compose up` serves Streamlit. Persist nothing sensitive. Document port.

**Done when:** compose up on a clean Docker host reaches the UI.

---

### T-4.16 — Optional extras (not v1 gates)

PostgreSQL dialect profile; DuckDB + CSV/xlsx/parquet upload with size limits, still through T-2.10. Track here only if you choose to do them.

**Done when:** skipped, or extra profile documented as optional.

---

## Phase 4 — task table

| Task num | Plan dependency | Status | Files involved |
|---|---|---|---|
| T-4.01 | T-1.08, T-1.09, T-1.10 | Not started | `smartsql/knowledge/okf.py` or `glossary.py`, `data/knowledge/university/`, `data/knowledge/ecommerce/`, `data/knowledge/hr/`, `tests/knowledge/test_loader.py` |
| T-4.02 | T-4.01, T-2.04 | Not started | `smartsql/knowledge/gate.py`, `tests/knowledge/test_gate.py` |
| T-4.03 | T-1.07 | Not started | `smartsql/rag/documents.py`, `tests/rag/test_documents.py` |
| T-4.04 | T-4.03 | Not started | `smartsql/rag/index.py`, `requirements.txt` (`chromadb`, `sentence-transformers`), `.gitignore` (`.chroma/`) |
| T-4.05 | T-4.04 | Not started | `smartsql/rag/retrieve.py`, `tests/rag/test_retrieve.py` |
| T-4.06 | T-4.04, T-1.12 | Not started | `smartsql/rag/fewshot.py`, `tests/rag/test_fewshot.py` |
| T-4.07 | T-1.06 | Not started | `smartsql/rag/grounding.py`, `requirements.txt` (`rapidfuzz`), `tests/rag/test_grounding.py` |
| T-4.08 | T-3.10, T-4.02, T-4.05, T-4.06, T-4.07 | Not started | `smartsql/agent/ask.py`, `smartsql/agent/prompt.py`, `smartsql/settings.py`, `tests/agent/test_ask_rag.py` |
| T-4.09 | T-1.03 | Not started | `smartsql/viz/heuristic.py`, `requirements.txt` (`plotly`), `tests/viz/test_heuristic.py` |
| T-4.10 | T-3.13, T-4.09 | Not started | `app/streamlit_app.py`, `app/components/charts.py` |
| T-4.11 | T-3.10, T-1.12 | Not started | `smartsql/eval/run.py`, `smartsql/eval/compare.py`, `data/eval/.gitkeep` |
| T-4.12 | T-3.10, T-1.07 | Not started | `smartsql/agent/cache.py`, `tests/agent/test_cache.py` |
| T-4.13 | T-4.05, T-4.09, T-4.11 | Not started | `tests/rag/test_recall.py`, `tests/viz/`, `data/eval/` |
| T-4.14 | T-3.11, T-4.01 | Not started | `README.md` |
| T-4.15 | T-3.11, T-4.14 | Not started | `Dockerfile`, `docker-compose.yml`, `.dockerignore` |
| T-4.16 | T-2.10 | Not started | `smartsql/db/profiles.py` (optional), `app/` upload (optional) |

**Phase 4 complete when:** T-4.13, T-4.14, T-4.15 are Done and PHASEDOWN §4.7 exit criteria hold. T-4.12 and T-4.16 may stay `Not started` without blocking v1 if README says cache/upload are optional.

---

# Master status board

Same rows as above, condensed for scanning. Update **Status** here or in the phase tables (keep them in sync).

| Task num | Phase | Plan dependency | Status | Files involved (primary) |
|---|---|---|---|---|
| T-1.01 | 1 | — | Not started | `requirements.txt`, `smartsql/`, `.venv/` (local) |
| T-1.02 | 1 | T-1.01 | Not started | `smartsql/db/connection.py`, `profiles.py` |
| T-1.03 | 1 | T-1.02 | Not started | `smartsql/db/execute.py` |
| T-1.04 | 1 | T-1.02 | Not started | `smartsql/db/inspector.py` |
| T-1.05 | 1 | T-1.04 | Not started | `smartsql/db/comments.py`, `data/schema_comments/` |
| T-1.06 | 1 | T-1.04 | Not started | `smartsql/db/sampler.py` |
| T-1.07 | 1 | T-1.04–T-1.06 | Not started | `smartsql/db/serialize.py`, `hashing.py` |
| T-1.08 | 1 | T-1.02 | Not started | `data/university.db`, `data/seeds/university.sql` |
| T-1.09 | 1 | T-1.02 | Not started | `data/ecommerce.db`, `data/seeds/ecommerce.sql` |
| T-1.10 | 1 | T-1.02 | Not started | `data/hr_analytics.db`, `data/seeds/hr_analytics.sql` |
| T-1.11 | 1 | T-1.01 | Not started | `smartsql/eval/gold.py` |
| T-1.12 | 1 | T-1.08–T-1.11, T-1.03 | Not started | `data/gold/*.yaml` |
| T-1.13 | 1 | T-1.03–T-1.12 | Not started | `tests/db/`, `tests/eval/` |
| T-2.01 | 2 | T-1.01 | Not started | `smartsql/safety/errors.py` |
| T-2.02 | 2 | T-2.01 | Not started | `smartsql/safety/prefilter.py` |
| T-2.03 | 2 | T-2.01 | Not started | `smartsql/safety/parse.py` |
| T-2.04 | 2 | T-2.03 | Not started | `smartsql/safety/walker.py` |
| T-2.05 | 2 | T-2.03 | Not started | `smartsql/safety/statements.py` |
| T-2.06 | 2 | T-2.03, T-1.07 | Not started | `smartsql/safety/schema_check.py` |
| T-2.07 | 2 | T-2.03 | Not started | `smartsql/safety/limits.py` |
| T-2.08 | 2 | T-1.02 | Not started | `smartsql/db/readonly.py` |
| T-2.09 | 2 | T-1.03, T-2.08 | Not started | `smartsql/db/execute.py` |
| T-2.10 | 2 | T-2.02–T-2.09 | Not started | `smartsql/safety/pipeline.py` |
| T-2.11 | 2 | T-2.10 | Not started | `tests/security/` |
| T-2.12 | 2 | T-2.10, T-1.12 | Not started | `tests/eval/test_gold_safe_execute.py` |
| T-3.01 | 3 | T-1.01 | Not started | `smartsql/settings.py` |
| T-3.02 | 3 | T-3.01 | Not started | `smartsql/agent/providers/` |
| T-3.03 | 3 | T-3.02 | Not started | `smartsql/agent/providers/gemini.py` or `groq.py` |
| T-3.04 | 3 | T-3.02 | Not started | `smartsql/agent/providers/ollama.py` |
| T-3.05 | 3 | T-1.07, T-3.02 | Not started | `smartsql/agent/prompt.py` |
| T-3.06 | 3 | T-3.02, T-3.05 | Not started | `smartsql/agent/rewrite.py` |
| T-3.07 | 3 | T-3.02 | Not started | `smartsql/agent/ambiguity.py` |
| T-3.08 | 3 | T-2.10, T-3.05 | Not started | `smartsql/agent/retry.py` |
| T-3.09 | 3 | T-2.03 | Not started | `smartsql/agent/explain.py` |
| T-3.10 | 3 | T-3.06–T-3.09 | Not started | `smartsql/agent/ask.py` |
| T-3.11 | 3 | T-3.10 | Not started | `app/streamlit_app.py` |
| T-3.12 | 3 | T-3.11, T-2.10 | Not started | `app/components/sql_editor.py` |
| T-3.13 | 3 | T-3.11, T-3.09 | Not started | `app/components/results.py` |
| T-3.14 | 3 | T-3.10–T-3.13 | Not started | `tests/agent/` |
| T-4.01 | 4 | T-1.08–T-1.10 | Not started | `smartsql/knowledge/`, `data/knowledge/` |
| T-4.02 | 4 | T-4.01, T-2.04 | Not started | `smartsql/knowledge/gate.py` |
| T-4.03 | 4 | T-1.07 | Not started | `smartsql/rag/documents.py` |
| T-4.04 | 4 | T-4.03 | Not started | `smartsql/rag/index.py` |
| T-4.05 | 4 | T-4.04 | Not started | `smartsql/rag/retrieve.py` |
| T-4.06 | 4 | T-4.04, T-1.12 | Not started | `smartsql/rag/fewshot.py` |
| T-4.07 | 4 | T-1.06 | Not started | `smartsql/rag/grounding.py` |
| T-4.08 | 4 | T-3.10, T-4.02–T-4.07 | Not started | `smartsql/agent/ask.py`, `prompt.py` |
| T-4.09 | 4 | T-1.03 | Not started | `smartsql/viz/heuristic.py` |
| T-4.10 | 4 | T-3.13, T-4.09 | Not started | `app/components/charts.py` |
| T-4.11 | 4 | T-3.10, T-1.12 | Not started | `smartsql/eval/run.py` |
| T-4.12 | 4 | T-3.10, T-1.07 | Not started | `smartsql/agent/cache.py` |
| T-4.13 | 4 | T-4.05, T-4.09, T-4.11 | Not started | `tests/rag/test_recall.py` |
| T-4.14 | 4 | T-3.11, T-4.01 | Not started | `README.md` |
| T-4.15 | 4 | T-3.11, T-4.14 | Not started | `Dockerfile`, `docker-compose.yml` |
| T-4.16 | 4 | T-2.10 | Not started | optional profiles / upload |

**v1 ship bar:** all Phase 1–3 tasks Done; Phase 4 through T-4.11, T-4.13, T-4.14, T-4.15 Done; T-4.12 and T-4.16 optional.
