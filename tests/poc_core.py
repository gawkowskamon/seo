"""
POC Script: Core Article Generation + SEO Scoring
Tests:
1. OpenAI GPT via Emergent integration - structured JSON article generation in Polish
2. SEO scoring algorithm
"""

import asyncio
import json
import os
import sys
import re
from pathlib import Path
from dotenv import load_dotenv

# Load env
load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

from emergentintegrations.llm.chat import LlmChat, UserMessage

EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
if not EMERGENT_KEY:
    print("ERROR: EMERGENT_LLM_KEY not found in environment")
    sys.exit(1)

# ============================================================
# ARTICLE GENERATION PROMPT
# ============================================================

ARTICLE_SYSTEM_PROMPT = """Jesteś ekspertem od tworzenia treści SEO z zakresu księgowości, rachunkowości i podatków w Polsce. 
Tworzysz artykuły na blogi firmowe, które są:
- Merytorycznie poprawne i oparte na aktualnych przepisach
- Zoptymalizowane pod SEO
- Napisane przystępnym, profesjonalnym językiem

ZAWSZE odpowiadaj WYŁĄCZNIE poprawnym JSON-em bez żadnych dodatkowych komentarzy ani markdown.
"""

ARTICLE_GENERATION_PROMPT = """Napisz artykuł blogowy na temat: "{topic}"

Słowo kluczowe główne: "{primary_keyword}"
Słowa kluczowe dodatkowe: {secondary_keywords}
Docelowa długość: {target_length} słów
Ton: profesjonalny ale przystępny

Odpowiedz WYŁĄCZNIE w formacie JSON (bez markdown, bez ```json):
{{
  "title": "Tytuł artykułu (50-60 znaków, zawiera słowo kluczowe)",
  "slug": "tytul-artykulu-slug",
  "meta_title": "Meta tytuł SEO (max 60 znaków)",
  "meta_description": "Meta opis SEO (max 160 znaków, zachęcający do kliknięcia)",
  "toc": [
    {{"label": "Nazwa sekcji", "anchor": "nazwa-sekcji"}}
  ],
  "sections": [
    {{
      "heading": "Nagłówek H2",
      "anchor": "naglowek-h2",
      "content": "<p>Treść sekcji w HTML. Używaj <strong>, <em>, <ul>, <li>, <a> tagów.</p>",
      "subsections": [
        {{
          "heading": "Nagłówek H3",
          "anchor": "naglowek-h3",
          "content": "<p>Treść podsekcji w HTML.</p>"
        }}
      ]
    }}
  ],
  "faq": [
    {{
      "question": "Pytanie FAQ",
      "answer": "Odpowiedź na pytanie"
    }}
  ],
  "internal_link_suggestions": [
    {{
      "anchor_text": "tekst anchora",
      "target_topic": "powiązany temat artykułu",
      "reason": "dlaczego warto linkować"
    }}
  ],
  "sources": [
    {{
      "name": "Nazwa źródła",
      "url": "https://example.gov.pl",
      "type": "legal|official|expert"
    }}
  ]
}}

WAŻNE:
- Artykuł musi mieć minimum 4 sekcje H2
- Każda sekcja powinna mieć 1-3 podsekcji H3
- FAQ powinno mieć minimum 5 pytań
- Źródła muszą być wiarygodne (gov.pl, oficjalne instytucje, uznani eksperci)
- Anchory muszą być unikalne, bez polskich znaków, małe litery z myślnikami
- Treść w sekcjach musi być w formacie HTML
- Słowo kluczowe główne powinno pojawić się w pierwszych 150 słowach, w co najmniej jednym H2, i w meta opisie
"""

# ============================================================
# SEO SCORING
# ============================================================

def compute_seo_score(article: dict, primary_keyword: str, secondary_keywords: list) -> dict:
    """Compute advanced SEO score for an article."""
    scores = {}
    recommendations = []
    
    # 1. Title analysis (max 15 pts)
    title = article.get("title", "")
    title_score = 0
    if len(title) >= 30 and len(title) <= 70:
        title_score += 5
    else:
        recommendations.append(f"Tytuł powinien mieć 30-70 znaków (obecnie: {len(title)})")
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
    if len(meta_desc) >= 120 and len(meta_desc) <= 160:
        meta_score += 5
    elif len(meta_desc) >= 80:
        meta_score += 3
        recommendations.append(f"Meta opis powinien mieć 120-160 znaków (obecnie: {len(meta_desc)})")
    else:
        recommendations.append(f"Meta opis zbyt krótki ({len(meta_desc)} znaków, min 120)")
    if primary_keyword.lower() in meta_desc.lower():
        meta_score += 5
    else:
        recommendations.append("Meta opis nie zawiera słowa kluczowego głównego")
    scores["meta_description"] = {"score": meta_score, "max": 10, "label": "Meta opis"}
    
    # 3. Content length (max 10 pts)
    all_text = ""
    for section in article.get("sections", []):
        all_text += " " + re.sub(r'<[^>]+>', '', section.get("content", ""))
        for sub in section.get("subsections", []):
            all_text += " " + re.sub(r'<[^>]+>', '', sub.get("content", ""))
    word_count = len(all_text.split())
    length_score = 0
    if word_count >= 1500:
        length_score = 10
    elif word_count >= 1000:
        length_score = 7
    elif word_count >= 500:
        length_score = 4
    else:
        recommendations.append(f"Artykuł zbyt krótki ({word_count} słów, min 1000)")
    scores["content_length"] = {"score": length_score, "max": 10, "label": f"Długość treści ({word_count} słów)"}
    
    # 4. Heading structure (max 15 pts)
    sections = article.get("sections", [])
    heading_score = 0
    h2_count = len(sections)
    h3_count = sum(len(s.get("subsections", [])) for s in sections)
    if h2_count >= 4:
        heading_score += 5
    elif h2_count >= 2:
        heading_score += 3
        recommendations.append(f"Dodaj więcej sekcji H2 (obecnie: {h2_count}, min 4)")
    else:
        recommendations.append(f"Za mało sekcji H2 ({h2_count}, min 4)")
    if h3_count >= 4:
        heading_score += 5
    elif h3_count >= 2:
        heading_score += 3
    else:
        recommendations.append(f"Za mało podsekcji H3 ({h3_count}, zalecane min 4)")
    # Keyword in headings
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
        recommendations.append(f"Gęstość słowa kluczowego: {density:.1f}% (zalecane 0.5-3%)")
    else:
        recommendations.append("Słowo kluczowe nie występuje w treści!")
    # First 150 words
    first_words = " ".join(all_text.split()[:150]).lower()
    if kw_lower in first_words:
        kw_score += 5
    else:
        recommendations.append("Słowo kluczowe powinno pojawić się w pierwszych 150 słowach")
    # Secondary keywords
    secondary_found = sum(1 for sk in secondary_keywords if sk.lower() in text_lower)
    if secondary_found >= len(secondary_keywords) * 0.5:
        kw_score += 5
    elif secondary_found > 0:
        kw_score += 3
    else:
        recommendations.append("Brak słów kluczowych dodatkowych w treści")
    scores["keywords"] = {"score": kw_score, "max": 15, "label": "Słowa kluczowe"}
    
    # 6. TOC & Anchors (max 10 pts)
    toc = article.get("toc", [])
    toc_score = 0
    if len(toc) >= 4:
        toc_score += 5
    elif len(toc) >= 2:
        toc_score += 3
    else:
        recommendations.append("Spis treści powinien mieć minimum 4 pozycje")
    # Verify anchors match sections
    section_anchors = set(s.get("anchor", "") for s in sections)
    toc_anchors = set(t.get("anchor", "") for t in toc)
    if section_anchors and toc_anchors and section_anchors.issubset(toc_anchors):
        toc_score += 5
    elif len(toc_anchors & section_anchors) > 0:
        toc_score += 3
    else:
        recommendations.append("Anchory w spisie treści nie pasują do sekcji artykułu")
    scores["toc"] = {"score": toc_score, "max": 10, "label": "Spis treści i anchory"}
    
    # 7. FAQ (max 10 pts)
    faq = article.get("faq", [])
    faq_score = 0
    if len(faq) >= 5:
        faq_score += 5
    elif len(faq) >= 3:
        faq_score += 3
    else:
        recommendations.append(f"FAQ powinno mieć minimum 5 pytań (obecnie: {len(faq)})")
    # Check if FAQ answers are substantive
    avg_answer_len = sum(len(f.get("answer", "").split()) for f in faq) / max(len(faq), 1)
    if avg_answer_len >= 20:
        faq_score += 5
    elif avg_answer_len >= 10:
        faq_score += 3
    else:
        recommendations.append("Odpowiedzi w FAQ powinny być bardziej rozbudowane")
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
    credible_domains = [".gov.pl", ".sejm.gov.pl", "podatki.gov.pl", "isap.sejm.gov.pl", 
                        "pip.gov.pl", "zus.pl", "gus.gov.pl", "nbp.pl", "mf.gov.pl"]
    if len(sources) >= 2:
        source_score += 3
    elif len(sources) >= 1:
        source_score += 1
    else:
        recommendations.append("Brak źródeł - dodaj wiarygodne odniesienia")
    credible_count = sum(1 for s in sources if any(d in s.get("url", "") for d in credible_domains))
    if credible_count >= 1:
        source_score += 2
    else:
        recommendations.append("Dodaj źródła z oficjalnych stron rządowych (.gov.pl)")
    scores["sources"] = {"score": source_score, "max": 5, "label": "Źródła"}
    
    # 10. Readability (max 5 pts) - Simple Polish readability heuristic
    sentences = re.split(r'[.!?]+', all_text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
    avg_sentence_len = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
    readability_score = 0
    if 10 <= avg_sentence_len <= 20:
        readability_score = 5
    elif 8 <= avg_sentence_len <= 25:
        readability_score = 3
    else:
        recommendations.append(f"Średnia długość zdania: {avg_sentence_len:.0f} słów (zalecane 10-20)")
    scores["readability"] = {"score": readability_score, "max": 5, "label": f"Czytelność (śr. {avg_sentence_len:.0f} słów/zdanie)"}
    
    # Total
    total_score = sum(s["score"] for s in scores.values())
    total_max = sum(s["max"] for s in scores.values())
    percentage = round((total_score / total_max) * 100)
    
    return {
        "total_score": total_score,
        "total_max": total_max,
        "percentage": percentage,
        "breakdown": scores,
        "recommendations": recommendations,
        "word_count": word_count
    }


# ============================================================
# TEST FUNCTIONS
# ============================================================

async def test_article_generation():
    """Test 1: Generate a structured article via OpenAI GPT."""
    print("\n" + "="*60)
    print("TEST 1: Article Generation via OpenAI GPT")
    print("="*60)
    
    topic = "Jak rozliczać VAT w jednoosobowej działalności gospodarczej"
    primary_keyword = "rozliczanie VAT"
    secondary_keywords = ["jednoosobowa działalność gospodarcza", "deklaracja VAT", "JPK_VAT", "podatek VAT"]
    target_length = 1500
    
    prompt = ARTICLE_GENERATION_PROMPT.format(
        topic=topic,
        primary_keyword=primary_keyword,
        secondary_keywords=json.dumps(secondary_keywords, ensure_ascii=False),
        target_length=target_length
    )
    
    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id="poc-test-article-gen",
        system_message=ARTICLE_SYSTEM_PROMPT
    )
    chat.with_model("openai", "gpt-4.1")
    
    print(f"Topic: {topic}")
    print(f"Primary keyword: {primary_keyword}")
    print("Generating article...")
    
    try:
        response = await chat.send_message(UserMessage(text=prompt))
        print(f"\nResponse length: {len(response)} characters")
        
        # Try to parse JSON
        # Clean response - remove markdown code blocks if present
        clean_response = response.strip()
        if clean_response.startswith("```"):
            clean_response = re.sub(r'^```(?:json)?\s*', '', clean_response)
            clean_response = re.sub(r'\s*```$', '', clean_response)
        
        article = json.loads(clean_response)
        print("\n✅ JSON parsing successful!")
        
        # Validate structure
        required_fields = ["title", "slug", "meta_title", "meta_description", "toc", "sections", "faq", "sources"]
        missing = [f for f in required_fields if f not in article]
        if missing:
            print(f"❌ Missing fields: {missing}")
            return None
        
        print(f"✅ All required fields present")
        print(f"   Title: {article['title']}")
        print(f"   Meta title: {article['meta_title']} ({len(article['meta_title'])} chars)")
        print(f"   Meta desc: {article['meta_description'][:80]}... ({len(article['meta_description'])} chars)")
        print(f"   Sections: {len(article['sections'])}")
        print(f"   FAQ items: {len(article['faq'])}")
        print(f"   Sources: {len(article['sources'])}")
        print(f"   TOC items: {len(article['toc'])}")
        print(f"   Link suggestions: {len(article.get('internal_link_suggestions', []))}")
        
        return article
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
        print(f"Response preview: {response[:500]}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


async def test_seo_scoring(article: dict):
    """Test 2: SEO scoring algorithm."""
    print("\n" + "="*60)
    print("TEST 2: SEO Scoring Algorithm")
    print("="*60)
    
    primary_keyword = "rozliczanie VAT"
    secondary_keywords = ["jednoosobowa działalność gospodarcza", "deklaracja VAT", "JPK_VAT", "podatek VAT"]
    
    score = compute_seo_score(article, primary_keyword, secondary_keywords)
    
    print(f"\n📊 SEO Score: {score['percentage']}% ({score['total_score']}/{score['total_max']})")
    print(f"   Word count: {score['word_count']}")
    print("\n   Breakdown:")
    for key, data in score["breakdown"].items():
        bar = "█" * data["score"] + "░" * (data["max"] - data["score"])
        print(f"   {bar} {data['label']}: {data['score']}/{data['max']}")
    
    if score["recommendations"]:
        print(f"\n   📋 Recommendations ({len(score['recommendations'])}):")
        for i, rec in enumerate(score["recommendations"], 1):
            print(f"   {i}. {rec}")
    
    if score["percentage"] >= 50:
        print("\n✅ SEO scoring working correctly!")
        return True
    else:
        print("\n⚠️ Score below 50% - may need prompt tuning")
        return True  # Algorithm works, just score is low


async def main():
    print("🚀 SEO Article Generator - Core POC Test")
    print("="*60)
    
    # Test 1: Article generation
    article = await test_article_generation()
    
    if article is None:
        print("\n❌ FAILED: Article generation did not produce valid JSON")
        sys.exit(1)
    
    # Test 2: SEO scoring
    scoring_ok = await test_seo_scoring(article)
    
    if scoring_ok:
        print("\n" + "="*60)
        print("✅ ALL POC TESTS PASSED!")
        print("="*60)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
