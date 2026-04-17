"""
Advanced SEO Scoring Engine for Polish accounting articles.
Scores articles on multiple dimensions and provides actionable recommendations.
Enhanced with E-E-A-T signals, URL optimization, content freshness, and stricter quality checks.
"""

import re
from typing import Dict, List
from datetime import datetime, timezone

# Polish stop words to ignore in keyword matching
POLISH_STOP_WORDS = {
    "w", "z", "i", "do", "na", "nie", "się", "o", "od", "za", "po", "ze",
    "dla", "jak", "co", "to", "jest", "są", "lub", "oraz", "a", "czy",
    "przy", "przez", "nad", "pod", "przed", "między", "bez", "ku",
    "roku", "r", "r.", "nr", "poz", "art", "ust", "pkt"
}


def _extract_keyword_terms(keyword: str) -> list:
    """Extract significant terms from a keyword phrase, ignoring stop words."""
    words = keyword.lower().split()
    return [w for w in words if w not in POLISH_STOP_WORDS and len(w) > 2]


def _flexible_keyword_count(text: str, keyword: str) -> tuple:
    """
    Count keyword occurrences with flexible matching.
    Returns (exact_count, flexible_count, matched_terms_ratio).
    """
    text_lower = text.lower()
    kw_lower = keyword.lower().strip()
    
    if not kw_lower:
        return (0, 0, 0.0)
    
    # 1. Exact match
    exact_count = text_lower.count(kw_lower)
    
    # 2. Flexible match - count how many significant terms appear
    terms = _extract_keyword_terms(kw_lower)
    if not terms:
        return (exact_count, exact_count, 1.0 if exact_count > 0 else 0.0)
    
    term_counts = {}
    for term in terms:
        pattern = re.compile(r'\b' + re.escape(term) + r'\w{0,3}\b', re.IGNORECASE)
        matches = pattern.findall(text_lower)
        term_counts[term] = len(matches)
    
    terms_present = sum(1 for t in terms if term_counts.get(t, 0) > 0)
    matched_ratio = terms_present / len(terms) if terms else 0.0
    
    if terms_present == len(terms):
        flexible_count = min(term_counts.get(t, 0) for t in terms)
    else:
        flexible_count = 0
    
    total_effective = exact_count + (flexible_count - exact_count) * 0.7 if flexible_count > exact_count else exact_count
    
    return (exact_count, max(int(total_effective), exact_count), matched_ratio)


def _keyword_in_text(text: str, keyword: str) -> bool:
    """Check if keyword (or its significant terms) appear in text."""
    text_lower = text.lower()
    kw_lower = keyword.lower().strip()
    
    if not kw_lower:
        return False
    
    if kw_lower in text_lower:
        return True
    
    terms = _extract_keyword_terms(kw_lower)
    if not terms:
        return False
    
    found = sum(1 for t in terms if t in text_lower)
    return found >= len(terms) * 0.7


def _count_legal_references(text: str) -> int:
    """Count legal references (art., ust., Dz.U., etc.) in text."""
    patterns = [
        r'art\.\s*\d+',
        r'ust\.\s*\d+',
        r'pkt\s*\d+',
        r'Dz\.?\s*U\.?\s*\d{4}',
        r'rozporządz\w+\s+(?:Ministr|MF|Minister)',
        r'ustaw[aąyę]\s+(?:z\s+dnia|o\s+)',
    ]
    count = 0
    for p in patterns:
        count += len(re.findall(p, text, re.IGNORECASE))
    return count


def _count_concrete_data(text: str) -> int:
    """Count concrete data points: amounts in PLN, percentages, dates."""
    patterns = [
        r'\d[\d\s,\.]*\s*(?:PLN|zł|złotych|złotych)',
        r'\d[\d,\.]*\s*%',
        r'\d{1,2}\s+(?:stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|września|października|listopada|grudnia)',
        r'(?:do|od)\s+\d{1,2}[\./]\d{1,2}[\./]\d{2,4}',
        r'\d{4}\s*r\.',
    ]
    count = 0
    for p in patterns:
        count += len(re.findall(p, text, re.IGNORECASE))
    return count


def _check_slug_quality(slug: str, keyword: str) -> tuple:
    """Check slug SEO quality. Returns (score, recommendations)."""
    recs = []
    score = 0
    if not slug:
        recs.append("Brak slugu URL")
        return (0, recs)
    
    # No Polish characters
    if re.search(r'[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', slug):
        recs.append("Slug URL zawiera polskie znaki diakrytyczne - usuń je")
    else:
        score += 1
    
    # Reasonable length
    if 10 <= len(slug) <= 75:
        score += 1
    else:
        recs.append(f"Slug URL ma {len(slug)} znaków (zalecane 10-75)")
    
    # Contains keyword terms
    kw_terms = _extract_keyword_terms(keyword)
    slug_lower = slug.lower()
    if kw_terms:
        found = sum(1 for t in kw_terms if t in slug_lower)
        if found >= len(kw_terms) * 0.5:
            score += 1
        else:
            recs.append("Slug URL powinien zawierać słowo kluczowe")
    
    return (score, recs)


def compute_seo_score(article: dict, primary_keyword: str, secondary_keywords: list) -> dict:
    """Compute advanced SEO score for an article."""
    scores = {}
    recommendations = []
    
    # Extract all text content
    all_text = ""
    headings_text = ""
    for section in (article.get("sections") or []):
        headings_text += " " + (section.get("heading") or "")
        all_text += " " + re.sub(r'<[^>]+>', '', section.get("content") or "")
        for sub in (section.get("subsections") or []):
            headings_text += " " + (sub.get("heading") or "")
            all_text += " " + re.sub(r'<[^>]+>', '', sub.get("content") or "")
    
    # Also count FAQ text
    faq_text = ""
    for faq in (article.get("faq") or []):
        faq_text += " " + (faq.get("question") or "") + " " + (faq.get("answer") or "")
    
    total_text = all_text + faq_text
    word_count = len(all_text.split())
    total_word_count = len(total_text.split())
    
    # Get HTML content for deeper analysis
    html_content = article.get("html_content") or ""
    if not html_content:
        for section in (article.get("sections") or []):
            html_content += (section.get("content") or "")
            for sub in section.get("subsections", []):
                html_content += sub.get("content") or ""

    # ============================================================
    # 1. Title analysis (max 12 pts)
    # ============================================================
    title = article.get("title") or ""
    title_score = 0
    if 30 <= len(title) <= 70:
        title_score += 4
    elif len(title) > 0:
        title_score += 2
        recommendations.append(f"Tytuł powinien mieć 30-70 znaków (obecnie: {len(title)})")
    else:
        recommendations.append("Brak tytułu artykułu")
    if _keyword_in_text(title, primary_keyword):
        title_score += 4
    else:
        recommendations.append("Tytuł nie zawiera słowa kluczowego głównego")
    # Power words / emotional triggers
    power_words = ["kompletny", "przewodnik", "najważniejsz", "krok po kroku", "jak", "co warto", "wszystko", "praktyczn", "aktualn"]
    if any(pw in title.lower() for pw in power_words):
        title_score += 2
    else:
        title_score += 1
        recommendations.append("Dodaj słowa mocy do tytułu (np. 'kompletny przewodnik', 'krok po kroku', 'najważniejsze')")
    # Year in title
    if re.search(r'202[4-9]|203\d', title):
        title_score += 2
    else:
        recommendations.append("Dodaj rok do tytułu (np. '2026') - zwiększa CTR i sygnalizuje aktualność")
    scores["title"] = {"score": title_score, "max": 12, "label": "Tytuł artykułu"}
    
    # ============================================================
    # 2. Meta description (max 8 pts)
    # ============================================================
    meta_desc = article.get("meta_description") or ""
    meta_score = 0
    if 120 <= len(meta_desc) <= 160:
        meta_score += 3
    elif 80 <= len(meta_desc) < 120:
        meta_score += 2
        recommendations.append(f"Meta opis powinien mieć 120-160 znaków (obecnie: {len(meta_desc)})")
    elif len(meta_desc) > 0:
        meta_score += 1
        recommendations.append(f"Meta opis za krótki lub za długi ({len(meta_desc)} znaków)")
    else:
        recommendations.append("Brak meta opisu")
    if _keyword_in_text(meta_desc, primary_keyword):
        meta_score += 3
    else:
        recommendations.append("Meta opis nie zawiera słowa kluczowego głównego")
    # CTA in meta description
    cta_words = ["dowiedz się", "sprawdź", "poznaj", "przeczytaj", "zobacz", "odkryj"]
    if any(cta in meta_desc.lower() for cta in cta_words):
        meta_score += 2
    else:
        recommendations.append("Dodaj wezwanie do działania w meta opisie (np. 'Dowiedz się...', 'Sprawdź...')")
    scores["meta_description"] = {"score": meta_score, "max": 8, "label": "Meta opis"}
    
    # ============================================================
    # 3. Content length (max 8 pts)
    # ============================================================
    length_score = 0
    if word_count >= 2000:
        length_score = 8
    elif word_count >= 1500:
        length_score = 6
    elif word_count >= 1000:
        length_score = 4
    elif word_count >= 500:
        length_score = 2
    else:
        recommendations.append(f"Artykuł zbyt krótki ({word_count} słów, zalecane min 1500)")
    scores["content_length"] = {"score": length_score, "max": 8, "label": f"Długość treści ({word_count} słów)"}
    
    # ============================================================
    # 4. Heading structure (max 12 pts)
    # ============================================================
    sections = article.get("sections", [])
    heading_score = 0
    h2_count = len(sections)
    h3_count = sum(len(s.get("subsections", [])) for s in sections)
    if h2_count >= 5:
        heading_score += 4
    elif h2_count >= 3:
        heading_score += 2
        recommendations.append(f"Dodaj więcej sekcji H2 (obecnie: {h2_count}, zalecane min 5)")
    elif h2_count >= 1:
        heading_score += 1
        recommendations.append(f"Za mało sekcji H2 ({h2_count}, zalecane min 5)")
    else:
        recommendations.append("Brak nagłówków H2")
    
    if h3_count >= 6:
        heading_score += 3
    elif h3_count >= 3:
        heading_score += 2
    else:
        recommendations.append(f"Za mało podsekcji H3 ({h3_count}, zalecane min 6)")
    
    keyword_in_h2 = sum(1 for s in sections if _keyword_in_text(s.get("heading") or "", primary_keyword))
    if keyword_in_h2 >= 2:
        heading_score += 3
    elif keyword_in_h2 >= 1:
        heading_score += 2
        recommendations.append("Słowo kluczowe powinno występować w co najmniej 2 nagłówkach H2")
    else:
        recommendations.append("Słowo kluczowe nie występuje w żadnym nagłówku H2")
    
    # Secondary keywords in headings
    sec_kw_in_headings = sum(1 for sk in secondary_keywords if _keyword_in_text(headings_text, sk))
    if sec_kw_in_headings >= 2:
        heading_score += 2
    elif sec_kw_in_headings >= 1:
        heading_score += 1
    else:
        if secondary_keywords:
            recommendations.append("Użyj słów kluczowych dodatkowych w nagłówkach H2/H3")
    scores["headings"] = {"score": heading_score, "max": 12, "label": "Struktura nagłówków"}
    
    # ============================================================
    # 5. Keyword density & placement (max 12 pts)
    # ============================================================
    kw_score = 0
    exact_count, flex_count, term_ratio = _flexible_keyword_count(all_text, primary_keyword)
    effective_count = flex_count if flex_count > 0 else exact_count
    density = (effective_count / max(word_count, 1)) * 100
    
    if 0.5 <= density <= 3.0:
        kw_score += 4
    elif density > 0:
        kw_score += 2
        if density < 0.5:
            recommendations.append(f"Gęstość słowa kluczowego zbyt niska: {density:.1f}% (zalecane 0.5-3%)")
        else:
            recommendations.append(f"Gęstość słowa kluczowego zbyt wysoka: {density:.1f}% (zalecane 0.5-3%)")
    elif term_ratio >= 0.5:
        kw_score += 1
        recommendations.append("Słowa kluczowe występują osobno - spróbuj użyć pełnej frazy kluczowej")
    else:
        recommendations.append("Słowo kluczowe nie występuje w treści!")
    
    first_words = " ".join(all_text.split()[:150]).lower()
    if _keyword_in_text(first_words, primary_keyword):
        kw_score += 4
    else:
        recommendations.append("Słowo kluczowe powinno pojawić się w pierwszych 150 słowach")
    
    secondary_found = sum(1 for sk in secondary_keywords if _keyword_in_text(all_text, sk))
    if len(secondary_keywords) > 0:
        if secondary_found >= len(secondary_keywords) * 0.7:
            kw_score += 4
        elif secondary_found >= len(secondary_keywords) * 0.4:
            kw_score += 2
        elif secondary_found > 0:
            kw_score += 1
        else:
            recommendations.append("Brak słów kluczowych dodatkowych w treści")
    else:
        kw_score += 2
    scores["keywords"] = {"score": kw_score, "max": 12, "label": f"Słowa kluczowe (gęstość: {density:.1f}%)"}
    
    # ============================================================
    # 6. TOC & Anchors (max 6 pts)
    # ============================================================
    toc = article.get("toc", [])
    toc_score = 0
    if len(toc) >= 5:
        toc_score += 3
    elif len(toc) >= 3:
        toc_score += 2
    elif len(toc) >= 1:
        toc_score += 1
    else:
        recommendations.append("Brak spisu treści")
    
    section_anchors = set(s.get("anchor", "") for s in sections)
    toc_anchors = set(t.get("anchor", "") for t in toc)
    if section_anchors and toc_anchors and len(section_anchors & toc_anchors) >= len(section_anchors) * 0.8:
        toc_score += 3
    elif len(toc_anchors & section_anchors) > 0:
        toc_score += 2
    else:
        recommendations.append("Anchory w spisie treści nie pasują do sekcji artykułu")
    scores["toc"] = {"score": toc_score, "max": 6, "label": "Spis treści i anchory"}
    
    # ============================================================
    # 7. FAQ (max 8 pts)
    # ============================================================
    faq = article.get("faq", [])
    faq_score = 0
    if len(faq) >= 6:
        faq_score += 3
    elif len(faq) >= 4:
        faq_score += 2
    elif len(faq) >= 1:
        faq_score += 1
    else:
        recommendations.append("Brak sekcji FAQ (Google Featured Snippets)")
    
    if faq:
        avg_answer_len = sum(len(f.get("answer") or "".split()) for f in faq) / len(faq)
        if avg_answer_len >= 40:
            faq_score += 3
        elif avg_answer_len >= 25:
            faq_score += 2
        elif avg_answer_len >= 15:
            faq_score += 1
        else:
            recommendations.append("Odpowiedzi w FAQ powinny mieć min. 40 słów - Google preferuje rozbudowane odpowiedzi")
        # FAQ with keyword
        faq_with_kw = sum(1 for f in faq if _keyword_in_text(f.get("question") or "", primary_keyword))
        if faq_with_kw >= 1:
            faq_score += 2
        else:
            recommendations.append("Co najmniej 1 pytanie FAQ powinno zawierać słowo kluczowe")
    scores["faq"] = {"score": faq_score, "max": 8, "label": "Sekcja FAQ"}
    
    # ============================================================
    # 8. Internal links (max 4 pts)
    # ============================================================
    links = article.get("internal_link_suggestions", [])
    link_score = 0
    if len(links) >= 3:
        link_score += 4
    elif len(links) >= 1:
        link_score += 2
    else:
        recommendations.append("Brak sugestii linkowania wewnętrznego")
    scores["internal_links"] = {"score": link_score, "max": 4, "label": "Linkowanie wewnętrzne"}
    
    # ============================================================
    # 9. Sources & E-E-A-T (max 10 pts) - ENHANCED
    # ============================================================
    sources = article.get("sources", [])
    source_score = 0
    credible_domains = [".gov.pl", "sejm.gov.pl", "podatki.gov.pl", "isap.sejm.gov.pl",
                        "pip.gov.pl", "zus.pl", "gus.gov.pl", "nbp.pl", "mf.gov.pl"]
    
    # Sources count
    if len(sources) >= 4:
        source_score += 3
    elif len(sources) >= 2:
        source_score += 2
    elif len(sources) >= 1:
        source_score += 1
    else:
        recommendations.append("Brak źródeł - E-E-A-T wymaga wiarygodnych odniesień")
    
    # Credible sources
    credible_count = sum(1 for s in sources if any(d in s.get("url", "") for d in credible_domains))
    if credible_count >= 3:
        source_score += 3
    elif credible_count >= 2:
        source_score += 2
    elif credible_count >= 1:
        source_score += 1
    else:
        recommendations.append("Dodaj min. 2 źródła z oficjalnych stron (.gov.pl) - wzmacnia E-E-A-T")
    
    # Legal references in text (art., ust., Dz.U.)
    legal_refs = _count_legal_references(all_text)
    if legal_refs >= 5:
        source_score += 2
    elif legal_refs >= 2:
        source_score += 1
    else:
        recommendations.append("Cytuj konkretne przepisy prawne (art., ust., Dz.U.) - wzmacnia autorytatywność")
    
    # Concrete data (amounts, dates, percentages)
    concrete_data = _count_concrete_data(all_text)
    if concrete_data >= 6:
        source_score += 2
    elif concrete_data >= 3:
        source_score += 1
    else:
        recommendations.append("Dodaj konkretne dane: kwoty w PLN, terminy, procenty - buduje wiarygodność")
    
    scores["sources_eeat"] = {"score": source_score, "max": 10, "label": "Źródła i E-E-A-T"}
    
    # ============================================================
    # 10. URL/Slug optimization (max 4 pts)
    # ============================================================
    slug = article.get("slug", "")
    slug_score, slug_recs = _check_slug_quality(slug, primary_keyword)
    slug_pts = min(slug_score, 4)
    recommendations.extend(slug_recs)
    scores["slug"] = {"score": slug_pts, "max": 4, "label": "Optymalizacja URL/slug"}
    
    # ============================================================
    # 11. Content formatting & richness (max 8 pts)
    # ============================================================
    format_score = 0
    
    # Lists in content
    list_count = html_content.count('<ul') + html_content.count('<ol')
    if list_count >= 3:
        format_score += 2
    elif list_count >= 1:
        format_score += 1
    else:
        recommendations.append("Dodaj listy punktowane/numerowane - ułatwiają skanowanie treści")
    
    # Bold/emphasis
    bold_count = html_content.count('<strong') + html_content.count('<b>')
    if bold_count >= 5:
        format_score += 2
    elif bold_count >= 2:
        format_score += 1
    else:
        recommendations.append("Użyj pogrubienia (<strong>) dla kluczowych pojęć i fraz")
    
    # Paragraph variety (not walls of text)
    p_count = html_content.count('<p')
    if p_count >= 10:
        format_score += 2
    elif p_count >= 5:
        format_score += 1
    else:
        recommendations.append("Podziel tekst na więcej akapitów (min. 10) - poprawia czytelność")
    
    # Links in content
    link_count = html_content.count('<a ')
    if link_count >= 3:
        format_score += 2
    elif link_count >= 1:
        format_score += 1
    else:
        recommendations.append("Dodaj linki w treści (wewnętrzne i zewnętrzne)")
    
    scores["formatting"] = {"score": format_score, "max": 8, "label": "Formatowanie treści"}
    
    # ============================================================
    # 12. Readability (max 6 pts)
    # ============================================================
    sentences = re.split(r'[.!?]+', all_text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
    if sentences:
        avg_sentence_len = sum(len(s.split()) for s in sentences) / len(sentences)
    else:
        avg_sentence_len = 0
    readability_score = 0
    if 10 <= avg_sentence_len <= 20:
        readability_score += 3
    elif 8 <= avg_sentence_len <= 25:
        readability_score += 2
    elif avg_sentence_len > 0:
        readability_score += 1
        recommendations.append(f"Średnia długość zdania: {avg_sentence_len:.0f} słów (zalecane 10-20)")
    
    # Paragraph length variety
    paragraphs = re.split(r'\n\n|\r\n\r\n', all_text)
    paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 20]
    if paragraphs:
        avg_para_len = sum(len(p.split()) for p in paragraphs) / len(paragraphs)
        if 40 <= avg_para_len <= 120:
            readability_score += 2
        elif avg_para_len > 0:
            readability_score += 1
    
    # Transition words (Polish)
    transitions = ["ponadto", "jednakże", "natomiast", "w związku z", "dlatego", "oprócz tego",
                    "w rezultacie", "co więcej", "z kolei", "w szczególności", "przede wszystkim",
                    "w konsekwencji", "niemniej jednak", "warto zauważyć", "należy podkreślić"]
    trans_found = sum(1 for t in transitions if t in all_text.lower())
    if trans_found >= 5:
        readability_score += 1
    scores["readability"] = {"score": readability_score, "max": 6, "label": f"Czytelność (śr. {avg_sentence_len:.0f} słów/zdanie)"}
    
    # ============================================================
    # 13. Content freshness (max 3 pts)
    # ============================================================
    freshness_score = 0
    created = article.get("created_at", "")
    updated = article.get("updated_at", "")
    
    # Year mentions in content
    current_year = datetime.now(timezone.utc).year
    if str(current_year) in all_text or str(current_year) in title:
        freshness_score += 2
    elif str(current_year - 1) in all_text:
        freshness_score += 1
        recommendations.append(f"Zaktualizuj odniesienia do roku {current_year} - sygnalizuje aktualność treści")
    else:
        recommendations.append(f"Dodaj odniesienia do aktualnego roku ({current_year}) w treści i tytule")
    
    # Was updated recently?
    if updated and created and updated != created:
        freshness_score += 1
    scores["freshness"] = {"score": freshness_score, "max": 3, "label": "Aktualność treści"}
    
    # ============================================================
    # 14. Meta title (separate from main title) (max 3 pts)
    # ============================================================
    meta_title = article.get("meta_title") or ""
    mt_score = 0
    if meta_title:
        if 30 <= len(meta_title) <= 60:
            mt_score += 1
        else:
            recommendations.append(f"Meta tytuł: {len(meta_title)} znaków (zalecane 30-60)")
        if _keyword_in_text(meta_title, primary_keyword):
            mt_score += 1
        else:
            recommendations.append("Meta tytuł nie zawiera słowa kluczowego")
        if meta_title != title:
            mt_score += 1
        else:
            recommendations.append("Meta tytuł powinien różnić się od tytułu artykułu (lepsza optymalizacja SERP)")
    else:
        recommendations.append("Brak meta tytułu SEO")
    scores["meta_title"] = {"score": mt_score, "max": 3, "label": "Meta tytuł"}
    
    # ============================================================
    # Total
    # ============================================================
    total_score = sum(s["score"] for s in scores.values())
    total_max = sum(s["max"] for s in scores.values())
    percentage = round((total_score / total_max) * 100) if total_max > 0 else 0
    
    return {
        "total_score": total_score,
        "total_max": total_max,
        "percentage": percentage,
        "breakdown": scores,
        "recommendations": recommendations,
        "word_count": word_count,
        "total_word_count": total_word_count
    }
