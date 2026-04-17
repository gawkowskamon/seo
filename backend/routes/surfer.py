"""SurferSEO routes: SERP analysis, scoring, keyword research, URL audit, content planner."""
import os, logging, asyncio
from fastapi import APIRouter, Depends
from shared import (
    db, get_current_user, executor, client, HTTPException, uuid, datetime, timezone, json, re,
    ScoreRequest
)
from surfer_seo_service import analyze_serp, compute_surfer_score
from seo_scorer import compute_seo_score

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




# In-memory job store for auto-optimize
_optimize_jobs = {}


@router.post("/surfer/seo-report/{article_id}")
async def generate_seo_report(article_id: str, user: dict = Depends(get_current_user)):
    """Generate a PDF SEO report for an article."""
    from fastapi.responses import Response
    from fpdf import FPDF

    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    surfer_score = article.get("surfer_score", {})
    surfer_data = article.get("surfer_data", {})
    meta_title = article.get("meta_title", "")
    meta_desc = article.get("meta_description", "")
    keyword = article.get("primary_keyword", "")
    title = article.get("title", "Bez tytulu")
    sections = article.get("sections", [])
    faq = article.get("faq", [])
    sources = article.get("sources", [])
    pct = surfer_score.get("percentage", 0)
    metrics = surfer_score.get("metrics", {})

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Use built-in fonts — Helvetica for body, Courier for data
    # Title
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(4, 56, 158)
    pdf.cell(0, 14, "Raport SEO", ln=True, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, title.encode('latin-1', 'replace').decode('latin-1'), ln=True, align="C")
    pdf.cell(0, 6, f"Wygenerowano: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC", ln=True, align="C")
    pdf.ln(6)

    # Separator
    pdf.set_draw_color(4, 56, 158)
    pdf.set_line_width(0.5)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(8)

    # Score box
    pdf.set_font("Helvetica", "B", 16)
    color = (34, 197, 94) if pct >= 80 else (245, 158, 11) if pct >= 60 else (239, 68, 68)
    pdf.set_text_color(*color)
    label = "Doskonaly" if pct >= 80 else "Dobry" if pct >= 60 else "Do poprawy" if pct >= 40 else "Slaby"
    pdf.cell(0, 10, f"Wynik SurferSEO: {pct}% - {label}", ln=True, align="C")
    pdf.ln(4)

    # SERP info
    if surfer_data:
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 100, 100)
        intent = surfer_data.get("search_intent", "")
        diff = surfer_data.get("difficulty", "")
        vol = surfer_data.get("monthly_volume", "")
        pdf.cell(0, 5, f"Intencja: {intent}   |   Trudnosc: {diff}/100   |   Wolumen: {vol}/mies", ln=True, align="C")
        pdf.ln(4)

    # Metrics table
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(4, 56, 158)
    pdf.cell(0, 9, "Metryki tresci", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(240, 244, 255)
    pdf.set_text_color(4, 56, 158)
    pdf.cell(80, 7, "Metryka", border=1, fill=True)
    pdf.cell(30, 7, "Wynik", border=1, fill=True, align="C")
    pdf.cell(30, 7, "Cel", border=1, fill=True, align="C")
    pdf.cell(30, 7, "Status", border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(40, 40, 40)
    for key, m in metrics.items():
        if key == "nlp_terms":
            continue
        lbl = m.get("label", key).encode('latin-1', 'replace').decode('latin-1')
        sc = m.get("score", 0)
        mx = m.get("max", 5)
        status = "OK" if sc >= mx * 0.8 else "Poprawa" if sc >= mx * 0.5 else "Slaby"
        s_color = (34, 197, 94) if status == "OK" else (245, 158, 11) if status == "Poprawa" else (239, 68, 68)
        pdf.cell(80, 6, lbl, border=1)
        pdf.cell(30, 6, str(sc), border=1, align="C")
        pdf.cell(30, 6, str(mx), border=1, align="C")
        pdf.set_text_color(*s_color)
        pdf.cell(30, 6, status, border=1, align="C")
        pdf.set_text_color(40, 40, 40)
        pdf.ln()
    pdf.ln(6)

    # Google SERP preview
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(4, 56, 158)
    pdf.cell(0, 9, "Podglad w Google", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(26, 13, 171)
    pdf.multi_cell(0, 6, meta_title.encode('latin-1', 'replace').decode('latin-1') or "Brak meta tytulu")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(0, 102, 33)
    pdf.cell(0, 5, f"twoja-strona.pl > {article.get('slug', 'artykul')}", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(84, 84, 84)
    pdf.multi_cell(0, 5, meta_desc.encode('latin-1', 'replace').decode('latin-1') or "Brak meta opisu")
    pdf.ln(4)

    # Meta fields
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(4, 56, 158)
    pdf.cell(0, 9, "Meta dane", ln=True)
    pdf.ln(2)

    for lbl_name, val, mx_len in [("Meta tytul", meta_title, 60), ("Meta opis", meta_desc, 160), ("Slowo kluczowe", keyword, None)]:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(80, 80, 80)
        count_str = f"  ({len(val)}/{mx_len})" if mx_len else ""
        pdf.cell(0, 6, f"{lbl_name}{count_str}", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(40, 40, 40)
        pdf.multi_cell(0, 5, val.encode('latin-1', 'replace').decode('latin-1') or "Brak")
        pdf.ln(2)
    pdf.ln(4)

    # Readiness checklist
    checks = [
        (len(meta_title) > 0 and len(meta_title) <= 60, "Meta tytul (max 60 znakow)"),
        (len(meta_desc) >= 120 and len(meta_desc) <= 160, "Meta opis (120-160 znakow)"),
        (len(keyword) > 0, "Slowo kluczowe ustawione"),
        (len(sections) >= 3, f"Min. 3 sekcje tresci ({len(sections)})"),
        (len(faq) >= 3, f"Min. 3 pytania FAQ ({len(faq)})"),
        (len(sources) >= 1, f"Zrodla podlinkowane ({len(sources)})"),
    ]
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(4, 56, 158)
    passed = sum(1 for c in checks if c[0])
    pdf.cell(0, 9, f"Gotowosci SEO ({passed}/{len(checks)})", ln=True)
    pdf.ln(2)

    for ok, label_str in checks:
        pdf.set_font("Helvetica", "", 10)
        mark = "[OK]" if ok else "[!!]"
        pdf.set_text_color(34, 197, 94) if ok else pdf.set_text_color(239, 68, 68)
        pdf.cell(12, 6, mark)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 6, label_str, ln=True)
    pdf.ln(6)

    # Article structure overview
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(4, 56, 158)
    pdf.cell(0, 9, "Struktura artykulu", ln=True)
    pdf.ln(2)

    for i, sec in enumerate(sections):
        heading = sec.get("heading", "").encode('latin-1', 'replace').decode('latin-1')
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 6, f"H2: {heading}", ln=True)
        for sub in sec.get("subsections", []):
            sub_heading = sub.get("heading", "").encode('latin-1', 'replace').decode('latin-1')
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(10, 5, "")
            pdf.cell(0, 5, f"H3: {sub_heading}", ln=True)

    # Output PDF
    pdf_bytes = pdf.output()
    safe_title = re.sub(r'[^\w\-]', '_', title[:40])
    safe_title = safe_title.encode('ascii', 'ignore').decode('ascii') or "artykul"
    return Response(
        content=bytes(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="raport_seo_{safe_title}.pdf"'}
    )


@router.post("/surfer/auto-optimize/{article_id}")
async def auto_optimize_article(article_id: str, user: dict = Depends(get_current_user)):
    """Start async auto-optimization of article based on SurferSEO recommendations."""
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    surfer_score = article.get("surfer_score")
    surfer_data = article.get("surfer_data")
    if not surfer_score or not surfer_data:
        raise HTTPException(status_code=400, detail="Najpierw uruchom analize SurferSEO")

    job_id = str(uuid.uuid4())
    _optimize_jobs[job_id] = {"status": "running", "article_id": article_id}

    def _run_optimize(jid, art, score, sdata):
        try:
            from llm_helper import llm_chat_sync
            import json as jmod

            keyword = art.get("primary_keyword", "")
            sections = art.get("sections", [])
            faq = art.get("faq", [])
            metrics = score.get("metrics", {})

            # Build improvement instructions
            issues = []
            for key, m in metrics.items():
                if key == "nlp_terms":
                    nlp_terms = m.get("terms", [])
                    missing = [t["term"] for t in nlp_terms if not t.get("used")]
                    if missing:
                        issues.append(f"Brakujace terminy NLP: {', '.join(missing[:10])}")
                    continue
                sc, mx = m.get("score", 0), m.get("max", 5)
                if sc < mx:
                    bench = m.get("benchmark", {})
                    rec = bench.get("recommended", bench.get("avg", ""))
                    issues.append(f"{m.get('label','')}: masz {m.get('value','?')}, zalecane: {rec}")

            sections_summary = jmod.dumps([{"heading": s["heading"], "subsections": [sub["heading"] for sub in s.get("subsections",[])]} for s in sections], ensure_ascii=False)
            issues_text = "\n".join(f"- {i}" for i in issues)

            def _try_parse_json(text):
                """Try to parse JSON, repairing truncated responses."""
                clean = text.strip()
                if clean.startswith("```"):
                    clean = re.sub(r'^```(?:json)?\s*', '', clean)
                    clean = re.sub(r'\s*```$', '', clean)
                try:
                    return jmod.loads(clean)
                except jmod.JSONDecodeError:
                    # Try to repair truncated JSON by closing open structures
                    repaired = clean
                    # Remove trailing incomplete string
                    if repaired.count('"') % 2 != 0:
                        last_quote = repaired.rfind('"')
                        repaired = repaired[:last_quote + 1]
                    # Close open arrays and objects
                    opens = repaired.count('[') - repaired.count(']')
                    openo = repaired.count('{') - repaired.count('}')
                    # Remove trailing comma
                    repaired = re.sub(r',\s*$', '', repaired)
                    repaired += ']' * max(0, opens) + '}' * max(0, openo)
                    return jmod.loads(repaired)

            # STEP 1: Get meta + structure plan (small response)
            prompt_plan = f"""Zoptymalizuj SEO artykulu na slowo: "{keyword}".

Problemy: {issues_text}

Aktualna struktura: {sections_summary[:2000]}
Aktualne FAQ: {len(faq)} pytan
Meta tytul: {art.get('meta_title','')}
Meta opis: {art.get('meta_description','')}

Zwroc KROTKI JSON:
{{"meta_title":"max 60 znakow z keyword","meta_description":"120-155 znakow z keyword","section_plan":[{{"heading":"H2","action":"rozszerz/dodaj","subsections":["H3a","H3b"]}}],"faq_plan":[{{"question":"?","answer_hint":"krotko"}}],"changes_summary":["zmiana1"]}}

WAZNE: section_plan - minimum {max(len(sections), 5)} sekcji. faq_plan - minimum 5 pytan. Zachowaj istniejace sekcje."""

            plan_text = llm_chat_sync(prompt_plan, system_message="Odpowiadaj WYLACZNIE poprawnym JSON. Krotki i zwiezly.", session_id=f"opt-plan-{jid[:8]}", timeout=120)
            plan = _try_parse_json(plan_text)

            # STEP 2: Generate content for each section (one at a time)
            final_sections = []
            section_plans = plan.get("section_plan", [])
            for idx, sp in enumerate(section_plans[:12]):
                heading = sp.get("heading", f"Sekcja {idx+1}")
                subs = sp.get("subsections", [])
                existing_content = ""
                for s in sections:
                    if s.get("heading", "").lower().strip() == heading.lower().strip():
                        existing_content = s.get("content", "")[:500]
                        break

                prompt_sec = f"""Napisz sekcje artykulu SEO na slowo "{keyword}".

Naglowek H2: {heading}
Podsekcje H3: {', '.join(subs) if subs else 'brak'}
Istniejaca tresc (rozszerz): {existing_content[:400]}
Brakujace terminy NLP do uzycia: {', '.join(issues[0].replace('Brakujace terminy NLP: ','').split(', ')[:5]) if issues and 'NLP' in issues[0] else 'brak'}

WYMAGANIA:
- Sekcja H2 musi miec 150-250 slow merytorycznej tresci
- Kazda podsekcja H3 musi miec 80-150 slow merytorycznej tresci
- Uzyj <strong> do pogrubien kluczowych pojec (minimum 2)
- Uzyj <ul><li> do listy punktowanej (minimum 1 lista w sekcji H2)
- Cytuj konkretne przepisy (art., ust., Dz.U.) jesli dotyczy ksiegowosci/podatkow
- Podaj konkretne kwoty, stawki, terminy gdzie to mozliwe

Zwroc WYLACZNIE JSON (bez markdown) o strukturze:
{{"heading":"{heading}","content":"<p>Pelna merytoryczna tresc sekcji...</p>","subsections":[{{"heading":"Nazwa H3","content":"<p>Pelna tresc podsekcji...</p>"}}]}}"""

                try:
                    sec_text = llm_chat_sync(prompt_sec, system_message="Odpowiadaj WYLACZNIE poprawnym JSON. Jedna sekcja artykulu.", session_id=f"opt-s{idx}-{jid[:6]}", timeout=90)
                    sec = _try_parse_json(sec_text)
                    final_sections.append(sec)
                except Exception as se:
                    logging.warning(f"Section {idx} generation failed: {se}, using placeholder")
                    final_sections.append({"heading": heading, "content": existing_content or f"<p>{heading}</p>", "subsections": [{"heading": h, "content": ""} for h in subs]})

            # STEP 3: Generate FAQ
            faq_plans = plan.get("faq_plan", [])
            final_faq = []
            if faq_plans:
                faq_questions = jmod.dumps(faq_plans[:8], ensure_ascii=False)
                prompt_faq = f"""Odpowiedz na pytania FAQ dla artykulu SEO o slowie kluczowym "{keyword}".

Pytania do odpowiedzenia: {faq_questions}

WYMAGANIA:
- Kazda odpowiedz: minimum 40 slow, maksimum 80 slow
- Konkretne, merytoryczne odpowiedzi (kwoty, terminy, przepisy gdy dotyczy)
- Naturalne uzycie slowa kluczowego w 1-2 odpowiedziach
- Odpowiedzi gotowe pod Google Featured Snippets

Zwroc WYLACZNIE tablice JSON o strukturze:
[{{"question":"Pelne pytanie z listy powyzej","answer":"Pelna merytoryczna odpowiedz 40-80 slow."}}]"""

                try:
                    faq_text = llm_chat_sync(prompt_faq, system_message="Odpowiadaj WYLACZNIE poprawnym JSON. Tablica FAQ.", session_id=f"opt-faq-{jid[:6]}", timeout=90)
                    final_faq = _try_parse_json(faq_text)
                    if not isinstance(final_faq, list):
                        final_faq = final_faq.get("faq", []) if isinstance(final_faq, dict) else []
                except Exception as fe:
                    logging.warning(f"FAQ generation failed: {fe}")
                    final_faq = [{"question": fp.get("question",""), "answer": fp.get("answer_hint","")} for fp in faq_plans]

            result = {
                "meta_title": plan.get("meta_title", art.get("meta_title", "")),
                "meta_description": plan.get("meta_description", art.get("meta_description", "")),
                "sections": final_sections,
                "faq": final_faq,
                "changes_summary": plan.get("changes_summary", ["Zoptymalizowano artykul"])
            }

            _optimize_jobs[jid]["status"] = "completed"
            _optimize_jobs[jid]["result"] = result
        except Exception as e:
            logging.error(f"Auto-optimize error: {e}")
            _optimize_jobs[jid]["status"] = "failed"
            _optimize_jobs[jid]["error"] = str(e)

    executor.submit(_run_optimize, job_id, article, surfer_score, surfer_data)
    return {"job_id": job_id, "status": "running"}


@router.get("/surfer/auto-optimize/status/{job_id}")
async def optimize_status(job_id: str, user: dict = Depends(get_current_user)):
    """Check auto-optimize job status."""
    job = _optimize_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, **job}


@router.post("/surfer/auto-optimize/apply/{article_id}")
async def apply_optimization(article_id: str, request: dict, user: dict = Depends(get_current_user)):
    """Apply AI-generated optimization to the article."""
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    optimized = request.get("optimized", {})
    if not optimized:
        raise HTTPException(status_code=400, detail="No optimized data provided")

    # Save version before applying
    version_doc = {
        "id": str(uuid.uuid4()),
        "article_id": article_id,
        "user_id": user.get("id", ""),
        "version_data": {k: v for k, v in article.items() if k != "_id"},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.article_versions.insert_one(version_doc)

    update = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if optimized.get("meta_title"):
        update["meta_title"] = optimized["meta_title"]
    if optimized.get("meta_description"):
        update["meta_description"] = optimized["meta_description"]
    if optimized.get("sections"):
        # Add anchors to sections
        for sec in optimized["sections"]:
            if not sec.get("anchor"):
                sec["anchor"] = re.sub(r'[^\w-]', '-', sec.get("heading", "").lower().strip())[:60]
            for sub in sec.get("subsections", []):
                if not sub.get("anchor"):
                    sub["anchor"] = re.sub(r'[^\w-]', '-', sub.get("heading", "").lower().strip())[:60]
        update["sections"] = optimized["sections"]
        # Rebuild TOC from sections
        toc = []
        for sec in optimized["sections"]:
            toc.append({"text": sec["heading"], "anchor": sec.get("anchor", ""), "level": 2})
            for sub in sec.get("subsections", []):
                toc.append({"text": sub["heading"], "anchor": sub.get("anchor", ""), "level": 3})
        update["toc"] = toc
    if optimized.get("faq"):
        update["faq"] = optimized["faq"]

    await db.articles.update_one({"id": article_id}, {"$set": update})

    return {
        "message": "Optymalizacja zastosowana",
        "meta_title": update.get("meta_title", ""),
        "meta_description": update.get("meta_description", ""),
        "sections_count": len(update.get("sections", [])),
        "faq_count": len(update.get("faq", []))
    }


# In-memory store for iterative optimization
_loop_optimize_jobs = {}


@router.post("/surfer/optimize-loop/{article_id}")
async def start_optimize_loop(article_id: str, user: dict = Depends(get_current_user)):
    """Start iterative optimization loop targeting 80%+ SurferSEO score."""
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    surfer_data = article.get("surfer_data")
    if not surfer_data:
        raise HTTPException(status_code=400, detail="Najpierw uruchom analize SERP")

    job_id = str(uuid.uuid4())
    _loop_optimize_jobs[job_id] = {
        "status": "running",
        "article_id": article_id,
        "iterations": [],
        "current_iteration": 0,
        "target_score": 80,
        "final_score": 0
    }

    def _run_loop(jid, art_id, s_data, user_id):
        import json as jmod
        from llm_helper import llm_chat_sync
        from pymongo import MongoClient

        # Use synchronous pymongo to avoid async event loop issues
        sync_client = MongoClient(os.environ.get('MONGO_URL'), serverSelectionTimeoutMS=5000)
        sync_db = sync_client[os.environ.get('DB_NAME', 'seo_article_writer')]

        MAX_ITERATIONS = 4
        TARGET = 80

        def _try_parse_json(text):
            clean = text.strip()
            if clean.startswith("```"):
                clean = re.sub(r'^```(?:json)?\s*', '', clean)
                clean = re.sub(r'\s*```$', '', clean)
            try:
                return jmod.loads(clean)
            except jmod.JSONDecodeError:
                repaired = clean
                if repaired.count('"') % 2 != 0:
                    repaired = repaired[:repaired.rfind('"') + 1]
                opens = repaired.count('[') - repaired.count(']')
                openo = repaired.count('{') - repaired.count('}')
                repaired = re.sub(r',\s*$', '', repaired)
                repaired += ']' * max(0, opens) + '}' * max(0, openo)
                return jmod.loads(repaired)

        def _apply_to_db(art_id, optimized, uid):
            """Apply optimized content to DB (synchronous)."""
            article = sync_db.articles.find_one({"id": art_id}, {"_id": 0})
            # Save version
            sync_db.article_versions.insert_one({
                "id": str(uuid.uuid4()), "article_id": art_id,
                "user_id": uid,
                "version_data": {k: v for k, v in article.items() if k != "_id"},
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            update = {"updated_at": datetime.now(timezone.utc).isoformat()}
            if optimized.get("meta_title"):
                update["meta_title"] = optimized["meta_title"]
            if optimized.get("meta_description"):
                update["meta_description"] = optimized["meta_description"]
            if optimized.get("sections"):
                clean_sections = []
                for sec in optimized["sections"]:
                    if not isinstance(sec, dict) or not sec.get("heading"):
                        continue
                    sec.setdefault("content", "")
                    sec.setdefault("subsections", [])
                    if not sec.get("anchor"):
                        sec["anchor"] = re.sub(r'[^\w-]', '-', sec["heading"].lower().strip())[:60]
                    clean_subs = []
                    for sub in sec.get("subsections", []):
                        if not isinstance(sub, dict) or not sub.get("heading"):
                            continue
                        sub.setdefault("content", "")
                        if not sub.get("anchor"):
                            sub["anchor"] = re.sub(r'[^\w-]', '-', sub["heading"].lower().strip())[:60]
                        clean_subs.append(sub)
                    sec["subsections"] = clean_subs
                    clean_sections.append(sec)
                if clean_sections:
                    update["sections"] = clean_sections
                    toc = []
                    for sec in clean_sections:
                        toc.append({"text": sec["heading"], "anchor": sec.get("anchor", ""), "level": 2})
                        for sub in sec.get("subsections", []):
                            toc.append({"text": sub["heading"], "anchor": sub.get("anchor", ""), "level": 3})
                    update["toc"] = toc
            if optimized.get("faq"):
                clean_faq = [f for f in optimized["faq"] if isinstance(f, dict) and f.get("question")]
                if clean_faq:
                    update["faq"] = clean_faq
            sync_db.articles.update_one({"id": art_id}, {"$set": update})

        def _score_and_save(art, s_data):
            """Compute SurferSEO score and save (synchronous)."""
            score = compute_surfer_score(art, s_data)
            sync_db.articles.update_one(
                {"id": art["id"]},
                {"$set": {"surfer_score": score, "surfer_data": s_data}}
            )
            return score

        try:
            for iteration in range(1, MAX_ITERATIONS + 1):
                _loop_optimize_jobs[jid]["current_iteration"] = iteration

                # Get fresh article
                article = sync_db.articles.find_one({"id": art_id}, {"_id": 0})

                # Score current state
                current_score = _score_and_save(article, s_data)
                pct = current_score.get("percentage", 0)
                _loop_optimize_jobs[jid]["iterations"].append({
                    "iteration": iteration,
                    "phase": "scored",
                    "score_before": pct
                })

                logging.info(f"[Loop {jid[:8]}] Iteration {iteration}: score={pct}%")

                if pct >= TARGET:
                    _loop_optimize_jobs[jid]["iterations"][-1]["phase"] = "target_reached"
                    _loop_optimize_jobs[jid]["final_score"] = pct
                    _loop_optimize_jobs[jid]["status"] = "completed"
                    return

                # Build issues from score
                metrics = current_score.get("metrics", {})
                issues = []
                for key, m in metrics.items():
                    if key == "nlp_terms":
                        missing = [t["term"] for t in m.get("terms", []) if not t.get("used")]
                        if missing:
                            issues.append(f"Brakujace terminy NLP: {', '.join(missing[:10])}")
                        continue
                    sc, mx = m.get("score", 0), m.get("max", 5)
                    if sc < mx:
                        bench = m.get("benchmark", {})
                        rec = bench.get("recommended", bench.get("avg", ""))
                        issues.append(f"{m.get('label','')}: masz {m.get('value','?')}, zalecane: {rec}")

                keyword = article.get("primary_keyword", "")
                sections = article.get("sections", [])
                faq = article.get("faq", [])
                issues_text = "\n".join(f"- {i}" for i in issues)
                sections_summary = jmod.dumps(
                    [{"heading": s["heading"],
                      "word_count": len(s.get("content", "").split()),
                      "subsections": [sub["heading"] for sub in s.get("subsections", [])]}
                     for s in sections], ensure_ascii=False)

                _loop_optimize_jobs[jid]["iterations"][-1]["phase"] = "optimizing"
                _loop_optimize_jobs[jid]["iterations"][-1]["issues"] = [i[:80] for i in issues[:5]]

                # Step 1: Plan
                plan_prompt = f"""Zoptymalizuj SEO artykulu. Slowo kluczowe: "{keyword}". Iteracja {iteration}.

Aktualny wynik: {pct}%, cel: {TARGET}%
Problemy:
{issues_text}

Struktura: {sections_summary[:2000]}
FAQ: {len(faq)} pytan | Meta: {article.get('meta_title','')} | Opis: {article.get('meta_description','')}

Zwroc KROTKI JSON:
{{"meta_title":"max 60 zn z keyword","meta_description":"120-155 zn z keyword","section_plan":[{{"heading":"H2","action":"rozszerz/dodaj","subsections":["H3"]}}],"faq_plan":[{{"question":"?","answer_hint":"krotko"}}],"changes_summary":["zmiana"]}}

WAZNE: min {max(len(sections), 5)} sekcji, min 5 FAQ. Skup sie na: {issues_text[:200]}"""

                plan_text = llm_chat_sync(plan_prompt, system_message="JSON. Krotki.", session_id=f"loop-p{iteration}-{jid[:6]}", timeout=120)
                plan = _try_parse_json(plan_text)

                # Step 2: Sections
                final_sections = []
                for idx, sp in enumerate(plan.get("section_plan", [])[:12]):
                    heading = sp.get("heading", f"Sekcja {idx+1}")
                    subs = sp.get("subsections", [])
                    existing = ""
                    for s in sections:
                        if s.get("heading", "").lower().strip() == heading.lower().strip():
                            existing = s.get("content", "")[:500]
                            break

                    nlp_hint = ', '.join(issues[0].replace('Brakujace terminy NLP: ', '').split(', ')[:5]) if issues and 'NLP' in issues[0] else 'brak'
                    sec_prompt = f"""Napisz sekcje artykulu SEO. Slowo kluczowe: "{keyword}".

Naglowek H2: {heading}
Podsekcje H3: {', '.join(subs) if subs else 'brak'}
Istniejaca tresc (rozszerz): {existing[:300]}
Terminy NLP do naturalnego uzycia: {nlp_hint}

WYMAGANIA:
- Sekcja H2: 200-300 slow merytorycznej tresci (nie placeholder, tylko rzeczywista tresc)
- Kazda podsekcja H3: 100-200 slow merytorycznej tresci
- Uzyj <strong> do pogrubien kluczowych pojec (min. 3)
- Uzyj <ul><li>...</li></ul> listy punktowanej (min. 1 w H2)
- Cytuj konkretne przepisy (art., ust., Dz.U.) gdy dotyczy
- Podaj konkretne kwoty, stawki, terminy

Zwroc WYLACZNIE JSON (bez markdown) o strukturze:
{{"heading":"{heading}","content":"<p>Pelna merytoryczna tresc H2 z pogrubieniami i lista...</p>","subsections":[{{"heading":"Nazwa H3","content":"<p>Pelna tresc H3...</p>"}}]}}"""
                    try:
                        sec = _try_parse_json(llm_chat_sync(sec_prompt, system_message="JSON.", session_id=f"loop-s{iteration}{idx}-{jid[:5]}", timeout=90))
                        final_sections.append(sec)
                    except Exception:
                        final_sections.append({"heading": heading, "content": existing or f"<p>{heading}</p>", "subsections": [{"heading": h, "content": ""} for h in subs]})

                # Step 3: FAQ
                final_faq = faq  # keep existing
                faq_plans = plan.get("faq_plan", [])
                if faq_plans and len(faq) < 5:
                    try:
                        faq_prompt = f"""Odpowiedz na pytania FAQ dla artykulu SEO o "{keyword}".

Pytania: {jmod.dumps(faq_plans[:8], ensure_ascii=False)}

WYMAGANIA:
- Kazda odpowiedz: 40-80 slow merytorycznej tresci
- Konkretne kwoty, terminy, przepisy gdy dotyczy
- Naturalne slowo kluczowe w 1-2 odpowiedziach

Zwroc WYLACZNIE tablice JSON:
[{{"question":"Pelne pytanie","answer":"Pelna merytoryczna odpowiedz 40-80 slow."}}]"""
                        faq_text = llm_chat_sync(
                            faq_prompt,
                            system_message="Odpowiadaj WYLACZNIE poprawnym JSON (tablica FAQ).",
                            session_id=f"loop-faq{iteration}-{jid[:5]}",
                            timeout=90)
                        parsed_faq = _try_parse_json(faq_text)
                        if isinstance(parsed_faq, list):
                            final_faq = parsed_faq
                        elif isinstance(parsed_faq, dict):
                            final_faq = parsed_faq.get("faq", faq)
                    except Exception:
                        pass

                optimized = {
                    "meta_title": plan.get("meta_title", article.get("meta_title", "")),
                    "meta_description": plan.get("meta_description", article.get("meta_description", "")),
                    "sections": final_sections,
                    "faq": final_faq,
                    "changes_summary": plan.get("changes_summary", [])
                }

                # Apply
                _loop_optimize_jobs[jid]["iterations"][-1]["phase"] = "applying"
                _apply_to_db(art_id, optimized, user_id)

                # Re-score
                updated = sync_db.articles.find_one({"id": art_id}, {"_id": 0})
                new_score = _score_and_save(updated, s_data)
                new_pct = new_score.get("percentage", 0)

                _loop_optimize_jobs[jid]["iterations"][-1]["score_after"] = new_pct
                _loop_optimize_jobs[jid]["iterations"][-1]["changes"] = optimized.get("changes_summary", [])[:3]
                _loop_optimize_jobs[jid]["iterations"][-1]["phase"] = "done"
                _loop_optimize_jobs[jid]["final_score"] = new_pct

                logging.info(f"[Loop {jid[:8]}] Iteration {iteration}: {pct}% -> {new_pct}%")

                if new_pct >= TARGET:
                    break

            _loop_optimize_jobs[jid]["status"] = "completed"

        except Exception as e:
            logging.error(f"Optimize loop error: {e}")
            _loop_optimize_jobs[jid]["status"] = "failed"
            _loop_optimize_jobs[jid]["error"] = str(e)
        finally:
            sync_client.close()

    executor.submit(_run_loop, job_id, article_id, surfer_data, user.get("id", ""))
    return {"job_id": job_id, "status": "running"}


@router.get("/surfer/optimize-loop/status/{job_id}")
async def optimize_loop_status(job_id: str, user: dict = Depends(get_current_user)):
    """Check iterative optimization status with per-iteration progress."""
    job = _loop_optimize_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, **job}
