# plan.md (updated after Phase 4 — AI Image Generation + Phase 5 kickoff — AI SEO Assistant)

## Objectives
- Deliver a working MVP that supports the full flow end‑to‑end:
  **topic/keywords → AI generates Polish accounting article (JSON) → TOC+anchors + headings + FAQ + meta → SEO scoring → dual editor (Visual + HTML) → export (FB/Google Business + HTML/PDF)**.
- Provide a complete **media workflow** for blog publishing:
  **AI image generation (Gemini “Nano Banana”) → gallery per article → preview → copy HTML embed → download**.
- Add an interactive **AI SEO Assistant** to help improve drafts inside the editor:
  - Combines **actionable suggestion list (with Apply actions)** + **interactive chat**.
  - Uses **OpenAI `gpt-5.2`** via Emergent integrations.
- Ensure reliability and production readiness:
  - Stable LLM generation (model fallback/retries where relevant).
  - Consistent Polish UX (UTF‑8 chars, no escaped sequences).
  - Credible sources included in every draft.
  - Robust export formats.
- Preserve and extend Phase 3 UX upgrades:
  - shadcn Select components (no native select warnings).
  - Autosave + unsaved changes indicator.
  - AI regeneration of FAQ and meta data.

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
  - Editor (3-panel layout):
    - Left: TOC + anchor copy, internal link suggestions, sources.
    - Center: Visual editor + HTML editor tabs.
    - Right: SEO score panel + FAQ editor + Export panel tabs.
- Polish UI and correct UTF‑8 rendering fixed (no `\uXXXX` artifacts).

### Testing (done)
- Backend tests: **100% pass** (articles, stats, export, scoring).
- Frontend E2E: **functional flow verified** (dashboard → editor → tabs → export).

---

## Phase 3 — Feature Expansion (UX + regeneration + stability) ✅ COMPLETED
> Goal achieved: implement planned UX improvements and AI regeneration capabilities.

### Goals (completed)
- Remove low-priority console warnings by replacing native selects.
- Add autosave to improve editing reliability.
- Add AI regeneration actions to iterate faster on SEO elements.
- Add backend endpoint to support regeneration.

### User stories (delivered)
1. As a user, I can use polished dropdowns (shadcn Select) in Generator and Topics pages.
2. As a user, I can edit an article and have it autosave with clear “Zapisano/Niezapisane” status.
3. As a user, I can regenerate **FAQ** with AI without regenerating the full article.
4. As a user, I can regenerate **meta title + meta description** with AI.

### Implementation steps (completed)
#### 3.1 UX improvements
- Replaced native `<select>` elements with **shadcn/ui Select** in:
  - `/generator`
  - `/topics`

#### 3.2 Autosave
- Added autosave with **10-second debounce** in the editor.
- Added toolbar indicator:
  - **Zapisano** (saved)
  - **Niezapisane** (unsaved)

#### 3.3 AI regeneration
- Frontend:
  - Meta: “Regeneruj” action next to meta title.
  - FAQ: “AI” button in FAQ editor.
- Backend:
  - Added `POST /api/articles/{id}/regenerate` supporting:
    - `{ "section": "meta" }`
    - `{ "section": "faq" }`
  - Uses **`gpt-4.1-mini`**.

### Testing (done)
- Backend: regeneration endpoint tested successfully.
- Frontend: regeneration buttons verified, autosave indicator verified.
- Overall: **Backend 100%**, **Frontend 95%** (minor console warnings only; no functional impact).

---

## Phase 4 — AI Image Generation (Gemini “Nano Banana”) ✅ COMPLETED
> Goal achieved: add an image generation workflow for article illustrations, integrated into the editor.

### Goals (completed)
- Add AI image generation using Gemini image model (“Nano Banana”).
- Allow generating multiple image types/styles for blog publishing.
- Provide per-article image management (gallery, preview, download, delete).
- Make it easy to embed images into the article HTML.

### User stories (delivered)
1. As a user, I can generate an image for an article with a selected style (Hero/Sekcja/Infografika/Własny prompt).
2. As a user, I can view all images generated for a specific article.
3. As a user, I can open a full preview of an image.
4. As a user, I can **copy HTML** for an image (data URI) and paste it into the HTML editor.
5. As a user, I can download an image file.
6. As a user, I can delete images I don’t want.

### Implementation details (as built)
#### Backend (FastAPI)
- New service:
  - `image_generator.py`: Gemini image generation via Emergent:
    - Model: **`gemini-3-pro-image-preview`**
    - Modalities: `[..., "image", "text"]`
    - Supported styles: `hero`, `section`, `infographic`, `custom`
- New persistence:
  - MongoDB collection `images` storing:
    - `id`, `article_id`, `prompt`, `style`, `mime_type`, `data` (base64), `created_at`
- New endpoints under `/api`:
  - `POST /api/images/generate` (returns base64 image + metadata)
  - `GET /api/images/{image_id}` (fetch full base64)
  - `GET /api/articles/{article_id}/images` (list images for an article; excludes `data` for performance)
  - `DELETE /api/images/{image_id}`

#### Frontend (React)
- New component:
  - `ImageGenerator.js` embedded into the editor.
- Editor updates:
  - Added new right-panel tab: **Obrazy**.
  - Image panel includes:
    - Style selector
    - Prompt input (auto-filled from article topic/title)
    - Generate action (loading state)
    - Gallery grid per article
    - Full preview with:
      - Copy HTML
      - Download
      - Delete

### Testing (done)
- Backend: **100%** (images list + retrieval tested; generation validated via POC and direct endpoint test).
- Frontend: **100%** (Obrazy tab verified, gallery/preview/actions verified; existing flows preserved).

---

## Phase 5 — AI SEO Assistant (Suggestions + Chat) 🔥 IN PROGRESS (P0)
> Goal: help users actively improve drafts by providing prioritized SEO suggestions with one-click apply actions, plus an interactive chat for iterative improvements. Uses **OpenAI `gpt-5.2`**.

### User stories (to deliver)
1. As a user, I can open an **Asystent AI** panel inside the Article Editor.
2. As a user, I can generate a **prioritized list of SEO improvement suggestions** for the current article.
3. As a user, I can click **Zastosuj** on a suggestion to apply it to the article (meta/HTML/FAQ/structure) and mark the article as having unsaved changes.
4. As a user, I can chat with the assistant about the article (e.g., “jak poprawić CTR meta opisu?”) and get concrete edits.
5. As a user, I can re-run SEO scoring after applying changes and see improvement.

### Architecture plan
#### Backend (FastAPI)
- New endpoint:
  - `POST /api/articles/{article_id}/seo-assistant`
- Request payload (concept):
  - `mode`: `"analyze" | "chat"` (or inferred)
  - `message`: optional user message (chat)
  - `history`: conversation history (stored client-side initially; later can be persisted)
  - `context`: article snapshot fields (title/meta/html/keywords) or fetched server-side by `article_id`
- Response payload (concept):
  - `assistant_message`: natural-language reply (PL)
  - `suggestions`: structured list with:
    - `id`, `title`, `severity/impact`, `category` (meta, headings, content, keywords, internal links, faq)
    - `rationale`
    - `proposed_change` (structured patch: which field, what replacement/insert)
    - `apply_target` (e.g., `meta_title`, `meta_description`, `html_content`, `faq[]`, `sections[]`)
- LLM implementation:
  - Provider/model: `("openai", "gpt-5.2")` via `emergentintegrations.llm.chat.LlmChat`.
  - System message: SEO expert (Polish accounting), output must be strict JSON for suggestions + optional assistant text.
  - Safety/reliability:
    - JSON-only contract for structured suggestions.
    - Basic cleaning for accidental fenced blocks.
    - Guardrails to avoid hallucinated legal claims (assistant should recommend adding/confirming sources).

#### Frontend (React)
- ArticleEditor right panel:
  - Add a new tab: **Asystent AI** (next to SEO/FAQ/Obrazy/Eksport).
  - Component: `SEOAssistantPanel.js` (new)
    - Upper section: **Sugestie** list with filters (optional) and **Zastosuj** buttons.
    - Lower section: **Chat** interface (message list + input + send).
    - “Analizuj artykuł” primary action to generate initial suggestions.
    - Loading, error and empty states consistent with current UI.
  - Apply behavior:
    - For simple targets (meta fields): update `metaTitle`/`metaDescription` state.
    - For HTML patch: update `htmlContent` and mark `hasUnsavedChanges=true`.
    - For FAQ updates: update `article.faq` state and mark unsaved.
- Data-testid requirements:
  - `article-ai-assistant-tab`
  - `ai-assistant-suggestions`
  - `ai-assistant-apply-suggestion-button`
  - `ai-assistant-chat`
  - `ai-assistant-chat-input`
  - `ai-assistant-chat-send-button`

### Implementation steps
1. Backend: implement `POST /api/articles/{id}/seo-assistant`.
2. Define strict JSON schema for suggestions + assistant reply.
3. Add model configuration using `gpt-5.2` and reuse `EMERGENT_LLM_KEY` from `/app/backend/.env`.
4. Frontend: add **Asystent AI** tab and new panel component.
5. Implement apply actions that mutate editor state (meta/html/faq) and trigger unsaved indicator.
6. Add timeouts and UI spinners (similar to regenerate endpoints).
7. Add minimal tests:
   - Backend: endpoint returns valid structure.
   - Frontend: tab renders, suggestions list renders, apply changes modifies state.

### Success criteria
- Assistant can generate suggestions for a loaded article within acceptable latency.
- Suggestions are **actionable** and apply cleanly without breaking editor content.
- Chat is usable and context-aware of current article.
- After applying changes, user can rescore and typically see measurable improvement.

---

## Phase 6 — Hardening + Auth + Workspaces (only after approval)

### User stories
1. As a user, I can sign in and see only my articles.
2. As a user, I can manage multiple brands/clients (workspaces).
3. As a user, I can set default templates and SEO rules per workspace.
4. As a user, I can audit generation history (prompt, model, time, cost estimate).
5. As a user, I can collaborate via shareable review links (view/comment).
6. As a user, I can manage media assets per workspace (quotas, tagging, reuse across articles).

### Implementation steps
- Add JWT auth + workspace isolation.
- Rate limiting, caching, cost tracking.
- Robust HTML sanitization + export consistency.
- Media storage improvements:
  - Optionally store images in object storage (S3/GCS) instead of base64 in MongoDB.
  - CDN delivery + resizing/optimization.

---

## Next Actions (updated)
1. **Build Phase 5 — AI SEO Assistant (P0)**:
   - Backend endpoint + structured suggestions + chat flow on `gpt-5.2`.
   - Frontend panel integrated into editor with Apply actions.
2. After Phase 5 is stable:
   - Phase 6: Auth + workspaces + templates + audit trail.
   - Optional: One-click internal-link insertion and competitor comparison.
   - Optional: Add image insertion directly into Visual editor (not only copy HTML).

---

## Success Criteria (updated)
- POC: ✅ Valid JSON generation + scoring proven.
- V1: ✅ User can generate → edit (Visual/HTML) → score → export (FB/Google + HTML/PDF).
- Phase 3: ✅ UX improvements + autosave + regeneration delivered.
- Phase 4: ✅ AI image generation integrated (styles + gallery + preview + copy HTML + download + delete).
- Phase 5 (target):
  - ✅ AI SEO Assistant panel (suggestions + chat) available in editor.
  - ✅ Uses **`gpt-5.2`**.
  - ✅ Suggestions can be applied to content/meta/FAQ without breaking the article.
- Reliability:
  - No broken anchors.
  - Correct UTF‑8 Polish UI.
  - Stable LLM generation using **`gpt-4.1-mini`** with retries/fallback (generation/regeneration).
  - Exports work (copy-ready FB/GBP + HTML + PDF).
  - Image workflow works end-to-end (generate/list/retrieve/manage).
