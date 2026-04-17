"""
SurferSEO-style service: AI-simulated SERP analysis, NLP terms, and content benchmarks.
"""
import json
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def analyze_serp(keyword: str, language: str = "pl") -> dict:
    """
    AI-simulated SERP analysis for a keyword.
    Returns benchmarks based on simulated top-10 Google results.
    """
    from llm_helper import llm_chat

    prompt = f"""Jesteś ekspertem SEO. Symuluj analizę TOP 10 wyników Google dla frazy: "{keyword}" (język: {language}).

Wygeneruj realistyczne dane benchmarkowe oparte na analizie konkurencji. Odpowiedz WYŁĄCZNIE JSON:

{{
    "keyword": "{keyword}",
    "search_intent": "informacyjny" lub "transakcyjny" lub "nawigacyjny" lub "komercyjny",
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
        {{"term": "termin powiązany", "importance": "wysoka", "recommended_count": 3, "category": "główny"}},
        {{"term": "inny termin", "importance": "średnia", "recommended_count": 2, "category": "wspierający"}},
        {{"term": "long tail", "importance": "niska", "recommended_count": 1, "category": "semantyczny"}}
    ],
    "top_competitors": [
        {{
            "position": 1,
            "title": "Tytuł artykułu konkurenta",
            "url": "https://example.pl/artykul",
            "word_count": 2500,
            "h2_count": 8,
            "score_estimate": 85
        }}
    ],
    "content_outline_suggestion": [
        "H2: Sugerowany nagłówek 1",
        "H2: Sugerowany nagłówek 2",
        "H3: Podsekcja",
        "H2: Sugerowany nagłówek 3"
    ],
    "questions_to_answer": [
        "Pytanie które warto uwzględnić w artykule 1?",
        "Pytanie 2?",
        "Pytanie 3?"
    ]
}}

WAŻNE:
- Wygeneruj 20-30 NLP terms (terminy powiązane semantycznie z frazą kluczową)
- NLP terms powinny zawierać: synonimy, frazy LSI, powiązane pojęcia, pytania
- Każdy NLP term ma importance: "wysoka" (5-8 terminów), "średnia" (8-12), "niska" (5-10)
- Wygeneruj 5-8 konkurentów w top_competitors
- Benchmarki powinny być realistyczne dla polskiego rynku
- content_outline_suggestion: 8-12 sugerowanych nagłówków
- questions_to_answer: 5-8 pytań"""

    response = await llm_chat(
        prompt,
        system_message="Jesteś zaawansowanym narzędziem SEO typu SurferSEO. Analizujesz SERP i generujesz benchmarki dla optymalizacji treści. Odpowiadaj WYŁĄCZNIE poprawnym JSON-em.",
        session_id=f"surfer-serp-{hash(keyword) % 100000}",
        timeout=180,
    )

    clean = response.strip()
    if clean.startswith("```"):
        clean = re.sub(r'^```(?:json)?\s*', '', clean)
        clean = re.sub(r'\s*```$', '', clean)

    data = json.loads(clean)
    return data


def compute_surfer_score(article: dict, surfer_data: dict) -> dict:
    """
    Compute SurferSEO-style score comparing article against SERP benchmarks.
    Returns a detailed score with per-metric breakdown.
    """
    benchmarks = surfer_data.get("benchmarks", {})
    nlp_terms = surfer_data.get("nlp_terms", [])
    primary_keyword = article.get("primary_keyword") or ""

    # Extract article content
    sections = article.get("sections") or []
    html_content = article.get("html_content") or ""
    all_text = ""
    headings_text = ""
    for section in sections:
        headings_text += " " + (section.get("heading") or "")
        all_text += " " + re.sub(r'<[^>]+>', '', section.get("content") or "")
        for sub in (section.get("subsections") or []):
            headings_text += " " + (sub.get("heading") or "")
            all_text += " " + re.sub(r'<[^>]+>', '', sub.get("content") or "")

    faq_text = ""
    for faq in (article.get("faq") or []):
        faq_text += " " + (faq.get("question") or "") + " " + (faq.get("answer") or "")
    total_text = (all_text + " " + faq_text).lower()

    if not html_content:
        for section in sections:
            html_content += (section.get("content") or "")
            for sub in (section.get("subsections") or []):
                html_content += (sub.get("content") or "")

    word_count = len(all_text.split())
    h2_count = len(sections)
    h3_count = sum(len(s.get("subsections", [])) for s in sections)
    p_count = max(html_content.count('<p'), 1)
    img_count = html_content.count('<img')
    list_count = html_content.count('<ul') + html_content.count('<ol')
    bold_count = html_content.count('<strong') + html_content.count('<b>')
    internal_links = html_content.count('<a ')
    faq_count = len(article.get("faq", []))

    metrics = {}

    # --- Word Count (20 pts) ---
    wc_bench = benchmarks.get("word_count", {})
    wc_rec = wc_bench.get("recommended", 2000)
    wc_min = wc_bench.get("min", 1000)
    wc_max = wc_bench.get("max", 4000)
    if wc_min <= word_count <= wc_max:
        wc_ratio = min(word_count / wc_rec, 1.0) if word_count <= wc_rec else max(1.0 - (word_count - wc_rec) / wc_rec * 0.3, 0.6)
        wc_score = round(20 * wc_ratio)
    elif word_count < wc_min:
        wc_score = round(20 * (word_count / wc_min) * 0.6)
    else:
        wc_score = round(20 * 0.5)
    metrics["word_count"] = {
        "score": min(wc_score, 20), "max": 20,
        "label": "Liczba słów", "value": word_count,
        "benchmark": {"min": wc_min, "max": wc_max, "recommended": wc_rec},
        "status": "ok" if wc_min <= word_count <= wc_max else ("low" if word_count < wc_min else "high"),
    }

    # --- Headings (15 pts) ---
    h_bench = benchmarks.get("headings", {})
    h2_avg = h_bench.get("h2_avg", 7)
    h3_avg = h_bench.get("h3_avg", 8)
    h2_pts = min(round(8 * min(h2_count / max(h2_avg, 1), 1.2)), 8)
    h3_pts = min(round(7 * min(h3_count / max(h3_avg, 1), 1.2)), 7)
    metrics["headings"] = {
        "score": h2_pts + h3_pts, "max": 15,
        "label": "Nagłówki", "value": {"h2": h2_count, "h3": h3_count},
        "benchmark": {"h2_avg": h2_avg, "h3_avg": h3_avg},
        "status": "ok" if h2_count >= h2_avg * 0.7 else "low",
    }

    # --- Paragraphs (5 pts) ---
    p_bench = benchmarks.get("paragraphs", {})
    p_avg = p_bench.get("avg", 25)
    p_pts = min(round(5 * min(p_count / max(p_avg, 1), 1.2)), 5)
    metrics["paragraphs"] = {
        "score": p_pts, "max": 5, "label": "Akapity", "value": p_count,
        "benchmark": {"avg": p_avg}, "status": "ok" if p_count >= p_avg * 0.6 else "low",
    }

    # --- Images (5 pts) ---
    img_bench = benchmarks.get("images", {})
    img_avg = img_bench.get("avg", 4)
    img_pts = min(round(5 * min(img_count / max(img_avg, 1), 1.2)), 5)
    metrics["images"] = {
        "score": img_pts, "max": 5, "label": "Obrazy", "value": img_count,
        "benchmark": {"avg": img_avg}, "status": "ok" if img_count >= img_avg * 0.5 else "low",
    }

    # --- NLP Terms (30 pts) --- THE KEY SURFER METRIC
    nlp_results = []
    nlp_found = 0
    for term_data in nlp_terms:
        term = term_data.get("term", "").lower()
        recommended = term_data.get("recommended_count", 2)
        importance = term_data.get("importance", "średnia")
        count = len(re.findall(re.escape(term), total_text))
        used = count > 0
        if used:
            nlp_found += 1
        nlp_results.append({
            "term": term_data.get("term", ""),
            "count": count,
            "recommended": recommended,
            "importance": importance,
            "used": used,
            "status": "ok" if count >= recommended else ("partial" if count > 0 else "missing"),
        })

    nlp_total = len(nlp_terms) if nlp_terms else 1
    nlp_ratio = nlp_found / nlp_total
    nlp_pts = round(30 * nlp_ratio)
    metrics["nlp_terms"] = {
        "score": min(nlp_pts, 30), "max": 30,
        "label": "Terminy NLP", "value": f"{nlp_found}/{nlp_total}",
        "terms": nlp_results,
        "status": "ok" if nlp_ratio >= 0.7 else ("partial" if nlp_ratio >= 0.4 else "low"),
    }

    # --- Bold phrases (5 pts) ---
    b_bench = benchmarks.get("bold_phrases", {})
    b_avg = b_bench.get("avg", 10)
    b_pts = min(round(5 * min(bold_count / max(b_avg, 1), 1.2)), 5)
    metrics["bold"] = {
        "score": b_pts, "max": 5, "label": "Pogrubienia", "value": bold_count,
        "benchmark": {"avg": b_avg}, "status": "ok" if bold_count >= b_avg * 0.5 else "low",
    }

    # --- Lists (5 pts) ---
    l_bench = benchmarks.get("lists", {})
    l_avg = l_bench.get("avg", 3)
    l_pts = min(round(5 * min(list_count / max(l_avg, 1), 1.2)), 5)
    metrics["lists"] = {
        "score": l_pts, "max": 5, "label": "Listy", "value": list_count,
        "benchmark": {"avg": l_avg}, "status": "ok" if list_count >= l_avg * 0.5 else "low",
    }

    # --- FAQ (5 pts) ---
    faq_bench = benchmarks.get("faq_questions", {})
    faq_avg = faq_bench.get("avg", 5)
    faq_pts = min(round(5 * min(faq_count / max(faq_avg, 1), 1.2)), 5)
    metrics["faq"] = {
        "score": faq_pts, "max": 5, "label": "FAQ", "value": faq_count,
        "benchmark": {"avg": faq_avg}, "status": "ok" if faq_count >= faq_avg * 0.5 else "low",
    }

    # --- Title & Meta (10 pts) ---
    title = article.get("title") or ""
    meta_desc = article.get("meta_description") or ""
    tm_pts = 0
    kw_lower = primary_keyword.lower()
    if kw_lower and kw_lower in title.lower():
        tm_pts += 3
    if 30 <= len(title) <= 65:
        tm_pts += 2
    if kw_lower and kw_lower in meta_desc.lower():
        tm_pts += 2
    if 120 <= len(meta_desc) <= 160:
        tm_pts += 2
    if re.search(r'202[4-9]', title):
        tm_pts += 1
    metrics["title_meta"] = {
        "score": min(tm_pts, 10), "max": 10,
        "label": "Tytuł i Meta",
        "value": {"title_len": len(title), "meta_len": len(meta_desc)},
        "status": "ok" if tm_pts >= 7 else ("partial" if tm_pts >= 4 else "low"),
    }

    # --- TOTAL ---
    total = sum(m["score"] for m in metrics.values())
    total_max = sum(m["max"] for m in metrics.values())
    percentage = round((total / total_max) * 100) if total_max > 0 else 0

    return {
        "total_score": total,
        "total_max": total_max,
        "percentage": percentage,
        "metrics": metrics,
        "word_count": word_count,
        "grade": _get_grade(percentage),
    }


def _get_grade(pct: int) -> dict:
    if pct >= 80:
        return {"label": "Doskonały", "color": "#22c55e"}
    elif pct >= 60:
        return {"label": "Dobry", "color": "#f59e0b"}
    elif pct >= 40:
        return {"label": "Do poprawy", "color": "#f97316"}
    else:
        return {"label": "Słaby", "color": "#ef4444"}
