# plan.md (updated after Phase 12 — Series + Sources ✅ COMPLETED; Phase 9–12 ✅ COMPLETED)

## Objectives
- Deliver a working end‑to‑end content workflow for Polish accounting/tax marketing:
  **topic/keywords → AI generates Polish article (JSON) → TOC+anchors + headings + FAQ + meta → SEO scoring → dual editor (Visual + HTML) → export (FB/Google Business + HTML/PDF)**.
- Provide a complete **media workflow** for blog publishing:
  **AI image generation → per‑article gallery → preview → copy HTML embed → download/delete → insert image into content**.
- Provide an in-editor **AI SEO Assistant** to improve drafts faster:
  - Combines **prioritized suggestions (with Apply actions)** + **interactive chat**.
  - Uses **OpenAI `gpt-5.2`** via Emergent integrations.
- Deliver a **brand-aligned, premium SaaS UI**:
  - **Kurdynowski branding** (primary blue `#04389E`, accent orange `#F28C28`), modern‑classic look.
  - Typography: **Instrument Serif** for display/headings + IBM Plex Sans for UI + IBM Plex Mono for code.
- Add **advanced content creation** for specialized, higher‑value deliverables:
  - Template-based generation with specialized structures.
  - Advanced formatting blocks (callouts, tables, checklists) rendered and styled in the visual editor.
  - Series generation + sources-driven planning/generation.
- Add **simple authentication** and deliver **multi-tenant separation**:
  - Email/password auth (JWT) and protected routes ✅.
  - Workspaces + user/workspace-scoped data isolation ✅.
- Preserve reliability and production readiness:
  - Stable LLM calls.
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

## Phase 6 — UI Redesign: Kurdynowski Branding ✅ COMPLETED (P1)
> Goal achieved: modernize the UI to a premium “modern-classic” feel consistent with Kurdynowski brand. Text-only wordmark (no logo image).

### Brand constraints (confirmed)
- Primary: **brand blue `#04389E`**
- Accent: **brand orange `#F28C28`**
- Sidebar: stylized **text wordmark** “Kurdynowski” (serif) + descriptor “Accounting & Tax Solutions” (sans)

### Delivered changes
1. **Global tokens & typography**
   - Updated `/app/frontend/src/index.css` design tokens to match brand.
   - Added Google Fonts import and applied:
     - **Instrument Serif** to headings/wordmark
     - IBM Plex Sans to UI
     - IBM Plex Mono to code
2. **App-wide styling refresh**
   - Updated `/app/frontend/src/App.css` with:
     - brand color mapping (blue actions, orange accents)
     - modern surfaces, borders, spacing, hover/focus states
3. **Sidebar wordmark**
   - Updated `/app/frontend/src/components/Sidebar.js`:
     - stylized “Kurdynowski.” with orange dot
     - descriptor line
     - improved nav active/hover states

### Success criteria (met)
- App visually reads as “Kurdynowski” across Dashboard/Generator/Editor.
- No regressions in existing flows.

---

## Phase 7 — Advanced Content Creation (Templates + Blocks) ✅ COMPLETED (P1)
> Goal achieved: add specialized, higher-value content creation beyond basic generation.

### Scope (delivered)
- **8 content templates** with specialized structures:
  - `standard`, `poradnik`, `case_study`, `porownanie`, `checklist`, `pillar`, `nowelizacja`, `kalkulator`
- **Advanced formatting blocks** supported in generated HTML and styled in visual editor:
  - callout boxes (`.callout-tip/.callout-warning/.callout-info/.callout-link`)
  - tables (`.data-table/.comparison-table/.changes-table`)
  - checklist items (`.checklist-item`)

### Implementation details (as built)
- Backend:
  - New module `/app/backend/content_templates.py`:
    - template registry + specialized prompts
    - strict JSON schema contract shared across templates
  - New endpoint: `GET /api/templates`
  - Updated `generate_article(...)` to accept `template` and switch prompt accordingly.
  - Stored `template` on the article document.
- Frontend:
  - Updated `/app/frontend/src/pages/ArticleGenerator.js`:
    - template cards grouped by category
    - template selection persists into generation request
- Styling:
  - Added advanced block CSS rules into `/app/frontend/src/App.css` for visual editor rendering.

---

## Phase 8 — JWT Authentication (Email/Password) ✅ COMPLETED (P1)
> Goal achieved: introduce basic auth and protected routes.

### Requirements (delivered)
- **Email + password** registration/login.
- JWT-based auth.
- Protected routes.
- Logged-in user panel + logout in sidebar.

### Implementation details (as built)
#### Backend
- New module: `/app/backend/auth.py`
  - bcrypt password hashing
  - JWT issuance + verification
- Endpoints:
  - `POST /api/auth/register`
  - `POST /api/auth/login`
  - `GET /api/auth/me`

#### Frontend
- New Auth context: `/app/frontend/src/contexts/AuthContext.js`
  - token storage in localStorage
  - axios default Authorization header
  - fetch current user `/auth/me`
- New page: `/app/frontend/src/pages/AuthPage.js` (login/register UI)
- Updated routing in `/app/frontend/src/App.js`:
  - route guards
  - redirect unauthenticated users to `/auth`
- Sidebar updated to show user profile + logout.

### Admin account (verified)
- `monika.gawkowska@kurdynowski.pl` (admin)

---

## Phase 9 — Workspaces (Multi-Client) ✅ COMPLETED
> Goal achieved: multi-tenant separation. Decision implemented: **each user owns one workspace**; **admin (Monika) can see all workspaces/content**.

### Delivered scope
1. User-scoped content isolation (articles, stats, generation)
2. Admin bypass (global visibility)
3. Workspace ID persisted per user

### Implementation details (as built)
#### Backend
- `users` fields:
  - `workspace_id: str` (one per user)
  - `is_admin: bool`
- `articles` fields (on create):
  - `user_id`, `workspace_id`
- Access control:
  - `GET /api/articles` scoped by `user_id` unless admin
  - `GET/PUT/DELETE /api/articles/{id}` owner-only unless admin
  - `GET /api/stats` scoped by `user_id` unless admin
- Migration:
  - ensured `workspace_id` exists for users
  - set Monika `is_admin=true`

#### Frontend
- Admin badge shown in sidebar when `user.is_admin === true`.

### Testing
- Verified Monika `/auth/me` returns `is_admin=true`.
- Verified scoping logic passes automated tests.

---

## Phase 10 — Enhanced Image Generator ✅ COMPLETED
> Goal achieved: improve image generation quality, consistency, UX, and add variant generation.

### Delivered scope
1. **8 style presets** via backend registry:
   - `hero`, `fotorealizm`, `ilustracja`, `infografika`, `ikona`, `diagram`, `wykres`, `custom`
2. **Contextual prompts**
   - Optional article context (topic + primary keyword) injected when `article_id` provided.
3. **Variants**
   - Variant types: `color`, `composition`, `mood`, `simplify`

### Implementation details (as built)
#### Backend
- Updated `/app/backend/image_generator.py`:
  - style preset registry + prompt builder
  - `generate_image_variant(...)`
- New endpoint: `GET /api/image-styles`
- Updated endpoint: `POST /api/images/generate` now accepts:
  - `prompt`, `style`, `article_id`, optional `variation_type`
- Images stored with:
  - `user_id`, `style`, optional `variation_type`, optional `article_id`

#### Frontend
- Updated `/app/frontend/src/components/ImageGenerator.js`:
  - style picker
  - prompt auto-fill from article
  - variant buttons
  - improved gallery interaction

### Testing
- Verified `GET /api/image-styles` returns 8 styles.
- Verified generation + variants workflow end-to-end.

---

## Phase 11 — Insert Images in Visual Editor ✅ COMPLETED
> Goal achieved: one-click insertion of generated image into the article HTML.

### Delivered behavior
- In Images panel, the generated image preview includes **"Wstaw w tresc"**.
- Inserts an `img` HTML snippet into editor content and marks state as unsaved.

### Implementation details (as built)
- Frontend:
  - `ImageGenerator` accepts `onInsertImage(imgHtml)`
  - `ArticleEditor` passes callback that appends the snippet to `htmlContent` + sets unsaved flag

### Testing
- UI smoke-tested; insertion triggers unsaved indicator.

---

## Phase 12 — Series Generation + Sources-Driven Content ✅ COMPLETED
> Goal achieved: generate multi-part content plans (clusters) and enable sources/context injection.

### Delivered scope
- Series outline generation (N parts)
- Optional source text context (paste notes/URLs/excerpts)
- Per-part article generation using suggested templates

### Implementation details (as built)
#### Backend
- New module: `/app/backend/series_generator.py`
- New collection: `series`
- Endpoints:
  - `POST /api/series/generate` (outline)
  - `GET /api/series` (list)
- Uses `gpt-5.2` to generate strict JSON series outline.

#### Frontend
- New page: `/app/frontend/src/pages/SeriesGenerator.js`
- New route: `/series`
- Sidebar nav entry: **Serie**
- Outline view allows expanding each part and generating an article for that part (calls `/api/articles/generate` with `template` from outline).

### Testing
- Backend: outline generation + listing verified.
- Frontend: navigation and form verified via screenshots.

---

## Next Actions (updated)
1. **Hardening / Production readiness**
   - Add configurable JWT expiration / refresh strategy (optional)
   - Add rate limiting for AI endpoints (optional)
   - Add audit logging for admin actions (optional)
2. **Workspace expansion (if needed later)**
   - Many-workspaces-per-user, workspace switching UI
   - Invitations/roles
3. **Sources (future)**
   - Server-side URL fetcher + parsing + safety timeouts
   - File upload (PDF) → extraction → grounded generation
4. **Editor enhancements**
   - Insert image at cursor position (instead of append)
   - Figure/caption UI component

---

## Success Criteria (updated)
- Phase 1–12: ✅ delivered as documented.
- Multi-tenant data isolation:
  - Regular users see only their own workspace content.
  - Admin can access all.
- Enhanced images:
  - Presets + context improve relevance.
  - Variants workflow available.
- Image insertion:
  - One-click insert works and preserves export compatibility.
- Series + sources:
  - Outline + per-part generation available; source text can be provided.
- Reliability preserved:
  - No broken anchors.
  - Correct UTF‑8.
  - Exports and image workflows continue to work end-to-end.
