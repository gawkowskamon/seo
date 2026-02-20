"""
Auto-Update Service
Monitors legal/tax changes and suggests article updates.
"""

import json
import logging
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

UPDATE_PROMPT = """Przeanalizuj ponizsze artykuly na blogu ksiegowym i sprawdz czy wymagaja aktualizacji.

Dzisiejsza data: {today}
Biezacy rok podatkowy: {current_year}

Artykuly do sprawdzenia:
{articles_data}

Sprawdz:
1. Czy stawki podatkowe sa aktualne (PIT, CIT, VAT, ZUS na {current_year})?
2. Czy przepisy wspomniane w artykulach sie nie zmienily?
3. Czy terminy podatkowe sa prawidlowe?
4. Czy artykul nie jest przedawniony (starsze niz 12 miesiecy)?
5. Czy sa nowe regulacje ktore warto dodac?

Odpowiedz WYLACZNIE JSON-em:
{{
  "articles_needing_update": [
    {{
      "article_id": "id artykulu",
      "article_title": "tytul",
      "urgency": "pilny|zalecany|opcjonalny",
      "reasons": [
        {{
          "type": "zmiana_przepisow|nieaktualne_stawki|nowa_regulacja|przedawniony|blad_merytoryczny",
          "description": "Szczegolowy opis co trzeba zaktualizowac",
          "specific_change": "Np. stawka ZUS wzrosla z X do Y"
        }}
      ],
      "suggested_changes": [
        "Konkretna sugestia zmiany w artykule"
      ]
    }}
  ],
  "up_to_date_articles": [
    {{
      "article_id": "id",
      "article_title": "tytul",
      "note": "Krotka informacja ze artykul jest aktualny"
    }}
  ],
  "legal_updates_summary": [
    {{
      "area": "Obszar prawa (np. PIT, VAT, ZUS)",
      "change": "Opis zmiany",
      "effective_date": "Data wejscia w zycie",
      "affected_articles_count": 2
    }}
  ],
  "summary": "Podsumowanie stanu artykulow"
}}"""


async def check_articles_for_updates(articles: list, emergent_key: str) -> dict:
    """Check if articles need updating based on legal/tax changes."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    articles_data = []
    for a in articles[:15]:
        sections_text = ""
        for s in a.get("sections", [])[:3]:
            sections_text += f"  {s.get('heading', '')}: {str(s.get('content', ''))[:200]}\n"

        articles_data.append(
            f"ID: {a['id']}\n"
            f"Tytul: {a.get('title', '')}\n"
            f"Slowo kluczowe: {a.get('primary_keyword', '')}\n"
            f"Data utworzenia: {a.get('created_at', 'nieznana')}\n"
            f"Sekcje:\n{sections_text}\n---"
        )

    prompt = UPDATE_PROMPT.format(
        today=now.strftime("%Y-%m-%d"),
        current_year=now.year,
        articles_data="\n".join(articles_data)
    )

    chat = LlmChat(api_key=emergent_key)
    chat = chat.with_model("gpt-4.1-mini")
    chat = chat.with_system_message(
        "Jestes ekspertem od polskiego prawa podatkowego i ksiegowosci. "
        "Znasz najnowsze przepisy, stawki i terminy na 2026 rok. "
        "Odpowiadaj WYLACZNIE JSON-em."
    )

    response = await chat.send_async(UserMessage(text=prompt))
    text = response if isinstance(response, str) else response.text
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    result = json.loads(text)
    return result
