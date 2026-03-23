"""
Article Generation Service using OpenAI GPT via Emergent integrations.
Generates SEO-optimized articles in Polish about accounting topics.
Enhanced for content reliability: legal references, concrete data, E-E-A-T compliance.
"""

import json
import re
import os
import logging
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

ARTICLE_SYSTEM_PROMPT = """Jesteś EKSPERTEM-PRAKTYKIEM od tworzenia treści SEO z zakresu księgowości, rachunkowości i podatków w Polsce.
Masz wieloletnie doświadczenie w biurze rachunkowym. Tworzysz artykuły na blogi firmowe, które są:

1. MERYTORYCZNIE BEZBŁĘDNE:
   - Cytuj KONKRETNE przepisy: art., ust., pkt z Dz.U. (np. "zgodnie z art. 86 ust. 1 ustawy o VAT")
   - Podawaj KONKRETNE kwoty w PLN, stawki procentowe, terminy (daty dzienne)
   - Odwołuj się WYŁĄCZNIE do aktualnych przepisów (stan na 2026 r.)
   - NIE wymyślaj przepisów - jeśli nie jesteś pewien, napisz ogólniej

2. ZOPTYMALIZOWANE POD SEO:
   - Odpowiednia struktura H2/H3 z naturalnym rozmieszczeniem słów kluczowych
   - Słowo kluczowe w pierwszym akapicie, w 2+ nagłówkach H2, w meta danych
   - Bogate formatowanie: listy, pogrubienia, linki, tabele
   - FAQ zoptymalizowane pod Google Featured Snippets

3. WIARYGODNE (E-E-A-T):
   - Źródła WYŁĄCZNIE z: gov.pl, sejm.gov.pl, mf.gov.pl, zus.pl, gus.gov.pl, pip.gov.pl, nbp.pl, isap.sejm.gov.pl
   - Wspomnij o tym KTO powinien skonsultować się z doradcą/księgowym
   - Dodaj disclaimery prawne gdzie potrzeba

ZAWSZE odpowiadaj WYŁĄCZNIE poprawnym JSON-em bez żadnych dodatkowych komentarzy, markdown ani formatowania.
"""

ARTICLE_GENERATION_PROMPT = """Napisz obszerny, RZETELNY artykuł blogowy na temat: "{topic}"

Słowo kluczowe główne: "{primary_keyword}"
Słowa kluczowe dodatkowe: {secondary_keywords}
Docelowa długość: {target_length} słów (WAŻNE: artykuł musi mieć minimum {target_length} słów treści)
Ton: {tone}

Odpowiedz WYŁĄCZNIE w formacie JSON (bez markdown, bez ```json, bez żadnego tekstu poza JSON):
{{
  "title": "Tytuł artykułu (50-60 znaków, zawiera słowo kluczowe + rok np. 2026)",
  "slug": "tytul-artykulu-slug-bez-polskich-znakow",
  "meta_title": "Meta tytuł SEO (max 60 znaków, RÓŻNY od tytułu, z CTA np. Sprawdź/Poznaj)",
  "meta_description": "Meta opis SEO (120-160 znaków, zawiera słowo kluczowe, CTA i zachętę do kliknięcia)",
  "toc": [
    {{"label": "Nazwa sekcji w spisie treści", "anchor": "nazwa-sekcji"}}
  ],
  "sections": [
    {{
      "heading": "Nagłówek H2 (naturalny, zawiera słowo kluczowe w 2 z 5 nagłówków)",
      "anchor": "naglowek-h2-slug",
      "content": "<p>Treść sekcji w HTML. WYMAGANIA:<br/>- Minimum 200 słów na sekcję<br/>- Cytuj KONKRETNE przepisy (np. 'Zgodnie z art. 22 ust. 1 ustawy o PIT...')<br/>- Podaj KONKRETNE kwoty, terminy, stawki procentowe<br/>- Używaj <strong>, <em>, <ul>, <li>, <a href='URL'> tagów<br/>- Wstaw listy punktowane dla kluczowych informacji<br/>- Każde twierdzenie popieraj podstawą prawną</p><p>Kolejny akapit z przykładami liczbowymi, terminami i konkretnymi sytuacjami z praktyki księgowej.</p>",
      "subsections": [
        {{
          "heading": "Nagłówek H3 (użyj słów kluczowych dodatkowych)",
          "anchor": "naglowek-h3-slug",
          "content": "<p>Treść podsekcji. Minimum 120 słów. Podaj:<br/>- Konkretne kwoty w PLN<br/>- Daty graniczne (np. 'do 20 dnia miesiąca')<br/>- Podstawy prawne (art., ust.)<br/>- Przykłady z praktyki</p>"
        }}
      ]
    }}
  ],
  "faq": [
    {{
      "question": "Pytanie FAQ (naturalne, jak w wyszukiwarce Google, zawiera słowo kluczowe w 1-2 pytaniach)",
      "answer": "Szczegółowa odpowiedź (minimum 50 słów). Podaj konkretne informacje: kwoty, terminy, podstawy prawne. Odpowiedź musi być kompletna i wyczerpująca."
    }}
  ],
  "internal_link_suggestions": [
    {{
      "anchor_text": "tekst anchora do linkowania",
      "target_topic": "powiązany temat artykułu na który warto linkować",
      "reason": "dlaczego warto linkować - jak wspiera SEO"
    }}
  ],
  "sources": [
    {{
      "name": "Ustawa z dnia XX XX XXXX r. o ... (Dz.U. XXXX poz. XXXX)",
      "url": "https://isap.sejm.gov.pl/...",
      "type": "legal"
    }},
    {{
      "name": "Informacja Ministerstwa Finansów - temat",
      "url": "https://www.gov.pl/web/finanse/...",
      "type": "official"
    }}
  ]
}}

KRYTYCZNE WYMAGANIA RZETELNOŚCI:
1. Artykuł MUSI mieć 5-6 sekcji H2, każda z 1-2 podsekcjami H3
2. Każda sekcja: min. 200 słów, konkretne przepisy, kwoty w PLN, terminy
3. FAQ: 5 pytań z rozbudowanymi odpowiedziami (min. 50 słów każda)
4. Źródła: min. 4 oficjalne źródła (isap.sejm.gov.pl, gov.pl, mf.gov.pl, zus.pl)
5. Min. 5 cytowań konkretnych przepisów (art. X ust. Y ustawy o...)
6. Min. 8 konkretnych danych liczbowych (kwoty PLN, %, terminy)
7. Listy punktowane: min. 3 w całym artykule
8. Pogrubienia <strong>: min. 5 kluczowych pojęć
9. Meta tytuł RÓŻNY od tytułu artykułu
10. Rok {current_year} wymieniony w tytule lub pierwszej sekcji
"""

TOPIC_SUGGESTION_PROMPT = """Jako ekspert od księgowości i SEO, zaproponuj 10 tematów artykułów blogowych z zakresu księgowości, rachunkowości i podatków w Polsce.

Kategoria: {category}
Kontekst: {context}

Dla każdego tematu podaj:
- Temat artykułu
- Główne słowo kluczowe
- Szacowany wolumen wyszukiwań (niski/średni/wysoki)
- Trudność SEO (łatwa/średnia/trudna)
- Krótki opis dlaczego warto napisać ten artykuł

Odpowiedz WYŁĄCZNIE w formacie JSON (bez markdown):
{{
  "topics": [
    {{
      "title": "Temat artykułu",
      "primary_keyword": "główne słowo kluczowe",
      "secondary_keywords": ["słowo1", "słowo2", "słowo3"],
      "search_volume": "niski|średni|wysoki",
      "seo_difficulty": "łatwa|średnia|trudna",
      "description": "Krótki opis dlaczego warto",
      "category": "vat|pit|cit|zus|kadry|księgowość|inne"
    }}
  ]
}}"""


async def generate_article(topic: str, primary_keyword: str, secondary_keywords: list, 
                           target_length: int = 1500, tone: str = "profesjonalny",
                           template: str = "standard") -> dict:
    """Generate a full SEO-optimized article using OpenAI GPT."""
    from content_templates import get_template_prompt
    from datetime import datetime, timezone
    
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise ValueError("EMERGENT_LLM_KEY not configured")
    
    current_year = datetime.now(timezone.utc).year
    
    # Use template-based prompt if template is not standard, otherwise use default
    if template and template != "standard":
        prompt = get_template_prompt(
            template_id=template,
            topic=topic,
            primary_keyword=primary_keyword,
            secondary_keywords=secondary_keywords,
            target_length=target_length,
            tone=tone
        )
    else:
        prompt = ARTICLE_GENERATION_PROMPT.format(
            topic=topic,
            primary_keyword=primary_keyword,
            secondary_keywords=json.dumps(secondary_keywords, ensure_ascii=False),
            target_length=target_length,
            tone=tone,
            current_year=current_year
        )
    
    models_to_try = [
        ("gemini", "gemini-2.0-flash", 3),
        ("openai", "gpt-4.1-mini", 1),
        ("openai", "gpt-5.2", 1),
    ]
    last_error = None
    
    for model_idx, (provider, model, max_retries) in enumerate(models_to_try):
        logger.info(f"=== Model {model_idx+1}/{len(models_to_try)}: {provider}/{model} (max {max_retries} retries) ===")
        for attempt in range(max_retries):
            try:
                logger.info(f"[{model}] Attempt {attempt+1}/{max_retries} - sending request...")
                chat = LlmChat(
                    api_key=api_key,
                    session_id=f"article-gen-{hash(topic) % 100000}-m{model_idx}-a{attempt}",
                    system_message=ARTICLE_SYSTEM_PROMPT
                )
                chat.with_model(provider, model).with_params(timeout=180)
                
                response = await chat.send_message(UserMessage(text=prompt))
                logger.info(f"[{model}] Got response ({len(response)} chars). Parsing JSON...")
                
                clean_response = response.strip()
                if clean_response.startswith("```"):
                    clean_response = re.sub(r'^```(?:json)?\s*', '', clean_response)
                    clean_response = re.sub(r'\s*```$', '', clean_response)
                
                article = json.loads(clean_response)
                
                required_fields = ["title", "slug", "meta_title", "meta_description", "toc", "sections"]
                missing = [f for f in required_fields if f not in article]
                if missing:
                    raise ValueError(f"Article missing required fields: {missing}")
                
                article.setdefault("faq", [])
                article.setdefault("sources", [])
                article.setdefault("internal_link_suggestions", [])
                
                logger.info(f"SUCCESS: Article generated with {provider}/{model} on attempt {attempt+1}")
                return article
                
            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                is_transient = any(x in err_str for x in ["502", "503", "504", "bad gateway", "timeout", "rate_limit", "overloaded", "connection", "reset"])
                
                if is_transient and attempt < max_retries - 1:
                    wait_time = 5 * (2 ** attempt)  # exponential: 5s, 10s, 20s
                    logger.warning(f"[{model}] Transient error (attempt {attempt+1}): {e}. Retrying in {wait_time}s...")
                    import asyncio
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.warning(f"[{model}] Failed after attempt {attempt+1}: {e}")
                    break
        
        logger.info(f"[{model}] Exhausted. Switching to next model...")
    
    err_msg = str(last_error) if last_error else "Nieznany blad"
    if "502" in err_msg or "bad gateway" in err_msg.lower():
        raise ValueError("Usluga AI jest tymczasowo niedostepna (blad 502). Sprawdz saldo Universal Key w profilu (Profile > Universal Key > Add Balance) lub sprobuj ponownie za chwile.")
    elif "401" in err_msg or "auth" in err_msg.lower():
        raise ValueError("Blad autoryzacji klucza AI. Sprawdz konfiguracje EMERGENT_LLM_KEY.")
    elif "429" in err_msg or "rate" in err_msg.lower():
        raise ValueError("Przekroczono limit zapytan AI. Sprobuj ponownie za kilka minut.")
    else:
        raise last_error or ValueError("Generowanie artykulu nie powiodlo sie")


async def suggest_topics(category: str = "ogólne", context: str = "aktualne tematy podatkowe") -> dict:
    """Generate topic suggestions for accounting articles."""
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise ValueError("EMERGENT_LLM_KEY not configured")
    
    prompt = TOPIC_SUGGESTION_PROMPT.format(category=category, context=context)
    
    models = [("gemini", "gemini-2.0-flash"), ("openai", "gpt-4.1-mini"), ("openai", "gpt-5.2")]
    last_error = None
    for provider, model in models:
        try:
            chat = LlmChat(
                api_key=api_key,
                session_id=f"topic-suggest-{hash(category) % 100000}",
                system_message="Jesteś ekspertem SEO od księgowości w Polsce. Odpowiadaj WYŁĄCZNIE poprawnym JSON-em."
            )
            chat.with_model(provider, model).with_params(timeout=120)
            
            response = await chat.send_message(UserMessage(text=prompt))
            
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = re.sub(r'^```(?:json)?\s*', '', clean_response)
                clean_response = re.sub(r'\s*```$', '', clean_response)
            
            return json.loads(clean_response)
        except Exception as e:
            last_error = e
            logger.warning(f"[suggest_topics] {model} failed: {e}")
            continue
    
    raise last_error or ValueError("Nie udalo sie wygenerowac sugestii tematow")
