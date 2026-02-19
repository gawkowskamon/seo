# plan.md

## 1) Objectives
- **Admin (P0) — COMPLETED:** Udostępnić w aplikacji ekran **Zarządzanie użytkownikami** tylko dla adminów (routing + sidebar), korzystając z istniejącego backendu `/api/admin/users` i strony `AdminUsers.js`.
- **Image Generator — COMPLETED:** Dodać możliwość **załączania plików (obrazów referencyjnych)** do generatora obrazów i przekazywać je do modelu jako input multimodalny.
- **Stabilność v1 — COMPLETED:** Przetestować end-to-end oba przepływy i potwierdzić brak regresji (backend 100%, frontend 90% — jedynie low-priority uwaga dot. złożoności nawigacji w automatycznych testach UI).

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

#### 2A) Admin User Management integration (quick) (COMPLETED)
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
- Sanity check:
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
  - Rozszerzono `ImageGenerateRequest` o `reference_image` (base64 + `mime_type` + opcjonalna nazwa).
  - Dodano walidacje MIME (`png/jpg/jpeg/webp`) oraz limit rozmiaru (~5MB).
  - Przekazanie `reference_image` do `image_generator.generate_image()` i `generate_image_variant()`.
- Backend `image_generator.py`:
  - Dodano obsługę `FileContent` i przekazanie `reference_image` w `UserMessage.file_contents`.
  - Warianty uwzględniają referencję.
- Frontend `ImageGenerator.js`:
  - Dodano UI do załączania pliku (ukryty input + przycisk „Dolacz obraz referencyjny”).
  - Dodano preview (miniatura, nazwa) i możliwość usunięcia.
  - Payload do `/api/images/generate` zawiera `reference_image` (base64 bez prefixu `data:`).

- Conclude Phase 2:
  - Przeprowadzono rundę testów backend + UI (manual/screenshot).

---

### Phase 3: Testing & Polish (COMPLETED)
**User stories**
1. Jako użytkownik, chcę by generowanie nie zawieszało UI i pokazywało loading state.
2. Jako użytkownik, chcę jasnych komunikatów błędów (timeout/model unavailable, zły plik, zbyt duży plik).
3. Jako admin, chcę by UI nie pozwalało dezaktywować mnie samego.
4. Jako użytkownik, chcę by upload nie psuł generowania bez pliku.
5. Jako użytkownik, chcę by dane były poprawnie zapisywane i widoczne w galerii.

**Wykonane**
- Uruchomiono testing agent:
  - Backend: **100%** (admin CRUD + walidacje `reference_image` przechodzą).
  - Frontend: **90%** (funkcje admin OK; low-priority uwaga — automatyczny test nie w pełni pokrył UI uploadu z powodu złożoności nawigacji; manualnie potwierdzono widoczność i działanie UI).
- Final sanity:
  - Potwierdzono poprawne redirecty i brak dostępu do admin panelu dla nie-adminów.
  - Brak wykrytych regresji w istniejących funkcjach.

---

## 3) Next Actions (konkretne, kolejność)
1. **(Opcjonalnie) Podnieść pokrycie testów UI** dla uploadu w Image Generatorze (usprawnić nawigację testów / dodać stabilne selektory w miejscach nawigacji w edytorze).
2. **(Opcjonalnie) Rozszerzenia UX**:
   - Pokazać limit rozmiaru i obsługiwane formaty w krótkim helper-tekście pod przyciskiem.
   - Dodać informację „Załącznik użyty” przy wygenerowanym obrazie (np. badge).
3. Monitorować logi produkcyjne (timeouts/limity) i dostroić timeouty, jeśli będą zgłoszenia.

---

## 4) Success Criteria
- **Admin — ACHIEVED:**
  - Admin widzi link i stronę `/admin/users`.
  - Nie-admin nie widzi linku i jest blokowany (redirect/403).
  - CRUD działa: create/toggle admin/deactivate/reactivate.
- **Image attachment — ACHIEVED:**
  - Generowanie działa w 2 trybach: bez załącznika i z 1 obrazem referencyjnym.
  - Walidacje i komunikaty błędów (format/rozmiar) działają.
  - Warianty działają również z referencją.
- **No regressions — ACHIEVED:**
  - Dotychczasowe generowanie obrazów, galeria, artykuły i auth działają jak przed zmianami.
