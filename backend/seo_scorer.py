"""
Advanced SEO Scoring Engine for Polish accounting articles.
Scores articles on multiple dimensions and provides actionable recommendations.
"""

import re
from typing import Dict, List


def compute_seo_score(article: dict, primary_keyword: str, secondary_keywords: list) -> dict:
    """Compute advanced SEO score for an article."""
    scores = {}
    recommendations = []
    
    # Extract all text content
    all_text = ""
    for section in article.get("sections", []):
        all_text += " " + re.sub(r'<[^>]+>', '', section.get("content", ""))
        for sub in section.get("subsections", []):
            all_text += " " + re.sub(r'<[^>]+>', '', sub.get("content", ""))
    
    # Also count FAQ text
    faq_text = ""
    for faq in article.get("faq", []):
        faq_text += " " + faq.get("question", "") + " " + faq.get("answer", "")
    
    total_text = all_text + faq_text
    word_count = len(all_text.split())
    total_word_count = len(total_text.split())
    
    # 1. Title analysis (max 15 pts)
    title = article.get("title", "")
    title_score = 0
    if 30 <= len(title) <= 70:
        title_score += 5
    elif len(title) > 0:
        title_score += 2
        recommendations.append(f"Tytuł powinien mieć 30-70 znaków (obecnie: {len(title)})")
    else:
        recommendations.append("Brak tytułu artykułu")
    if primary_keyword.lower() in title.lower():
        title_score += 5
    else:
        recommendations.append("Tytuł nie zawiera słowa kluczowego głównego")
    if len(title) > 0:
        title_score += 5
    scores["title"] = {"score": title_score, "max": 15, "label": "Tytuł artykułu"}
    
    # 2. Meta description (max 10 pts)
    meta_desc = article.get("meta_description", "")
    meta_score = 0
    if 120 <= len(meta_desc) <= 160:
        meta_score += 5
    elif 80 <= len(meta_desc) < 120:
        meta_score += 3
        recommendations.append(f"Meta opis powinien mieć 120-160 znaków (obecnie: {len(meta_desc)})")
    elif len(meta_desc) > 0:
        meta_score += 1
        recommendations.append(f"Meta opis za krótki lub za długi ({len(meta_desc)} znaków)")
    else:
        recommendations.append("Brak meta opisu")
    if primary_keyword.lower() in meta_desc.lower():
        meta_score += 5
    else:
        recommendations.append("Meta opis nie zawiera słowa kluczowego głównego")
    scores["meta_description"] = {"score": meta_score, "max": 10, "label": "Meta opis"}
    
    # 3. Content length (max 10 pts)
    length_score = 0
    if word_count >= 1500:
        length_score = 10
    elif word_count >= 1000:
        length_score = 7
    elif word_count >= 500:
        length_score = 4
    elif word_count >= 200:
        length_score = 2
    else:
        recommendations.append(f"Artykuł zbyt krótki ({word_count} słów, zalecane min 1000)")
    scores["content_length"] = {"score": length_score, "max": 10, "label": f"Długość treści ({word_count} słów)"}
    
    # 4. Heading structure (max 15 pts)
    sections = article.get("sections", [])
    heading_score = 0
    h2_count = len(sections)
    h3_count = sum(len(s.get("subsections", [])) for s in sections)
    if h2_count >= 5:
        heading_score += 5
    elif h2_count >= 3:
        heading_score += 3
        recommendations.append(f"Dodaj więcej sekcji H2 (obecnie: {h2_count}, zalecane min 5)")
    elif h2_count >= 1:
        heading_score += 1
        recommendations.append(f"Za mało sekcji H2 ({h2_count}, zalecane min 5)")
    else:
        recommendations.append("Brak nagłówków H2")
    
    if h3_count >= 6:
        heading_score += 5
    elif h3_count >= 3:
        heading_score += 3
    else:
        recommendations.append(f"Za mało podsekcji H3 ({h3_count}, zalecane min 6)")
    
    keyword_in_h2 = any(primary_keyword.lower() in s.get("heading", "").lower() for s in sections)
    if keyword_in_h2:
        heading_score += 5
    else:
        recommendations.append("Słowo kluczowe nie występuje w żadnym nagłówku H2")
    scores["headings"] = {"score": heading_score, "max": 15, "label": "Struktura nagłówków"}
    
    # 5. Keyword density & placement (max 15 pts)
    kw_score = 0
    text_lower = all_text.lower()
    kw_lower = primary_keyword.lower()
    kw_count = text_lower.count(kw_lower)
    density = (kw_count / max(word_count, 1)) * 100
    
    if 0.5 <= density <= 3.0:
        kw_score += 5
    elif density > 0:
        kw_score += 2
        if density < 0.5:
            recommendations.append(f"Gęstość słowa kluczowego zbyt niska: {density:.1f}% (zalecane 0.5-3%)")
        else:
            recommendations.append(f"Gęstość słowa kluczowego zbyt wysoka: {density:.1f}% (zalecane 0.5-3%)")
    else:
        recommendations.append("Słowo kluczowe nie występuje w treści!")
    
    first_words = " ".join(all_text.split()[:150]).lower()
    if kw_lower in first_words:
        kw_score += 5
    else:
        recommendations.append("Słowo kluczowe powinno pojawić się w pierwszych 150 słowach")
    
    secondary_found = sum(1 for sk in secondary_keywords if sk.lower() in text_lower)
    if secondary_found >= len(secondary_keywords) * 0.5:
        kw_score += 5
    elif secondary_found > 0:
        kw_score += 3
    else:
        recommendations.append("Brak słów kluczowych dodatkowych w treści")
    scores["keywords"] = {"score": kw_score, "max": 15, "label": f"Słowa kluczowe (gęstość: {density:.1f}%)"}
    
    # 6. TOC & Anchors (max 10 pts)
    toc = article.get("toc", [])
    toc_score = 0
    if len(toc) >= 5:
        toc_score += 5
    elif len(toc) >= 3:
        toc_score += 3
    elif len(toc) >= 1:
        toc_score += 1
    else:
        recommendations.append("Brak spisu treści")
    
    section_anchors = set(s.get("anchor", "") for s in sections)
    toc_anchors = set(t.get("anchor", "") for t in toc)
    if section_anchors and toc_anchors and len(section_anchors & toc_anchors) >= len(section_anchors) * 0.8:
        toc_score += 5
    elif len(toc_anchors & section_anchors) > 0:
        toc_score += 3
    else:
        recommendations.append("Anchory w spisie treści nie pasują do sekcji artykułu")
    scores["toc"] = {"score": toc_score, "max": 10, "label": "Spis treści i anchory"}
    
    # 7. FAQ (max 10 pts)
    faq = article.get("faq", [])
    faq_score = 0
    if len(faq) >= 6:
        faq_score += 5
    elif len(faq) >= 4:
        faq_score += 3
    elif len(faq) >= 1:
        faq_score += 1
    else:
        recommendations.append("Brak sekcji FAQ")
    
    if faq:
        avg_answer_len = sum(len(f.get("answer", "").split()) for f in faq) / len(faq)
        if avg_answer_len >= 25:
            faq_score += 5
        elif avg_answer_len >= 15:
            faq_score += 3
        else:
            recommendations.append("Odpowiedzi w FAQ powinny być bardziej rozbudowane (min 25 słów)")
    scores["faq"] = {"score": faq_score, "max": 10, "label": "Sekcja FAQ"}
    
    # 8. Internal links (max 5 pts)
    links = article.get("internal_link_suggestions", [])
    link_score = 0
    if len(links) >= 3:
        link_score += 5
    elif len(links) >= 1:
        link_score += 3
    else:
        recommendations.append("Brak sugestii linkowania wewnętrznego")
    scores["internal_links"] = {"score": link_score, "max": 5, "label": "Linkowanie wewnętrzne"}
    
    # 9. Sources (max 5 pts)
    sources = article.get("sources", [])
    source_score = 0
    credible_domains = [".gov.pl", "sejm.gov.pl", "podatki.gov.pl", "isap.sejm.gov.pl",
                        "pip.gov.pl", "zus.pl", "gus.gov.pl", "nbp.pl", "mf.gov.pl"]
    if len(sources) >= 3:
        source_score += 3
    elif len(sources) >= 1:
        source_score += 1
    else:
        recommendations.append("Brak źródeł - dodaj wiarygodne odniesienia")
    credible_count = sum(1 for s in sources if any(d in s.get("url", "") for d in credible_domains))
    if credible_count >= 2:
        source_score += 2
    elif credible_count >= 1:
        source_score += 1
    else:
        recommendations.append("Dodaj źródła z oficjalnych stron rządowych (.gov.pl)")
    scores["sources"] = {"score": source_score, "max": 5, "label": "Źródła"}
    
    # 10. Readability (max 5 pts)
    sentences = re.split(r'[.!?]+', all_text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
    if sentences:
        avg_sentence_len = sum(len(s.split()) for s in sentences) / len(sentences)
    else:
        avg_sentence_len = 0
    readability_score = 0
    if 10 <= avg_sentence_len <= 20:
        readability_score = 5
    elif 8 <= avg_sentence_len <= 25:
        readability_score = 3
    elif avg_sentence_len > 0:
        readability_score = 1
        recommendations.append(f"Średnia długość zdania: {avg_sentence_len:.0f} słów (zalecane 10-20)")
    scores["readability"] = {"score": readability_score, "max": 5, "label": f"Czytelność (śr. {avg_sentence_len:.0f} słów/zdanie)"}
    
    # Total
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
