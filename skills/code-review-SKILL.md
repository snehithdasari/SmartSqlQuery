---
name: code-review
description: Perform a structured code review on a diff, pull request, or set of changed files in any project/language. Use this whenever the user asks to "review this code", "review my PR/diff", "check this before I ship", "is this ready to merge", or hands over changed files and wants feedback. Surfaces ship-blockers (bugs, security issues, broken behavior), suggested improvements (design, performance, error handling), readability issues (naming, clarity, structure), and in-scope polish (things worth fixing now because you're already touching that code) — while explicitly flagging out-of-scope suggestions separately so the review doesn't turn into scope creep. Trigger even if the user just pastes a diff or code snippet and asks "thoughts?" or "anything wrong with this?".
---

# Code Review

A structured process for reviewing code changes in any language or project, producing feedback that's honest, prioritized, and actionable — not a wall of nitpicks.

## Core philosophy

A good code review answers one question first: **"Is this safe to ship?"** — and only after that, "how could it be better?"

Most low-value reviews fail in one of two ways:
1. **Too soft** — a pile of vague praise ("looks good!") that misses real bugs.
2. **Too noisy** — dozens of stylistic nitpicks that bury the two things that actually matter, or that drag unrelated code into scope.

This skill exists to avoid both. Every finding gets sorted into a category by *severity and scope*, not just "issues I noticed." That categorization is the deliverable — it's what lets a busy reader triage in 30 seconds.

## Step 1: Establish scope

Before reviewing, figure out what's actually being reviewed:

- **If given a diff / PR / git range**: the changed lines are the primary subject. Read surrounding code for context, but don't review untouched code as if it were part of this change.
- **If given whole files with no diff**: ask (or infer from context, e.g. "review my auth module") whether this is a full review or review-as-if-new-code. Default to treating it as new/unreviewed code.
- **If no clear scope is given**: ask one clarifying question rather than guessing — e.g. "Is this a full review of these files, or just the recent changes?"

Identify, if possible:
- What language/framework/ecosystem this is (affects idioms and common pitfalls)
- What the change is trying to accomplish (commit message, PR description, or ask the user)
- Any project conventions available (linter config, CONTRIBUTING.md, existing code style) — check for these files if working in a repo, since "readable" and "idiomatic" are project-relative, not universal

## Step 2: Read for understanding before critiquing

Don't start listing issues line-by-line on a first pass. First:
1. Understand what the code is supposed to do.
2. Trace the main path(s) through it.
3. Note where it touches state, I/O, external systems, auth, money, or user input — these are where ship-blockers hide.

Only after that, go line-by-line.

## Step 3: Sort every finding into exactly one category

This is the core structure of the output. Use these four buckets, in this order:

### 🛑 Ship-blockers
Things that must be fixed before this merges/ships. Be conservative about what qualifies — this category loses its power if everything lands here. Includes:
- Bugs: logic errors, off-by-one, wrong operator, incorrect edge-case handling
- Broken behavior: doesn't do what it claims to do, fails the stated requirement
- Security issues: injection, auth bypass, secrets in code, unsafe deserialization, missing input validation on untrusted input
- Data loss / corruption risks
- Crashes, unhandled exceptions on realistic inputs (not just adversarial ones)
- Race conditions / concurrency bugs
- Silent failures that would be hard to debug in production

For each: state *what* breaks, *when/how* it breaks (concrete trigger, not just "this could be an issue"), and a suggested fix or fix direction. If you're not certain it's actually broken, say so explicitly ("I think this breaks when X — worth confirming") rather than asserting it as fact.

### 🔧 Improvements
Not broken, but meaningfully better if changed. Includes:
- Performance issues with real-world impact (not micro-optimizations on cold paths)
- Missing error handling / error messages that won't help whoever hits them
- Design/architecture concerns: tight coupling, wrong abstraction level, duplicated logic
- Missing tests for behavior that matters (especially the ship-blocker-adjacent kind)
- Edge cases that are unhandled but low-risk (vs. ship-blocker edge cases, which are high-risk)

### 📖 Readability
Doesn't change behavior, but affects how easily someone else (or future-them) can understand or maintain this. Includes:
- Naming (variables, functions, files) that doesn't convey intent
- Functions/files doing too much — could be split for clarity
- Missing or misleading comments where the *why* isn't obvious from the *what*
- Inconsistent style *within the change itself* (inconsistency is worse than a style you personally dislike)
- Dead code, commented-out code, leftover debug statements

### ✅ In-scope polish
Small things worth fixing *right now, in this change* because the code is already open and it's cheap — but wouldn't justify their own PR. The test: "would it be reasonable to ask for this in review?" If yes, it's in-scope. Includes:
- Typos in strings/comments in touched lines
- Minor cleanup adjacent to the actual change
- Small consistency fixes in code already being edited

### 🔭 Out-of-scope (mention separately, don't block on it)
Real issues you noticed that live *outside* the diff/change boundary — pre-existing tech debt, unrelated files, "this whole module could use a rewrite." List these separately, clearly labeled as not blocking this review, so the reader isn't confused about why "the whole file needs work" is a comment on a 5-line diff. This category exists specifically to prevent scope creep from polluting the other four.

## Step 4: Write the output

Structure:

```
## Summary
[1-3 sentences: what this change does, and the headline verdict —
ready to ship / needs fixes first / needs discussion]

## 🛑 Ship-blockers (N)
[or "None found" — say this explicitly, don't just omit the section]

## 🔧 Improvements (N)

## 📖 Readability (N)

## ✅ In-scope polish (N)

## 🔭 Out of scope (not blocking)
[only include this section if there's something to say]
```

Rules for the writeup itself:
- **Lead with the summary and verdict.** A reviewer's time is precious — don't make them read 40 lines to find out if this is mergeable.
- **Cite specifics.** File name, line number or function name, and a short code reference for every finding. "This function has an issue" is useless; "`validateUser()` in `auth.js`: doesn't check `user.role` before line 42's admin action" is useful.
- **If a category is empty, say so.** "No ship-blockers found" is valuable signal, not filler.
- **Don't manufacture findings to fill categories.** If there are 2 real issues total, report 2. Padding a review with marginal nitpicks to look thorough is worse than a short honest review.
- **Be direct about severity, kind about delivery.** "This will crash on empty input" not "this might possibly want to consider handling empty input in some cases." Precision is a form of respect for the reader's time.
- **Suggest, don't just criticize.** Where a fix isn't obvious, at least point at a direction.
- **If you're unsure whether something is actually a bug**, say that explicitly rather than presenting a guess as a finding — "worth double-checking: X looks like it could Y, but I may be missing context on Z."

## Calibration notes

- A tiny, low-risk change (e.g., a copy tweak, a config value) doesn't need all five sections — just say so ("small, low-risk change; no concerns") rather than forcing structure onto something trivial.
- A large or high-stakes change (touches auth, payments, data migrations, public APIs) deserves extra scrutiny in Step 2 — spend more time tracing edge cases before writing findings.
- Match the project's actual conventions over generic "best practices" when the two conflict and there's no clear correctness/safety reason to prefer one — e.g., don't flag a project-wide pattern as a readability issue just because a different style is more common elsewhere.
- Don't invent requirements the code was never trying to meet. If scope is unclear, ask rather than reviewing against assumed requirements.
