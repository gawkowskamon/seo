# plan.md

## 1) Objectives
- **Admin (P0):** Udostępnić w aplikacji ekran **Zarządzanie użytkownikami** tylko dla adminów (routing + sidebar), korzystając z istniejącego backendu `/api/admin/users` i istniejącej strony `AdminUsers.js`.
- **Image Generator:** Dodać możliwość **załączania plików (obrazów referencyjnych)** do generatora obrazów i przekazywać je do modelu jako input multimodalny.
- **Stabilność v1:** Przetestować end-to-end oba przepływy i poprawić regresje.

---

## 2) Implementation Steps

### Phase 1: Core POC (Isolation) — File attachment for image generation
*(Core ryzyka: multimodalne wejście do modelu + format payloadu/limity)*

**User stories (POC)**
1. Jako użytkownik, chcę wysłać obraz referencyjny i dostać wygenerowany obraz na jego podstawie.
2. Jako użytkownik, chcę zobaczyć czy backend akceptuje PNG/JPG i zwraca poprawny `mime_type` oraz `data`.
3. Jako użytkownik, chcę dostać czytelny błąd, gdy plik jest za duży lub w złym formacie.
4. Jako użytkownik, chcę móc wygenerować obraz bez załącznika (kompatybilność wstecz).
5. Jako użytkownik, chcę móc wysłać 1 obraz referencyjny (MVP), bez komplikowania UI.

**Steps**
- Web research (krótko): best practice dla Gemini multimodal input (jak przekazywać image bytes/base64 w message).
- Backend: dodać minimalną obsługę `reference_image` w request (base64 + mime) i wpiąć w wywołanie modelu.
- Dodać **python test script** w `/app/tests/poc_image_attachment.py`:
  - 1) generate bez pliku (control)
  - 2) generate z plikiem (np. mały PNG)
  - asercje: 200, obecne `data`, sensowny `mime_type`
- Iterować aż POC przechodzi stabilnie.

---

### Phase 2: V1 App Development — Admin routing + file upload UI

#### 2A) Admin User Management integration (quick)
**User stories**
1. Jako admin, chcę wejść w **/admin/users** i zobaczyć listę użytkowników.
2. Jako admin, chcę utworzyć konto użytkownika z poziomu UI.
3. Jako admin, chcę nadać/odebrać uprawnienia admina innym użytkownikom.
4. Jako admin, chcę dezaktywować i ponownie aktywować użytkownika.
5. Jako nie-admin, nie chcę widzieć linku w sidebarze ani mieć dostępu do `/admin/users`.

**Steps**
- Frontend `App.js`:
  - dodać route `/admin/users`.
  - dodać prosty **admin-guard** (sprawdzenie `user.is_admin` z `AuthContext`; redirect na `/`).
- Frontend `Sidebar.js`:
  - dodać link „Użytkownicy” widoczny tylko gdy `user.is_admin`.
- Szybki sanity check: `AdminUsers.js` działa z istniejącymi nagłówkami auth (axios defaults).

#### 2B) Image Generator — file attachment UI + API plumbing
**User stories**
1. Jako użytkownik, chcę dodać plik referencyjny (JPG/PNG) przed generowaniem obrazu.
2. Jako użytkownik, chcę zobaczyć nazwę/miniaturę załączonego pliku i możliwość usunięcia załącznika.
3. Jako użytkownik, chcę generować warianty również z uwzględnieniem załącznika.
4. Jako użytkownik, chcę aby galeria i podgląd działały jak wcześniej (bez regresji).
5. Jako użytkownik, chcę dostać toast z błędem, jeśli plik jest nieobsługiwany.

**Steps**
- Backend `server.py`:
  - rozszerzyć `ImageGenerateRequest` o opcjonalne `reference_image` (np. `{ data: base64, mime_type: "image/png", name?: str }`).
  - w `/api/images/generate` przekazać `reference_image` do `image_generator.generate_image*`.
- Backend `image_generator.py`:
  - rozszerzyć budowę `UserMessage` o część multimodalną zawierającą obraz referencyjny (MVP: 1 obraz).
  - walidacje: typy MIME, limit rozmiaru (np. 5MB po base64 lub po decode).
- Frontend `ImageGenerator.js`:
  - dodać `input type=file` (accept `image/png,image/jpeg,webp` jeśli wspierane) + stan `referenceFile`.
  - konwersja do base64 i wysyłka w payload `reference_image`.
  - UI: chip/miniatura + przycisk „Usuń załącznik”.

- Conclude Phase 2: 1 runda testów e2e (manual + testing agent) dla:
  - admin flow
  - image generation z/bez załącznika

---

### Phase 3: Testing & Polish
**User stories**
1. Jako użytkownik, chcę by generowanie nie zawieszało UI i pokazywało loading state.
2. Jako użytkownik, chcę jasnych komunikatów błędów (timeout/model unavailable).
3. Jako admin, chcę by UI nie pozwalało dezaktywować mnie samego.
4. Jako użytkownik, chcę by upload nie psuł generowania bez pliku.
5. Jako użytkownik, chcę by dane były poprawnie zapisywane i widoczne w galerii.

**Steps**
- Uruchomić testing agent: scenariusze regresji + edge cases.
- Poprawki: walidacje, timeouts, UX drobiazgi (toasty, disable states).
- Final sanity: sprawdzić brak 401/403 w normalnych ścieżkach, brak crashy w UI.

---

## 3) Next Actions (konkretne, kolejność)
1. POC: dodać `reference_image` do backendu + test script, dopiąć multimodal do modelu i odpalić test.
2. Frontend: dodać admin route + sidebar link.
3. Frontend: dodać upload UI w `ImageGenerator.js` + wysyłka `reference_image`.
4. E2E testy + poprawki.

---

## 4) Success Criteria
- **Admin:** admin widzi link i stronę `/admin/users`, nie-admin dostaje redirect/403 UX; CRUD działa (create/toggle admin/deactivate/reactivate).
- **Image attachment:** generowanie działa w 2 trybach: bez załącznika i z 1 obrazem referencyjnym; błędy plików są czytelne; warianty działają.
- **No regressions:** dotychczasowe generowanie obrazów, galeria, artykuły i auth działają jak przed zmianami.
