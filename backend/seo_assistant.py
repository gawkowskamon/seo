"""
SEO Assistant Service using OpenAI GPT-5.2 via Emergent integrations.
Provides structured SEO improvement suggestions + interactive chat for Polish accounting articles.
"""

import json
import re
import os
import logging
import uuid
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

SEO_ASSISTANT_SYSTEM_PROMPT = """Jestes ekspertem SEO specjalizujacym sie w tresciach ksiegowych, podatkowych i rachunkowych w Polsce.
Twoja rola to analiza artykulow blogowych i dostarczanie KONKRETNYCH, WYKONALNYCH sugestii poprawy SEO.

ZASADY:
- Odpowiadaj ZAWSZE po polsku.
- Dawaj KONKRETNE propozycje zmian (nie ogolniki).
- Uwzgledniaj polskie przepisy podatkowe i ksiegowe.
- Priorytetyzuj sugestie wg wplywu na SEO.
- Odpowiadaj WYLACZNIE poprawnym JSON-em bez zadnych dodatkowych komentarzy, markdown ani formatowania.
"""

ANALYZE_PROMPT = """Przeanalizuj ponizszy artykul blogowy pod katem SEO i zaproponuj konkretne poprawki.

TEMAT: {topic}
SLOWO KLUCZOWE GLOWNE: {primary_keyword}
SLOWA KLUCZOWE DODATKOWE: {secondary_keywords}

META TYTUL: {meta_title}
META OPIS: {meta_description}

AKTUALNY WYNIK SEO: {seo_score}%

TRESC ARTYKULU (HTML):
{html_content_truncated}

FAQ:
{faq_summary}

LICZBA SEKCJI H2: {h2_count}
LICZBA SLOW: {word_count}

Odpowiedz WYLACZNIE w formacie JSON (bez markdown, bez ```json):
{{
  "assistant_message": "Krotkie podsumowanie analizy (2-3 zdania po polsku)",
  "suggestions": [
    {{
      "id": "unikalny-id-sugestii",
      "title": "Krotki tytul sugestii",
      "category": "meta|headings|content|keywords|faq|links|readability",
      "impact": "high|medium|low",
      "rationale": "Dlaczego ta zmiana jest wazna dla SEO",
      "current_value": "Obecna wartosc (jesli dotyczy)",
      "proposed_value": "Proponowana nowa wartosc",
      "apply_target": "meta_title|meta_description|html_content|faq|none"
    }}
  ]
}}

WAZNE:
- Zaproponuj 5-10 sugestii, posortowanych od najwazniejszych.
- Dla kazdej sugestii z apply_target != "none", podaj konkretna proposed_value gotowa do zastosowania.
- Dla meta_title: max 60 znakow.
- Dla meta_description: 120-160 znakow.
- Sugestie dotyczace tresci HTML powinny byc konkretnymi akapitami/zdaniami do dodania lub modyfikacji.
- Dla FAQ: proposed_value to JSON string z obiektem {{"question": "...", "answer": "..."}}.
"""

CHAT_PROMPT = """Kontekst artykulu:
- Temat: {topic}
- Slowo kluczowe: {primary_keyword}
- Wynik SEO: {seo_score}%
- Meta tytul: {meta_title}
- Dlugosc: {word_count} slow

Historia rozmowy:
{conversation_history}

Wiadomosc uzytkownika: {user_message}

Odpowiedz WYLACZNIE w formacie JSON (bez markdown, bez ```json):
{{
  "assistant_message": "Twoja odpowiedz po polsku, konkretna i merytoryczna",
  "suggestions": [
    {{
      "id": "unikalny-id",
      "title": "Tytul sugestii",
      "category": "meta|headings|content|keywords|faq|links|readability",
      "impact": "high|medium|low",
      "rationale": "Uzasadnienie",
      "current_value": "",
      "proposed_value": "Konkretna wartosc do zastosowania",
      "apply_target": "meta_title|meta_description|html_content|faq|none"
    }}
  ]
}}

Jesli pytanie nie wymaga sugestii, zwroc pusta liste suggestions.
Zawsze odpowiadaj po polsku, konkretnie i merytorycznie.
"""


def _truncate_html(html: str, max_chars: int = 6000) -> str:
    """Truncate HTML content for prompt context."""
    if not html:
        return ""
    # Strip tags for analysis, keep structure indicators
    clean = re.sub(r'<[^>]+>', ' ', html)
    clean = re.sub(r'\s+', ' ', clean).strip()
    if len(clean) > max_chars:
        return clean[:max_chars] + "... [skrocono]"
    return clean


def _build_html_from_sections(article: dict) -> str:
    """Build HTML content from article sections."""
    html = ""
    for section in article.get("sections", []):
        html += f"<h2>{section.get('heading', '')}</h2>\n{section.get('content', '')}\n"
        for sub in section.get("subsections", []):
            html += f"<h3>{sub.get('heading', '')}</h3>\n{sub.get('content', '')}\n"
    return html


def _clean_json_response(response: str) -> dict:
    """Clean and parse JSON from LLM response."""
    clean = response.strip()
    if clean.startswith("```"):
        clean = re.sub(r'^```(?:json)?\s*', '', clean)
        clean = re.sub(r'\s*```$', '', clean)
    return json.loads(clean)


async def analyze_article_seo(article: dict) -> dict:
    """Generate SEO improvement suggestions for an article."""
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise ValueError("EMERGENT_LLM_KEY not configured")
    
    # Build context
    html_content = article.get("html_content") or _build_html_from_sections(article)
    faq_summary = ""
    for faq in article.get("faq", [])[:6]:
        faq_summary += f"Q: {faq.get('question', '')}\nA: {faq.get('answer', '')[:100]}...\n\n"
    
    seo_score = article.get("seo_score", {})
    sections = article.get("sections", [])
    
    word_count = seo_score.get("word_count", 0)
    if word_count == 0:
        text = re.sub(r'<[^>]+>', ' ', html_content)
        word_count = len(text.split())
    
    prompt = ANALYZE_PROMPT.format(
        topic=article.get("topic", ""),
        primary_keyword=article.get("primary_keyword", ""),
        secondary_keywords=json.dumps(article.get("secondary_keywords", []), ensure_ascii=False),
        meta_title=article.get("meta_title", ""),
        meta_description=article.get("meta_description", ""),
        seo_score=seo_score.get("percentage", 0),
        html_content_truncated=_truncate_html(html_content),
        faq_summary=faq_summary or "Brak FAQ",
        h2_count=len(sections),
        word_count=word_count
    )
    
    session_id = f"seo-assistant-{article.get('id', 'unknown')}-{uuid.uuid4().hex[:6]}"
    
    chat = LlmChat(
        api_key=api_key,
        session_id=session_id,
        system_message=SEO_ASSISTANT_SYSTEM_PROMPT
    )
    chat.with_model("openai", "gpt-5.2")
    
    response = await chat.send_message(UserMessage(text=prompt))
    result = _clean_json_response(response)
    
    # Validate structure
    if "suggestions" not in result:
        result["suggestions"] = []
    if "assistant_message" not in result:
        result["assistant_message"] = "Analiza zakonczona."
    
    # Ensure each suggestion has an id
    for s in result["suggestions"]:
        if "id" not in s or not s["id"]:
            s["id"] = f"sug-{uuid.uuid4().hex[:8]}"
    
    return result


async def chat_about_seo(article: dict, user_message: str, conversation_history: list) -> dict:
    """Interactive chat about SEO improvements for an article."""
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise ValueError("EMERGENT_LLM_KEY not configured")
    
    # Format conversation history
    history_text = ""
    for msg in (conversation_history or [])[-6:]:
        role = "Uzytkownik" if msg.get("role") == "user" else "Asystent"
        history_text += f"{role}: {msg.get('content', '')}\n"
    
    if not history_text:
        history_text = "(Brak wczesniejszej rozmowy)"
    
    seo_score = article.get("seo_score", {})
    html_content = article.get("html_content") or _build_html_from_sections(article)
    text = re.sub(r'<[^>]+>', ' ', html_content)
    word_count = seo_score.get("word_count", len(text.split()))
    
    prompt = CHAT_PROMPT.format(
        topic=article.get("topic", ""),
        primary_keyword=article.get("primary_keyword", ""),
        seo_score=seo_score.get("percentage", 0),
        meta_title=article.get("meta_title", ""),
        word_count=word_count,
        conversation_history=history_text,
        user_message=user_message
    )
    
    session_id = f"seo-chat-{article.get('id', 'unknown')}-{uuid.uuid4().hex[:6]}"
    
    chat = LlmChat(
        api_key=api_key,
        session_id=session_id,
        system_message=SEO_ASSISTANT_SYSTEM_PROMPT
    )
    chat.with_model("openai", "gpt-5.2")
    
    response = await chat.send_message(UserMessage(text=prompt))
    result = _clean_json_response(response)
    
    # Validate
    if "suggestions" not in result:
        result["suggestions"] = []
    if "assistant_message" not in result:
        result["assistant_message"] = "Przepraszam, nie udalo sie przetworzyc odpowiedzi."
    
    for s in result["suggestions"]:
        if "id" not in s or not s["id"]:
            s["id"] = f"sug-{uuid.uuid4().hex[:8]}"
    
    return result
