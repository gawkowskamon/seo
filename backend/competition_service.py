"""
Competition Analysis Service
Compare your article with a competitor's article for SEO advantages.
"""

import json
import logging
import httpx
from bs4 import BeautifulSoup
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

COMPETITION_PROMPT = """Porownaj dwa artykuly pod katem SEO. Znajdz przewagi i slabosci.

TWOJ ARTYKUL:
Tytul: {my_title}
Slowo kluczowe: {my_keyword}
Liczba slow: {my_word_count}
Sekcje: {my_sections}
Meta tytul: {my_meta_title}
Meta opis: {my_meta_desc}

ARTYKUL KONKURENCJI:
URL: {comp_url}
Tytul: {comp_title}
Liczba slow: {comp_word_count}
Naglowki: {comp_headings}
Meta opis: {comp_meta_desc}
Fragment tresci: {comp_content}

Odpowiedz WYLACZNIE JSON-em:
{{
  "overall_verdict": "lepszy|porownywlny|gorszy",
  "my_score": 72,
  "competitor_score": 68,
  "strengths": [
    {{
      "aspect": "Nazwa aspektu SEO",
      "description": "Dlaczego twoj artykul jest lepszy w tym aspekcie"
    }}
  ],
  "weaknesses": [
    {{
      "aspect": "Nazwa aspektu SEO",
      "description": "Dlaczego konkurent jest lepszy",
      "recommendation": "Co zrobic zeby poprawic"
    }}
  ],
  "content_gaps": [
    {{
      "topic": "Temat brakujacy w twoim artykule",
      "importance": "wysoka|srednia",
      "suggestion": "Jak uzupelnic te luki"
    }}
  ],
  "keyword_comparison": {{
    "shared_keywords": ["wspolne slowa"],
    "competitor_unique": ["slowa tylko u konkurenta"],
    "your_opportunities": ["slowa ktore powinienes dodac"]
  }},
  "action_plan": [
    {{
      "priority": 1,
      "action": "Konkretne dzialanie do podjecia",
      "expected_impact": "Szacowany wplyw"
    }}
  ],
  "summary": "2-3 zdania podsumowania analizy"
}}"""


async def scrape_competitor(url: str) -> dict:
    """Scrape competitor article."""
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, verify=False) as client:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.find("title")
        title_text = title.get_text(strip=True) if title else ""

        meta_desc = ""
        md_tag = soup.find("meta", attrs={"name": "description"})
        if md_tag:
            meta_desc = md_tag.get("content", "")

        headings = []
        for tag in ["h1", "h2", "h3"]:
            for h in soup.find_all(tag):
                headings.append(f"{tag.upper()}: {h.get_text(strip=True)}")

        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        article = soup.find("article") or soup.find("main") or soup.find("body")
        text = article.get_text(separator=" ", strip=True) if article else ""

        return {
            "url": url,
            "title": title_text,
            "meta_desc": meta_desc,
            "headings": headings[:15],
            "word_count": len(text.split()),
            "content_sample": text[:3000]
        }


async def analyze_competition(my_article: dict, competitor_url: str, emergent_key: str) -> dict:
    """Compare your article against a competitor."""
    comp = await scrape_competitor(competitor_url)

    sections_str = ", ".join([s.get("heading", "") for s in my_article.get("sections", [])][:10]) or "brak"

    prompt = COMPETITION_PROMPT.format(
        my_title=my_article.get("title", ""),
        my_keyword=my_article.get("primary_keyword", ""),
        my_word_count=len(str(my_article.get("sections", "")).split()),
        my_sections=sections_str,
        my_meta_title=my_article.get("meta_title", ""),
        my_meta_desc=my_article.get("meta_description", ""),
        comp_url=comp["url"],
        comp_title=comp["title"],
        comp_word_count=comp["word_count"],
        comp_headings="\n".join(comp["headings"][:10]) or "brak",
        comp_meta_desc=comp["meta_desc"],
        comp_content=comp["content_sample"][:1500]
    )

    chat = LlmChat(
        api_key=emergent_key,
        session_id=f"competition-{competitor_url[:30]}",
        system_message="Jestes ekspertem SEO analizujacym konkurencje. Odpowiadaj WYLACZNIE JSON-em."
    )
    chat.with_model("openai", "gpt-4.1-mini")

    response = await chat.send_message(UserMessage(text=prompt))
    text = response.strip() if isinstance(response, str) else str(response)
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    result = json.loads(text)
    result["competitor_data"] = {
        "url": comp["url"],
        "title": comp["title"],
        "word_count": comp["word_count"],
        "headings_count": len(comp["headings"])
    }
    return result
