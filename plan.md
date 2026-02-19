# plan.md (updated after Phase 8 — JWT Auth ✅ COMPLETED; Phase 6–8 ✅ COMPLETED; Phase 9–12 ✅ PLANNED)

## Objectives
- Deliver a working end‑to‑end content workflow for Polish accounting/tax marketing:
  **topic/keywords → AI generates Polish article (JSON) → TOC+anchors + headings + FAQ + meta → SEO scoring → dual editor (Visual + HTML) → export (FB/Google Business + HTML/PDF)**.
- Provide a complete **media workflow** for blog publishing:
  **AI image generation → per‑article gallery → preview → copy HTML embed → download/delete → (Next) insert image into content**.
- Provide an in-editor **AI SEO Assistant** to improve drafts faster:
  - Combines **prioritized suggestions (with Apply actions)** + **interactive chat**.
  - Uses **OpenAI `gpt-5.2`** via Emergent integrations.
- Deliver a **brand-aligned, premium SaaS UI**:
  - **Kurdynowski branding** (primary blue `#04389E`, accent orange `#F28C28`), modern‑classic look.
  - Typography: **Instrument Serif** for display/headings + IBM Plex Sans for UI + IBM Plex Mono for code.
- Add **advanced content creation** for specialized, higher‑value deliverables:
  - Template-based generation with specialized structures.
  - Advanced formatting blocks (callouts, tables, checklists) rendered and styled in the visual editor.
  - (Next) Series generation + sources-driven generation.
- Add **simple authentication** and deliver **multi-tenant separation**:
  - Email/password auth (JWT) and protected routes ✅.
  - (Next) **Workspaces** + user/workspace-scoped data isolation.
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

### Follow-ups (still planned)
- Series generation (N-part outlines + per-part drafts).
- Sources-driven generation (URL/paste; optional file upload).

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

### Progress note (recent)
- Admin account created:
  - `monika.gawkowska@kurdynowski.pl` (admin)

### Follow-ups (still planned)
- Workspaces (multi-client/brand separation) and scoping articles/images by workspace.

---

## Phase 9 — Workspaces (Multi-Client) ✅ PLANNED (STARTING NOW)
> Goal: introduce multi-tenant separation. Per current decision: **each user owns one workspace**; **admin (Monika) can see all workspaces**.

### User stories
1. As a user, I see only my own articles and images.
2. As an admin, I can see all users’ workspaces and all content.
3. Articles and images created by a user are automatically associated with that user/workspace.

### Implementation steps (revised, concrete)
#### Backend
- Data model
  - Add to `users`:
    - `is_admin: bool` (default false)
    - `workspace_id: str` (one per user)
  - Add to `articles`:
    - `user_id: str`
    - `workspace_id: str`
  - Add to `images`:
    - `user_id: str`
    - `workspace_id: str`
- Auth token
  - Include `is_admin` and `workspace_id` in `/auth/me` response (or resolve server-side from DB).
- Access control
  - Update all relevant endpoints to enforce scoping:
    - `GET /api/articles` → return only `{user_id=current}` unless `is_admin`
    - `GET/PUT/DELETE /api/articles/{id}` → allow only owner unless `is_admin`
    - `POST /api/articles/generate` → attach user/workspace
    - Image endpoints → same scoping
- Admin
  - Mark `monika.gawkowska@kurdynowski.pl` as `is_admin=true`.
- Migration
  - Migrate existing articles/images (no `user_id`) to Monika’s `user_id` and `workspace_id`.

#### Frontend
- Ensure auth token is attached to all API calls (axios default header already in AuthContext).
- Dashboard/Editor lists reflect scoped data automatically.
- Optional: show **Admin** badge in sidebar for admin users.

### Testing
- Verify:
  - Non-admin cannot access other users’ resources.
  - Admin can access all.
  - Existing content visible to admin after migration.

---

## Phase 10 — Enhanced Image Generator ✅ PLANNED
> Goal: improve image generation quality, consistency, and UX.

### Scope (per decision: “d”)
1. **More style presets**
   - Photorealistic, Illustration, Minimal icon, Infographic, 3D, Flat vector, Corporate / brand-safe.
2. **Contextual prompts**
   - Automatically include article topic, primary keyword, and section intent.
   - Brand-safe guidance aligned with Kurdynowski palette.
3. **Variants / edits**
   - “Generate variations” from an existing image (same composition, different style or minor changes).

### Implementation steps
#### Backend
- Extend image generation request schema:
  - `style_preset`
  - `context` (topic/keyword)
  - `variant_of_image_id` (optional)
- Prompt builder:
  - enforce brand-safe, professional accounting visuals
  - optional orange/blue accent suggestions
- Store:
  - `prompt`, `preset`, `context`, `variant_of`

#### Frontend
- Update Images tab UI:
  - preset picker (with preview chips)
  - toggle “use article context”
  - action “Generate variants” on existing images

### Testing
- Verify presets, context inclusion, variant workflow end-to-end.

---

## Phase 11 — Insert Images in Visual Editor ✅ PLANNED (optional but requested)
> Goal: insert selected gallery images into the article content.

### User stories
1. Insert image at cursor position.
2. Auto-add alt text + caption fields.
3. Maintain HTML validity and export compatibility.

### Implementation steps
- Frontend:
  - Add “Insert into article” action in Images tab.
  - Insert HTML snippet:
    - `cfigureecimg src="..." alt="..." /ecfigcaptione...c/figcaptionec/figuree`
  - If editor cannot place at cursor reliably, fallback to insert after current section.
- Backend:
  - No changes required (unless storing image CDN URLs or structured blocks).

---

## Phase 12 — Series Generation + Sources-Driven Content ✅ PLANNED
> Goal: generate multi-part content plans and drafts; allow feeding source URLs/text.

### Scope
- Series generation
  - Generate series outline (N parts) + part-by-part generation.
- Sources-driven
  - Accept URL(s) and pasted text as context for generation.

### Implementation steps
- Backend:
  - New endpoint(s):
    - `POST /api/series/outline`
    - `POST /api/series/generate-part`
    - `POST /api/articles/generate-from-sources`
  - Basic URL fetcher (server-side) with safety/timeouts.
- Frontend:
  - New “Series” view in generator or separate page.
  - Inputs for URLs/paste and preview of extracted context.

---

## Next Actions (updated)
1. **Phase 9 — Workspaces** (start now)
2. **Phase 10 — Enhanced image generator** (presets + contextual prompts + variants)
3. **Phase 11 — Insert images into Visual editor**
4. **Phase 12 — Series generation + sources-driven content**

---

## Success Criteria (updated)
- Phase 1–8: ✅ delivered as documented.
- Multi-tenant data isolation:
  - Regular users see only their own workspace content.
  - Admin can access all.
- Enhanced images:
  - Presets + context improve relevance.
  - Variants workflow available.
- Image insertion:
  - One-click insert with alt/caption.
- Series + sources:
  - Outline + per-part generation, source-driven drafts.
- Reliability preserved:
  - No broken anchors.
  - Correct UTF‑8.
  - Exports and image workflows continue to work end-to-end.
