# plan.md (updated after Phase 5 — AI SEO Assistant ✅ COMPLETED; Phase 6–8 approved and queued)

## Objectives
- Deliver a working end‑to‑end content workflow for Polish accounting/tax marketing:
  **topic/keywords → AI generates Polish article (JSON) → TOC+anchors + headings + FAQ + meta → SEO scoring → dual editor (Visual + HTML) → export (FB/Google Business + HTML/PDF)**.
- Provide a complete **media workflow** for blog publishing:
  **AI image generation → per‑article gallery → preview → copy HTML embed → download/delete**.
- Provide an in-editor **AI SEO Assistant** to improve drafts faster:
  - Combines **prioritized suggestions (with Apply actions)** + **interactive chat**.
  - Uses **OpenAI `gpt-5.2`** via Emergent integrations.
- Upgrade the product from MVP UI to a **brand-aligned, premium SaaS**:
  - **Kurdynowski branding** (primary blue `#04389E`, accent orange `#F28C28`), modern‑classic look.
  - Improved typography (serif display headings + sans UI body).
- Add **advanced content creation** for specialized, high-value deliverables:
  - Templates, multi‑part series, advanced formatting blocks, generation from sources.
- Add **simple authentication + workspaces** for client/brand separation:
  - Email/password auth (JWT) and user-scoped data.
- Preserve reliability and production readiness:
  - Stable LLM calls (retries/fallbacks where relevant).
  - Correct Polish UX (UTF‑8, no `\uXXXX` artifacts).
  - Exports remain consistent.

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
    - **Model updated for reliability:** primary **`gpt-4.1-mini`** with retry/fallback.
  - `seo_scorer.py`: advanced scoring engine.
  - `export_service.py`: FB/GBP copy + full HTML + server-side PDF generation.
- Persistence: MongoDB collection `articles`.

#### Frontend (React)
- Pages:
  - Dashboard (stats + article list + search + delete).
  - Generator (topic + keywords + tone + length + staged loading UI).
  - Topics (AI topic suggestions; “use in generator” deep-linking).
  - Editor (3-panel layout): left TOC, center editor, right SEO/FAQ/Export.
- Polish UI and correct UTF‑8 rendering fixed.

### Testing (done)
- Backend tests: **100% pass** (articles, stats, export, scoring).
- Frontend E2E: flow verified.

---

## Phase 3 — Feature Expansion (UX + regeneration + stability) ✅ COMPLETED
> Goal achieved: implement planned UX improvements and AI regeneration capabilities.

### Goals (completed)
- Replace native selects with shadcn Select.
- Add autosave + unsaved indicator.
- Add AI regeneration actions for FAQ and meta.

### User stories (delivered)
1. Polished dropdowns (shadcn Select) in Generator and Topics.
2. Autosave with “Zapisano/Niezapisane” indicator.
3. Regenerate **FAQ** via AI.
4. Regenerate **meta title + meta description** via AI.

### Implementation steps (completed)
- Frontend regeneration actions + autosave.
- Backend `POST /api/articles/{id}/regenerate` for `faq` and `meta`.

### Testing (done)
- Backend regeneration tested successfully.

---

## Phase 4 — AI Image Generation (Gemini “Nano Banana”) ✅ COMPLETED
> Goal achieved: add an image generation workflow for article illustrations, integrated into the editor.

### Goals (completed)
- Generate images with styles.
- Per‑article gallery and preview.
- Copy HTML embed + download + delete.

### Implementation details (as built)
#### Backend
- `image_generator.py` using `gemini-3-pro-image-preview`.
- MongoDB collection `images`.
- Endpoints:
  - `POST /api/images/generate`
  - `GET /api/images/{image_id}`
  - `GET /api/articles/{article_id}/images`
  - `DELETE /api/images/{image_id}`

#### Frontend
- `ImageGenerator.js` in editor.
- Right panel tab **Obrazy**.

### Testing (done)
- Backend and frontend flows verified.

---

## Phase 5 — AI SEO Assistant (Suggestions + Chat) ✅ COMPLETED (P0)
> Goal achieved: provide in-editor SEO improvement with suggestions + chat, using **OpenAI `gpt-5.2`**.

### User stories (delivered)
1. AI assistant panel in editor.
2. Prioritized SEO suggestions list.
3. One-click **Zastosuj** for suggestions.
4. Interactive chat about improvements.
5. Works with rescoring + unsaved indicator.

### Implementation details (as built)
#### Backend
- New service: `/app/backend/seo_assistant.py`.
- Endpoint: `POST /api/articles/{article_id}/seo-assistant` supporting:
  - `mode: analyze | chat`, optional `history`, `message`.
- Strict JSON parsing + cleanup.

#### Frontend
- New component: `/app/frontend/src/components/SEOAssistantPanel.js`.
- Editor right-panel tab: **AI**.
- Apply behavior supports: `meta_title`, `meta_description`, `html_content` (append), `faq` (append item).

### Testing / verification (done)
- Backend 100%.
- Frontend verified by automated screenshots (AI tab, suggestions, apply, chat UI).

---

## Phase 6 — UI Redesign: Kurdynowski Branding 🔥 IN PROGRESS (P1)
> Goal: modernize the UI to a premium “modern-classic” feel consistent with Kurdynowski brand. Text-only wordmark (no logo image).

### Brand constraints (confirmed)
- Primary: **brand blue `#04389E`**
- Accent: **brand orange `#F28C28`**
- Sidebar: stylized **text wordmark** “Kurdynowski” (serif) + descriptor “Accounting & Tax Solutions” (sans)

### Goals
- Replace existing blue palette with brand blue and warm neutrals.
- Introduce orange accent sparingly for highlights/CTAs.
- Update typography: **Instrument Serif** for headings/wordmark, keep IBM Plex Sans for UI and IBM Plex Mono for code.
- Improve layout polish: spacing, surfaces, shadows, hover/focus rings.

### Implementation steps (planned)
1. **Global tokens**: update `/app/frontend/src/index.css` `:root` tokens to match brand HSL mapping (primary/ring = brand blue; accent/secondary warm neutrals).
2. **Typography**:
   - Add Google Font import for **Instrument Serif**.
   - Apply serif only to headings + brand wordmark.
3. **App-wide color replacement**:
   - Update `/app/frontend/src/App.css` hardcoded HSL values to use brand blue equivalents and ensure consistent borders/muted tones.
4. **Sidebar wordmark**:
   - Update `/app/frontend/src/components/Sidebar.js` to display “Kurdynowski” with a subtle orange accent (dot/mark) and a small descriptor line.
5. **Page polish pass**:
   - Dashboard KPI cards and table headers.
   - Generator card + progress overlay.
   - Editor panels and tab styles (SEO/AI/FAQ/Images/Export).
6. Accessibility regression check: focus rings, contrast.

### Success criteria
- The entire app visually reads as “Kurdynowski” brand: deep blue actions, warm neutral surfaces, subtle orange highlights.
- No regressions in existing flows.

---

## Phase 7 — Advanced Content Creation (Templates + Sources + Blocks) ⏳ PLANNED (P1)
> Goal: add specialized, higher-value content creation beyond basic article generation.

### Scope (confirmed by user)
- “Wszystko plus”:
  - Content templates (poradnik, case study, porównanie, lista, FAQ-heavy, local SEO, pillar page).
  - Multi‑part article series.
  - Advanced formatting blocks (tables, callout boxes, checklists).
  - Generation from sources (URL / pasted text; optional file upload later).
  - More specialized content: e.g., compliance updates, deadlines calendars, step-by-step procedures, segment-specific variants.

### Implementation steps (planned)
1. **Template system**
   - Extend generator UI with template selection (shadcn Select).
   - Add backend prompt variants per template and enforce output JSON schema.
2. **Advanced blocks**
   - Define allowed HTML blocks (table, callouts, checklist) and extend editor styling.
   - Add “Insert block” actions (optional) in editor.
3. **Series generation**
   - Backend: generate outline for N-part series + generate per-part article drafts.
   - Frontend: series view with list of parts and navigation.
4. **Sources-driven generation**
   - UI: input for URLs / pasted sources.
   - Backend: fetch/parse text (safe allowlist) and use as context.
5. **Quality controls**
   - More strict factuality prompts + citation enforcement.

### Success criteria
- User can generate specialized content reliably with consistent structure and reusable blocks.

---

## Phase 8 — JWT Authentication (Email/Password) + Workspaces ⏳ PLANNED (P1)
> Goal: introduce basic auth and user-scoped data, with workspace concept for multiple clients/brands.

### Requirements (confirmed)
- **Email + password** registration/login.
- JWT-based auth.
- Protected routes.
- User-specific articles and images.

### Implementation steps (planned)
1. Backend:
   - Users collection (hashed passwords).
   - JWT issuance + refresh strategy (simple MVP: access token only).
   - Middleware/dependency to enforce auth.
2. Workspaces:
   - Workspace collection + membership.
   - Add `workspace_id` to articles/images.
   - Update endpoints to scope by user/workspace.
3. Frontend:
   - Login + Register pages.
   - Auth state storage + axios interceptor.
   - Route guards.

### Success criteria
- Each user sees only their content; can switch workspace.

---

## Next Actions (updated)
1. **Start Phase 6 (now): UI redesign to Kurdynowski branding**.
2. Phase 7: Advanced content creation feature set.
3. Phase 8: JWT auth + workspaces.
4. Then:
   - P2: Improve image generator (prompting, styles, variations, consistency).
   - P3 (optional): Insert images directly in visual editor.

---

## Success Criteria (updated)
- Phase 1–5: ✅ delivered as documented.
- Phase 6: Brand-consistent premium UI across all pages.
- Phase 7: Advanced, specialized content generation with templates + blocks + sources.
- Phase 8: Authenticated, user-scoped workspaces and data isolation.
- Reliability preserved:
  - No broken anchors.
  - Correct UTF‑8.
  - Exports and image workflows continue to work end-to-end.
