"""
Content Calendar Service
AI generates monthly/quarterly content plans based on Polish tax season calendar.
"""

import json
import logging
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

CALENDAR_SYSTEM_PROMPT = """Jestes ekspertem od planowania tresci SEO z zakresu ksiegowosci, rachunkowosci i podatkow w Polsce.
Znasz dokladnie polski kalendarz podatkowy i wszystkie wazne terminy:
- Styczen: PIT-4R, PIT-8AR, deklaracje roczne
- Luty: PIT roczny, korekty ZUS
- Marzec: CIT-8 roczny, bilans roczny
- Kwiecien: PIT-36/37 termin, JPK_V7M
- Maj: sprawozdania finansowe KRS
- Czerwiec: polrocze, zaliczki CIT
- Lipiec: wakacje od ZUS (maly ZUS+)
- Sierpien: przygotowanie do roku szkolnego, benefity
- Wrzesien: nowy rok podatkowy planowanie
- Pazdziernik: zmiany przepisow (Polski Lad)
- Listopad: planowanie podatkowe na nowy rok
- Grudzien: zamkniecie roku, inwentaryzacja

Odpowiadaj WYLACZNIE poprawnym JSON-em."""

CALENDAR_PROMPT = """Wygeneruj plan tresci na {period} ({months}) dla bloga ksiegowego.

Biezacy miesiac: {current_month}/{current_year}
Istniejace artykuly (nie powtarzaj tematow): {existing_titles}

Dla kazdego tygodnia zaproponuj 1-2 artykuly, dopasowane do:
- Aktualnych terminow podatkowych i obowiazkow
- Sezonowych tematow ksiegowych
- Wyszukiwan uzytkownikow (trending topics)

Odpowiedz WYLACZNIE w formacie JSON:
{{
  "plan_title": "Plan tresci na {period}",
  "period": "{period}",
  "items": [
    {{
      "week": 1,
      "month": "styczen",
      "year": 2026,
      "suggested_date": "2026-01-05",
      "title": "Tytul artykulu",
      "primary_keyword": "glowne slowo kluczowe",
      "secondary_keywords": ["slowo1", "slowo2"],
      "category": "vat|pit|cit|zus|kadry|ksiegowosc|inne",
      "priority": "wysoki|sredni|niski",
      "reason": "Dlaczego ten temat teraz - np. zblizajacy sie termin PIT",
      "estimated_length": 1500,
      "target_audience": "przedsiebiorcy|ksiegowi|kadry|wszyscy"
    }}
  ]
}}

Wygeneruj minimum 8 pozycji na miesiac, 20+ na kwartal."""


async def generate_content_calendar(period: str, current_month: int, current_year: int,
                                     existing_titles: list, emergent_key: str) -> dict:
    """Generate AI content calendar."""
    months_map = {
        "miesiac": "1 miesiac",
        "kwartal": "3 miesiace",
        "polrocze": "6 miesiecy"
    }
    
    month_names = ["styczen", "luty", "marzec", "kwiecien", "maj", "czerwiec",
                   "lipiec", "sierpien", "wrzesien", "pazdziernik", "listopad", "grudzien"]
    
    current_month_name = month_names[current_month - 1] if 1 <= current_month <= 12 else "styczen"
    
    titles_str = ", ".join(existing_titles[:20]) if existing_titles else "brak"
    
    prompt = CALENDAR_PROMPT.format(
        period=period,
        months=months_map.get(period, "1 miesiac"),
        current_month=current_month_name,
        current_year=current_year,
        existing_titles=titles_str
    )
    
    chat = LlmChat(
        api_key=emergent_key,
        session_id=f"calendar-{current_month}-{current_year}",
        system_message=CALENDAR_SYSTEM_PROMPT
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
