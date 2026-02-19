# plan.md (updated)

## Objectives
- Deliver a working MVP that supports the full flow end‑to‑end:
  **topic/keywords → AI generates Polish accounting article (JSON) → TOC+anchors + headings + FAQ + meta → SEO scoring → dual editor (Visual + HTML) → export (FB/Google Business + HTML/PDF)**.
- Ensure reliability and production readiness:
  - Stable LLM generation (model fallback/retries).
  - Consistent Polish UX (UTF‑8 chars, no escaped sequences).
  - Credible sources included in every draft.
  - Robust export formats.
- Move into **Phase 3** to expand topic engine, internal linking, and stronger SEO analysis.

---

## Phase 1 — Core POC (LLM + structured article + SEO score) ✅ COMPLETED
> Goal achieved: validate OpenAI (Emergent key) integration + prompt/output contract + scoring in isolation.

### User stories (delivered)
1. Generate a full Polish article draft from topic + keywords.
2. Produce meta title + meta description within SEO limits.
3. Auto-generate TOC with working anchors matching headings.
4. Auto-generate an FAQ section aligned to the article.
5. Produce advanced SEO score breakdown (readability, headings, keyword placement, links, length, etc.).

### Implementation (done)
- Implemented POC script (`/app/tests/poc_core.py`) that:
  - Calls OpenAI via Emergent integration.
  - Enforces strict JSON structure and validates required fields.
  - Computes SEO scoring across 10 dimensions.

### Deliverables (done)
- Working POC generation + scoring.
- JSON output contract proven.
- Scoring rubric implemented.

---

## Phase 2 — V1 App Development (React + FastAPI + MongoDB) ✅ COMPLETED
> Goal achieved: build the app around the proven POC contracts. No auth in v1.

### User stories (delivered)
1. Generate a new article by filling a short form (topic, keywords, tone, length).
2. Edit content in **visual WYSIWYG** and **HTML source** modes.
3. Run SEO scoring anytime and see actionable recommendations.
4. Export copy-ready versions for Facebook and Google Business.
5. Download the article as HTML and PDF.
6. Browse topic suggestions (AI-powered).
7. See dashboard stats (total, avg SEO score, needs improvement).

### Implementation details (as built)
#### Backend (FastAPI)
- Implemented endpoints under `/api`:
  - `POST /api/articles/generate`
  - `GET /api/articles` | `GET /api/articles/{id}` | `PUT /api/articles/{id}` | `DELETE /api/articles/{id}`
  - `POST /api/articles/{id}/score`
  - `POST /api/articles/{id}/export` (facebook, google_business, html, pdf)
  - `POST /api/topics/suggest`
  - `GET /api/stats`
- Services:
  - `article_generator.py`: AI generation + strict JSON parsing
    - **Model updated for reliability:** switched from `gpt-4.1` to **`gpt-4.1-mini`** with retry/fallback logic.
  - `seo_scorer.py`: advanced scoring engine.
  - `export_service.py`: FB/GBP copy + full HTML + server-side PDF generation.
- Persistence: MongoDB collection `articles`.

#### Frontend (React)
- Pages:
  - Dashboard (stats + article list + search + delete).
  - Generator (topic + keywords + tone + length + staged loading UI).
  - Topics (AI topic suggestions; “use in generator” deep-linking).
  - Editor (3-panel layout):
    - Left: TOC + anchor copy, internal link suggestions, sources.
    - Center: Visual editor + HTML editor tabs.
    - Right: SEO score panel + FAQ editor + Export panel tabs.
- Polish UI and correct UTF‑8 rendering fixed (no `\uXXXX` artifacts).

### Testing (done)
- Backend tests: **100% pass** (articles, stats, export, scoring).
- Frontend E2E: **functional flow verified** (dashboard → editor → tabs → export).
- Remaining minor issues:
  - **Low priority:** console warnings related to native `select/option` hydration/structure on Generator/Topics.

---

## Phase 3 — Feature Expansion (Topic engine + linking + stronger SEO) 🚧 NEXT

### Goals
- Improve topic discovery and planning.
- Upgrade internal linking from “suggestions only” to one-click insertion.
- Strengthen SEO analysis (Polish readability, competitor comparisons, structured data checks).
- Tighten “credible sources” enforcement and traceability.

### User stories
1. As a user, I can browse topic suggestions based on trends for Polish accounting/taxes.
2. As a user, I can get keyword suggestions (primary/secondary) and intent classification.
3. As a user, I can insert internal links from my article library with one click.
4. As a user, I can compare my draft SEO score against competitor heuristics (based on user-provided URLs).
5. As a user, I can lock a “company profile” (services, city) to tailor local SEO outputs.

### Implementation steps
#### 3.1 Topic suggestions engine (upgrade)
- Add multi-source topic pipeline:
  - Trending: curated RSS feeds (MF, ZUS, GOV, Sejm/ISAP updates), plus manual “hot topics”.
  - Keyword ideas: autocomplete-style suggestions + clustering.
  - Saveable “topic lists” (collections) per category.
- Persist suggestions/history in MongoDB (`topic_suggestions`).

#### 3.2 Internal linking (upgrade)
- Build an internal article index (title, slug, keywords, embeddings/overlap scores).
- Add “Insert link” action in the editor:
  - choose target article,
  - auto-suggest anchor text,
  - insert `<a href="/slug#anchor">` into Visual editor and HTML.

#### 3.3 SEO scoring upgrades
- Improve Polish readability:
  - Add syllable/word proxy + FOG-PL-like heuristic.
  - Add paragraph length distribution and passive voice heuristics (approx).
- Add structured SEO checks:
  - H1 uniqueness, missing H2/H3 gaps, image alt placeholders.
  - FAQ schema validity checks.
  - Anchor uniqueness and collision detection.
- Competitor comparison MVP (user-provided URLs only):
  - Extract headings/meta length and compare to draft.

#### 3.4 Source reliability hardening
- Add server-side whitelist validation for source domains.
- Add “missing citation” heuristics for legal/tax claims (rule-based triggers).
- Store sources separately (`article_sources`) and surface in UI with “credibility” badges.

#### 3.5 UX improvements
- Fix low-priority console warnings:
  - replace native `select` with shadcn/ui `Select` components.
- Add autosave with debounce + “unsaved changes” indicator.
- Add “Regenerate” actions (meta only / FAQ only / section only) with change diff preview.

### Testing (end of Phase 3)
- E2E:
  - Topic suggestion → open in generator → generate → insert internal link → rescore → export.
- Validation:
  - No broken anchors; links inserted correctly in both Visual and HTML views.
  - Export outputs match editor content.
  - Sources pass whitelist checks.

---

## Phase 4 — Hardening + Auth (only after approval)

### User stories
1. As a user, I can sign in and see only my articles.
2. As a user, I can manage multiple brands/clients (workspaces).
3. As a user, I can set default templates and SEO rules per workspace.
4. As a user, I can audit generation history (prompt, model, time, cost estimate).
5. As a user, I can collaborate via shareable review links (view/comment).

### Implementation steps
- Add JWT auth + workspace isolation.
- Rate limiting, caching, cost tracking.
- Robust HTML sanitization + export consistency.

---

## Next Actions (updated)
1. Phase 3.5 quick win: replace native `select` with shadcn `Select` to remove console warnings.
2. Implement internal linking index + one-click insertion in editor.
3. Upgrade topic engine (RSS/trending + saved lists).
4. Improve readability metrics and add competitor comparison (user-provided URLs).
5. Expand and enforce source whitelist validation server-side.

---

## Success Criteria (updated)
- POC: ✅ Valid JSON generation + scoring proven.
- V1: ✅ User can generate → edit → score → export (FB/Google + HTML/PDF) without manual fixes.
- Phase 3:
  - Topic suggestions provide actionable, trend-aware ideas.
  - Internal linking can be inserted reliably from library.
  - SEO scoring includes stronger Polish readability + structured checks.
  - Source reliability enforced via whitelist + UI indicators.
- Reliability:
  - No broken anchors.
  - Sanitized HTML.
  - PDF export matches preview.
  - Stable LLM generation using `gpt-4.1-mini` with fallback/retries.
