# SEO Article Writer - PRD

## Original Problem Statement
Aplikacja do pisania artykulow blogowych zwiazanych z ksiegowoscia, zoptymalizowana pod SEO AI.

## Core Requirements
- Generowanie artykulow zoptymalizowanych pod SEO (cel: 99%+)
- Edytor wizualny z paskiem formatowania i widokiem HTML
- Sugestie tematow artykulow
- Asystent AI do poprawy wynikow SEO
- Generator obrazow (Nano Banana) z obsluga wielu obrazow referencyjnych
- Rozne szablony tresci (standard, listicle, case study)
- Generowanie serii powiazanych artykulow
- Uwierzytelnianie JWT, wieloklientowe workspace, rola admina
- Eksport PDF i HTML
- Integracja z WordPress (publikowanie, import, stylizacja)
- System subskrypcji z TPay
- Nowoczesny, profesjonalny design

## Tech Stack
- **Backend**: FastAPI + MongoDB (Motor async + PyMongo sync for threads)
- **Frontend**: React + Shadcn UI
- **AI**: OpenAI gpt-4.1-mini (text), gpt-5.2 (SEO assistant), Gemini nano-banana (images) via Emergent LLM Key
- **Payments**: TPay
- **CMS**: WordPress REST API

## Completed Features
- [x] Generowanie artykulow AI (async z MongoDB job persistence)
- [x] Edytor wizualny z HTML sync
- [x] SEO scoring engine (flexible keyword matching)
- [x] SEO AI Assistant (async z polling, GPT-5.2)
- [x] Auto-optymalizacja SEO ("Zastosuj wszystkie" - jednorazowe aplikowanie sugestii)
- [x] Smart find-and-replace sugestii SEO (nie append)
- [x] Generator obrazow (single + multi reference)
- [x] Szablony tresci
- [x] Serie artykulow
- [x] JWT auth + admin role (auto-seeding z env vars)
- [x] Eksport PDF/HTML/Facebook/Google Business
- [x] WordPress publish z inline styling
- [x] WordPress import z autodiscovery REST API
- [x] Kalendarz tresci
- [x] Zaplanowane publikacje WordPress
- [x] Automatyczne linkowanie wewnetrzne
- [x] Import artykulow z URL
- [x] AI Chat Assistant
- [x] Dark Mode
- [x] Keyword Analytics Dashboard
- [x] AI Rewriter
- [x] Generator Newsletterow
- [x] System subskrypcji TPay
- [x] Panel admina (users CRUD)

## Production Deployment Fixes (Feb 2026)
- [x] load_dotenv(override=False)
- [x] Admin credentials w env vars (ADMIN_EMAIL, ADMIN_PASSWORD)
- [x] JWT secret wymaga env var (JWT_SECRET)
- [x] MongoDB client z serverSelectionTimeoutMS=5000
- [x] seed_admin_user() w try/except
- [x] os.environ.get() zamiast os.environ[] dla MONGO_URL
- [x] N+1 query fix w admin users endpoint
- [x] PDF font fallback

## SEO AI Async + Auto-Optimize (Mar 10, 2026)
- [x] SEO Assistant async polling (POST start + GET status)
- [x] LLM w ThreadPoolExecutor (nie blokuje event loop)
- [x] Sync PyMongo w watku
- [x] Smart find-and-replace sugestii
- [x] Przycisk "Zastosuj wszystkie" - aplikuje wszystkie sugestie jednorazowo

## Credentials
- **Admin**: ADMIN_EMAIL / ADMIN_PASSWORD (z .env)
- **WordPress**: monika.gawkowska@kurdynowski.pl / jY67 vfXG WSqw Wic4 LRRg CJUw
- **WordPress URL**: https://kurdynowski.com.pl/cms-biuro

## Backlog (P2+)
- [ ] A/B Testing tytulow
- [ ] Integracja Social Media
- [ ] Masowe operacje na artykulach
- [ ] Historia wersji artykulow
- [ ] Auto generowanie meta tagow
