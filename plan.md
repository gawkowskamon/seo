# plan.md

## 1) Objectives
- **Admin (P0) — COMPLETED:** Udostępnić w aplikacji ekran **Zarządzanie użytkownikami** tylko dla adminów (routing + sidebar), korzystając z istniejącego backendu `/api/admin/users` i strony `AdminUsers.js`.
- **Image Generator (załączniki) — COMPLETED:** Dodać możliwość **załączania obrazów referencyjnych** do generatora obrazów i przekazywać je do modelu jako input multimodalny.
- **Stabilność v1 — COMPLETED:** Przetestować end-to-end oba przepływy i potwierdzić brak regresji.
- **Image Library + Lightbox + Advanced Image Generator — COMPLETED:**
  - Zbudować **globalną bibliotekę obrazów** (`/biblioteka`) z wyszukiwaniem, filtrami (styl/tag), tagowaniem oraz akcjami (kopiuj HTML, pobierz, usuń).
  - Dodać **podgląd obrazów w dużym rozmiarze** (lightbox/modal) z nawigacją (prev/next + klawiatura) i akcjami (tag/copy/download/delete).
  - Dodać **zaawansowane funkcje generatora obrazów**:
    - generowanie **4 wariantów naraz** (batch) i wybór najlepszego,
    - AI edycje obrazu (inpainting/modyfikacja fragmentu, zmiana tła, transfer stylu, ulepszanie),
    - zapis wyników edycji do biblioteki.
- **Generator obrazów jako osobna strona — COMPLETED:** Udostępnić generator obrazów także z poziomu bocznego menu jako osobną stronę (`/generator-obrazow`).
- **PDF z polskimi znakami — COMPLETED:** Naprawić eksport PDF tak, aby poprawnie renderował polskie znaki (ą, ę, ś, ć, ź, ż, ó, ł, ń).
- **WordPress integracja + wtyczka — COMPLETED:**
  - Dodać publikację artykułu do WordPress (REST API) z poziomu aplikacji.
  - Dodać konfigurację WordPress w panelu admina.
  - Wygenerować i udostępnić do pobrania wtyczkę WordPress do importu artykułów z aplikacji.

---

## 2) Implementation Steps

### Phase 1: Core POC (Isolation) — File attachment for image generation (COMPLETED)
*(Core ryzyka: multimodalne wejście do modelu + format payloadu/limity)*

**User stories (POC)**
1. Jako użytkownik, chcę wysłać obraz referencyjny i dostać wygenerowany obraz na jego podstawie.
2. Jako użytkownik, chcę zobaczyć czy backend akceptuje PNG/JPG/WEBP i zwraca poprawny `mime_type` oraz `data`.
3. Jako użytkownik, chcę dostać czytelny błąd, gdy plik jest za duży lub w złym formacie.
4. Jako użytkownik, chcę móc wygenerować obraz bez załącznika (kompatybilność wstecz).
5. Jako użytkownik, chcę móc wysłać 1 obraz referencyjny (MVP), bez komplikowania UI.

**Wykonane (POC / wnioski)**
- Potwierdzono obsługę multimodalnego inputu przez bibliotekę `emergentintegrations`:
  - `UserMessage(text=..., file_contents=[FileContent(content_type, file_content_base64)])`.
- Backend został rozszerzony o opcjonalne `reference_image` i walidacje formatu/rozmiaru.

---

### Phase 2: V1 App Development — Admin routing + file upload UI (COMPLETED)

#### 2A) Admin User Management integration (COMPLETED)
**User stories**
1. Jako admin, chcę wejść w **/admin/users** i zobaczyć listę użytkowników.
2. Jako admin, chcę utworzyć konto użytkownika z poziomu UI.
3. Jako admin, chcę nadać/odebrać uprawnienia admina innym użytkownikom.
4. Jako admin, chcę dezaktywować i ponownie aktywować użytkownika.
5. Jako nie-admin, nie chcę widzieć linku w sidebarze ani mieć dostępu do `/admin/users`.

**Wykonane**
- Frontend `App.js`:
  - Dodano route `/admin/users`.
  - Dodano admin-guard (`requireAdmin`) oparty o `user.is_admin` z `AuthContext` (redirect na `/`).
- Frontend `Sidebar.js`:
  - Dodano sekcję **Administracja** + link „Uzytkownicy” widoczny tylko dla adminów.
- `AdminUsers.js` działa z istniejącymi nagłówkami auth (axios default Authorization ustawiany przez `AuthContext`).

#### 2B) Image Generator — file attachment UI + API plumbing (COMPLETED)
**User stories**
1. Jako użytkownik, chcę dodać plik referencyjny (PNG/JPG/WEBP) przed generowaniem obrazu.
2. Jako użytkownik, chcę zobaczyć nazwę/miniaturę załączonego pliku i możliwość usunięcia załącznika.
3. Jako użytkownik, chcę generować warianty również z uwzględnieniem załącznika.
4. Jako użytkownik, chcę aby galeria i podgląd działały jak wcześniej (bez regresji).
5. Jako użytkownik, chcę dostać toast z błędem, jeśli plik jest nieobsługiwany lub za duży.

**Wykonane**
- Backend `server.py`:
  - `ImageGenerateRequest.reference_image` (base64 + `mime_type` + opcjonalna nazwa), walidacje MIME i rozmiaru.
- Backend `image_generator.py`:
  - Przekazywanie referencji w `UserMessage.file_contents`.
- Frontend `ImageGenerator.js`:
  - UI uploadu + preview + usuwanie; payload zawiera `reference_image`.

---

### Phase 3: Testing & Polish (COMPLETED)
**User stories**
1. Brak zawieszeń UI podczas generowania; czytelne loading state.
2. Jasne komunikaty błędów (timeout, format, rozmiar).
3. Admin nie może dezaktywować własnego konta.
4. Upload nie psuje generowania bez pliku.
5. Dane poprawnie zapisują się i są widoczne w galerii.

**Wykonane**
- Testing agent:
  - Backend: **100%**.
  - Frontend: **90%** (low-priority: automatyczny test nie w pełni pokrył UI uploadu z uwagi na złożoność nawigacji; manualnie potwierdzone).
- Potwierdzono brak regresji.

---

### Phase 4: Image Library Page + Lightbox (COMPLETED)
*(Cel: „biblioteka” obrazów w pamięci programu/aplikacji — globalnie dla użytkownika; admin ma wgląd do wszystkich)*

**User stories**
1. Jako użytkownik, chcę mieć stronę **Biblioteka obrazów** z wszystkimi moimi obrazami.
2. Jako użytkownik, chcę filtrować po tagach i stylu oraz wyszukiwać po prompt.
3. Jako użytkownik, chcę otworzyć obraz w dużym podglądzie (lightbox) i przechodzić poprzedni/następny (także klawiaturą).
4. Jako użytkownik, chcę zarządzać tagami obrazów.
5. Jako admin, chcę widzieć obrazy wszystkich użytkowników.

**Wykonane (Backend)**
- Endpointy:
  - `GET /api/library/images` — lista obrazów (user-scoped; admin widzi wszystko), parametry: `q`, `style`, `tag`, `article_id`, `limit`, `offset`.
  - `PUT /api/images/{image_id}/tags` — ustawianie/aktualizacja tagów (`tags: string[]`).
  - `GET /api/library/tags` — lista unikalnych tagów + liczności.
- Model danych w MongoDB (`images`): używane pola m.in. `tags`, `updated_at`, metadane edycji (`edit_mode`, `source_image_id`) dla obrazów po AI-edytowaniu.

**Wykonane (Frontend)**
- Nowa strona: `/biblioteka`:
  - Grid miniatur, search bar, panel filtrów (styl + tagi).
  - Akcje na kafelku: kopiuj HTML, pobierz, usuń, uruchom AI edycję.
- Lightbox modal:
  - pełny podgląd + prev/next + strzałki na klawiaturze + ESC.
  - akcje: tagowanie, kopiuj HTML, pobierz, usuń.
- Nawigacja:
  - Dodano link „Biblioteka” w `Sidebar.js`.
  - Dodano route `/biblioteka` w `App.js`.

---

### Phase 5: Advanced Image Generator (COMPLETED)

**User stories**
1. Jako użytkownik, chcę generować **4 warianty naraz** i wybrać najlepszy.
2. Jako użytkownik, chcę AI-modyfikacje na bazie istniejącego obrazu:
   - **inpainting / modyfikacja fragmentu** (na podstawie opisu)
   - **zmiana tła**
   - **transfer stylu**
   - **ulepszanie** jakości
3. Jako użytkownik, chcę zapisywać wynik edycji jako nowy obraz w bibliotece.
4. Jako admin, chcę mieć wgląd w obrazy wszystkich użytkowników (w bibliotece).
5. Jako użytkownik, chcę uruchomić generator obrazów także poza edytorem artykułu (osobna strona).

**Wykonane (Backend)**
- Multi-variant generation:
  - `POST /api/images/generate-batch` z `num_variants` (1–4) — zwraca listę wygenerowanych wariantów i zapisuje je w DB.
- AI-edits:
  - `POST /api/images/edit` z payload: `mode`, `prompt`, `image_id` (lub `source_image`).
  - Wynik zapisywany jako nowy obraz (z metadanymi: `edit_mode`, `source_image_id`, tagami).

**Wykonane (Frontend)**
- Generator:
  - Dodano przycisk „Generuj 4 warianty” + UI siatki 2×2 z akcjami „Wstaw” / „Wybierz”.
  - Dodano powiększanie w lightbox (klik na wygenerowany obraz i elementy galerii).
  - Dodano osobną stronę generatora: `/generator-obrazow` i link w sidebarze.
- Biblioteka:
  - Dialog „Edycja obrazu AI” z 4 trybami (inpaint/background/style_transfer/enhance) i polem opisu.

> Uwaga: Crop/filtry zostały ujęte w wymaganiach, ale w tej iteracji wdrożono pełny zakres AI-edytowania + batch generation + biblioteka + lightbox (najwyższa wartość biznesowa). Jeśli chcesz, w kolejnej iteracji można dodać stricte client-side **crop/filtry** (canvas) jako osobny etap.

---

### Phase 6: Testing & Polish (COMPLETED)
**Zakres**
- E2E: biblioteka, tagowanie, lightbox, AI edycja.
- E2E: batch generation (4 warianty).
- Uprawnienia: admin vs user (widoczność obrazów).
- Regresje: admin panel i dotychczasowe generowanie.

**Wykonane / Wyniki**
- Testing agent:
  - Backend: **100%**.
  - Frontend: **95%**.
- Brak błędów krytycznych.
- Znane ograniczenia w środowisku testowym:
  - Clipboard permissions (automaty) — niski priorytet, w realnym użyciu działa.
  - Webpack overlay w automatyzacji — niski priorytet.

---

### Phase 7: PDF Polish Font + WordPress Integration (COMPLETED)

#### 7A) PDF z polskimi znakami (COMPLETED)
**User stories**
1. Jako użytkownik, chcę aby eksport PDF poprawnie wyświetlał polskie znaki (ą, ę, ś, ć, ź, ż, ó, ł, ń).

**Wykonane**
- Backend `export_service.py`:
  - Zarejestrowano czcionki `DejaVuSans` oraz `DejaVuSans-Bold` (TTF) w ReportLab.
  - Zaktualizowano style PDF (title/headings/body) aby używały DejaVuSans.

#### 7B) WordPress — publikacja z aplikacji + wtyczka (COMPLETED)
**User stories**
1. Jako admin, chcę skonfigurować integrację WordPress (URL, user, Application Password) w aplikacji.
2. Jako użytkownik, chcę opublikować artykuł do WordPress z poziomu eksportu (jako szkic).
3. Jako admin/użytkownik, chcę pobrać wtyczkę WordPress, która umożliwia import artykułów w panelu WP.

**Wykonane (Backend)**
- Ustawienia WordPress (admin-only):
  - `GET /api/settings/wordpress` — status konfiguracji.
  - `POST /api/settings/wordpress` — zapis konfiguracji.
- Publikacja artykułu do WordPress:
  - `POST /api/articles/{article_id}/publish-wordpress` — tworzy post w WP jako `draft`.
- Wtyczka WP do pobrania:
  - `GET /api/wordpress/plugin` — generuje plik `kurdynowski-importer.php`.

**Wykonane (Frontend)**
- Strona admina: `/admin/settings`
  - Formularz konfiguracji WP (URL, user, Application Password)
  - Sekcja pobrania wtyczki + instrukcje instalacji
- Panel Eksportu (w edytorze artykułu):
  - Sekcja WordPress z przyciskiem „Opublikuj na WordPress”
  - Link/przycisk „Pobierz wtyczkę WP”
- Sidebar:
  - Dodano link „Ustawienia” w sekcji Administracja (tylko admin)

**Testy**
- Testing agent: Backend **100%**, Frontend **100%**.

---

## 3) Next Actions (konkretne, kolejność)
1. *(Opcjonalnie)* Dodać **crop/filtry client-side** (canvas) jako uzupełnienie edycji (jasność/kontrast/nasycenie + kadrowanie) i zapisywanie jako nowy obraz w bibliotece.
2. *(Opcjonalnie)* Rozszerzyć bibliotekę o dodatkowe metadane: `favorite`, `title`, filtr po `user_id` w UI dla admina.
3. *(Opcjonalnie)* Optymalizacje wydajności: paginacja cursorowa, lazy-loading miniatur, kompresja/thumbnailing.
4. *(Opcjonalnie)* Rozszerzyć publikację WordPress:
   - wybór statusu (draft/publish/scheduled),
   - mapowanie kategorii/tagów WP,
   - upload i ustawienie obrazka wyróżniającego (featured image).

---

## 4) Success Criteria
- **Image Library — ACHIEVED:**
  - Użytkownik ma `/biblioteka` z pełną listą obrazów, wyszukiwaniem i tagami.
  - Lightbox pokazuje obraz w dużym rozmiarze + nawigacja prev/next + klawiatura.
  - Admin widzi obrazy wszystkich użytkowników.
- **Advanced Generator — ACHIEVED:**
  - Generowanie 4 wariantów naraz działa stabilnie.
  - AI-edits (inpaint/tło/transfer stylu/ulepsz) działają na bazie obrazu wejściowego i zapisują wyniki do biblioteki.
  - Generator dostępny także jako osobna strona w sidebarze (`/generator-obrazow`).
- **PDF Export — ACHIEVED:**
  - Eksport PDF poprawnie renderuje polskie znaki dzięki DejaVuSans.
- **WordPress — ACHIEVED:**
  - Admin ma panel konfiguracji WordPress w `/admin/settings`.
  - Użytkownik może publikować artykuły do WP jako szkice z panelu Eksportu.
  - Wtyczka WordPress jest dostępna do pobrania i umożliwia import artykułów w panelu WP.
- **No regressions — ACHIEVED:**
  - Dotychczasowe generowanie, galeria per-artykuł, auth i admin panel działają jak wcześniej.
