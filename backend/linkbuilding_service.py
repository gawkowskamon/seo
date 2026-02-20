"""
Internal Linkbuilding Service
AI analyzes all articles and suggests internal links between them.
"""

import json
import logging
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

LINKBUILDING_PROMPT = """Przeanalizuj ponizsze artykuly na blogu ksiegowym i zasugeruj linkowanie wewnetrzne.

Aktualny artykul (do ktorego szukamy linkow):
Tytul: {current_title}
Slowo kluczowe: {current_keyword}
Sekcje: {current_sections}

Inne artykuly na blogu:
{other_articles}

Zasugeruj linki wewnetrzne w obu kierunkach:
1. Z aktualnego artykulu DO innych (outgoing)
2. Z innych artykulow DO aktualnego (incoming)

Odpowiedz WYLACZNIE JSON-em:
{{
  "outgoing_links": [
    {{
      "target_article_id": "id artykulu docelowego",
      "target_title": "tytul artykulu docelowego",
      "anchor_text": "naturalny tekst anchora po polsku",
      "context_sentence": "Przykladowe zdanie z linkiem: <a href>anchor</a> w kontekscie",
      "insert_after_section": "nazwa sekcji po ktorej wstawic",
      "relevance": "wysoka|srednia"
    }}
  ],
  "incoming_links": [
    {{
      "source_article_id": "id artykulu zrodlowego",
      "source_title": "tytul artykulu zrodlowego",
      "anchor_text": "naturalny tekst anchora",
      "context_sentence": "Przykladowe zdanie z linkiem w kontekscie",
      "relevance": "wysoka|srednia"
    }}
  ],
  "summary": "Krotkie podsumowanie strategii linkowania"
}}"""


async def analyze_internal_links(current_article: dict, all_articles: list, emergent_key: str) -> dict:
    """Analyze and suggest internal links for an article."""
    # Build sections summary
    sections = []
    for s in current_article.get("sections", []):
        sections.append(s.get("heading", ""))
        for sub in s.get("subsections", []):
            sections.append(f"  - {sub.get('heading', '')}")
    sections_str = "\n".join(sections) if sections else "brak"
    
    # Build other articles summary
    other = []
    for a in all_articles:
        if a.get("id") == current_article.get("id"):
            continue
        other.append(f"- ID: {a['id']} | Tytul: {a.get('title', '')} | Slowo kluczowe: {a.get('primary_keyword', '')}")
    
    if not other:
        return {"outgoing_links": [], "incoming_links": [], "summary": "Brak innych artykulow do linkowania."}
    
    other_str = "\n".join(other[:15])
    
    prompt = LINKBUILDING_PROMPT.format(
        current_title=current_article.get("title", ""),
        current_keyword=current_article.get("primary_keyword", ""),
        current_sections=sections_str,
        other_articles=other_str
    )
    
    chat = LlmChat(
        api_key=emergent_key,
        session_id=f"linkbuild-{current_article.get('id', 'unknown')}",
        system_message="Jestes ekspertem SEO specjalizujacym sie w linkowaniu wewnetrznym. Odpowiadaj WYLACZNIE JSON-em."
    )
    chat.with_model("openai", "gpt-4.1-mini")
    
    response = await chat.send_message(UserMessage(text=prompt))
    
    text = response.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    
    result = json.loads(text)
    return result
