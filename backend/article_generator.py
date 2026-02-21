"""
Article Generation Service using OpenAI GPT via Emergent integrations.
Generates SEO-optimized articles in Polish about accounting topics.
"""

import json
import re
import os
import logging
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

ARTICLE_SYSTEM_PROMPT = """Jesteś ekspertem od tworzenia treści SEO z zakresu księgowości, rachunkowości i podatków w Polsce. 
Tworzysz artykuły na blogi firmowe, które są:
- Merytorycznie poprawne i oparte na aktualnych przepisach prawa polskiego
- Zoptymalizowane pod SEO (odpowiednia struktura nagłówków, słowa kluczowe, meta opisy)
- Napisane przystępnym, profesjonalnym językiem
- Oparte WYŁĄCZNIE na wiarygodnych źródłach (gov.pl, sejm.gov.pl, mf.gov.pl, zus.pl, gus.gov.pl, pip.gov.pl, nbp.pl, oficjalne dzienniki ustaw)

ZAWSZE odpowiadaj WYŁĄCZNIE poprawnym JSON-em bez żadnych dodatkowych komentarzy, markdown ani formatowania.
"""

ARTICLE_GENERATION_PROMPT = """Napisz obszerny artykuł blogowy na temat: "{topic}"

Słowo kluczowe główne: "{primary_keyword}"
Słowa kluczowe dodatkowe: {secondary_keywords}
Docelowa długość: {target_length} słów (WAŻNE: artykuł musi mieć minimum {target_length} słów treści)
Ton: {tone}

Odpowiedz WYŁĄCZNIE w formacie JSON (bez markdown, bez ```json, bez żadnego tekstu poza JSON):
{{
  "title": "Tytuł artykułu (50-60 znaków, zawiera słowo kluczowe główne)",
  "slug": "tytul-artykulu-slug-bez-polskich-znakow",
  "meta_title": "Meta tytuł SEO (max 60 znaków)",
  "meta_description": "Meta opis SEO (120-160 znaków, zachęcający do kliknięcia, zawiera słowo kluczowe)",
  "toc": [
    {{"label": "Nazwa sekcji w spisie treści", "anchor": "nazwa-sekcji"}}
  ],
  "sections": [
    {{
      "heading": "Nagłówek H2 (zawiera słowo kluczowe w co najmniej jednym)",
      "anchor": "naglowek-h2-slug",
      "content": "<p>Treść sekcji w HTML. Minimum 150-200 słów na sekcję. Używaj <strong>, <em>, <ul>, <li>, <a href> tagów. Pisz rozbudowane, merytoryczne akapity.</p><p>Kolejny akapit z dodatkowymi informacjami, przykładami, konkretnymi kwotami i terminami.</p>",
      "subsections": [
        {{
          "heading": "Nagłówek H3",
          "anchor": "naglowek-h3-slug",
          "content": "<p>Treść podsekcji w HTML. Minimum 100 słów. Podaj konkretne informacje, przykłady liczbowe, terminy.</p>"
        }}
      ]
    }}
  ],
  "faq": [
    {{
      "question": "Pytanie FAQ (naturalne, jak w wyszukiwarce)",
      "answer": "Szczegółowa odpowiedź na pytanie (minimum 30 słów, konkretna i merytoryczna)"
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
      "name": "Nazwa źródła (np. Ustawa o VAT, Rozporządzenie MF)",
      "url": "https://oficjalna-strona.gov.pl/konkretny-link",
      "type": "legal|official|expert"
    }}
  ]
}}

WAŻNE WYMAGANIA:
- Artykuł MUSI mieć 4-5 sekcji H2
- Każda sekcja MUSI mieć 1-2 podsekcje H3
- Treść w sekcjach w formacie HTML z tagami <p>, <strong>, <em>, <ul>, <li>
- FAQ: 4 pytania ze szczegółowymi odpowiedziami
- Źródła: wiarygodne (gov.pl, oficjalne instytucje polskie)
- Anchory: bez polskich znaków, małe litery z myślnikami
- Słowo kluczowe główne: w pierwszych 100 słowach, w co najmniej 2 nagłówkach H2
- Pisz konkretnie: kwoty, terminy, podstawy prawne
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
    
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise ValueError("EMERGENT_LLM_KEY not configured")
    
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
            tone=tone
        )
    
    # Try with retries - use gpt-4.1-mini (fast), single attempt per model
    models_to_try = [("openai", "gpt-4.1-mini")]
    last_error = None
    
    for provider, model in models_to_try:
        try:
            logger.info(f"Attempting article generation with {model}")
            chat = LlmChat(
                api_key=api_key,
                session_id=f"article-gen-{hash(topic) % 100000}",
                system_message=ARTICLE_SYSTEM_PROMPT
            )
            chat.with_model(provider, model)
            
            response = await chat.send_message(UserMessage(text=prompt))
            
            # Clean and parse JSON response
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = re.sub(r'^```(?:json)?\s*', '', clean_response)
                clean_response = re.sub(r'\s*```$', '', clean_response)
            
            article = json.loads(clean_response)
            
            # Validate required fields
            required_fields = ["title", "slug", "meta_title", "meta_description", "toc", "sections"]
            missing = [f for f in required_fields if f not in article]
            if missing:
                raise ValueError(f"Article missing required fields: {missing}")
            
            # Add defaults for optional fields
            article.setdefault("faq", [])
            article.setdefault("sources", [])
            article.setdefault("internal_link_suggestions", [])
            
            logger.info(f"Article generated successfully with {model}")
            return article
            
        except Exception as e:
            last_error = e
            logger.warning(f"Attempt with {model} failed: {e}")
            continue
    
    raise last_error or ValueError("Article generation failed")


async def suggest_topics(category: str = "ogólne", context: str = "aktualne tematy podatkowe") -> dict:
    """Generate topic suggestions for accounting articles."""
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise ValueError("EMERGENT_LLM_KEY not configured")
    
    prompt = TOPIC_SUGGESTION_PROMPT.format(category=category, context=context)
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"topic-suggest-{hash(category) % 100000}",
        system_message="Jesteś ekspertem SEO od księgowości w Polsce. Odpowiadaj WYŁĄCZNIE poprawnym JSON-em."
    )
    chat.with_model("openai", "gpt-4.1-mini")
    
    response = await chat.send_message(UserMessage(text=prompt))
    
    clean_response = response.strip()
    if clean_response.startswith("```"):
        clean_response = re.sub(r'^```(?:json)?\s*', '', clean_response)
        clean_response = re.sub(r'\s*```$', '', clean_response)
    
    return json.loads(clean_response)
