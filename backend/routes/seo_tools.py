"""SEO tools: audit, competition analysis, keyword analytics, rewriter, newsletter, subscriptions, AI suggestions, performance, plagiarism, verification, auto-competition, A/B titles."""
import os, logging, asyncio
from fastapi import APIRouter, Depends
from shared import (
    db, get_current_user, require_admin, serialize_doc, executor, client, HTTPException,
    uuid, datetime, timezone, json, re, BaseModel,
    SEOAuditRequest, CompetitionRequest, KeywordAnalyticsRequest,
    RewriteRequest, NewsletterRequest, PlagiarismCheckRequest,
    ContentVerifyRequest, AutoCompetitionRequest, ABTitleRequest,
    Optional, List, Dict, Any
)
from seo_audit_service import run_seo_audit
from competition_service import analyze_competition
from tpay_service import get_all_plans, get_plan, create_tpay_transaction, calculate_subscription_end

router = APIRouter()

# In-memory job stores for async operations
_plagiarism_jobs = {}
_verification_jobs = {}
_auto_competition_jobs = {}
_ab_title_jobs = {}
_keyword_analytics_jobs = {}
_rewrite_jobs = {}

# --- SEO Audit ---


# Background job storage for SEO audit
_seo_audit_jobs = {}

def _sync_run_seo_audit(job_id: str, url: str, emergent_key: str, user_id: str):
    """Run SEO audit in thread to avoid blocking event loop."""
    import pymongo
    sync_client = pymongo.MongoClient(os.environ.get('MONGO_URL'), serverSelectionTimeoutMS=5000)
    sync_db = sync_client[os.environ.get('DB_NAME', 'seo_article_writer')]
    try:
        _seo_audit_jobs[job_id]["status"] = "running"
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(run_seo_audit(url, emergent_key))
        finally:
            loop.close()
        audit_id = str(uuid.uuid4())
        sync_db.seo_audits.insert_one({
            "id": audit_id, "user_id": user_id, "url": url,
            "result": result, "created_at": datetime.now(timezone.utc).isoformat()
        })
        _seo_audit_jobs[job_id]["status"] = "completed"
        _seo_audit_jobs[job_id]["result"] = {"id": audit_id, **result}
    except Exception as e:
        logging.error(f"SEO audit background error: {e}")
        _seo_audit_jobs[job_id]["status"] = "failed"
        _seo_audit_jobs[job_id]["error"] = str(e)
    finally:
        sync_client.close()

@router.post("/seo-audit")
async def run_audit(request: SEOAuditRequest, user: dict = Depends(get_current_user)):
    """Start async SEO audit on a URL - returns job_id for polling."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    
    job_id = str(uuid.uuid4())
    _seo_audit_jobs[job_id] = {
        "status": "queued",
        "result": None,
        "error": None,
        "user_id": user["id"]
    }
    
    asyncio.get_event_loop().run_in_executor(None, _sync_run_seo_audit, job_id, request.url, emergent_key, user["id"])
    
    return {"job_id": job_id, "status": "queued"}

@router.get("/seo-audit/status/{job_id}")
async def get_audit_status(job_id: str, user: dict = Depends(get_current_user)):
    """Poll SEO audit job status."""
    job = _seo_audit_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    if job["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Brak dostepu")
    
    result = {"job_id": job_id, "status": job["status"]}
    
    if job["status"] == "completed":
        result["result"] = job["result"]
        del _seo_audit_jobs[job_id]
    elif job["status"] == "failed":
        result["error"] = job["error"]
        del _seo_audit_jobs[job_id]
    
    return result

@router.get("/seo-audit/history")
async def get_audit_history(user: dict = Depends(get_current_user)):
    """Get user's audit history."""
    audits = await db.seo_audits.find(
        {"user_id": user["id"]},
        {"_id": 0, "id": 1, "url": 1, "created_at": 1, "result.overall_score": 1, "result.grade": 1}
    ).sort("created_at", -1).to_list(20)
    return audits


# --- Competition Analysis ---


# Background job storage for competition analysis
_competition_jobs = {}

def _sync_run_competition(job_id: str, article: dict, competitor_url: str, emergent_key: str, user_id: str):
    """Run competition analysis in thread."""
    try:
        _competition_jobs[job_id]["status"] = "running"
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(analyze_competition(article, competitor_url, emergent_key))
        finally:
            loop.close()
        _competition_jobs[job_id]["status"] = "completed"
        _competition_jobs[job_id]["result"] = result
    except Exception as e:
        logging.error(f"Competition analysis background error: {e}")
        _competition_jobs[job_id]["status"] = "failed"
        _competition_jobs[job_id]["error"] = str(e)

@router.post("/competition/analyze")
async def analyze_comp(request: CompetitionRequest, user: dict = Depends(get_current_user)):
    """Start async competition analysis - returns job_id for polling."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    
    article = await db.articles.find_one({"id": request.article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Artykul nie znaleziony")
    
    job_id = str(uuid.uuid4())
    _competition_jobs[job_id] = {
        "status": "queued",
        "result": None,
        "error": None,
        "user_id": user["id"]
    }
    
    asyncio.get_event_loop().run_in_executor(None, _sync_run_competition, job_id, article, request.competitor_url, emergent_key, user["id"])
    
    return {"job_id": job_id, "status": "queued"}

@router.get("/competition/status/{job_id}")
async def get_competition_status(job_id: str, user: dict = Depends(get_current_user)):
    """Poll competition analysis job status."""
    job = _competition_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    if job["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Brak dostepu")
    
    result = {"job_id": job_id, "status": job["status"]}
    
    if job["status"] == "completed":
        result["result"] = job["result"]
        del _competition_jobs[job_id]
    elif job["status"] == "failed":
        result["error"] = job["error"]
        del _competition_jobs[job_id]
    
    return result


# --- Keyword Analytics ---

def _sync_run_keyword_analytics(job_id: str, keywords: list, industry: str, emergent_key: str, user_id: str):
    """Run keyword analytics in thread."""
    import pymongo
    sync_client = pymongo.MongoClient(os.environ.get('MONGO_URL'), serverSelectionTimeoutMS=5000)
    sync_db = sync_client[os.environ.get('DB_NAME', 'seo_article_writer')]
    try:
        _keyword_analytics_jobs[job_id]["status"] = "running"
        from llm_helper import llm_chat_sync
        
        kw_list = ", ".join(keywords[:10]) if keywords else "ulgi podatkowe, VAT 2026, ZUS, PIT, CIT, księgowość online, biuro rachunkowe, faktury elektroniczne"
        
        prompt = f"""Jesteś ekspertem SEO w branży: {industry}.
Przeanalizuj poniższe słowa kluczowe i wygeneruj dane analityczne w formacie JSON.

Słowa kluczowe: {kw_list}

Dla każdego słowa kluczowego podaj:
- keyword: nazwa
- monthly_searches: szacunkowa miesięczna liczba wyszukiwań (realistyczna dla polskiego rynku)
- difficulty: trudność 1-100
- trend: "rosnący", "stabilny" lub "malejący"
- trend_data: tablica 6 wartości (ostatnie 6 miesięcy, np. [80,85,90,88,95,100])
- cpc_pln: szacunkowy koszt za klik w PLN
- season_peak: miesiąc szczytowy (1-12)
- related_topics: lista 3 powiązanych tematów na artykuły
- opportunity_score: wynik szansy 1-100 (wysoki = łatwe do pozycjonowania + dużo wyszukiwań)

Odpowiedz TYLKO prawidłowym JSON: {{"keywords": [...]}}"""
        
        text = llm_chat_sync(prompt, system_message="Jesteś ekspertem SEO i analityki słów kluczowych w Polsce. Odpowiadaj WYŁĄCZNIE poprawnym JSON-em.", session_id=f"kw-analytics-{job_id[:8]}", timeout=120)
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        
        import json as json_mod
        data = json_mod.loads(text)
        
        _keyword_analytics_jobs[job_id]["status"] = "completed"
        _keyword_analytics_jobs[job_id]["result"] = data
        
        sync_db.keyword_analytics.insert_one({
            "id": job_id, "user_id": user_id, "keywords": keywords,
            "result": data, "created_at": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logging.error(f"Keyword analytics error: {e}")
        _keyword_analytics_jobs[job_id]["status"] = "failed"
        _keyword_analytics_jobs[job_id]["error"] = str(e)
    finally:
        sync_client.close()

@router.post("/keyword-analytics/analyze")
async def analyze_keywords(request: KeywordAnalyticsRequest, user: dict = Depends(get_current_user)):
    """Start async keyword analytics."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    
    job_id = str(uuid.uuid4())
    _keyword_analytics_jobs[job_id] = {"status": "queued", "result": None, "error": None, "user_id": user["id"]}
    asyncio.get_event_loop().run_in_executor(None, _sync_run_keyword_analytics, job_id, request.keywords, request.industry, emergent_key, user["id"])
    return {"job_id": job_id, "status": "queued"}

@router.get("/keyword-analytics/status/{job_id}")
async def get_keyword_analytics_status(job_id: str, user: dict = Depends(get_current_user)):
    """Poll keyword analytics job status."""
    job = _keyword_analytics_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    result = {"job_id": job_id, "status": job["status"]}
    if job["status"] == "completed":
        result["result"] = job["result"]
        del _keyword_analytics_jobs[job_id]
    elif job["status"] == "failed":
        result["error"] = job["error"]
        del _keyword_analytics_jobs[job_id]
    return result

@router.get("/keyword-analytics/history")
async def get_keyword_analytics_history(user: dict = Depends(get_current_user)):
    """Get keyword analytics history."""
    docs = await db.keyword_analytics.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).limit(10).to_list(10)
    return docs


# --- AI Rewriter ---

def _sync_run_rewrite(job_id: str, text: str, style: str, emergent_key: str):
    """Run rewrite in thread."""
    try:
        _rewrite_jobs[job_id]["status"] = "running"
        from llm_helper import llm_chat_sync
        
        style_prompts = {
            "profesjonalny": "Przepisz tekst w profesjonalnym, eksperckim tonie. Używaj fachowej terminologii podatkowej i księgowej. Zachowaj precyzję i powagę.",
            "przystępny": "Przepisz tekst prostym, przystępnym językiem. Wyjaśniaj trudne terminy. Używaj przykładów z życia. Pisz jak do osoby bez wiedzy podatkowej.",
            "ekspercki": "Przepisz tekst w tonie autorytetu branżowego. Cytuj przepisy prawne, dodawaj kontekst historyczny i porównania. Pisz jak doradca podatkowy z 20-letnim doświadczeniem.",
            "seo": "Przepisz tekst z optymalizacją pod SEO. Używaj naturalnie słów kluczowych, twórz krótkie akapity, dodaj pytania retoryczne i wezwania do działania.",
            "skrócony": "Skróć tekst zachowując najważniejsze informacje. Usuń powtórzenia i zbędne słowa. Maks 50% oryginalnej długości.",
            "rozszerzony": "Rozszerz tekst o dodatkowe szczegóły, przykłady, dane liczbowe i kontekst prawny. Dodaj minimum 50% więcej treści."
        }
        
        instruction = style_prompts.get(style, style_prompts["profesjonalny"])
        
        prompt = f"""{instruction}

ORYGINALNY TEKST:
{text[:8000]}

WAŻNE:
- Zachowaj formatowanie HTML jeśli występuje
- Nie dodawaj komentarzy, zwróć TYLKO przepisany tekst
- Zachowaj wszystkie dane liczbowe i faktograficzne"""

        response = llm_chat_sync(prompt, system_message="Jesteś ekspertem od pisania treści w języku polskim. Przepisuj tekst zgodnie z instrukcjami.", session_id=f"rewrite-{job_id[:8]}", timeout=120)
        _rewrite_jobs[job_id]["status"] = "completed"
        _rewrite_jobs[job_id]["result"] = {"rewritten_text": response.strip(), "style": style}
    except Exception as e:
        logging.error(f"Rewrite error: {e}")
        _rewrite_jobs[job_id]["status"] = "failed"
        _rewrite_jobs[job_id]["error"] = str(e)

@router.post("/rewrite")
async def rewrite_text(request: RewriteRequest, user: dict = Depends(get_current_user)):
    """Start async text rewrite."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Brak tekstu do przepisania")
    
    job_id = str(uuid.uuid4())
    _rewrite_jobs[job_id] = {"status": "queued", "result": None, "error": None}
    asyncio.get_event_loop().run_in_executor(None, _sync_run_rewrite, job_id, request.text, request.style, emergent_key)
    return {"job_id": job_id, "status": "queued"}

@router.get("/rewrite/status/{job_id}")
async def get_rewrite_status(job_id: str, user: dict = Depends(get_current_user)):
    """Poll rewrite job status."""
    job = _rewrite_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    result = {"job_id": job_id, "status": job["status"]}
    if job["status"] == "completed":
        result["result"] = job["result"]
        del _rewrite_jobs[job_id]
    elif job["status"] == "failed":
        result["error"] = job["error"]
        del _rewrite_jobs[job_id]
    return result


# --- Newsletter Generator ---


@router.post("/newsletter/generate")
async def generate_newsletter(request: NewsletterRequest, user: dict = Depends(get_current_user)):
    """Generate newsletter from selected articles."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    
    # Get articles
    if request.article_ids:
        articles = await db.articles.find({"id": {"$in": request.article_ids}, "user_id": user["id"]}, {"_id": 0}).to_list(20)
    else:
        articles = await db.articles.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    
    if not articles:
        raise HTTPException(status_code=400, detail="Brak artykułów do newslettera")
    
    articles_summary = ""
    for a in articles:
        articles_summary += f"\n- Tytuł: {a.get('title','')}\n  Meta opis: {a.get('meta_description','')}\n  SEO: {a.get('seo_score',{}).get('percentage',0)}%\n"
    
    from llm_helper import llm_chat
    
    title = request.title or "Cotygodniowy newsletter podatkowy"
    
    prompt = f"""Wygeneruj profesjonalny newsletter email w HTML dla biura rachunkowego Kurdynowski.
Tytuł: {title}
Styl: {request.style}

Artykuły do uwzględnienia:
{articles_summary}

Wygeneruj:
1. Nagłówek newslettera z logo tekstowym "Kurdynowski"
2. Krótkie powitanie (2-3 zdania)
3. Dla każdego artykułu: tytuł, krótki opis (2-3 zdania), przycisk "Czytaj więcej"
4. Sekcja "Ważne terminy" z najbliższymi datami podatkowymi
5. Stopka z danymi kontaktowymi

Format: kompletny HTML email z inline CSS. Kolory: #04389E (główny), #0B1220 (tekst), #F7F8FA (tło).
Zwróć TYLKO kod HTML."""
    
    response = await llm_chat(prompt, system_message="Jesteś ekspertem od email marketingu dla biur rachunkowych w Polsce. Tworzysz profesjonalne newslettery w HTML.", session_id=f"newsletter-{uuid.uuid4().hex[:8]}", timeout=120)
    html = response.strip()
    if html.startswith("```"):
        html = html.split("\n", 1)[1].rsplit("```", 1)[0]
    
    newsletter_id = str(uuid.uuid4())
    await db.newsletters.insert_one({
        "id": newsletter_id,
        "user_id": user["id"],
        "title": title,
        "html": html,
        "article_ids": [a["id"] for a in articles],
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"id": newsletter_id, "title": title, "html": html}

@router.get("/newsletter/list")
async def list_newsletters(user: dict = Depends(get_current_user)):
    """List generated newsletters."""
    docs = await db.newsletters.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).limit(20).to_list(20)
    return docs

@router.get("/newsletter/{newsletter_id}")
async def get_newsletter(newsletter_id: str, user: dict = Depends(get_current_user)):
    """Get a specific newsletter."""
    doc = await db.newsletters.find_one({"id": newsletter_id, "user_id": user["id"]}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Newsletter nie znaleziony")
    return doc


# --- Subscriptions & Payments ---

@router.get("/subscription/plans")
async def list_subscription_plans():
    """Return all available subscription plans."""
    return get_all_plans()

class SubscriptionCheckoutRequest(BaseModel):
    plan_id: str

@router.post("/subscription/checkout")
async def create_checkout(request: SubscriptionCheckoutRequest, user: dict = Depends(get_current_user)):
    """Create a tpay checkout session for the selected plan."""
    plan = get_plan(request.plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="Nieznany plan subskrypcji")
    
    # Get base URL for callbacks
    base_url = os.environ.get("APP_BASE_URL", os.environ.get("REACT_APP_BACKEND_URL", ""))
    callback_url = f"{base_url}/api/subscription/webhook"
    return_url = f"{base_url}/cennik"
    
    result = await create_tpay_transaction(
        plan_id=request.plan_id,
        user=user,
        callback_url=callback_url,
        return_url=return_url
    )
    
    if result.get("success"):
        # Save pending subscription
        sub_id = str(uuid.uuid4())
        sub_doc = {
            "id": sub_id,
            "user_id": user["id"],
            "plan_id": request.plan_id,
            "plan_name": plan["name"],
            "price_netto": plan["price_netto"],
            "price_brutto": plan["price_brutto"],
            "transaction_id": result.get("transaction_id"),
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.subscriptions.insert_one(sub_doc)
        
        return {
            "subscription_id": sub_id,
            "transaction_url": result.get("transaction_url"),
            "plan": plan
        }
    else:
        error_msg = result.get("error", "Blad tworzenia platnosci")
        if result.get("demo"):
            raise HTTPException(status_code=503, detail=error_msg)
        raise HTTPException(status_code=502, detail=error_msg)

@router.post("/subscription/webhook")
async def tpay_webhook(request_data: dict):
    """Handle tpay payment notification."""
    tx_id = request_data.get("tr_id") or request_data.get("transactionId")
    status = request_data.get("tr_status") or request_data.get("status")
    
    if not tx_id:
        raise HTTPException(status_code=400, detail="Missing transaction ID")
    
    # Find subscription
    sub = await db.subscriptions.find_one({"transaction_id": str(tx_id)})
    if not sub:
        logging.warning(f"Subscription not found for tx: {tx_id}")
        return {"status": "ok"}
    
    if status in ("TRUE", "paid", "correct"):
        # Payment confirmed
        end_date = calculate_subscription_end(sub["plan_id"])
        
        await db.subscriptions.update_one(
            {"id": sub["id"]},
            {"$set": {
                "status": "active",
                "paid_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": end_date.isoformat()
            }}
        )
        
        # Update user subscription status
        await db.users.update_one(
            {"id": sub["user_id"]},
            {"$set": {
                "subscription_plan": sub["plan_id"],
                "subscription_active": True,
                "subscription_expires": end_date.isoformat()
            }}
        )
        
        logging.info(f"Subscription activated: user={sub['user_id']}, plan={sub['plan_id']}")
    elif status in ("FALSE", "failed", "error"):
        await db.subscriptions.update_one(
            {"id": sub["id"]},
            {"$set": {"status": "failed"}}
        )
    
    return {"status": "ok"}

@router.get("/subscription/status")
async def get_subscription_status(user: dict = Depends(get_current_user)):
    """Get current user's subscription status."""
    # Check latest active subscription
    sub = await db.subscriptions.find_one(
        {"user_id": user["id"], "status": "active"},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    
    user_data = await db.users.find_one({"id": user["id"]}, {"_id": 0, "subscription_plan": 1, "subscription_active": 1, "subscription_expires": 1})
    
    return {
        "has_subscription": bool(sub),
        "plan": sub.get("plan_id") if sub else None,
        "plan_name": sub.get("plan_name") if sub else None,
        "expires_at": sub.get("expires_at") if sub else None,
        "status": sub.get("status") if sub else "none",
        "user_subscription": user_data
    }


# --- AI Article Suggestions (Smart) ---

class AIArticleSuggestionsRequest(BaseModel):
    count: int = 6
    focus: str = ""  # optional focus area

_ai_suggestions_jobs = {}

def _sync_run_ai_suggestions(job_id: str, existing_articles: list, focus: str, count: int, emergent_key: str, user_id: str):
    """Run AI article suggestions in thread."""
    import pymongo
    sync_client = pymongo.MongoClient(os.environ.get('MONGO_URL'), serverSelectionTimeoutMS=5000)
    sync_db = sync_client[os.environ.get('DB_NAME', 'seo_article_writer')]
    try:
        _ai_suggestions_jobs[job_id]["status"] = "running"
        from llm_helper import llm_chat_sync

        existing_titles = [a.get("title", "") for a in existing_articles[:20]]
        existing_keywords = list(set([a.get("primary_keyword", "") for a in existing_articles[:20] if a.get("primary_keyword")]))
        titles_str = "\n".join([f"- {t}" for t in existing_titles]) if existing_titles else "Brak artykułów"
        keywords_str = ", ".join(existing_keywords[:15]) if existing_keywords else "brak"
        focus_str = f"\nSkup się szczególnie na: {focus}" if focus else ""

        prompt = f"""Przeanalizuj istniejące artykuły na blogu biura rachunkowego i zaproponuj {count} NOWYCH tematów artykułów, które uzupełnią luki w treści i przyciągną ruch.

Istniejące artykuły:
{titles_str}

Użyte słowa kluczowe: {keywords_str}
{focus_str}

Dla każdej sugestii podaj:
- title: tytuł artykułu (przyciągający, SEO-friendly, po polsku)
- primary_keyword: główne słowo kluczowe (2-4 słowa)
- secondary_keywords: lista 3-5 dodatkowych słów kluczowych
- description: krótki opis artykułu (2-3 zdania)
- rationale: dlaczego warto napisać ten artykuł (uzupełnia lukę, sezonowość, trending, itp.)
- estimated_traffic: szacunkowy miesięczny ruch (np. "500-1000")
- difficulty: "łatwa", "średnia", "trudna"
- priority: "wysoki", "średni", "niski"
- content_type: "poradnik", "analiza", "case study", "lista", "aktualności"
- seasonal: true/false (czy temat jest sezonowy)

Odpowiedz TYLKO prawidłowym JSON: {{"suggestions": [...]}}"""

        text = llm_chat_sync(prompt, system_message="Jesteś ekspertem SEO i content strategistą dla polskiej branży księgowej i podatkowej. Odpowiadaj WYŁĄCZNIE poprawnym JSON-em.", session_id=f"ai-suggestions-{job_id[:8]}", timeout=120)
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]

        import json as json_mod
        data = json_mod.loads(text)

        _ai_suggestions_jobs[job_id]["status"] = "completed"
        _ai_suggestions_jobs[job_id]["result"] = data

        sync_db.ai_suggestions.insert_one({
            "id": job_id, "user_id": user_id,
            "result": data, "focus": focus,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logging.error(f"AI suggestions error: {e}")
        _ai_suggestions_jobs[job_id]["status"] = "failed"
        _ai_suggestions_jobs[job_id]["error"] = str(e)
    finally:
        sync_client.close()

@router.post("/articles/ai-suggestions")
async def ai_article_suggestions(request: AIArticleSuggestionsRequest, user: dict = Depends(get_current_user)):
    """Start async AI article suggestions based on existing content."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")

    query = {} if user.get("is_admin") else {"user_id": user["id"]}
    existing = await db.articles.find(query, {"_id": 0, "title": 1, "primary_keyword": 1, "seo_score": 1}).sort("created_at", -1).limit(20).to_list(20)

    job_id = str(uuid.uuid4())
    _ai_suggestions_jobs[job_id] = {"status": "queued", "result": None, "error": None}
    asyncio.get_event_loop().run_in_executor(None, _sync_run_ai_suggestions, job_id, existing, request.focus, request.count, emergent_key, user["id"])
    return {"job_id": job_id, "status": "queued"}

@router.get("/articles/ai-suggestions/status/{job_id}")
async def ai_suggestions_status(job_id: str, user: dict = Depends(get_current_user)):
    """Poll AI suggestions job status."""
    job = _ai_suggestions_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    result = {"job_id": job_id, "status": job["status"]}
    if job["status"] == "completed":
        result["result"] = job["result"]
        del _ai_suggestions_jobs[job_id]
    elif job["status"] == "failed":
        result["error"] = job["error"]
        del _ai_suggestions_jobs[job_id]
    return result

@router.get("/articles/ai-suggestions/history")
async def ai_suggestions_history(user: dict = Depends(get_current_user)):
    """Get AI suggestions history."""
    docs = await db.ai_suggestions.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).limit(10).to_list(10)
    return docs


# --- Performance Dashboard ---

@router.get("/performance/dashboard")
async def performance_dashboard(user: dict = Depends(get_current_user)):
    """Get comprehensive performance metrics."""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Dostęp tylko dla administratorów")

    now = datetime.now(timezone.utc)

    # Total users
    total_users = await db.users.count_documents({})

    # Active users in last 24h (DAU) - based on articles created/updated
    from datetime import timedelta
    day_ago = (now - timedelta(days=1)).isoformat()
    week_ago = (now - timedelta(days=7)).isoformat()
    month_ago = (now - timedelta(days=30)).isoformat()

    # DAU - unique users who created/updated articles in last 24h
    dau_pipeline = [
        {"$match": {"$or": [
            {"created_at": {"$gte": day_ago}},
            {"updated_at": {"$gte": day_ago}}
        ]}},
        {"$group": {"_id": "$user_id"}},
        {"$count": "count"}
    ]
    dau_result = await db.articles.aggregate(dau_pipeline).to_list(1)
    dau = dau_result[0]["count"] if dau_result else 0

    # MAU - unique users who created/updated articles in last 30 days
    mau_pipeline = [
        {"$match": {"$or": [
            {"created_at": {"$gte": month_ago}},
            {"updated_at": {"$gte": month_ago}}
        ]}},
        {"$group": {"_id": "$user_id"}},
        {"$count": "count"}
    ]
    mau_result = await db.articles.aggregate(mau_pipeline).to_list(1)
    mau = mau_result[0]["count"] if mau_result else 0

    # Total articles
    total_articles = await db.articles.count_documents({})

    # Articles created in last 7 days
    articles_this_week = await db.articles.count_documents({"created_at": {"$gte": week_ago}})

    # Articles created in last 30 days
    articles_this_month = await db.articles.count_documents({"created_at": {"$gte": month_ago}})

    # Average SEO score
    seo_pipeline = [
        {"$match": {"seo_score.percentage": {"$exists": True}}},
        {"$group": {"_id": None, "avg": {"$avg": "$seo_score.percentage"}, "max": {"$max": "$seo_score.percentage"}, "min": {"$min": "$seo_score.percentage"}}}
    ]
    seo_result = await db.articles.aggregate(seo_pipeline).to_list(1)
    avg_seo = round(seo_result[0]["avg"]) if seo_result else 0
    max_seo = round(seo_result[0]["max"]) if seo_result else 0
    min_seo = round(seo_result[0]["min"]) if seo_result else 0

    # Articles by SEO score range
    high_seo = await db.articles.count_documents({"seo_score.percentage": {"$gte": 80}})
    medium_seo = await db.articles.count_documents({"seo_score.percentage": {"$gte": 50, "$lt": 80}})
    low_seo = await db.articles.count_documents({"seo_score.percentage": {"$lt": 50, "$exists": True}})
    no_seo = await db.articles.count_documents({"$or": [{"seo_score": {"$exists": False}}, {"seo_score.percentage": {"$exists": False}}]})

    # Top 5 articles by SEO score
    top_articles = await db.articles.find(
        {"seo_score.percentage": {"$exists": True}},
        {"_id": 0, "id": 1, "title": 1, "seo_score": 1, "primary_keyword": 1, "created_at": 1}
    ).sort("seo_score.percentage", -1).limit(5).to_list(5)

    # Recent articles (last 5)
    recent_articles = await db.articles.find(
        {}, {"_id": 0, "id": 1, "title": 1, "seo_score": 1, "created_at": 1, "user_id": 1}
    ).sort("created_at", -1).limit(5).to_list(5)

    # Articles created per day (last 14 days)
    articles_per_day = []
    for i in range(13, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = (now - timedelta(days=i)).replace(hour=23, minute=59, second=59, microsecond=999999)
        count = await db.articles.count_documents({
            "created_at": {"$gte": day_start.isoformat(), "$lte": day_end.isoformat()}
        })
        articles_per_day.append({
            "date": day_start.strftime("%d.%m"),
            "count": count
        })

    # Total images generated
    total_images = await db.images.count_documents({})

    # Total newsletters
    total_newsletters = await db.newsletters.count_documents({})

    # WordPress published count
    wp_published = await db.articles.count_documents({"wordpress_published": True})

    # Active subscriptions
    active_subs = await db.subscriptions.count_documents({"status": "active"})

    return {
        "users": {
            "total": total_users,
            "dau": dau,
            "mau": mau,
        },
        "articles": {
            "total": total_articles,
            "this_week": articles_this_week,
            "this_month": articles_this_month,
            "per_day": articles_per_day,
        },
        "seo": {
            "average": avg_seo,
            "max": max_seo,
            "min": min_seo,
            "high": high_seo,
            "medium": medium_seo,
            "low": low_seo,
            "no_score": no_seo,
        },
        "top_articles": top_articles,
        "recent_articles": recent_articles,
        "content": {
            "images": total_images,
            "newsletters": total_newsletters,
            "wp_published": wp_published,
        },
        "subscriptions": {
            "active": active_subs,
        }
    }


# --- Plagiarism Checker ---

def _sync_run_plagiarism_check(job_id: str, article_data: dict, emergent_key: str, user_id: str):
    """Run plagiarism check in thread using AI analysis."""
    import pymongo
    sync_client = pymongo.MongoClient(os.environ.get('MONGO_URL'), serverSelectionTimeoutMS=5000)
    sync_db = sync_client[os.environ.get('DB_NAME', 'seo_article_writer')]
    try:
        _plagiarism_jobs[job_id]["status"] = "running"
        from llm_helper import llm_chat_sync

        # Extract text content from sections
        text_parts = []
        for section in article_data.get("sections", []):
            text_parts.append(section.get("heading", ""))
            content = section.get("content", "")
            clean = re.sub(r'<[^>]+>', '', content)
            text_parts.append(clean)
            for sub in section.get("subsections", []):
                text_parts.append(sub.get("heading", ""))
                sub_content = sub.get("content", "")
                clean_sub = re.sub(r'<[^>]+>', '', sub_content)
                text_parts.append(clean_sub)

        full_text = "\n".join(text_parts)
        # Limit to ~3000 words for analysis
        words = full_text.split()
        if len(words) > 3000:
            full_text = " ".join(words[:3000])

        prompt = f"""Przeanalizuj poniższy tekst artykułu pod kątem oryginalności i potencjalnego plagiatu.

Tytuł: {article_data.get("title", "")}
Słowo kluczowe: {article_data.get("primary_keyword", "")}

Tekst artykułu:
{full_text}

Wykonaj następujące analizy:
1. Sprawdź czy tekst wygląda na oryginalny czy skopiowany
2. Zidentyfikuj fragmenty które mogą być popularnymi frazami lub szablonami
3. Oceń unikalność stylu pisania
4. Sprawdź czy są fragmenty które brzmią jak typowe treści AI bez personalizacji
5. Oceń jakość i oryginalność treści

Odpowiedz TYLKO prawidłowym JSON:
{{
    "overall_score": 85,
    "verdict": "oryginalny" lub "podejrzany" lub "prawdopodobny plagiat",
    "summary": "Krótkie podsumowanie analizy (2-3 zdania)",
    "details": {{
        "originality": 85,
        "style_uniqueness": 80,
        "ai_detection_risk": 20,
        "template_phrases_detected": 10
    }},
    "flagged_sections": [
        {{
            "text": "Fragment tekstu...",
            "reason": "Powód oznaczenia",
            "risk_level": "niski" lub "średni" lub "wysoki"
        }}
    ],
    "recommendations": [
        "Sugestia poprawy 1",
        "Sugestia poprawy 2"
    ]
}}"""

        text_resp = llm_chat_sync(prompt, system_message="Jesteś ekspertem od analizy treści i wykrywania plagiatu. Analizujesz tekst pod kątem oryginalności. Odpowiadaj WYŁĄCZNIE poprawnym JSON-em.", session_id=f"plagiarism-{job_id[:8]}", timeout=120)
        text_resp = text_resp.strip()
        if text_resp.startswith("```"):
            text_resp = text_resp.split("\n", 1)[1].rsplit("```", 1)[0]

        import json as json_mod
        data = json_mod.loads(text_resp)

        _plagiarism_jobs[job_id]["status"] = "completed"
        _plagiarism_jobs[job_id]["result"] = data

        sync_db.plagiarism_checks.insert_one({
            "id": job_id,
            "user_id": user_id,
            "article_id": article_data.get("id", ""),
            "result": data,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logging.error(f"Plagiarism check error: {e}")
        _plagiarism_jobs[job_id]["status"] = "failed"
        _plagiarism_jobs[job_id]["error"] = str(e)
    finally:
        sync_client.close()

@router.post("/plagiarism/check")
async def check_plagiarism(request: PlagiarismCheckRequest, user: dict = Depends(get_current_user)):
    """Start async plagiarism check for an article."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")

    article = await db.articles.find_one({"id": request.article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Artykuł nie znaleziony")

    job_id = str(uuid.uuid4())
    _plagiarism_jobs[job_id] = {"status": "queued", "result": None, "error": None}
    asyncio.get_event_loop().run_in_executor(None, _sync_run_plagiarism_check, job_id, article, emergent_key, user["id"])
    return {"job_id": job_id, "status": "queued"}

@router.get("/plagiarism/status/{job_id}")
async def plagiarism_status(job_id: str, user: dict = Depends(get_current_user)):
    """Poll plagiarism check status."""
    job = _plagiarism_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    result = {"job_id": job_id, "status": job["status"]}
    if job["status"] == "completed":
        result["result"] = job["result"]
        del _plagiarism_jobs[job_id]
    elif job["status"] == "failed":
        result["error"] = job["error"]
        del _plagiarism_jobs[job_id]
    return result

@router.get("/plagiarism/history/{article_id}")
async def plagiarism_history(article_id: str, user: dict = Depends(get_current_user)):
    """Get plagiarism check history for an article."""
    docs = await db.plagiarism_checks.find(
        {"article_id": article_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    return docs


# --- User Activity Tracking ---

@router.post("/activity/track")
async def track_activity(user: dict = Depends(get_current_user)):
    """Track user activity for DAU/MAU calculations."""
    await db.user_activity.update_one(
        {"user_id": user["id"], "date": datetime.now(timezone.utc).strftime("%Y-%m-%d")},
        {"$set": {
            "user_id": user["id"],
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "last_active": datetime.now(timezone.utc).isoformat()
        }, "$inc": {"actions": 1}},
        upsert=True
    )
    return {"status": "ok"}


# --- Content Verification (Fact-Check) ---

def _sync_run_content_verification(job_id: str, article_data: dict, emergent_key: str, user_id: str):
    """Run content verification/fact-check in thread using AI analysis."""
    import pymongo
    sync_client = pymongo.MongoClient(os.environ.get('MONGO_URL'), serverSelectionTimeoutMS=5000)
    sync_db = sync_client[os.environ.get('DB_NAME', 'seo_article_writer')]
    try:
        _verification_jobs[job_id]["status"] = "running"
        from llm_helper import llm_chat_sync

        # Extract text content from sections
        text_parts = []
        for section in article_data.get("sections", []):
            text_parts.append(f"## {section.get('heading', '')}")
            content = section.get("content", "")
            clean = re.sub(r'<[^>]+>', ' ', content)
            text_parts.append(clean)
            for sub in section.get("subsections", []):
                text_parts.append(f"### {sub.get('heading', '')}")
                sub_content = sub.get("content", "")
                clean_sub = re.sub(r'<[^>]+>', ' ', sub_content)
                text_parts.append(clean_sub)

        full_text = "\n".join(text_parts)
        words = full_text.split()
        if len(words) > 3000:
            full_text = " ".join(words[:3000])

        sources_str = ""
        for s in article_data.get("sources", []):
            sources_str += f"- {s.get('name', '')}: {s.get('url', '')}\n"

        faq_str = ""
        for f in article_data.get("faq", []):
            faq_str += f"Q: {f.get('question','')}\nA: {f.get('answer','')[:150]}\n\n"

        chat_sys = "Jesteś doświadczonym BIEGŁYM REWIDENTEM i doradcą podatkowym w Polsce. Weryfikujesz treści pod kątem zgodności z obowiązującym prawem podatkowym i księgowym (stan na 2026 r.). Odpowiadaj WYŁĄCZNIE poprawnym JSON-em."

        prompt = f"""Zweryfikuj poniższy artykuł blogowy z zakresu księgowości/podatków pod kątem RZETELNOŚCI MERYTORYCZNEJ.

Tytuł: {article_data.get("title", "")}
Słowo kluczowe: {article_data.get("primary_keyword", "")}

Treść artykułu:
{full_text}

Źródła podane w artykule:
{sources_str or "Brak źródeł"}

FAQ:
{faq_str or "Brak FAQ"}

SPRAWDŹ:
1. Czy cytowane przepisy prawne istnieją i są aktualne (art., ust., Dz.U.)?
2. Czy podane kwoty, stawki, terminy są prawidłowe (stan na 2026 r.)?
3. Czy twierdzenia są zgodne z obowiązującym prawem?
4. Czy źródła są wiarygodne i prowadzą do oficjalnych instytucji?
5. Czy FAQ zawiera poprawne informacje?
6. Czy brakuje istotnych zastrzeżeń prawnych (disclaimerów)?
7. Czy artykuł mógłby wprowadzić czytelnika w błąd?

Odpowiedz TYLKO prawidłowym JSON:
{{
    "overall_reliability_score": 85,
    "verdict": "rzetelny" lub "wymaga poprawek" lub "nierzetelny",
    "summary": "Krótkie podsumowanie weryfikacji (2-3 zdania)",
    "legal_accuracy": {{
        "score": 80,
        "verified_references": [
            {{
                "reference": "art. X ust. Y ustawy o ...",
                "status": "poprawny" lub "nieaktualny" lub "błędny" lub "nie do zweryfikowania",
                "note": "Komentarz"
            }}
        ]
    }},
    "factual_accuracy": {{
        "score": 85,
        "verified_facts": [
            {{
                "claim": "Twierdzenie z artykułu",
                "status": "poprawne" lub "nieprecyzyjne" lub "błędne" lub "nieaktualne",
                "correction": "Poprawna informacja (jeśli błędne)",
                "source": "Źródło poprawnej informacji"
            }}
        ]
    }},
    "completeness": {{
        "score": 75,
        "missing_info": [
            "Brakująca istotna informacja 1",
            "Brakująca istotna informacja 2"
        ],
        "missing_disclaimers": [
            "Brakujące zastrzeżenie prawne"
        ]
    }},
    "sources_quality": {{
        "score": 80,
        "assessment": "Ocena jakości źródeł",
        "missing_sources": ["Sugestia brakującego źródła"]
    }},
    "recommendations": [
        {{
            "priority": "wysoki" lub "średni" lub "niski",
            "area": "przepisy" lub "kwoty" lub "terminy" lub "źródła" lub "disclaimery" lub "kompletność",
            "description": "Konkretna rekomendacja poprawy",
            "suggested_text": "Proponowany tekst do wstawienia (jeśli dotyczy)"
        }}
    ]
}}"""

        text_resp = llm_chat_sync(prompt, system_message=chat_sys, session_id=f"verify-{job_id[:8]}", timeout=120)
        text_resp = text_resp.strip()
        if text_resp.startswith("```"):
            text_resp = text_resp.split("\n", 1)[1].rsplit("```", 1)[0]

        import json as json_mod
        data = json_mod.loads(text_resp)

        _verification_jobs[job_id]["status"] = "completed"
        _verification_jobs[job_id]["result"] = data

        sync_db.content_verifications.insert_one({
            "id": job_id,
            "user_id": user_id,
            "article_id": article_data.get("id", ""),
            "result": data,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logging.error(f"Content verification error: {e}")
        _verification_jobs[job_id]["status"] = "failed"
        _verification_jobs[job_id]["error"] = str(e)
    finally:
        sync_client.close()

@router.post("/verify/check")
async def verify_content(request: ContentVerifyRequest, user: dict = Depends(get_current_user)):
    """Start async content verification for an article."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")

    article = await db.articles.find_one({"id": request.article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Artykuł nie znaleziony")

    job_id = str(uuid.uuid4())
    _verification_jobs[job_id] = {"status": "queued", "result": None, "error": None}
    asyncio.get_event_loop().run_in_executor(None, _sync_run_content_verification, job_id, article, emergent_key, user["id"])
    return {"job_id": job_id, "status": "queued"}

@router.get("/verify/status/{job_id}")
async def verification_status(job_id: str, user: dict = Depends(get_current_user)):
    """Poll content verification status."""
    job = _verification_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    result = {"job_id": job_id, "status": job["status"]}
    if job["status"] == "completed":
        result["result"] = job["result"]
        del _verification_jobs[job_id]
    elif job["status"] == "failed":
        result["error"] = job["error"]
        del _verification_jobs[job_id]
    return result

@router.get("/verify/history/{article_id}")
async def verification_history(article_id: str, user: dict = Depends(get_current_user)):
    """Get verification history for an article."""
    docs = await db.content_verifications.find(
        {"article_id": article_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    return docs


# --- Auto Competition Analysis (Top Google Results) ---

def _sync_run_auto_competition(job_id: str, article_data: dict, emergent_key: str, user_id: str):
    """Scrape top search results for keyword, extract content, compare with article via AI."""
    import pymongo
    import httpx as httpx_sync
    from bs4 import BeautifulSoup
    sync_client = pymongo.MongoClient(os.environ.get('MONGO_URL'), serverSelectionTimeoutMS=5000)
    sync_db = sync_client[os.environ.get('DB_NAME', 'seo_article_writer')]
    try:
        _auto_competition_jobs[job_id]["status"] = "running"

        keyword = article_data.get("primary_keyword", "")
        my_title = article_data.get("title", "")
        my_sections = [s.get("heading", "") for s in article_data.get("sections", [])]
        my_word_count = 0
        my_text = ""
        for section in article_data.get("sections", []):
            text = re.sub(r'<[^>]+>', ' ', section.get("content", ""))
            my_text += " " + text
            for sub in section.get("subsections", []):
                my_text += " " + re.sub(r'<[^>]+>', ' ', sub.get("content", ""))
        my_word_count = len(my_text.split())

        # Scrape search results using DuckDuckGo HTML (no API key needed)
        search_url = f"https://html.duckduckgo.com/html/?q={keyword.replace(' ', '+')}+poradnik+polska"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

        competitors = []
        try:
            import httpx
            with httpx.Client(timeout=20.0, follow_redirects=True, verify=False) as client:
                resp = client.get(search_url, headers=headers)
                soup = BeautifulSoup(resp.text, "html.parser")
                results = soup.select(".result__a")
                urls = []
                from urllib.parse import unquote, urlparse, parse_qs
                for r in results[:8]:
                    href = r.get("href", "")
                    if not href:
                        continue
                    # Extract actual URL from DDG redirect first
                    if "uddg=" in href:
                        try:
                            parsed = parse_qs(urlparse(href).query)
                            href = unquote(parsed.get("uddg", [href])[0])
                        except Exception:
                            continue
                    # Skip DDG internal and ad URLs
                    if "duckduckgo" in href or not href.startswith("http"):
                        continue
                    urls.append(href)
                urls = urls[:5]

                # Scrape each competitor
                for url in urls:
                    try:
                        page = client.get(url, headers=headers, timeout=10.0)
                        page_soup = BeautifulSoup(page.text, "html.parser")
                        page_title = page_soup.find("title")
                        page_title_text = page_title.get_text(strip=True) if page_title else ""
                        meta_desc = ""
                        md = page_soup.find("meta", attrs={"name": "description"})
                        if md:
                            meta_desc = md.get("content", "")
                        headings = []
                        for tag in ["h1", "h2", "h3"]:
                            for h in page_soup.find_all(tag)[:10]:
                                headings.append(f"{tag.upper()}: {h.get_text(strip=True)}")
                        for tag in page_soup(["script", "style", "nav", "footer", "header", "aside"]):
                            tag.decompose()
                        article_el = page_soup.find("article") or page_soup.find("main") or page_soup.find("body")
                        content = article_el.get_text(separator=" ", strip=True)[:2000] if article_el else ""
                        competitors.append({
                            "url": url,
                            "title": page_title_text[:200],
                            "meta_desc": meta_desc[:300],
                            "headings": headings[:12],
                            "word_count": len(content.split()),
                            "content_sample": content[:1500]
                        })
                    except Exception:
                        continue
        except Exception as e:
            logging.warning(f"Search scraping failed: {e}")

        # AI analysis
        from llm_helper import llm_chat_sync

        comp_str = ""
        for i, c in enumerate(competitors[:5], 1):
            comp_str += f"\n--- KONKURENT {i} ---\n"
            comp_str += f"URL: {c['url']}\nTytuł: {c['title']}\n"
            comp_str += f"Meta opis: {c['meta_desc']}\n"
            comp_str += f"Nagłówki: {'; '.join(c['headings'][:8])}\n"
            comp_str += f"Słów: ~{c['word_count']}\n"
            comp_str += f"Fragment: {c['content_sample'][:600]}\n"

        prompt = f"""Przeanalizuj mój artykuł w porównaniu z TOP wynikami wyszukiwania dla słowa kluczowego: "{keyword}"

MÓJ ARTYKUŁ:
Tytuł: {my_title}
Sekcje: {', '.join(my_sections)}
Słów: ~{my_word_count}
Meta opis: {article_data.get('meta_description', '')}

WYNIKI KONKURENCJI:
{comp_str if comp_str else 'Nie udało się pobrać wyników konkurencji - analizuj sam artykuł.'}

Odpowiedz TYLKO prawidłowym JSON:
{{
    "competitors_found": {len(competitors)},
    "overall_position": "silniejszy" lub "porównywalny" lub "słabszy",
    "content_gaps": [
        {{
            "topic": "Temat/aspekt którego brakuje w moim artykule",
            "found_in": "URL lub 'wielu konkurentów'",
            "importance": "wysoka" lub "średnia" lub "niska",
            "suggestion": "Konkretna sugestia co dodać (1-2 zdania)",
            "suggested_heading": "Proponowany nagłówek H2/H3 do dodania"
        }}
    ],
    "keyword_opportunities": [
        {{
            "keyword": "Słowo kluczowe używane przez konkurencję",
            "frequency": "jak często występuje u konkurencji",
            "my_usage": "czy występuje w moim artykule",
            "action": "Dodaj/Wzmocnij/Ignoruj"
        }}
    ],
    "structural_comparison": {{
        "my_sections": {len(my_sections)},
        "avg_competitor_sections": 0,
        "my_word_count": {my_word_count},
        "avg_competitor_word_count": 0,
        "recommendation": "Co zmienić w strukturze"
    }},
    "strengths": ["Mocne strony mojego artykułu vs konkurencja"],
    "weaknesses": ["Słabe strony wymagające poprawy"],
    "action_plan": [
        {{
            "priority": 1,
            "action": "Konkretne działanie do podjęcia",
            "expected_impact": "wysoki" lub "średni" lub "niski"
        }}
    ],
    "summary": "Podsumowanie analizy (2-3 zdania)"
}}"""

        text_resp = llm_chat_sync(prompt, system_message="Jesteś ekspertem SEO. Analizujesz artykuły konkurencji i wskazujesz luki w treści. Odpowiadaj WYŁĄCZNIE poprawnym JSON-em.", session_id=f"auto-comp-{job_id[:8]}", timeout=120)
        text_resp = text_resp.strip()
        if text_resp.startswith("```"):
            text_resp = text_resp.split("\n", 1)[1].rsplit("```", 1)[0]

        import json as json_mod
        data = json_mod.loads(text_resp)
        data["competitors_scraped"] = [{"url": c["url"], "title": c["title"], "word_count": c["word_count"]} for c in competitors]

        _auto_competition_jobs[job_id]["status"] = "completed"
        _auto_competition_jobs[job_id]["result"] = data
    except Exception as e:
        logging.error(f"Auto competition error: {e}")
        _auto_competition_jobs[job_id]["status"] = "failed"
        _auto_competition_jobs[job_id]["error"] = str(e)
    finally:
        sync_client.close()

@router.post("/competition/auto-analyze")
async def auto_competition_analysis(request: AutoCompetitionRequest, user: dict = Depends(get_current_user)):
    """Start auto competition analysis - scrapes top results for keyword."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    article = await db.articles.find_one({"id": request.article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Artykuł nie znaleziony")
    job_id = str(uuid.uuid4())
    _auto_competition_jobs[job_id] = {"status": "queued", "result": None, "error": None}
    asyncio.get_event_loop().run_in_executor(None, _sync_run_auto_competition, job_id, article, emergent_key, user["id"])
    return {"job_id": job_id, "status": "queued"}

@router.get("/competition/auto-status/{job_id}")
async def auto_competition_status(job_id: str, user: dict = Depends(get_current_user)):
    """Poll auto competition analysis status."""
    job = _auto_competition_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    result = {"job_id": job_id, "status": job["status"]}
    if job["status"] == "completed":
        result["result"] = job["result"]
        del _auto_competition_jobs[job_id]
    elif job["status"] == "failed":
        result["error"] = job["error"]
        del _auto_competition_jobs[job_id]
    return result


# --- A/B Title Testing ---

def _sync_run_ab_title_test(job_id: str, article_data: dict, custom_variants: list, emergent_key: str):
    """Generate and evaluate title variants using AI."""
    try:
        _ab_title_jobs[job_id]["status"] = "running"
        from llm_helper import llm_chat_sync

        current_title = article_data.get("title", "")
        keyword = article_data.get("primary_keyword", "")
        topic = article_data.get("topic", "")
        meta_desc = article_data.get("meta_description", "")

        custom_str = ""
        if custom_variants:
            custom_str = "\n\nDODATKOWE WARIANTY OD UŻYTKOWNIKA (też oceń):\n" + "\n".join([f"- {v}" for v in custom_variants])

        prompt = f"""Przeanalizuj obecny tytuł artykułu i zaproponuj 5 alternatywnych wariantów. Oceń każdy wariant.

OBECNY TYTUŁ: "{current_title}"
SŁOWO KLUCZOWE: "{keyword}"
TEMAT: "{topic}"
META OPIS: "{meta_desc}"
{custom_str}

Dla każdego wariantu (włącznie z obecnym) oceń:
1. CTR Potential (0-100) - jak bardzo tytuł zachęca do kliknięcia
2. SEO Score (0-100) - optymalizacja pod wyszukiwarki (keyword placement, length)
3. Emotional Appeal (0-100) - siła emocjonalna, ciekawość, urgency
4. Clarity (0-100) - jasność przekazu, zrozumiałość

Odpowiedz TYLKO prawidłowym JSON:
{{
    "current_title": {{
        "text": "{current_title}",
        "scores": {{
            "ctr": 70,
            "seo": 80,
            "emotion": 60,
            "clarity": 85
        }},
        "total": 74,
        "feedback": "Krótka ocena obecnego tytułu"
    }},
    "variants": [
        {{
            "text": "Nowy wariant tytułu",
            "strategy": "power_words" lub "question" lub "numbers" lub "how_to" lub "list" lub "urgency",
            "scores": {{
                "ctr": 85,
                "seo": 90,
                "emotion": 75,
                "clarity": 88
            }},
            "total": 85,
            "feedback": "Dlaczego ten wariant jest lepszy/gorszy",
            "changes_made": "Co zostało zmienione i dlaczego"
        }}
    ],
    "winner": {{
        "text": "Najlepszy wariant",
        "total": 92,
        "reason": "Dlaczego ten wariant jest najlepszy"
    }},
    "tips": [
        "Ogólna porada dotycząca tytułów w tej branży"
    ]
}}"""

        text_resp = llm_chat_sync(prompt, system_message="Jesteś ekspertem od copywritingu SEO i CTR. Generujesz i oceniasz warianty tytułów artykułów. Odpowiadaj WYŁĄCZNIE poprawnym JSON-em.", session_id=f"ab-title-{job_id[:8]}", timeout=120)
        text_resp = text_resp.strip()
        if text_resp.startswith("```"):
            text_resp = text_resp.split("\n", 1)[1].rsplit("```", 1)[0]

        import json as json_mod
        data = json_mod.loads(text_resp)

        _ab_title_jobs[job_id]["status"] = "completed"
        _ab_title_jobs[job_id]["result"] = data
    except Exception as e:
        logging.error(f"A/B title test error: {e}")
        _ab_title_jobs[job_id]["status"] = "failed"
        _ab_title_jobs[job_id]["error"] = str(e)

@router.post("/articles/ab-title-test")
async def ab_title_test(request: ABTitleRequest, user: dict = Depends(get_current_user)):
    """Start A/B title test for an article."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    article = await db.articles.find_one({"id": request.article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Artykuł nie znaleziony")
    job_id = str(uuid.uuid4())
    _ab_title_jobs[job_id] = {"status": "queued", "result": None, "error": None}
    asyncio.get_event_loop().run_in_executor(None, _sync_run_ab_title_test, job_id, article, request.custom_variants, emergent_key)
    return {"job_id": job_id, "status": "queued"}

@router.get("/articles/ab-title-status/{job_id}")
async def ab_title_status(job_id: str, user: dict = Depends(get_current_user)):
    """Poll A/B title test status."""
    job = _ab_title_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    result = {"job_id": job_id, "status": job["status"]}
    if job["status"] == "completed":
        result["result"] = job["result"]
        del _ab_title_jobs[job_id]
    elif job["status"] == "failed":
        result["error"] = job["error"]
        del _ab_title_jobs[job_id]
    return result


