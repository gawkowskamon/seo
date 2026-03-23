# SEO Article Writer - PRD

## Original Problem Statement
Aplikacja do pisania artykulow blogowych zwiazanych z ksiegowoscia, zoptymalizowana pod SEO AI.

## Tech Stack
- Backend: FastAPI + MongoDB (Motor async + PyMongo sync for threads)
- Frontend: React + Shadcn UI + Recharts
- AI: OpenAI gpt-4.1-mini/gpt-5.2 + Gemini gemini-2.0-flash via Emergent LLM Key
- Scraping: httpx + BeautifulSoup (DuckDuckGo)

## Critical Architecture
- All LLM tasks use ThreadPoolExecutor + sync PyMongo + asyncio.new_event_loop()
- 3-model fallback chain: gpt-4.1-mini → gpt-5.2 → gemini-2.0-flash with exponential backoff
- Shared LLM helper: `/app/backend/llm_helper.py` provides `llm_chat()` (async) and `llm_chat_sync()` (sync)
- Stale job recovery on startup: auto-marks stuck "generating" jobs as failed

## Credentials
- Admin: ADMIN_EMAIL / ADMIN_PASSWORD (z .env)
- WordPress: monika.gawkowska@kurdynowski.pl / jY67 vfXG WSqw Wic4 LRRg CJUw

## All Completed Features (30+)
- [x] AI Article generation (E-E-A-T, legal refs, concrete data)
- [x] Visual editor + HTML view + formatting toolbar
- [x] Topic suggestions + AI Article Suggestions
- [x] AI SEO Assistant + Apply All
- [x] Image generator (Nano Banana) + batch
- [x] Content templates (standard, listicle, case study)
- [x] Series article generation
- [x] JWT auth, multi-client workspaces, admin role
- [x] PDF and HTML export
- [x] WordPress integration (styled inline export)
- [x] Subscription system (TPay - mocked)
- [x] Content Calendar + Scheduled WordPress Publishing
- [x] Internal Link Building + Article Import from URL
- [x] AI Chat Assistant + AI Rewriter
- [x] Dark Mode
- [x] Keyword Analytics Dashboard + Newsletter Generator
- [x] Performance Dashboard (admin, DAU/MAU, charts)
- [x] Plagiarism Checker + Content Verification / Fact-Check
- [x] Enhanced SEO Scorer (14 dimensions, E-E-A-T)
- [x] Auto Competition Analysis (DuckDuckGo scraping + AI)
- [x] A/B Title Testing (5 variants, CTR/SEO/Emotion/Clarity)
- [x] Bulk Article Operations (select, delete, categorize)
- [x] Auto Meta Tag Generation (3+3 variants + recommended)
- [x] Article Version History (auto-save, view, restore)
- [x] Smart Publishing Schedule (AI best day/time)
- [x] Social Media Post Generator (LinkedIn/Twitter/Facebook/Instagram x 3 tones)

## Bug Fixes (2026-03-23)
- [x] P0: Article generation 502 Bad Gateway - 3-model fallback chain
- [x] P0: Topic suggestions 502 - Same fallback pattern
- [x] Stale job recovery on startup
- [x] Reduced stale job detection from 600s to 180s
- [x] Applied 3-model fallback to ALL 17 LLM services (37/37 tests passed)

## Services with LLM Fallback
1. article_generator.py - generate_article, suggest_topics
2. seo_assistant.py - analyze_article_seo, chat_about_seo
3. competition_service.py - analyze_competition
4. seo_audit_service.py - run_seo_audit
5. chat_assistant_service.py - chat_with_assistant
6. auto_update_service.py - check_articles_for_updates
7. content_calendar_service.py - generate_content_calendar
8. import_service.py - optimize_imported_article
9. linkbuilding_service.py - analyze_internal_links
10. series_generator.py - generate_series_outline
11. server.py inline: regenerate_section, ai_suggestions, keyword_analytics, rewrite, plagiarism, verification, auto_competition, ab_title, auto_meta, smart_schedule, social_posts, newsletter

## Backlog
- [ ] Social Media Integration - automatyczne publikowanie (P2)
- [ ] Powiadomienia email o potrzebie aktualizacji artykulow (P2)
