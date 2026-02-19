"""
Article Series Generator.
Generates an outline for a multi-part article series, then individual articles.
"""

import json
import re
import os
import uuid
import logging
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

SERIES_OUTLINE_PROMPT = """Jestes ekspertem SEO i strategiem tresci specjalizujacym sie w polskich tresciach ksiegowych i podatkowych.

Zaplanuj serie {num_parts} artykulow blogowych na temat: "{topic}"

Glowne slowo kluczowe serii: "{primary_keyword}"

Dodatkowy kontekst/zrodla od uzytkownika:
{source_context}

Odpowiedz WYLACZNIE w formacie JSON (bez markdown, bez ```json):
{{
  "series_title": "Tytul calej serii artykulow",
  "series_description": "Opis serii (2-3 zdania)",
  "target_audience": "Dla kogo jest ta seria",
  "parts": [
    {{
      "part_number": 1,
      "title": "Tytul artykulu",
      "primary_keyword": "Glowne slowo kluczowe tego artykulu",
      "secondary_keywords": ["slowo1", "slowo2", "slowo3"],
      "summary": "Krotki opis tego co bedzie w artykule (2-3 zdania)",
      "key_points": ["Punkt 1", "Punkt 2", "Punkt 3"],
      "suggested_template": "standard|poradnik|case_study|porownanie|checklist|pillar|nowelizacja|kalkulator",
      "estimated_length": 1500,
      "internal_links_to": [2, 3]
    }}
  ],
  "seo_strategy": "Krotki opis strategii SEO dla calej serii (linkowanie wewnetrzne, klastry tematyczne)"
}}

WAZNE:
- Kazdy artykul powinien byc samodzielny ale tworzyc spojnosc z seria
- Zaproponuj odpowiedni szablon (template) dla kazdego artykulu
- Slowa kluczowe powinny sie uzupelniac (klaster tematyczny)
- Artykuly powinny linkowac do siebie nawzajem
- Dostosuj dlugosc do zlozonosci tematu
"""

SOURCE_CONTEXT_PROMPT = """Dodatkowe zrodla i kontekst podany przez uzytkownika:

{sources}

Wykorzystaj te informacje do stworzenia bardziej precyzyjnych i merytorycznych artykulow.
Odwoluj sie do konkretnych przepisow, terminow i kwot jesli sa podane w zrodlach.
"""


async def generate_series_outline(topic: str, primary_keyword: str, num_parts: int = 4, 
                                   source_text: str = "") -> dict:
    """Generate a multi-part article series outline."""
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise ValueError("EMERGENT_LLM_KEY not configured")
    
    source_context = "(Brak dodatkowych zrodel)"
    if source_text and source_text.strip():
        source_context = SOURCE_CONTEXT_PROMPT.format(sources=source_text[:3000])
    
    prompt = SERIES_OUTLINE_PROMPT.format(
        topic=topic,
        primary_keyword=primary_keyword,
        num_parts=num_parts,
        source_context=source_context
    )
    
    session_id = f"series-{uuid.uuid4().hex[:8]}"
    
    chat = LlmChat(
        api_key=api_key,
        session_id=session_id,
        system_message="Jestes ekspertem SEO planujacym serie artykulow dla polskiego biura rachunkowego. Odpowiadaj WYLACZNIE poprawnym JSON-em."
    )
    chat.with_model("openai", "gpt-5.2")
    
    response = await chat.send_message(UserMessage(text=prompt))
    
    # Clean and parse JSON
    clean = response.strip()
    if clean.startswith("```"):
        clean = re.sub(r'^```(?:json)?\s*', '', clean)
        clean = re.sub(r'\s*```$', '', clean)
    
    result = json.loads(clean)
    
    # Add series ID
    result["id"] = str(uuid.uuid4())
    
    return result
