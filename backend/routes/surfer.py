"""SurferSEO routes: SERP analysis, scoring, keyword research, URL audit, content planner."""
import os, logging, asyncio
from fastapi import APIRouter, Depends
from shared import (
    db, get_current_user, executor, client, HTTPException, uuid, datetime, timezone, json, re,
    ScoreRequest
)
from surfer_seo_service import analyze_serp, compute_surfer_score

router = APIRouter()

# In-memory job store for async SERP analysis
_surfer_jobs = {}

# --- SEO Scoring ---

@router.post("/surfer/analyze-serp")
async def surfer_analyze_serp(request: dict, user: dict = Depends(get_current_user)):
    """Analyze SERP for a keyword — SurferSEO style."""
    keyword = request.get("keyword", "")
    if not keyword:
        raise HTTPException(status_code=400, detail="Keyword is required")
    try:
        serp_data = await analyze_serp(keyword)
        return serp_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/surfer/score")
async def surfer_score_article(request: dict, user: dict = Depends(get_current_user)):
    """Compute SurferSEO-style score for an article against SERP data."""
    article_id = request.get("article_id")
    surfer_data = request.get("surfer_data")
    if not article_id or not surfer_data:
        raise HTTPException(status_code=400, detail="article_id and surfer_data required")
    
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    score = compute_surfer_score(article, surfer_data)
    
    # Save surfer score and data to article
    await db.articles.update_one(
        {"id": article_id},
        {"$set": {
            "surfer_data": surfer_data,
            "surfer_score": score,
            "seo_score": {"percentage": score["percentage"], "breakdown": score["metrics"], "total_score": score["total_score"], "total_max": score["total_max"]},
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return score


@router.post("/surfer/analyze-serp/async")
async def surfer_analyze_serp_async(request: dict, user: dict = Depends(get_current_user)):
    """Start async SERP analysis job."""
    keyword = request.get("keyword", "")
    if not keyword:
        raise HTTPException(status_code=400, detail="Keyword is required")
    
    job_id = str(uuid.uuid4())
    _surfer_jobs[job_id] = {"status": "running", "keyword": keyword}
    
    def _run(jid, kw):
        try:
            from llm_helper import llm_chat_sync
            import json as jmod
            prompt = f"""Jesteś ekspertem SEO. Symuluj analizę TOP 10 wyników Google dla frazy: "{kw}" (język: pl).

Wygeneruj realistyczne dane benchmarkowe. Odpowiedz WYŁĄCZNIE JSON:

{{
    "keyword": "{kw}",
    "search_intent": "informacyjny",
    "difficulty": 45,
    "monthly_volume": 2400,
    "benchmarks": {{
        "word_count": {{"min": 1200, "max": 3500, "avg": 2200, "recommended": 2500}},
        "headings": {{"h2_min": 5, "h2_max": 12, "h2_avg": 8, "h3_min": 4, "h3_max": 15, "h3_avg": 9}},
        "paragraphs": {{"min": 15, "max": 40, "avg": 25}},
        "images": {{"min": 2, "max": 8, "avg": 4}},
        "lists": {{"min": 2, "max": 6, "avg": 3}},
        "links_internal": {{"min": 3, "max": 10, "avg": 5}},
        "links_external": {{"min": 2, "max": 8, "avg": 4}},
        "bold_phrases": {{"min": 5, "max": 20, "avg": 10}},
        "avg_sentence_length": {{"min": 12, "max": 22, "avg": 16}},
        "faq_questions": {{"min": 3, "max": 8, "avg": 5}}
    }},
    "nlp_terms": [
        {{"term": "termin powiązany", "importance": "wysoka", "recommended_count": 3, "category": "główny"}}
    ],
    "top_competitors": [
        {{"position": 1, "title": "Tytuł artykułu", "url": "https://example.pl", "word_count": 2500, "h2_count": 8, "score_estimate": 85}}
    ],
    "content_outline_suggestion": ["H2: Nagłówek 1"],
    "questions_to_answer": ["Pytanie 1?"]
}}

WAŻNE: Wygeneruj 20-30 NLP terms z importance wysoka/średnia/niska, 5-8 konkurentów, 8-12 sugestii nagłówków, 5-8 pytań."""
            
            text = llm_chat_sync(prompt, system_message="Jesteś zaawansowanym narzędziem SEO. Odpowiadaj WYŁĄCZNIE poprawnym JSON-em.", session_id=f"surfer-{jid[:8]}", timeout=180)
            clean = text.strip()
            if clean.startswith("```"):
                clean = re.sub(r'^```(?:json)?\s*', '', clean)
                clean = re.sub(r'\s*```$', '', clean)
            data = jmod.loads(clean)
            _surfer_jobs[jid]["status"] = "completed"
            _surfer_jobs[jid]["result"] = data
        except Exception as e:
            logging.error(f"Surfer SERP error: {e}")
            _surfer_jobs[jid]["status"] = "failed"
            _surfer_jobs[jid]["error"] = str(e)
    
    executor.submit(_run, job_id, keyword)
    return {"job_id": job_id, "status": "running"}


@router.get("/surfer/analyze-serp/status/{job_id}")
async def surfer_serp_status(job_id: str, user: dict = Depends(get_current_user)):
    """Check SERP analysis job status."""
    job = _surfer_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, **job}


@router.post("/surfer/keyword-research")
async def surfer_keyword_research(request: dict, user: dict = Depends(get_current_user)):
    """AI-powered keyword research."""
    seed = request.get("seed_keyword", "")
    if not seed:
        raise HTTPException(status_code=400, detail="seed_keyword required")
    from llm_helper import llm_chat
    prompt = f"""Przeprowadź badanie słów kluczowych dla frazy: "{seed}" (rynek polski, branża księgowość/podatki).

Odpowiedz WYŁĄCZNIE JSON:
{{
    "main_keyword": {{
        "keyword": "{seed}",
        "monthly_volume": 2400,
        "difficulty": 45,
        "cpc_pln": 3.50,
        "search_intent": "informacyjny",
        "trend": "rosnący"
    }},
    "keywords": [
        {{
            "keyword": "powiązane słowo",
            "monthly_volume": 1200,
            "difficulty": 35,
            "cpc_pln": 2.80,
            "trend": "rosnący",
            "relevance": 0.9,
            "long_tail": false
        }}
    ]
}}

Wygeneruj 15-25 powiązanych słów kluczowych. Uwzględnij:
- Synonimy i warianty
- Long-tail keywords (3-5 słów)
- Pytania (jak, co, gdzie, kiedy)
- Powiązane tematy podatkowe/księgowe
Dane powinny być realistyczne dla polskiego rynku."""

    try:
        response = await llm_chat(prompt, system_message="Jesteś ekspertem SEO specjalizującym się w keyword research dla polskiego rynku. Odpowiadaj WYŁĄCZNIE JSON.", session_id=f"kw-research-{hash(seed)%100000}", timeout=120)
        clean = response.strip()
        if clean.startswith("```"):
            clean = re.sub(r'^```(?:json)?\s*', '', clean)
            clean = re.sub(r'\s*```$', '', clean)
        return json.loads(clean)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/surfer/content-planner")
async def surfer_content_planner(request: dict, user: dict = Depends(get_current_user)):
    """Cluster keywords into content topics/articles."""
    keywords = request.get("keywords", [])
    if not keywords:
        raise HTTPException(status_code=400, detail="keywords list required")
    from llm_helper import llm_chat
    kw_str = ", ".join(keywords[:30])
    prompt = f"""Pogrupuj poniższe słowa kluczowe w klastry tematyczne i zaproponuj artykuły do napisania.

Słowa kluczowe: {kw_str}

Odpowiedz WYŁĄCZNIE JSON:
{{
    "clusters": [
        {{
            "topic": "Temat artykułu",
            "primary_keyword": "główne słowo kluczowe",
            "keywords": ["słowo1", "słowo2"],
            "article_type": "poradnik" lub "listicle" lub "case study",
            "estimated_traffic": 1500,
            "priority": "wysoki" lub "średni" lub "niski"
        }}
    ]
}}

Utwórz 4-8 klastrów. Każdy klaster = 1 artykuł. Sortuj wg priorytetu."""

    try:
        response = await llm_chat(prompt, system_message="Jesteś content strategistą SEO. Klastrujesz słowa kluczowe w tematy artykułów. Odpowiadaj WYŁĄCZNIE JSON.", session_id=f"planner-{hash(kw_str)%100000}", timeout=120)
        clean = response.strip()
        if clean.startswith("```"):
            clean = re.sub(r'^```(?:json)?\s*', '', clean)
            clean = re.sub(r'\s*```$', '', clean)
        return json.loads(clean)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/surfer/audit-url")
async def surfer_audit_url(request: dict, user: dict = Depends(get_current_user)):
    """Audit an existing URL for SEO improvements."""
    url = request.get("url", "")
    if not url:
        raise HTTPException(status_code=400, detail="url required")
    
    # Scrape the URL first
    page_content = ""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            page_content = resp.text[:8000]
    except Exception as e:
        page_content = f"Nie udało się pobrać strony: {e}"

    from llm_helper import llm_chat
    prompt = f"""Przeprowadź audyt SEO strony: {url}

Fragment HTML strony:
{page_content[:5000]}

Odpowiedz WYŁĄCZNIE JSON:
{{
    "url": "{url}",
    "overall_score": 65,
    "title": "Tytuł strony",
    "meta_description": "Opis meta",
    "issues": [
        {{
            "category": "title" lub "meta" lub "headings" lub "content" lub "images" lub "links" lub "performance" lub "technical",
            "severity": "krytyczny" lub "wysoki" lub "średni" lub "niski",
            "issue": "Opis problemu",
            "recommendation": "Jak to naprawić",
            "impact": "Wpływ na SEO"
        }}
    ],
    "opportunities": [
        {{
            "title": "Szansa na poprawę",
            "description": "Opis",
            "estimated_impact": "wysoki"
        }}
    ],
    "content_analysis": {{
        "word_count": 1500,
        "h1_count": 1,
        "h2_count": 5,
        "h3_count": 3,
        "image_count": 3,
        "internal_links": 5,
        "external_links": 2
    }}
}}

Zidentyfikuj 8-15 problemów SEO i 3-5 szans na poprawę."""

    try:
        response = await llm_chat(prompt, system_message="Jesteś ekspertem SEO przeprowadzającym audyt stron internetowych. Odpowiadaj WYŁĄCZNIE JSON.", session_id=f"audit-{hash(url)%100000}", timeout=120)
        clean = response.strip()
        if clean.startswith("```"):
            clean = re.sub(r'^```(?:json)?\s*', '', clean)
            clean = re.sub(r'\s*```$', '', clean)
        return json.loads(clean)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/articles/{article_id}/score")
async def score_article(article_id: str, request: ScoreRequest):
    """Compute SEO score for an article."""
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    score = compute_seo_score(article, request.primary_keyword, request.secondary_keywords)
    
    # Update score in DB
    await db.articles.update_one(
        {"id": article_id},
        {"$set": {"seo_score": score, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return score


