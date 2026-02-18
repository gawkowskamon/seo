# plan.md

## Objectives
- Prove the **core flow** works end-to-end: topic/keywords → OpenAI GPT generates Polish accounting article → structured output (TOC+anchors, headings, FAQ, meta) → SEO scoring → editable dual-view → export (FB/Google Business + HTML/PDF) with **credible-source constraints**.
- Ship an MVP (v1) with a clean UX for creating, editing, scoring and exporting articles.

---

## Phase 1 — Core POC (LLM + structured article + SEO score) 
> Goal: validate OpenAI (Emergent key) integration + prompt/output contract + scoring in isolation. Do not proceed until stable.

### User stories
1. As a user, I can enter a topic + target keyword and get a full Polish article draft.
2. As a user, I receive a ready meta title + meta description within SEO length limits.
3. As a user, I get an auto-generated TOC with working anchors matching headings.
4. As a user, I get an FAQ section with concise Q/A aligned to the article.
5. As a user, I see an SEO score breakdown (readability, headings, keyword placement, links, length).

### Implementation steps
- Websearch best practices:
  - OpenAI structured outputs / JSON schema patterns.
  - Polish readability metrics (e.g., FOG-PL / Jasnopis-like heuristics) and practical approximations.
  - SEO checks: meta length, heading hierarchy, keyword placement.
- Create `scripts/poc_generate.py` (no DB, no UI):
  - Input: topic, primary keyword, secondary keywords, audience, desired length.
  - Call OpenAI GPT via Emergent.
  - Enforce **strict JSON output** schema: 
    - `title, slug, meta_title, meta_description, outline[], sections[{h2,h3[],html}], toc[{label,anchor}], faq[{q,a}], internal_link_suggestions[{anchor_text, target_slug, reason}], sources[{name,url,type}]`.
  - Validate JSON (schema + required fields) and sanitize anchors (ASCII/slug).
- Create `scripts/poc_score.py`:
  - Compute advanced SEO score (0–100) + breakdown:
    - Length vs target, heading structure (H2/H3), TOC/anchors consistency.
    - Keyword usage: first 150 words, at least 1 H2, density range.
    - Readability (simple heuristic: avg sentence length, syllable/word proxy, FOG-like).
    - Internal linking presence + suggested anchors.
    - Meta title/description character counts.
- Iterate prompt + validation until:
  - 10 consecutive runs produce valid JSON and acceptable score output.

### Deliverables
- Working POC scripts + prompt templates.
- Final JSON schema + scoring rubric.

---

## Phase 2 — V1 App Development (React + FastAPI + MongoDB)
> Build the app around the proven POC contracts. No auth in v1.

### User stories
1. As a user, I can generate a new article by filling a short form (topic, keywords, tone, length).
2. As a user, I can edit content in **visual WYSIWYG** and **HTML source** modes.
3. As a user, I can run SEO scoring anytime and see actionable recommendations.
4. As a user, I can export copy-ready versions for Facebook and Google Business.
5. As a user, I can download the article as HTML and PDF.

### Implementation steps
- Backend (FastAPI):
  - Models/collections: `articles`, `topics`, `source_whitelist`.
  - Endpoints:
    - `POST /generate` (calls OpenAI, stores draft)
    - `GET/PUT /articles/{id}` (load/update)
    - `POST /articles/{id}/score`
    - `POST /articles/{id}/export` (fb/google, html, pdf)
    - `GET /topic-suggestions` (stubbed v1: curated + simple keyword-based)
  - Implement credible-sources constraint:
    - Maintain whitelist (gov/legal/standards domains) + require `sources[]` returned.
    - Server-side validation: reject drafts lacking sources; request regeneration.
  - PDF generation: server-side (WeasyPrint or Playwright print-to-pdf) from sanitized HTML.
- Frontend (React + shadcn/ui):
  - Screens:
    - Article generator form + history list.
    - Editor page with tabs: Visual | HTML | SEO | Export.
  - Editor: TipTap/Quill for WYSIWYG + raw HTML textarea; keep single source of truth.
  - SEO panel: score gauge + checklist + highlighted issues (meta length, missing H2, etc.).
  - Export panel: platform-specific copy blocks + download buttons.
- Data flow + states:
  - Loading/streaming status for generation.
  - Regenerate sections (optional v1: regenerate FAQ/meta only).
  - Autosave on edit with debounce.

### Testing (end of Phase 2)
- 1 round end-to-end testing:
  - Generate → edit → score → export copy → download HTML/PDF.
  - Validate anchors work in preview and exported HTML.
  - Confirm sources appear and are from whitelist.

---

## Phase 3 — Feature Expansion (Topic engine + linking + stronger SEO)

### User stories
1. As a user, I can browse topic suggestions based on trends for Polish accounting/taxes.
2. As a user, I can get keyword suggestions (primary/secondary) and intent classification.
3. As a user, I can insert internal links from my article library with one click.
4. As a user, I can compare my draft SEO score against competitor heuristics (SERP-based signals).
5. As a user, I can lock a “company profile” (services, city) to tailor local SEO outputs.

### Implementation steps
- Topic suggestions:
  - Trending: ingest from curated RSS/official announcements (MVP list + periodic fetch).
  - Keyword analysis: simple integrations first (autocomplete/suggestions) + store results.
  - Manual: saved prompts/templates.
- Internal linking:
  - Build site/article index (Mongo) + suggest links based on keyword overlap/embeddings.
- SEO scoring upgrades:
  - Better Polish readability metric implementation.
  - Competitor analysis MVP: user-provided URLs → extract headings/meta and compare (no scraping beyond provided URLs).
- Source reliability:
  - Expand whitelist + add “citation required” checks for legal/tax claims.

### Testing (end of Phase 3)
- End-to-end run including topic suggestion → generation → internal link insert → export.

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

## Next Actions
1. Implement Phase 1 POC scripts with strict JSON schema and run 10-sample validation.
2. Finalize scoring rubric + thresholds for “publish-ready”.
3. Start Phase 2 with backend endpoints mirroring the POC contract.
4. Build the React editor (dual view) and wire generation/score/export.

---

## Success Criteria
- POC: 10/10 generations return valid JSON with TOC+anchors, FAQ, meta, and sources passing whitelist.
- V1: user can generate → edit → score → export (FB/Google + HTML/PDF) without manual fixes.
- SEO: scoring provides actionable items and improves after edits; meta and headings consistently valid.
- Reliability: no broken anchors, sanitized HTML, PDF export matches preview.
