"""
Content Templates for specialized article generation.
Each template defines a specific article structure, prompts, and formatting expectations.
"""

TEMPLATES = {
    "standard": {
        "id": "standard",
        "name": "Artykul standardowy",
        "description": "Klasyczny artykul blogowy SEO z sekcjami, FAQ i zrodlami",
        "icon": "file-text",
        "category": "podstawowe"
    },
    "poradnik": {
        "id": "poradnik",
        "name": "Poradnik krok po kroku",
        "description": "Szczegolowy przewodnik z ponumerowanymi krokami i praktycznymi wskazowkami",
        "icon": "list-ordered",
        "category": "specjalistyczne"
    },
    "case_study": {
        "id": "case_study",
        "name": "Case study / Analiza przypadku",
        "description": "Analiza konkretnego przypadku z danymi, wnioskami i rekomendacjami",
        "icon": "briefcase",
        "category": "specjalistyczne"
    },
    "porownanie": {
        "id": "porownanie",
        "name": "Porownanie / Zestawienie",
        "description": "Szczegolowe porownanie rozwiazan, metod lub narzedzi w formie tabeli",
        "icon": "columns",
        "category": "specjalistyczne"
    },
    "checklist": {
        "id": "checklist",
        "name": "Checklista / Lista kontrolna",
        "description": "Kompletna lista kontrolna z punktami do odhaczenia i objasieniami",
        "icon": "check-square",
        "category": "specjalistyczne"
    },
    "pillar": {
        "id": "pillar",
        "name": "Pillar page / Artykul filarowy",
        "description": "Obszerny artykul bazowy obejmujacy caly temat, z linkami do podtematow",
        "icon": "landmark",
        "category": "zaawansowane"
    },
    "nowelizacja": {
        "id": "nowelizacja",
        "name": "Aktualizacja przepisow",
        "description": "Omowienie zmian w przepisach: co sie zmienilo, od kiedy, jak sie przygotowac",
        "icon": "scale",
        "category": "zaawansowane"
    },
    "kalkulator": {
        "id": "kalkulator",
        "name": "Kalkulator / Przyklad obliczeniowy",
        "description": "Artykul z konkretnymi wyliczeniami, tabelami kwot i przykladami liczbowymi",
        "icon": "calculator",
        "category": "zaawansowane"
    }
}

TEMPLATE_PROMPTS = {
    "standard": """Napisz obszerny artykul blogowy na temat: "{topic}"

Slowowo kluczowe glowne: "{primary_keyword}"
Slowa kluczowe dodatkowe: {secondary_keywords}
Docelowa dlugosc: {target_length} slow
Ton: {tone}

STRUKTURA:
- Wprowadzenie (150+ slow)
- 5-6 sekcji H2 z podsekcjami H3
- FAQ (6+ pytan)
- Podsumowanie

Odpowiedz WYLACZNIE w formacie JSON (bez markdown, bez ```json):
{json_schema}
""",

    "poradnik": """Napisz szczegolowy poradnik krok po kroku na temat: "{topic}"

Slowowo kluczowe glowne: "{primary_keyword}"
Slowa kluczowe dodatkowe: {secondary_keywords}
Docelowa dlugosc: {target_length} slow
Ton: {tone}

SPECJALNA STRUKTURA PORADNIKA:
- Wprowadzenie: dlaczego ten poradnik jest potrzebny, dla kogo jest przeznaczony
- "Co bedziesz potrzebowac" - lista dokumentow/narzedzi/informacji na start
- KROKI ponumerowane jako sekcje H2 (np. "Krok 1: Zbierz dokumenty", "Krok 2: Wypelnij formularz")
- Kazdy krok: co robic, jak to zrobic, na co uwazac, typowe bledy
- W sekcjach uzyj CALLOUT BOXOW w HTML:
  <div class="callout callout-tip"><strong>Wskazowka:</strong> tresc wskazowki</div>
  <div class="callout callout-warning"><strong>Uwaga:</strong> tresc ostrzezenia</div>
  <div class="callout callout-info"><strong>Informacja:</strong> tresc informacji</div>
- Podsumowanie z checklistata do sprawdzenia
- FAQ specyficzne do poradnika

Odpowiedz WYLACZNIE w formacie JSON (bez markdown, bez ```json):
{json_schema}
""",

    "case_study": """Napisz analiz przypadku (case study) na temat: "{topic}"

Slowowo kluczowe glowne: "{primary_keyword}"
Slowa kluczowe dodatkowe: {secondary_keywords}
Docelowa dlugosc: {target_length} slow
Ton: {tone}

SPECJALNA STRUKTURA CASE STUDY:
- Wprowadzenie: prezentacja problemu/sytuacji
- "Profil klienta/firmy" - opis sytuacji wyjsciowej (mozesz uzyc fikcyjnej, ale realistycznej firmy)
- "Wyzwanie" - szczegolowy opis problemu
- "Rozwiazanie" - krok po kroku jak rozwiazano problem
- "Wyniki" - konkretne liczby, oszczednosci, rezultaty
  Uzyj TABEL w HTML:
  <table class="data-table"><thead><tr><th>Wskaznik</th><th>Przed</th><th>Po</th></tr></thead><tbody><tr><td>...</td><td>...</td><td>...</td></tr></tbody></table>
- "Wnioski i rekomendacje"
- "Kluczowe lekcje" - takeaways
- FAQ

Odpowiedz WYLACZNIE w formacie JSON (bez markdown, bez ```json):
{json_schema}
""",

    "porownanie": """Napisz szczegolowe porownanie na temat: "{topic}"

Slowowo kluczowe glowne: "{primary_keyword}"
Slowa kluczowe dodatkowe: {secondary_keywords}
Docelowa dlugosc: {target_length} slow
Ton: {tone}

SPECJALNA STRUKTURA POROWNANIA:
- Wprowadzenie: co porownujemy i dlaczego to wazne
- "Kryteria porownania" - lista kryteriow
- Sekcje dla kazdego porownowanego elementu (2-4 elementy)
- TABELA POROWNAWCZA w HTML:
  <table class="comparison-table"><thead><tr><th>Kryterium</th><th>Opcja A</th><th>Opcja B</th><th>Opcja C</th></tr></thead><tbody>...</tbody></table>
- "Dla kogo ktora opcja?" - rekomendacje dla roznych profilow
- "Podsumowanie" z jasna rekomendacja
- FAQ

Odpowiedz WYLACZNIE w formacie JSON (bez markdown, bez ```json):
{json_schema}
""",

    "checklist": """Napisz kompletna liste kontrolna na temat: "{topic}"

Slowowo kluczowe glowne: "{primary_keyword}"
Slowa kluczowe dodatkowe: {secondary_keywords}
Docelowa dlugosc: {target_length} slow
Ton: {tone}

SPECJALNA STRUKTURA CHECKLISTY:
- Wprowadzenie: dlaczego ta checklista jest niezbedna
- Sekcje tematyczne (H2) z punktami do odhaczenia
- Kazdy punkt checklisty w HTML:
  <div class="checklist-item"><input type="checkbox" disabled /> <strong>Punkt do sprawdzenia</strong><p>Szczegolowe objasnienie co i jak sprawdzic, terminy, podstawy prawne</p></div>
- Uzyj CALLOUT BOXOW dla waznych uwag:
  <div class="callout callout-warning"><strong>Uwaga:</strong> tresc ostrzezenia o konsekwencjach</div>
- "Terminarz" - kluczowe daty i terminy w tabeli
- FAQ
- Podsumowanie

Odpowiedz WYLACZNIE w formacie JSON (bez markdown, bez ```json):
{json_schema}
""",

    "pillar": """Napisz obszerny artykul filarowy (pillar page) na temat: "{topic}"

Slowowo kluczowe glowne: "{primary_keyword}"
Slowa kluczowe dodatkowe: {secondary_keywords}
Docelowa dlugosc: {target_length} slow (MINIMUM 2500 slow)
Ton: {tone}

SPECJALNA STRUKTURA PILLAR PAGE:
- Rozbudowane wprowadzenie (250+ slow): kompleksowy przeglad tematu
- 8-10 sekcji H2, kazda z 2-4 podsekcjami H3
- Kazda sekcja to potencjalny oddzielny artykul - daj przeglad i wskaż, ze mozna poglebic
- Na koncu kazdej sekcji dodaj:
  <div class="callout callout-link"><strong>Czytaj wiecej:</strong> [Tytul powiazanego artykulu] - szczegolowy poradnik na ten temat</div>
- SPIS TRESCI musi byc szczegolowy (wszystkie H2 i H3)
- Obfite uzylcie linkow wewnetrznych
- Podsumowanie z mapa tematow
- FAQ (minimum 8 pytan)

Odpowiedz WYLACZNIE w formacie JSON (bez markdown, bez ```json):
{json_schema}
""",

    "nowelizacja": """Napisz artykul o zmianach w przepisach dotyczacy: "{topic}"

Slowowo kluczowe glowne: "{primary_keyword}"
Slowa kluczowe dodatkowe: {secondary_keywords}
Docelowa dlugosc: {target_length} slow
Ton: {tone}

SPECJALNA STRUKTURA AKTUALIZACJI PRZEPISOW:
- Wprowadzenie: najwazniejsze zmiany w skrocie (streszczenie dla zajętych)
- "Co sie zmienia?" - przeglad zmian
- "Od kiedy obowiazuja nowe przepisy?" - daty wejscia w zycie
- "Kogo dotycza zmiany?" - grupy podmiotow
- TABELA ZMIAN:
  <table class="changes-table"><thead><tr><th>Aspekt</th><th>Stare przepisy</th><th>Nowe przepisy</th><th>Od kiedy</th></tr></thead><tbody>...</tbody></table>
- "Jak sie przygotowac?" - konkretne kroki
- <div class="callout callout-warning"><strong>Uwaga:</strong> kary i konsekwencje za niedostosowanie sie</div>
- "Praktyczne konsekwencje dla firm"
- FAQ
- Podsumowanie z timeline'm implementacji

Odpowiedz WYLACZNIE w formacie JSON (bez markdown, bez ```json):
{json_schema}
""",

    "kalkulator": """Napisz artykul z konkretnymi wyliczeniami na temat: "{topic}"

Slowowo kluczowe glowne: "{primary_keyword}"
Slowa kluczowe dodatkowe: {secondary_keywords}
Docelowa dlugosc: {target_length} slow
Ton: {tone}

SPECJALNA STRUKTURA KALKULATORA:
- Wprowadzenie: co bedziemy liczyc i dlaczego to wazne
- "Podstawy prawne" - aktualne stawki, limity, progi
- TABELA STAWEK/LIMITOW:
  <table class="data-table"><thead><tr><th>Element</th><th>Wartosc/Stawka</th><th>Podstawa prawna</th></tr></thead><tbody>...</tbody></table>
- "Przyklad 1: [Scenariusz]" - krok po kroku wyliczenie z konkretnymi kwotami
- "Przyklad 2: [Inny scenariusz]" - drugie wyliczenie do porownania
- TABELA POROWNAWCZA WYNIKOW:
  <table class="data-table"><thead><tr><th>Element</th><th>Przyklad 1</th><th>Przyklad 2</th></tr></thead><tbody>...</tbody></table>
- <div class="callout callout-tip"><strong>Wskazowka:</strong> jak zoptymalizowac/oszczedzic</div>
- "Najczestsze bledy w obliczeniach"
- FAQ
- Podsumowanie

Odpowiedz WYLACZNIE w formacie JSON (bez markdown, bez ```json):
{json_schema}
"""
}

# Common JSON schema for all templates
ARTICLE_JSON_SCHEMA = """{{
  "title": "Tytul artykulu (50-60 znakow, zawiera slowo kluczowe glowne)",
  "slug": "tytul-artykulu-slug-bez-polskich-znakow",
  "meta_title": "Meta tytul SEO (max 60 znakow)",
  "meta_description": "Meta opis SEO (120-160 znakow, zachecajacy do klikniecia, zawiera slowo kluczowe)",
  "toc": [
    {{"label": "Nazwa sekcji w spisie tresci", "anchor": "nazwa-sekcji"}}
  ],
  "sections": [
    {{
      "heading": "Naglowek H2",
      "anchor": "naglowek-h2-slug",
      "content": "<p>Tresc sekcji w HTML. Minimum 150-200 slow na sekcje. Uzywaj <strong>, <em>, <ul>, <li>, <a href> tagow.</p>",
      "subsections": [
        {{
          "heading": "Naglowek H3",
          "anchor": "naglowek-h3-slug",
          "content": "<p>Tresc podsekcji w HTML. Minimum 100 slow.</p>"
        }}
      ]
    }}
  ],
  "faq": [
    {{
      "question": "Pytanie FAQ",
      "answer": "Szczegolowa odpowiedz (minimum 30 slow)"
    }}
  ],
  "internal_link_suggestions": [
    {{
      "anchor_text": "tekst anchora",
      "target_topic": "powiazany temat",
      "reason": "dlaczego warto linkowac"
    }}
  ],
  "sources": [
    {{
      "name": "Nazwa zrodla",
      "url": "https://oficjalna-strona.gov.pl/link",
      "type": "legal|official|expert"
    }}
  ]
}}

WAZNE WYMAGANIA:
- Anchory: unikalne, bez polskich znakow (a->a, e->e, l->l, s->s, c->c, o->o, z->z, n->n), male litery z myslnikami
- Slowowo kluczowe glowne: w pierwszych 150 slowach, w co najmniej 2 naglowkach H2, w meta opisie
- Tresc w sekcjach MUSI byc w formacie HTML z tagami <p>, <strong>, <em>, <ul>, <li>
- Pisz konkretnie: podawaj kwoty, terminy, podstawy prawne, przyklady
- Zrodla MUSZA byc wiarygodne (gov.pl, oficjalne instytucje polskie)"""


def get_template_prompt(template_id: str, topic: str, primary_keyword: str,
                        secondary_keywords: list, target_length: int, tone: str) -> str:
    """Get the formatted prompt for a specific template."""
    import json as _json
    template = TEMPLATE_PROMPTS.get(template_id, TEMPLATE_PROMPTS["standard"])
    return template.format(
        topic=topic,
        primary_keyword=primary_keyword,
        secondary_keywords=_json.dumps(secondary_keywords, ensure_ascii=False),
        target_length=target_length,
        tone=tone,
        json_schema=ARTICLE_JSON_SCHEMA
    )


def get_all_templates():
    """Return all available templates."""
    return list(TEMPLATES.values())
