"""Article CRUD, generation, export, scheduled publishing, bulk ops, versions."""
import os, logging, asyncio
from fastapi import APIRouter, Depends
from shared import (
    db, get_current_user, serialize_doc, executor, HTTPException, uuid, datetime, timezone, json, re,
    ArticleGenerateRequest, ArticleUpdateRequest, ScoreRequest, ExportRequest,
    RegenerateRequest, TopicSuggestRequest, SchedulePublishRequest,
    BulkDeleteRequest, BulkCategoryRequest, WordPressSettingsRequest, SeriesRequest,
    ImportUrlRequest, ImportWordPressRequest, Response, Optional, List, Dict, Any
)
from article_generator import generate_article, suggest_topics
from seo_scorer import compute_seo_score
from surfer_seo_service import analyze_serp, compute_surfer_score
from export_service import generate_facebook_post, generate_google_business_post, generate_full_html, generate_pdf_bytes
from wordpress_service import publish_to_wordpress, generate_wordpress_plugin, build_styled_wordpress_content
from content_templates import get_all_templates
from series_generator import generate_series_outline
from import_service import scrape_article_from_url, import_from_wordpress, optimize_imported_article
from linkbuilding_service import analyze_internal_links

router = APIRouter()

# --- Article Generation ---


def _auto_optimize_to_target(job_id, article_id, s_data, user_id, sync_db, target=80, max_iter_safety=10):
    """Auto-optimize an article to reach target SEO score (default 80%).

    Runs iterative optimization with stagnation detection: if score doesn't
    improve for 2 consecutive iterations, stops. Updates generation_jobs doc
    with per-iteration progress for frontend polling.
    """
    import json as jmod
    from llm_helper import llm_chat_sync

    def _try_parse_json(text):
        if text is None:
            return None
        clean = text.strip()
        if clean.startswith("```"):
            clean = re.sub(r'^```(?:json)?\s*', '', clean)
            clean = re.sub(r'\s*```$', '', clean)
        try:
            return jmod.loads(clean)
        except jmod.JSONDecodeError:
            repaired = clean
            if repaired.count('"') % 2 != 0:
                last_quote = repaired.rfind('"')
                repaired = repaired[:last_quote + 1]
            opens = repaired.count('[') - repaired.count(']')
            openo = repaired.count('{') - repaired.count('}')
            repaired = re.sub(r',\s*$', '', repaired)
            repaired += ']' * max(0, opens) + '}' * max(0, openo)
            try:
                return jmod.loads(repaired)
            except Exception:
                return None

    def _score_and_save(art):
        score = compute_surfer_score(art, s_data)
        sync_db.articles.update_one({"id": art["id"]}, {"$set": {"surfer_score": score, "surfer_data": s_data}})
        return score

    def _apply_update(a_id, optimized, uid):
        article = sync_db.articles.find_one({"id": a_id}, {"_id": 0})
        sync_db.article_versions.insert_one({
            "id": str(uuid.uuid4()), "article_id": a_id, "user_id": uid,
            "version_data": {k: v for k, v in article.items() if k != "_id"},
            "source": "auto_generate_optimize",
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
                    sec["anchor"] = re.sub(r'[^\w-]', '-', (sec.get("heading") or "").lower().strip())[:60]
                clean_subs = []
                for sub in (sec.get("subsections") or []):
                    if not isinstance(sub, dict) or not sub.get("heading"):
                        continue
                    sub.setdefault("content", "")
                    if not sub.get("anchor"):
                        sub["anchor"] = re.sub(r'[^\w-]', '-', (sub.get("heading") or "").lower().strip())[:60]
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
        sync_db.articles.update_one({"id": a_id}, {"$set": update})

    stagnation_count = 0
    iteration = 0
    last_score = None

    while iteration < max_iter_safety:
        iteration += 1
        article = sync_db.articles.find_one({"id": article_id}, {"_id": 0})
        current_score = _score_and_save(article)
        pct = current_score.get("percentage", 0)

        # Log iteration start to job
        sync_db.generation_jobs.update_one(
            {"job_id": job_id},
            {"$push": {"optimization_iterations": {
                "iteration": iteration, "phase": "start",
                "score_before": pct, "score_after": None
            }}}
        )

        if pct >= target:
            sync_db.generation_jobs.update_one(
                {"job_id": job_id, "optimization_iterations.iteration": iteration},
                {"$set": {"optimization_iterations.$.phase": "target_reached",
                          "optimization_iterations.$.score_after": pct}}
            )
            return

        if last_score is not None and pct <= last_score:
            stagnation_count += 1
            if stagnation_count >= 2:
                sync_db.generation_jobs.update_one(
                    {"job_id": job_id, "optimization_iterations.iteration": iteration},
                    {"$set": {"optimization_iterations.$.phase": "stagnation",
                              "optimization_iterations.$.score_after": pct}}
                )
                return
        else:
            stagnation_count = 0

        # Expand content: add 1-2 new sections and improve meta
        keyword = article.get("primary_keyword") or ""
        sections = article.get("sections") or []
        metrics = current_score.get("metrics", {})
        nlp_missing = [t["term"] for t in metrics.get("nlp_terms", {}).get("terms", [])[:12] if not t.get("used")]

        plan_prompt = f"""Ulepsz artykul SEO. Slowo: "{keyword}".
Brakujace terminy NLP: {', '.join(nlp_missing[:10])}
Aktualne sekcje:
{jmod.dumps([{"heading": s.get("heading") or "", "words": len((s.get("content") or "").split())} for s in sections], ensure_ascii=False)}

Zaplanuj 2 nowe sekcje H2 do dodania, ktore wzmocnia SEO i uzyja brakujacych terminow NLP.
Zwroc JSON:
{{"meta_title":"max 60 znakow z keyword","meta_description":"120-155 znakow","new_sections":["H2 nowa sekcja 1","H2 nowa sekcja 2"]}}"""

        try:
            plan_text = llm_chat_sync(plan_prompt, system_message="JSON only.",
                                      session_id=f"gen-opt-plan-{job_id[:6]}-{iteration}", timeout=60)
            plan = _try_parse_json(plan_text) or {}
        except Exception:
            plan = {}

        added_sections = []
        for new_heading in plan.get("new_sections", [])[:2]:
            if not isinstance(new_heading, str) or len(new_heading) < 5:
                continue
            sec_prompt = f"""Napisz sekcje artykulu SEO. Slowo: "{keyword}". Naglowek H2: {new_heading}.
Terminy NLP do naturalnego uzycia: {', '.join(nlp_missing[:6])}.
WYMAGANIA:
- 200-300 slow merytorycznej tresci (nie placeholder)
- Uzyj <strong> (min 3) i <ul><li> (min 1 lista)
- Konkretne kwoty/terminy/przepisy gdy dotyczy branzy
Zwroc JSON: {{"heading":"{new_heading}","content":"<p>...</p>"}}"""
            try:
                sec = _try_parse_json(llm_chat_sync(sec_prompt, system_message="JSON.",
                                                    session_id=f"gen-opt-sec-{job_id[:6]}-{iteration}-{len(added_sections)}",
                                                    timeout=90))
                if isinstance(sec, dict) and sec.get("content"):
                    added_sections.append(sec)
            except Exception:
                pass

        optimized = {
            "meta_title": plan.get("meta_title", article.get("meta_title", "")),
            "meta_description": plan.get("meta_description", article.get("meta_description", "")),
            "sections": sections + added_sections
        }
        _apply_update(article_id, optimized, user_id)

        updated = sync_db.articles.find_one({"id": article_id}, {"_id": 0})
        new_score = _score_and_save(updated)
        new_pct = new_score.get("percentage", 0)

        sync_db.generation_jobs.update_one(
            {"job_id": job_id, "optimization_iterations.iteration": iteration},
            {"$set": {"optimization_iterations.$.phase": "done",
                      "optimization_iterations.$.score_after": new_pct}}
        )

        last_score = pct
        if new_pct >= target:
            return


def _sync_run_generation_job(job_id: str, request_data: dict, user: dict):
    """Run article generation in a separate thread to avoid blocking event loop."""
    import pymongo
    sync_client = pymongo.MongoClient(os.environ.get('MONGO_URL'), serverSelectionTimeoutMS=5000)
    sync_db = sync_client[os.environ.get('DB_NAME', 'seo_article_writer')]
    try:
        sync_db.generation_jobs.update_one(
            {"job_id": job_id},
            {"$set": {"status": "generating", "stage": 1}}
        )

        loop = asyncio.new_event_loop()
        try:
            article_data = loop.run_until_complete(generate_article(
                topic=request_data["topic"],
                primary_keyword=request_data["primary_keyword"],
                secondary_keywords=request_data["secondary_keywords"],
                target_length=request_data["target_length"],
                tone=request_data["tone"],
                template=request_data["template"],
                language=request_data.get("language", "pl")
            ))
        finally:
            loop.close()

        sync_db.generation_jobs.update_one(
            {"job_id": job_id},
            {"$set": {"stage": 3}}
        )

        # Compute both old SEO score and new SurferSEO score
        seo_score = compute_seo_score(
            article_data,
            request_data["primary_keyword"],
            request_data["secondary_keywords"]
        )

        # Run SurferSEO SERP analysis for the keyword
        surfer_data = None
        surfer_score = None
        try:
            loop2 = asyncio.new_event_loop()
            try:
                surfer_data = loop2.run_until_complete(analyze_serp(request_data["primary_keyword"]))
            finally:
                loop2.close()
            
            if surfer_data:
                surfer_score = compute_surfer_score(article_data, surfer_data)
                seo_score = {
                    "percentage": surfer_score["percentage"],
                    "breakdown": surfer_score["metrics"],
                    "total_score": surfer_score["total_score"],
                    "total_max": surfer_score["total_max"]
                }
        except Exception as e:
            logging.warning(f"Surfer SERP analysis failed, using basic scorer: {e}")

        article_id = str(uuid.uuid4())
        article_doc = {
            "id": article_id,
            "user_id": user["id"],
            "workspace_id": user.get("workspace_id", user["id"]),
            "topic": request_data["topic"],
            "primary_keyword": request_data["primary_keyword"],
            "secondary_keywords": request_data["secondary_keywords"],
            "target_length": request_data["target_length"],
            "tone": request_data["tone"],
            "template": request_data["template"],
            "language": request_data.get("language", "pl"),
            "title": article_data.get("title", ""),
            "slug": article_data.get("slug", ""),
            "meta_title": article_data.get("meta_title", ""),
            "meta_description": article_data.get("meta_description", ""),
            "toc": article_data.get("toc", []),
            "sections": article_data.get("sections", []),
            "faq": article_data.get("faq", []),
            "internal_link_suggestions": article_data.get("internal_link_suggestions", []),
            "sources": article_data.get("sources", []),
            "seo_score": seo_score,
            "surfer_data": surfer_data,
            "surfer_score": surfer_score,
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        sync_db.articles.insert_one(article_doc)

        # Auto-optimize to 80%+ if we have surfer_data
        if surfer_data and (not surfer_score or surfer_score.get("percentage", 0) < 80):
            try:
                sync_db.generation_jobs.update_one(
                    {"job_id": job_id},
                    {"$set": {
                        "stage": 5,
                        "status": "optimizing",
                        "optimization_iterations": [],
                        "initial_score": surfer_score.get("percentage", 0) if surfer_score else 0
                    }}
                )
                _auto_optimize_to_target(job_id, article_id, surfer_data, user.get("id", ""), sync_db)
            except Exception as opt_err:
                logging.warning(f"Auto-optimization failed (article saved as-is): {opt_err}")
                sync_db.generation_jobs.update_one(
                    {"job_id": job_id},
                    {"$set": {"optimization_error": str(opt_err)[:300]}}
                )

        # Fetch final score before marking complete
        final_article = sync_db.articles.find_one({"id": article_id}, {"_id": 0, "surfer_score": 1})
        final_score_pct = 0
        if final_article and final_article.get("surfer_score"):
            final_score_pct = final_article["surfer_score"].get("percentage", 0)

        sync_db.generation_jobs.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": "completed",
                "stage": 4,
                "article_id": article_id,
                "final_score": final_score_pct,
                "target_reached": final_score_pct >= 80
            }}
        )

    except Exception as e:
        err_msg = str(e)
        if "budget" in err_msg.lower() or "exceeded" in err_msg.lower():
            err_msg = "Budzet Universal Key wyczerpany. Doladuj w Profile > Universal Key > Add Balance."
        elif "502" in err_msg or "bad gateway" in err_msg.lower():
            err_msg = "Usluga AI tymczasowo niedostepna (blad 502). Sprawdz saldo Universal Key lub sprobuj za chwile."
        elif "429" in err_msg or "rate" in err_msg.lower():
            err_msg = "Przekroczono limit zapytan AI. Sprobuj za kilka minut."
        elif "401" in err_msg or "auth" in err_msg.lower():
            err_msg = "Blad autoryzacji klucza AI. Skontaktuj sie z administratorem."
        logging.error(f"Background generation error: {e}")
        sync_db.generation_jobs.update_one(
            {"job_id": job_id},
            {"$set": {"status": "failed", "error": err_msg}}
        )
    finally:
        sync_client.close()


@router.post("/articles/generate")
async def generate_article_endpoint(request: ArticleGenerateRequest, user: dict = Depends(get_current_user)):
    """Start async article generation - returns job ID immediately."""
    job_id = str(uuid.uuid4())
    
    job_doc = {
        "job_id": job_id,
        "status": "queued",
        "stage": 0,
        "article_id": None,
        "error": None,
        "user_id": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.generation_jobs.insert_one(job_doc)
    
    request_data = {
        "topic": request.topic,
        "primary_keyword": request.primary_keyword,
        "secondary_keywords": request.secondary_keywords,
        "target_length": request.target_length,
        "tone": request.tone,
        "template": request.template,
        "language": request.language
    }
    
    asyncio.get_event_loop().run_in_executor(
        None, _sync_run_generation_job, job_id, request_data, user
    )
    
    return {"job_id": job_id, "status": "queued"}


@router.get("/articles/generate/status/{job_id}")
async def get_generation_status(job_id: str, user: dict = Depends(get_current_user)):
    """Check article generation job status."""
    job = await db.generation_jobs.find_one({"job_id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    if job["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Brak dostepu")
    
    # Detect stale jobs: if generating for more than 5 minutes, mark as failed
    # (extend to 15 min during optimization since iterative loop takes longer)
    if job["status"] in ("generating", "optimizing"):
        from datetime import datetime as dt
        created = dt.fromisoformat(job["created_at"].replace("Z", "+00:00")) if isinstance(job["created_at"], str) else job["created_at"]
        elapsed = (datetime.now(timezone.utc) - created).total_seconds()
        max_elapsed = 900 if job["status"] == "optimizing" else 360
        if elapsed > max_elapsed:
            await db.generation_jobs.update_one(
                {"job_id": job_id},
                {"$set": {"status": "failed", "error": f"Generowanie przekroczylo limit czasu ({int(max_elapsed/60)} min). Sprobuj ponownie."}}
            )
            job["status"] = "failed"
            job["error"] = f"Generowanie przekroczylo limit czasu ({int(max_elapsed/60)} min). Sprobuj ponownie."

    result = {
        "job_id": job_id,
        "status": job["status"],
        "stage": job.get("stage", 0),
        "optimization_iterations": job.get("optimization_iterations", []),
        "initial_score": job.get("initial_score"),
        "final_score": job.get("final_score"),
        "target_reached": job.get("target_reached"),
    }
    
    if job["status"] == "completed":
        result["article_id"] = job.get("article_id")
        # Load article from DB
        if job.get("article_id"):
            article = await db.articles.find_one({"id": job["article_id"]}, {"_id": 0})
            if article:
                result["article"] = serialize_doc(article)
        # Cleanup old job
        await db.generation_jobs.delete_one({"job_id": job_id})
    elif job["status"] == "failed":
        result["error"] = job.get("error", "Nieznany blad")
        await db.generation_jobs.delete_one({"job_id": job_id})
    
    return result


# --- Scheduled Articles (must be before /articles/{article_id}) ---

@router.get("/articles/scheduled")
async def list_scheduled_articles(user: dict = Depends(get_current_user)):
    """List all scheduled articles."""
    articles = await db.articles.find(
        {"user_id": user["id"], "schedule_status": "scheduled"},
        {"_id": 0, "id": 1, "title": 1, "scheduled_at": 1, "scheduled_wp": 1}
    ).sort("scheduled_at", 1).to_list(50)
    return articles

@router.post("/articles/check-updates")
async def check_updates(user: dict = Depends(get_current_user)):
    """Check all articles for needed updates."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    
    articles = await db.articles.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).to_list(20)
    
    if not articles:
        return {"articles_needing_update": [], "up_to_date_articles": [], "summary": "Brak artykulow do sprawdzenia."}
    
    try:
        result = await check_articles_for_updates(articles, emergent_key)
        
        await db.update_checks.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "result": result,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return result
    except Exception as e:
        logging.error(f"Auto-update check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Article CRUD ---

@router.get("/articles")
async def list_articles(user: dict = Depends(get_current_user)):
    """List articles scoped to user (admin sees all)."""
    query = {} if user.get("is_admin") else {"user_id": user["id"]}
    articles = await db.articles.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return [{**serialize_doc(a)} for a in articles]

# NOTE: All /articles/STATIC_PATH routes must be placed BEFORE /articles/{article_id}
# to avoid FastAPI treating the static path as an article_id.

@router.get("/articles/categories-list")
async def list_categories_safe(user: dict = Depends(get_current_user)):
    """Get all unique categories (safe path to avoid conflict)."""
    pipeline = [
        {"$match": {"category": {"$exists": True, "$ne": ""}}},
        {"$group": {"_id": "$category"}},
        {"$sort": {"_id": 1}}
    ]
    result = await db.articles.aggregate(pipeline).to_list(50)
    return [r["_id"] for r in result]


@router.get("/articles/{article_id}")
async def get_article(article_id: str, user: dict = Depends(get_current_user)):
    """Get a single article by ID (owner or admin)."""
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if not user.get("is_admin") and article.get("user_id") and article["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Brak dostepu")
    return serialize_doc(article)


def _slugify(text: str) -> str:
    """Create a URL-friendly slug from text."""
    text = text.lower().strip()
    text = re.sub(r'[ąàáâãäå]', 'a', text)
    text = re.sub(r'[ćçč]', 'c', text)
    text = re.sub(r'[ęèéêë]', 'e', text)
    text = re.sub(r'[łl]', 'l', text)
    text = re.sub(r'[ńñ]', 'n', text)
    text = re.sub(r'[óòôõö]', 'o', text)
    text = re.sub(r'[śšş]', 's', text)
    text = re.sub(r'[żźž]', 'z', text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:80].strip('-')


def _parse_html_to_sections(html: str) -> list:
    """Parse HTML content from the visual editor back into structured sections."""
    if not html or not html.strip():
        return []
    
    # Split HTML by h2 tags to get sections
    # Pattern: find all h2 and content between them
    parts = re.split(r'(<h2[^>]*>.*?</h2>)', html, flags=re.IGNORECASE | re.DOTALL)
    
    sections = []
    current_section = None
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Check if this is an h2 heading
        h2_match = re.match(r'<h2[^>]*(?:id="([^"]*)")?[^>]*>(.*?)</h2>', part, re.IGNORECASE | re.DOTALL)
        if h2_match:
            # Save previous section
            if current_section:
                sections.append(current_section)
            
            heading_text = re.sub(r'<[^>]+>', '', h2_match.group(2)).strip()
            anchor = h2_match.group(1) or _slugify(heading_text)
            current_section = {
                "heading": heading_text,
                "anchor": anchor,
                "content": "",
                "subsections": []
            }
        elif current_section is not None:
            # Process content within current section - split by h3
            h3_parts = re.split(r'(<h3[^>]*>.*?</h3>)', part, flags=re.IGNORECASE | re.DOTALL)
            current_subsection = None
            
            for h3_part in h3_parts:
                h3_part = h3_part.strip()
                if not h3_part:
                    continue
                
                h3_match = re.match(r'<h3[^>]*(?:id="([^"]*)")?[^>]*>(.*?)</h3>', h3_part, re.IGNORECASE | re.DOTALL)
                if h3_match:
                    if current_subsection:
                        current_section["subsections"].append(current_subsection)
                    
                    sub_heading = re.sub(r'<[^>]+>', '', h3_match.group(2)).strip()
                    sub_anchor = h3_match.group(1) or _slugify(sub_heading)
                    current_subsection = {
                        "heading": sub_heading,
                        "anchor": sub_anchor,
                        "content": ""
                    }
                elif current_subsection is not None:
                    current_subsection["content"] += h3_part
                else:
                    current_section["content"] += h3_part
            
            if current_subsection:
                current_section["subsections"].append(current_subsection)
    
    # Don't forget the last section
    if current_section:
        sections.append(current_section)
    
    # Clean up content - trim whitespace
    for section in sections:
        section["content"] = section["content"].strip()
        for sub in section.get("subsections", []):
            sub["content"] = sub["content"].strip()
    
    return sections


@router.put("/articles/{article_id}")
async def update_article(article_id: str, request: ArticleUpdateRequest, user: dict = Depends(get_current_user)):
    """Update an existing article (owner or admin)."""
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if not user.get("is_admin") and article.get("user_id") and article["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Brak dostepu")
    
    update_data = {k: v for k, v in request.model_dump().items() if v is not None}
    
    # Sync html_content back to sections so SEO scorer has updated data
    html_to_parse = update_data.get("html_content", "")
    if html_to_parse:
        logging.info(f"Parsing html_content ({len(html_to_parse)} chars) to sections")
        parsed_sections = _parse_html_to_sections(html_to_parse)
        logging.info(f"Parsed {len(parsed_sections)} sections from html_content")
        if parsed_sections:
            update_data["sections"] = parsed_sections
            # Also extract title from H1 if present
            title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html_to_parse, re.IGNORECASE | re.DOTALL)
            if title_match:
                new_title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
                if new_title:
                    update_data["title"] = new_title
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Save version history before updating
    version_doc = {
        "id": str(uuid.uuid4()),
        "article_id": article_id,
        "user_id": user.get("id", ""),
        "version_data": {k: v for k, v in article.items() if k not in ("_id",)},
        "source": "manual_edit",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.article_versions.insert_one(version_doc)
    
    await db.articles.update_one({"id": article_id}, {"$set": update_data})
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    return serialize_doc(article)


@router.delete("/articles/{article_id}")
async def delete_article(article_id: str, user: dict = Depends(get_current_user)):
    """Delete an article (owner or admin)."""
    article = await db.articles.find_one({"id": article_id})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if not user.get("is_admin") and article.get("user_id") and article["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Brak dostepu")
    await db.articles.delete_one({"id": article_id})
    return {"message": "Article deleted", "id": article_id}

# --- Export ---

@router.post("/articles/{article_id}/export")
async def export_article(article_id: str, request: ExportRequest):
    """Export article in various formats."""
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    if request.format == "facebook":
        content = generate_facebook_post(article)
        return {"format": "facebook", "content": content}
    
    elif request.format == "google_business":
        content = generate_google_business_post(article)
        return {"format": "google_business", "content": content}
    
    elif request.format == "html":
        html = generate_full_html(article)
        return {"format": "html", "content": html}
    
    elif request.format == "wordpress":
        styled_content = build_styled_wordpress_content(article)
        return {"format": "wordpress", "content": styled_content}
    
    elif request.format == "pdf":
        pdf_bytes = generate_pdf_bytes(article)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={article.get('slug', 'article')}.pdf"}
        )
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown format: {request.format}")



# --- Regeneration ---


@router.post("/articles/{article_id}/regenerate")
async def regenerate_section(article_id: str, request: RegenerateRequest):
    """Regenerate a specific section of the article using AI."""
    if request.section not in ("faq", "meta"):
        raise HTTPException(status_code=400, detail=f"Nieznana sekcja: {request.section}. Dozwolone: faq, meta")
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    try:
        from article_generator import ARTICLE_SYSTEM_PROMPT
        from llm_helper import llm_chat
        
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            raise ValueError("EMERGENT_LLM_KEY not configured")
        
        topic = article.get("topic", "")
        primary_keyword = article.get("primary_keyword", "")
        
        if request.section == "faq":
            prompt = f"""Na podstawie artykułu o temacie: "{topic}" (słowo kluczowe: "{primary_keyword}"), wygeneruj 6-8 pytań FAQ ze szczegółowymi odpowiedziami.

Odpowiedz WYŁĄCZNIE w formacie JSON (bez markdown):
{{
  "faq": [
    {{
      "question": "Pytanie FAQ (naturalne, jak w wyszukiwarce)",
      "answer": "Szczegółowa odpowiedź (minimum 30 słów, konkretna i merytoryczna)"
    }}
  ]
}}"""
        elif request.section == "meta":
            prompt = f"""Na podstawie artykułu o temacie: "{topic}" (słowo kluczowe: "{primary_keyword}"), wygeneruj nowy meta tytuł i meta opis zoptymalizowane pod SEO.

Odpowiedz WYŁĄCZNIE w formacie JSON (bez markdown):
{{
  "meta_title": "Meta tytuł SEO (max 60 znaków, zawiera słowo kluczowe)",
  "meta_description": "Meta opis SEO (120-160 znaków, zachęcający do kliknięcia, zawiera słowo kluczowe)"
}}"""
        else:
            raise HTTPException(status_code=400, detail=f"Nieznana sekcja: {request.section}")
        
        
        response = await llm_chat(
            prompt,
            system_message="Jesteś ekspertem SEO od księgowości w Polsce. Odpowiadaj WYŁĄCZNIE poprawnym JSON-em.",
            session_id=f"regen-{article_id}-{request.section}",
            timeout=120
        )
        
        import re
        clean_response = response.strip()
        if clean_response.startswith("```"):
            clean_response = re.sub(r'^```(?:json)?\s*', '', clean_response)
            clean_response = re.sub(r'\s*```$', '', clean_response)
        
        result = json.loads(clean_response)
        return result
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"AI returned invalid JSON: {str(e)}")
    except Exception as e:
        logging.error(f"Regeneration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# --- Topic Suggestions ---

@router.post("/topics/suggest")
async def suggest_topics_endpoint(request: TopicSuggestRequest):
    """Get AI-powered topic suggestions."""
    try:
        result = await suggest_topics(
            category=request.category,
            context=request.context
        )
        return result
    except Exception as e:
        logging.error(f"Topic suggestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Dashboard Stats ---

@router.get("/stats")
async def get_stats(user: dict = Depends(get_current_user)):
    """Get dashboard statistics scoped to user (admin sees all)."""
    query = {} if user.get("is_admin") else {"user_id": user["id"]}
    total_articles = await db.articles.count_documents(query)
    
    # Average SEO score
    match_query = {**query, "seo_score.percentage": {"$exists": True}}
    pipeline = [
        {"$match": match_query},
        {"$group": {"_id": None, "avg_score": {"$avg": "$seo_score.percentage"}}}
    ]
    avg_result = await db.articles.aggregate(pipeline).to_list(1)
    avg_score = round(avg_result[0]["avg_score"]) if avg_result else 0
    
    # Articles needing improvement (score < 70)
    needs_query = {**query, "seo_score.percentage": {"$lt": 70}}
    needs_improvement = await db.articles.count_documents(needs_query)
    
    return {
        "total_articles": total_articles,
        "avg_seo_score": avg_score,
        "needs_improvement": needs_improvement
    }


@router.get("/stats/roi")
async def get_roi_stats(user: dict = Depends(get_current_user)):
    """Extended ROI dashboard stats: score distribution, top/bottom performers, trends."""
    query = {} if user.get("is_admin") else {"user_id": user["id"]}

    total = await db.articles.count_documents(query)

    # Status distribution
    status_pipeline = [
        {"$match": query},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_dist = await db.articles.aggregate(status_pipeline).to_list(10)
    status_counts = {"draft": 0, "published": 0, "scheduled": 0}
    for s in status_dist:
        status_counts[s["_id"] or "draft"] = s["count"]

    # Score buckets (excellent/good/needs-work)
    score_pipeline = [
        {"$match": {**query, "surfer_score.percentage": {"$exists": True}}},
        {"$bucket": {
            "groupBy": "$surfer_score.percentage",
            "boundaries": [0, 50, 70, 80, 101],
            "default": "unknown",
            "output": {"count": {"$sum": 1}}
        }}
    ]
    try:
        score_buckets_raw = await db.articles.aggregate(score_pipeline).to_list(10)
    except Exception:
        score_buckets_raw = []
    score_buckets = {"poor": 0, "medium": 0, "good": 0, "excellent": 0}
    for b in score_buckets_raw:
        bid = b["_id"]
        if bid == 0:
            score_buckets["poor"] = b["count"]
        elif bid == 50:
            score_buckets["medium"] = b["count"]
        elif bid == 70:
            score_buckets["good"] = b["count"]
        elif bid == 80:
            score_buckets["excellent"] = b["count"]

    # Top 5 performers
    top_pipeline = [
        {"$match": {**query, "surfer_score.percentage": {"$exists": True}}},
        {"$sort": {"surfer_score.percentage": -1}},
        {"$limit": 5},
        {"$project": {"_id": 0, "id": 1, "title": 1, "primary_keyword": 1, "surfer_score.percentage": 1, "created_at": 1}}
    ]
    top_performers = await db.articles.aggregate(top_pipeline).to_list(5)

    # Bottom 5 (needs work)
    bottom_pipeline = [
        {"$match": {**query, "surfer_score.percentage": {"$exists": True}}},
        {"$sort": {"surfer_score.percentage": 1}},
        {"$limit": 5},
        {"$project": {"_id": 0, "id": 1, "title": 1, "primary_keyword": 1, "surfer_score.percentage": 1, "created_at": 1}}
    ]
    bottom_performers = await db.articles.aggregate(bottom_pipeline).to_list(5)

    # Articles per language
    lang_pipeline = [
        {"$match": query},
        {"$group": {"_id": {"$ifNull": ["$language", "pl"]}, "count": {"$sum": 1}}}
    ]
    lang_dist_raw = await db.articles.aggregate(lang_pipeline).to_list(10)
    lang_dist = {item["_id"]: item["count"] for item in lang_dist_raw}

    # Monthly publish trend (last 6 months)
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    six_months_ago = (now - timedelta(days=180)).isoformat()
    trend_pipeline = [
        {"$match": {**query, "created_at": {"$gte": six_months_ago}}},
        {"$group": {
            "_id": {"$substr": ["$created_at", 0, 7]},
            "count": {"$sum": 1},
            "avg_score": {"$avg": "$surfer_score.percentage"}
        }},
        {"$sort": {"_id": 1}}
    ]
    trend_raw = await db.articles.aggregate(trend_pipeline).to_list(12)
    trend = [{"month": t["_id"], "count": t["count"], "avg_score": round(t.get("avg_score") or 0)} for t in trend_raw]

    # Avg scores
    avg_pipeline = [
        {"$match": query},
        {"$group": {
            "_id": None,
            "avg_surfer": {"$avg": "$surfer_score.percentage"},
            "avg_seo": {"$avg": "$seo_score.percentage"},
            "total_words_estimate": {"$sum": "$target_length"}
        }}
    ]
    avg_result = await db.articles.aggregate(avg_pipeline).to_list(1)
    avg_surfer = round(avg_result[0].get("avg_surfer") or 0) if avg_result else 0
    avg_seo = round(avg_result[0].get("avg_seo") or 0) if avg_result else 0
    total_words = avg_result[0].get("total_words_estimate") or 0 if avg_result else 0

    return {
        "total_articles": total,
        "status_counts": status_counts,
        "score_buckets": score_buckets,
        "avg_surfer_score": avg_surfer,
        "avg_seo_score": avg_seo,
        "total_words_estimate": total_words,
        "top_performers": top_performers,
        "bottom_performers": bottom_performers,
        "language_distribution": lang_dist,
        "monthly_trend": trend
    }



