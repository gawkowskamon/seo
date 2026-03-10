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
- [x] load_dotenv(override=False) - nie nadpisuje zmiennych Kubernetes
- [x] Admin credentials przeniesione do env vars (ADMIN_EMAIL, ADMIN_PASSWORD)
- [x] JWT secret wymaga env var (JWT_SECRET) - bez hardcoded fallback
- [x] MongoDB client z serverSelectionTimeoutMS=5000
- [x] seed_admin_user() w try/except - nie crashuje app jesli DB niedostepna
- [x] os.environ.get() zamiast os.environ[] dla MONGO_URL
- [x] N+1 query fix w admin users endpoint (aggregation)
- [x] PDF font fallback (DejaVu -> Helvetica)

## SEO AI Async Fix (Mar 10, 2026)
- [x] SEO Assistant przeniesiony na async polling (POST start + GET status)
- [x] LLM call uruchamiany w ThreadPoolExecutor (nie blokuje event loop)
- [x] Sync PyMongo w watku (zamiast async Motor) - unika problemow z event loop
- [x] Frontend polling co 3s, max 40 prob (2 min timeout)
- [x] Tryb analyze i chat oba async
- [x] Sugestie SEO: smart find-and-replace zamiast append
  - Proba exact match current_value
  - Fallback: stripped text match (bez tagow HTML)  
  - Ostateczny fallback: append

## Key Technical Details
- **Root cause SEO timeout**: litellm.completion() jest synchroniczne wewnatrz async metody emergentintegrations
- **Solution**: run_in_executor z ThreadPoolExecutor + sync PyMongo + asyncio.new_event_loop()
- **Production proxy timeout**: 30 sekund (Kubernetes ingress)
- **LLM response time**: ~50 sekund w watku

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
