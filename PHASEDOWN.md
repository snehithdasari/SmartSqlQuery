# SmartSQLQuery — Project Phased Roadmap (PHASEDOWN)

Implementation roadmap for **SmartSQLQuery**, the working name of the **SmartQuery** academic proposal: a natural-language-to-SQL engine with schema awareness, AST safety, optional retrieval, self-correction, and a learning-oriented explanation UI.

This file is the **build contract**. Task-level work (modules, dependencies, status, files) lives in [ROADMAP.md](ROADMAP.md). How to execute a task (git, GitHub CI, pytest-green, gitignore, secrets) lives in [GUARDRAILS.md](GUARDRAILS.md). This file supersedes the earlier seven-phase draft. It is aligned with:

* `SmartQuery11.pdf` — problem, objectives, Streamlit + SQLite/MySQL loop, SQL explanation as a teaching tool.
* `SmartQuery_Additions_260813_183632.pdf` — AST read-only guardrails, RAG, glossary/OKF, self-correction, Plotly, eval metrics.

**Product thesis:** ship a trustworthy question → SQL → result → explanation loop on realistic sample databases. Do not ship an analytics SaaS.

---

## Document alignment (scope vs proposal)

| Source | What it promises | How this roadmap treats it |
|---|---|---|
| SmartQuery11 | NL question → schema → SQL → validate → execute → table + explanation | **Core product** (Phases 1–3) |
| SmartQuery11 “future work” | Voice, regional languages, RBAC, enterprise DBs | **Out of v1** (see Deferred) |
| Additions | AST safety, RAG, OKF/glossary, retry loop, charts, Spider-style metrics | **Safety + retry in v1**; RAG/glossary when schema is large; **custom gold eval first**, Spider optional |
| Old 7-phase PHASEDOWN | Four LLM vendors, DuckDB files, glassmorphism, voice, semantic cache, Docker, Spider | **Trimmed.** Keep interfaces; implement only what v1 needs |

**Canonical name:** SmartSQLQuery (repository and UI). The report may still title the project SmartQuery; use both once in the README and then stick to SmartSQLQuery.

**v1 databases:** three embedded SQLite sample databases (zero-config demo) plus optional MySQL via SQLAlchemy, matching the proposal. PostgreSQL, DuckDB, and CSV/Parquet/Excel upload are Phase 4 optional extras, not Phase 1 blockers.

**v1 LLM surface:** one hosted provider (Gemini or Groq) and one local path (Ollama). Keep a small provider interface; do not implement four production adapters.

**v1 orchestration:** Python modules and function calls. Do **not** require LangChain or LlamaIndex.

---

## High-level architecture & phase progression

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     SMARTSQLQUERY v1 PHASE FLOW                           │
├──────────────────────────────────────────────────────────────────────────┤
│  [Phase 1] ──► [Phase 2] ──► [Phase 3] ──► [Phase 4]                      │
│  Data plane     Safety         Agent loop     Knowledge, viz,             │
│  & gold sets    guardrails     + thin UI      eval & packaging            │
└──────────────────────────────────────────────────────────────────────────┘
```

**Vertical slice rule:** after Phase 2, SQL can be executed safely by tests. After Phase 3, a human can ask a question in the browser. Phase 4 makes the system scale to larger schemas and look finished. Never wait until the last phase to have something runnable.

```
User question
    │
    ▼
Follow-up rewrite (if continuing a prior turn)
    │
    ▼
Schema context
    ├─ small DB  → full inspector DDL + comments
    └─ large DB  → hybrid RAG top-K tables + glossary/OKF hits
    │
    ▼
Ambiguity check (ask if two equally likely interpretations)
    │
    ▼
LLM SQL generation (dialect + few-shots if available)
    │
    ▼
AST safety + schema check + LIMIT policy
    │
    ├─ invalid ──► retry ≤ 3 (parse/DB error + targeted schema) ──┐
    │                                                             │
    └─ valid ──► read-only execute ──► table [+ optional chart]    │
                      │                                             │
                      └── SQL explainer ────────────────────────────┘
```

---

## Non-negotiable design rules (all phases)

1. **Never execute LLM SQL without the safety layer.** AST validation and a read-only connection are both required. Regex is only a cheap first reject, never the authority.
2. **Prefer sqlglot** for parse, dialect, validation, and LIMIT rewrite. Do not use sqlparse as a security validator.
3. **Read-only database credentials** (or SQLite URI mode / revoked grants) are the backstop if the AST misses something.
4. **Glossary or OKF snippets that contain SQL** must pass the same AST gate before they are injected into a prompt or composed into a query.
5. **Schema indexes are per database** and must be rebuilt when DDL changes (hash of inspector output).
6. **No silent guessing** when the question is ambiguous (two tables, two metrics). Ask a clarifying question.
7. **Show SQL before or beside results.** This is the teaching/trust surface from the proposal; it is not optional chrome.

---

## Deferred on purpose (do not schedule in v1)

| Item | Why it waits |
|---|---|
| Voice input / Web Speech API | Demo gimmick; proposal listed it as future work |
| Regional / multilingual NL | Separate NLP problem |
| Glassmorphism design system | Time sink; use a clean Streamlit layout |
| Four LLM vendors (Gemini + Groq + OpenAI + Ollama all first-class) | Two adapters are enough |
| Semantic **result** cache across users | Easy to serve the wrong answer or leak data |
| Full Spider / BIRD leaderboard harness | Research-sized; custom gold set is the honest metric |
| Role-based access control, SSO | Out of academic v1 scope |
| LangChain / LlamaIndex as the spine | Extra abstraction without benefit at this size |

These may appear in a later “v2” appendix; they are not Phase 4 exit criteria.

---

## Phase 1: Data plane, schema inspector, and gold sets

### 1.1 Objective

Build the foundation that every later phase depends on: connect to SQLite (and optionally MySQL), inspect relational metadata into a stable JSON/DDL representation, ship three realistic sample databases **with comments and gold NL↔SQL pairs**, and execute **parameterized, already-written** SELECT queries for tests (not LLM output yet).

### 1.2 Motivation

Text-to-SQL fails when schema context is incomplete, unnamed (`col1`, `t2`), or stale. The proposal’s examples (`students`, `employees`) are too flat to prove joins. Phase 1 must produce databases that look like coursework **and** like a small product, plus a gold file so accuracy is measurable from day one—not invented in a final “benchmarking” phase.

### 1.3 Scope and deliverables

**Connection manager (SQLAlchemy)**

* Dialects in v1: **SQLite required**, **MySQL optional** (same inspector interface).
* Connection validation, timeouts, and a session factory. No connection-string playground in the UI yet; named profiles (`university`, `ecommerce`, `hr`, `mysql_optional`).
* Execution helper used only by tests in this phase: parameterized SELECT, timing, row cap at the cursor/client (defense in depth even before AST).

**Schema inspector**

Collect and serialize:

* Table names, comments/descriptions (from SQLite `CREATE` comments or a sidecar `schema_comments.yaml` if the engine stores none).
* Columns: name, type, nullable, default, comment.
* Primary keys, foreign keys, and a simple join-path list (FK graph).
* Low-cardinality value samples (distinct values only when cardinality is below a threshold, e.g. 50).

Outputs:

* Structured JSON (canonical internal form).
* Dialect DDL string (for prompts).
* Markdown summary (for UI schema explorer later).

Compute a **schema hash** over the JSON. Later phases use it to invalidate RAG indexes and any SQL cache.

**Preloaded SQLite databases** (zero-config)

Each database needs real FKs, comments, and at least one metric that is **not** a column name (so a glossary can matter later).

| File | Domain | Suggested core tables |
|---|---|---|
| `ecommerce.db` | Commerce | Customers, Orders, OrderItems, Products, Categories, Payments |
| `university.db` | Academics | Students, Courses, Enrollments, Instructors, Departments, Grades |
| `hr_analytics.db` | HR | Employees, Departments, Salaries, PerformanceReviews, Projects |

**Gold evaluation set (required in Phase 1, not Phase 4)**

Per database, `gold.yaml` (or JSONL) entries:

* `id`, `question`, `gold_sql`, `required_tables`, `tags` (e.g. `join`, `aggregate`, `filter`, `ambiguous`).
* Optional `expected_row_count` or result hash for execution match.

Target **50–80 questions total** across the three DBs, including easy filters, joins, aggregates, and a few deliberately ambiguous items.

**Out of Phase 1:** DuckDB, file upload, PostgreSQL, LLM calls, Streamlit.

### 1.4 Exit criteria

* Inspector returns complete tables, columns, PKs, FKs for all three sample DBs.
* Unit tests connect to SQLite; MySQL tests skip if no server is configured.
* Parameterized SELECT tests run with timings.
* Gold files exist and gold SQL executes successfully on the sample DBs (the **gold** queries, not generated ones).

---

## Phase 2: AST safety, read-only execution, LIMIT policy

### 2.1 Objective

Make execution **safe enough that an LLM can be plugged in later without a new security design**. Parse with sqlglot, reject mutations and stacked statements, enforce read-only at the database, and apply a **row-returning** LIMIT policy that does not break aggregations.

### 2.2 Motivation

LLM SQL cannot be trusted. Regex is bypassed by comments, CTEs, and stacked statements (the Additions PDF’s regex line is insufficient; keep AST as the real check). The proposal’s “SQL validation & safety checking” becomes a deterministic compiler step, not a prompt instruction.

### 2.3 Scope and deliverables

**AST engine (sqlglot)**

* Parse for the **target dialect** (sqlite / mysql).
* Fail closed on parse errors.
* Walk the tree; raise `SecurityViolationError` on mutation/admin nodes, including at least:
  * DML: `INSERT`, `UPDATE`, `DELETE`, `MERGE`
  * DDL: `DROP`, `ALTER`, `TRUNCATE`, `CREATE`
  * Admin / dangerous: `GRANT`, `REVOKE`, `EXEC`/`EXECUTE`, destructive `PRAGMA`, `INTO OUTFILE` / `COPY`-style export, attached-database tricks where detectable
* Reject multiple statements / stacked queries.
* Optional cheap regex pre-filter for obvious `DROP`/`DELETE` — never a substitute for the AST.

**Schema check (static)**

* After parse, verify referenced tables/columns exist in the inspector snapshot for that database.
* Unknown identifiers fail validation (the agent loop in Phase 3 will retry).

**LIMIT / resource policy**

* Inject a default LIMIT (e.g. 100) and cap user LIMIT (e.g. 1000) on **row-returning** selects.
* **Do not** wrap pure aggregate queries (`SELECT COUNT(*)`, `SELECT AVG(salary) ...` with no raw row dump) in a dummy LIMIT that changes meaning.
* Apply LIMIT correctly across `UNION` branches without breaking `ORDER BY`.
* Client-side max rows and a **statement timeout** (bytes/time matter; a one-row huge blob still hurts).

**Connection isolation**

* Open sessions as read-only where the engine allows it (MySQL read-only user or `SET SESSION TRANSACTION READ ONLY`; SQLite query-only / restricted connection).
* Application code must not offer a write DSN in v1.

**Security fixture pack**

* Start with 50+ adversarial strings; **treat it as a living pack**. Every new bypass becomes a regression test.
* Do not claim “100% of all injection” as an exit line; claim “all fixtures in `tests/security/` fail closed.”

**Out of Phase 2:** LLM, UI, RAG.

### 2.4 Exit criteria

* Gold SQL from Phase 1 still executes after passing the validator (no false rejects on legitimate SELECT/JOIN/GROUP BY).
* All current security fixtures are rejected or rewritten safely.
* Unbounded row-returning selects receive LIMIT without breaking aggregates and UNION/ORDER BY cases covered by tests.
* Read-only connection rejects (or cannot perform) a direct `DELETE` even if AST were skipped in a unit test that calls the driver.

---

## Phase 3: Agent loop, explanation, and thin UI

### 3.1 Objective

Deliver the proposal’s end-to-end experience: natural-language question → dialect-aware SQL → validate → execute → table + **SQL explanation**, with a bounded self-correction loop and a **minimal Streamlit UI**. Use **full schema** in the prompt for the three sample databases (they are small). Do not block this phase on Chroma.

### 3.2 Motivation

The old roadmap put RAG before the agent and the UI last. That delays the only thing users and examiners can judge. Self-correction belongs here (Additions PDF), not as unnamed “future automatic query correction.” Multi-turn follow-ups (“only CSE”) are an **agent** problem, not a chat-widget problem.

### 3.3 Scope and deliverables

**LLM orchestrator**

* Interface: `generate_sql(question, schema_context, extras) -> sql`.
* Adapters: **one cloud** (Gemini or Groq) and **optional Ollama**. Config via `.env` (`python-dotenv` as in the proposal).
* Prompt contents (v1, small DBs):
  1. Dialect rules (SQLite vs MySQL).
  2. Full inspector DDL + FK join hints + comments.
  3. User question.
  4. Optional conversation rewrite result (below).
  5. Instruction: SELECT-only, qualified names, no stacked statements.

**Follow-up / query rewrite**

* If the user is continuing a thread, first produce a **standalone question** (or a patched SQL intent) from `{history, new utterance}`.
* Example: prior “average salary by department” + “only IT” → “average salary of employees in the IT department.”
* Do not naively concatenate chat logs into the SQL prompt without this step.

**Ambiguity handling**

* If the model (or a cheap heuristic) flags two tables/metrics, **do not execute**. Return a clarifying question in the UI.
* Gold set `ambiguous` tags should exercise this path.

**Self-correction loop (cap N = 3)**

1. AST + schema validation → on failure, feed **parse/security/schema error** (not a novel) back to the LLM.
2. Safe execute → on `OperationalError` / `ProgrammingError`, feed **DB error + failed SQL + relevant schema slice**.
3. Stop after N failures; show the last SQL and the error in plain language. Never infinite retry.
4. Do not dump unrelated tables into the retry prompt when a column-not-found error already names the object.

**SQL natural-language explainer**

Structured sections, as in the proposal’s teaching use case:

* Target entities (tables)
* Filters
* Joins
* Aggregations / calculations
* Sort and limits

This can be template-based from the AST (preferred, deterministic) with an optional LLM polish. Deterministic first so explanations cannot invent filters that are not in the SQL.

**Thin Streamlit UI (required in this phase)**

* DB picker (three samples; optional MySQL profile).
* Question box; submit.
* Panels: generated SQL (syntax highlight, editable), explanation, results table, validation/retry log (latency, retry count).
* **Human-in-the-loop:** user can edit SQL and “Run” (still through Phase 2). Toggle auto-execute vs preview-first.
* No glassmorphism, no voice, no dashboard product chrome.

**Out of Phase 3:** Chroma, OKF bundle, Plotly auto-viz (table is enough), Docker, Spider.

### 3.4 Exit criteria

* End-to-end: pick `university.db` → ask a join/aggregate question → see SQL, explanation, and correct table in the browser.
* Self-correction recovers from at least two **simulated** failures (wrong column name; missing GROUP BY) within ≤ 2 retries in tests.
* Follow-up rewrite tested with at least five scripted dialogues.
* Cloud adapter **or** Ollama works; the other may be skipped in CI if no key/runtime.
* Manual SQL edit still cannot run a `DROP` (Phase 2 on every execute).

---

## Phase 4: Knowledge layer, visualization, eval, and packaging

### 4.1 Objective

Add the Additions PDF capabilities that **matter when schemas grow** or when the demo must look complete: glossary/OKF, hybrid RAG, categorical value grounding, simple auto-charts, an honest eval harness, tests, and reproducible packaging. RAG is **off or bypassed** for the three small sample DBs unless a “force RAG” flag is on for demos.

### 4.2 Motivation

Full-schema prompts fail on large catalogs and on jargon that is not a column (`high performer`, `churned customer`). The proposal did not require this for the first demo; the Additions PDF correctly adds it. PHASEDOWN previously over-specified Spider, semantic caches, and five chart types. This phase stays proportional.

### 4.3 Knowledge format: glossary vs OKF

**Do not invent a fake “OKF YAML.”** Google Open Knowledge Format is a **directory of Markdown files with YAML frontmatter** (one concept per file: `type`, `title`, `description`, optional links).

**v1 approach (pick and document one):**

* **Preferred differentiator:** a small **OKF bundle** per sample DB, e.g. `knowledge/university/` with concepts of types `Table`, `Metric`, `Playbook` (few-shot), `Term`.
* **Acceptable simpler path:** `business_glossary.yaml` **called a semantic layer**, not OKF.

Concept examples (university):

* Term “high performer” → definition plus **certified SQL fragment** `grade >= 85` (fragment still AST-checked).
* Metric “average marks by department” → gold SQL playbook for few-shot retrieval.

Index **concept text** (and table documents) in the vector store. Inject only **top matching concepts**, not the whole bundle.

### 4.4 RAG and retrieval (large schema / force-RAG demo)

**Store:** Chroma (local). One collection **per database**, named with `schema_hash`. Rebuild on hash change.

**Table documents** (embedding text):

`table metadata + column comments + FK relations + low-cardinality sample values`

**Hybrid retrieve:** BM25 (keyword) + dense vectors → top-K tables (K configurable, default 5–8).

**Few-shots:** verified `(question, sql)` pairs from gold + user-accepted queries; retrieve top-3 **similar** examples for the prompt.

**Value grounding:** RapidFuzz / Levenshtein only on **low-cardinality** columns already sampled in Phase 1 (e.g. map “California” → `CA`). Do not scan every string column on each question.

**Retrieval evaluation (honest):** labeled `required_tables` from gold. Target **Recall@5 ≥ 0.9** on that set—not “100% of required tables in top-3.”

If retrieval confidence is low: widen K, or fall back to full schema if the DB is still small, or **ask** rather than guess.

### 4.5 Visualization

* Always show the table.
* Heuristic Plotly when the shape is obvious:
  * 1 categorical + 1 numeric → bar
  * 1 temporal + 1 numeric → line
  * single scalar → KPI number (no fake chart)
* Manual switcher limited to Table / Bar / Line. No donut/scatter/theme pack as a Phase 4 requirement.
* Export: CSV (required); Excel/JSON optional.

### 4.6 Evaluation, caching, packaging

**Primary eval:** run generated SQL vs `gold.yaml` on the three DBs.

* **Execution accuracy (EX):** result tables match (bag of rows / sorted compare).
* **Error taxonomy:** wrong table, wrong join, extra/missing filter, dialect error, safety false reject.
* Log latency split: **LLM time** vs **DB time**. Do not promise “&lt; 2.5s end-to-end” on cold API calls; report p50/p95 instead.

**Optional extra:** a small Spider subset runner if time remains. Not an exit gate. BIRD/Spider 2.0 are out of scope.

**SQL cache (optional, conservative):**

* Key = `database_id + schema_hash + normalized_question` (embedding match only if similarity is extremely high **and** the DB id matches).
* Cache **SQL**, not result sets, unless the DB is known static (the sample files are static; still do not cache across databases).
* Skip cache on follow-up turns until rewrite is standalone.

**Testing:** pytest for inspector, sqlglot fixtures, LIMIT policy, prompt assembly, retrieval recall on a fixture index, chart heuristic unit tests.

**Packaging:** `.env.example`, `README.md` (architecture + how to run + alignment with SmartQuery proposal), `Dockerfile` / `docker-compose.yml` for the Streamlit app + sample DBs. Single `docker compose up` for the demo.

**Optional extras (not exit gates):** PostgreSQL dialect, DuckDB + CSV/xlsx/parquet upload with file size limits (still Phase 2 on every query).

### 4.7 Exit criteria

* Glossary/OKF terms for jargon questions improve EX on a tagged gold subset vs a no-glossary ablation (document both numbers).
* Retrieval Recall@5 ≥ 0.9 on the labeled gold subset when RAG is enabled.
* Auto-chart runs without error on a fixed set of result shapes; table path always works if the heuristic declines.
* Gold-set EX and latency reported in a saved eval log.
* Tests covering connection, AST, LIMIT, and a smoke RAG index pass in CI.
* `docker compose up` serves the app with sample DBs.

---

## Suggested repository layout

```
SmartSQLQuery/
  PHASEDOWN.md
  README.md
  .env.example
  .venv/                  # local virtual environment — gitignored, never commit
  app/                    # Streamlit entry
  smartsql/
    db/                   # connections, inspector
    safety/               # sqlglot validate, limit rewrite
    agent/                # prompt, providers, retry, rewrite
    knowledge/            # OKF or glossary loaders
    rag/                  # embed, retrieve, invalidate
    viz/                  # dataframe → plotly heuristic
    eval/                 # gold runner
  data/
    ecommerce.db
    university.db
    hr_analytics.db
    gold/
    knowledge/            # OKF bundles or yaml
  tests/
    security/
```

---

## Library stack (consolidated)

| Library | Role | Phase |
|---|---|---|
| Python 3.11+ | Runtime | 1 |
| SQLAlchemy | Connections, inspector | 1 |
| Pandas | Result tables | 1 |
| sqlglot | Parse, security, dialect, LIMIT | 2 |
| python-dotenv | Secrets | 3 |
| Streamlit | UI | 3 |
| Google Gemini **or** Groq + optional Ollama | SQL generation | 3 |
| chromadb | Schema/concept vectors | 4 |
| sentence-transformers (local) or API embeddings | Embeddings | 4 |
| RapidFuzz | Value grounding | 4 |
| Plotly | Optional charts | 4 |
| pytest | Tests | 1–4 |

**Not in the required stack:** PyTorch/Transformers (unless a later experiment fine-tunes a local Text-to-SQL model), LangChain, LlamaIndex, sqlparse-as-security, FAISS-in-addition-to-Chroma, seaborn-in-addition-to-Plotly.

---

## Mapping to original proposal objectives

| SmartQuery11 objective | Where it is satisfied |
|---|---|
| Accept NL questions | Phase 3 UI |
| Understand intent (NLP/AI) | Phase 3 LLM + Phase 3 rewrite |
| Identify tables/columns/relations | Phase 1 inspector; Phase 4 RAG when large |
| Generate SQL | Phase 3 |
| Validate before execute | Phase 2 |
| Execute on relational DB | Phase 2–3 (SQLite/MySQL) |
| User-friendly results | Phase 3 table; Phase 4 chart |
| Explain generated SQL | Phase 3 explainer |
| Reduce manual SQL | Entire loop |
| Foundation for voice/multilingual | Explicitly deferred; architecture does not block them |

---

## What “done” means for v1

A reviewer can:

1. Clone / `docker compose up` (or `streamlit run` with SQLite files).
2. Ask a join and an aggregate in English on `university` or `ecommerce`.
3. See safe SQL, an accurate explanation, and the result table.
4. Fail to run `DROP TABLE` via the editor.
5. Read an eval log with EX on the gold set.

That is a complete SmartQuery. Everything else is increment, not the definition of the project.
