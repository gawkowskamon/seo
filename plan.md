# plan.md

## 1) Objectives
- **Admin (P0) — COMPLETED:** Udostępnić w aplikacji ekran **Zarządzanie użytkownikami** tylko dla adminów (routing + sidebar), korzystając z istniejącego backendu `/api/admin/users` i strony `AdminUsers.js`.
- **Image Generator (załączniki) — COMPLETED:** Dodać możliwość **załączania obrazów referencyjnych** do generatora obrazów i przekazywać je do modelu jako input multimodalny.
- **Stabilność v1 — COMPLETED:** Przetestować end-to-end oba przepływy i potwierdzić brak regresji.
- **Image Library + Lightbox + Advanced Image Generator — PLANNED (NOW):**
  - Zbudować **globalną bibliotekę obrazów** (dla użytkownika; admin widzi wszystkie), z tagami, filtrowaniem i możliwością wstawiania do dowolnego artykułu.
  - Dodać **podgląd obrazów w dużym rozmiarze** (lightbox/modal) z nawigacją po galerii.
  - Dodać **zaawansowane funkcje generatora obrazów**: generowanie wielu wariantów naraz, edycja (crop/filtry), AI modyfikacje (inpainting/modyfikacja fragmentu), zmiana tła, transfer stylu.

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

### Phase 4: Image Library Page + Lightbox (PLANNED)
*(Cel: „biblioteka” obrazów w pamięci programu/aplikacji — globalnie dla użytkownika; admin ma wgląd do wszystkich)*

**User stories**
1. Jako użytkownik, chcę mieć stronę **Biblioteka obrazów** z wszystkimi moimi obrazami.
2. Jako użytkownik, chcę filtrować po tagach, stylu, dacie, artykule i wyszukiwać po prompt.
3. Jako użytkownik, chcę otworzyć obraz w dużym podglądzie (lightbox) i przechodzić poprzedni/następny.
4. Jako użytkownik, chcę wstawić obraz z biblioteki do dowolnego artykułu.
5. Jako admin, chcę widzieć obrazy wszystkich użytkowników (z możliwością filtrowania po użytkowniku).

**Backend**
- Nowe endpointy:
  - `GET /api/library/images` — lista obrazów (user-scoped; admin widzi wszystko), parametry: `q`, `tags`, `style`, `article_id`, `user_id` (tylko admin), `limit`, `cursor`.
  - `PUT /api/images/{image_id}/tags` — ustawianie/aktualizacja tagów (`tags: string[]`).
  - *(opcjonalnie)* `PUT /api/images/{image_id}` — metadane (np. tytuł, opis, ulubione).
- Model danych w MongoDB (`images`):
  - dodać pola: `tags: []`, `title`, `favorite`, `updated_at`.

**Frontend**
- Nowa strona: `/biblioteka`.
  - Grid/lista miniatur, search bar, filtry (tagi, styl, data, artykuł, użytkownik dla admina).
  - Akcje na kafelku: podgląd, kopiuj HTML, pobierz, usuń, dodaj/usuń tagi, „Wstaw do artykułu…”.
- Lightbox modal:
  - pełny podgląd + nawigacja prev/next + klawisze strzałek + ESC.

---

### Phase 5: Advanced Image Generator (PLANNED)

**User stories**
1. Jako użytkownik, chcę generować **4 warianty naraz** i wybrać najlepszy.
2. Jako użytkownik, chcę edytować obraz: **crop**, **podstawowe filtry** (jasność/kontrast/nasycenie) przed wstawieniem.
3. Jako użytkownik, chcę AI-modyfikacje na bazie istniejącego obrazu:
   - **inpainting / modyfikacja fragmentu** (na podstawie opisu)
   - **zmiana tła**
   - **transfer stylu**
4. Jako użytkownik, chcę zapisywać wynik edycji jako nowy obraz w bibliotece.
5. Jako admin, chcę widzieć historię i metadane (kto wygenerował, do jakiego artykułu).

**Backend**
- Multi-variant generation:
  - `POST /api/images/generate` rozszerzyć o `num_variants: int` (np. 4) i zwracać listę wyników.
  - Alternatywnie: `POST /api/images/generate-batch`.
- AI-edits:
  - Nowy endpoint: `POST /api/images/{image_id}/edit` (lub `/api/images/edit`) z payload:
    - `mode: inpaint|background|style_transfer`
    - `prompt`
    - `reference_image` (bazowy obraz) + *(opcjonalnie)* maska (dla inpaint)
- Walidacje: limity rozmiaru, timeouty, obsługa błędów modelu.

**Frontend**
- Generator:
  - UI „Generuj 4 warianty” (siatka 2×2) + szybkie akcje: wybierz, zapisz do biblioteki, wstaw do treści.
- Edycja:
  - Panel edycji obrazu (crop + filtry) — client-side.
  - Tryby AI-edit jako osobne akcje z polem opisu.
  - Zapis jako nowy asset w bibliotece.

---

### Phase 6: Testing & Polish (PLANNED)
**Zakres**
- E2E: biblioteka, tagowanie, lightbox, insert do artykułu.
- E2E: multi-variant, edycje (client-side) i AI-edits.
- Uprawnienia: admin vs user (widoczność obrazów, filtry po user).
- Wydajność: paginacja/cursor, lazy-loading miniatur.

---

## 3) Next Actions (konkretne, kolejność)
1. **Phase 4**: Backend `GET /api/library/images` + strona `/biblioteka` + lightbox.
2. **Phase 4**: Tagowanie obrazów + filtry + wstawianie obrazu do artykułu z biblioteki.
3. **Phase 5**: Multi-variant generation (4 na raz) — backend + UI.
4. **Phase 5**: Podstawowa edycja client-side (crop/filtry) + zapis do biblioteki.
5. **Phase 5**: AI-edits (inpaint / zmiana tła / transfer stylu) + zapis wyników.
6. **Phase 6**: Testy automatyczne + ręczne + poprawki UX.

---

## 4) Success Criteria
- **Image Library — ACHIEVED gdy:**
  - Użytkownik ma `/biblioteka` z pełną listą obrazów, wyszukiwaniem i tagami.
  - Lightbox pokazuje obraz w dużym rozmiarze + nawigacja prev/next.
  - Admin widzi obrazy wszystkich użytkowników.
  - Obrazy z biblioteki można wstawić do dowolnego artykułu.
- **Advanced Generator — ACHIEVED gdy:**
  - Generowanie 4 wariantów naraz działa stabilnie.
  - Crop/filtry działają bez regresji i można zapisać wynik do biblioteki.
  - AI-edits (inpaint/tło/transfer stylu) działają na bazie obrazu wejściowego.
- **No regressions — ACHIEVED gdy:**
  - Dotychczasowe generowanie, galeria per-artykuł, auth i admin panel działają jak wcześniej.
