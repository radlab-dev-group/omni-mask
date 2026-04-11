## Omni‑Mask – Co znajduje się w repozytorium

### Struktura pakietu

```
omni_mask/
│
├─ core/
│   ├─ __init__.py
│   └─ logic.py                # AnonymizerCore, DeanonymizerCore
│
├─ gui/
│   ├─ __init__.py
│   └─ app.py                  # interfejs Tkinter (klasa App)
│
├─ loaders/
│   ├─ __init__.py
│   ├─ base.py                 # abstrakcyjny BaseLoader
│   ├─ docx_loader.py          # obsługa .docx/.doc
│   ├─ excel_loader.py         # obsługa .xlsx/.xls
│   ├─ pdf_loader.py           # obsługa .pdf (redakcja, brak przywracania)
│   └─ text_loader.py          # obsługa .txt/.csv
│
├─ resources/
│   └─ config.json             # listy słów i reguły wykluczeń
│
├─ utils/
│   ├─ __init__.py
│   └─ validators.py           # wyrażenia regularne, funkcje walidacyjne,
│                              # loader konfiguracji, słownik ANON_TYPE_LABELS
│
└─ __init__.py
```

### Logika(`omni_mask/core/logic.py`)

* **`AnonymizerCore`**
    * Przechowuje mapowanie oryginalna wartość → pseudonim.
    * Generuje deterministyczne placeholdery w postaci `[PESEL_1]`, `[NIP_2]` itd.
    * Udostępnia `extract_matches`, `anonymize_text` oraz pomocnicze metody do wyodrębniania kontekstu.
    * Korzysta z wyrażeń regularnych i funkcji walidacyjnych z `utils.validators`.

* **`DeanonymizerCore`**
    * Wczytuje klucz mapowania (plik Excel) wygenerowany przez anonimizer.
    * Buduje wyrażenie regularne dopasowujące wszystkie pseudonimy.
    * Zastępuje pseudonimy ich pierwotnymi wartościami w podanym tekście.

### Narzędzia walidacyjne (`omni_mask/utils/validators.py`)

* Wyrażenia regularne dla: PESEL, NIP, telefon, adres, imię + nazwisko, e‑mail, IBAN, numer dowodu.
* Funkcje: `is_valid_pesel`, `is_valid_nip`, `is_likely_person_name`.
* `load_exclusions()` odczytuje domyślne wykluczenia z pliku JSON oraz opcjonalny plik `nie_koduj.txt`.
* `ANON_TYPE_LABELS` – słownik mapujący wewnętrzne klucze typu na etykiety czytelne dla użytkownika.

### Loadery (`omni_mask/loaders/`)

Wszystkie ładowarki dziedziczą po `BaseLoader` i implementują trzy metody:

| Ładowarka     | Obsługiwane rozszerzenia | `anonymize`                                                                                                 | `deanonymize`                                                    |
|---------------|--------------------------|-------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| `DocxLoader`  | `.docx`, `.doc`          | Otwiera dokument `python‑docx`, podmienia tekst w akapitach, runach i tabelach.                             | Odwraca podmianę.                                                |
| `ExcelLoader` | `.xlsx`, `.xls`          | Otwiera plik `openpyxl`, przetwarza każdą komórkę zawierającą ciąg znaków.                                  | Odwraca podmianę.                                                |
| `PDFLoader`   | `.pdf`                   | Używa PyMuPDF (`fitz`). Znajduje dopasowania, tworzy adnotacje redakcyjne z pseudonimem, aplikuje redakcję. | Rzuca `NotImplementedError` (plik PDF nie może być przywrócony). |
| `TextLoader`  | `.txt`, `.csv`           | Czyta cały plik jako UTF‑8, wywołuje `core.anonymize_text`, zapisuje wynik.                                 | Analogicznie wywołuje `core.deanonymize_text`.                   |

`BaseLoader` definiuje abstrakcyjny interfejs (`can_handle`, `anonymize`, `deanonymize`).

### Interfejs graficzny (`omni_mask/gui/app.py`)

* Jedna klasa `App` dziedzicząca po `tk.Tk`.
* Dwa zakładki w `ttk.Notebook`: **Anonimizacja** i **De‑anonimizacja**.
* Elementy UI umożliwiają wybór katalogów wejściowych/wyjściowych, zaznaczenie typów danych do maskowania oraz wskazanie
  pliku klucza przy de‑anonimizacji.
* Długotrwałe operacje wykonywane są w wątkach; kolejka `queue.Queue` przekazuje logi i postępy do UI.
* Po zakończeniu anonimizacji automatycznie tworzony jest:
    * `klucz_mapowania.xlsx` – arkusz Excel z kolumnami *Oryginalna wartość*, *Typ danych*, *Wygenerowany pseudonim*,
      *Kontekst*.
    * Raport HTML (`*_Raport_Zmian.html`).

### Konfiguracja (`omni_mask/resources/config.json`)

Plik JSON zawiera cztery listy wykorzystywane w logice wykrywania nazwisk:

* `non_name_words` – słowa, które **nigdy** nie są traktowane jako imię + nazwisko.
* `blocked_name_bigrams` – pary słów, które razem są wyraźnie wykluczone jako nazwiska (np. „szanowni państwo”).
* `non_name_suffixes` – typowe końcówki wskazujące, że wyraz nie jest nazwiskiem (np. „‑stwo”, „‑acja”).
* `default_exclusions` – ogólne wyrazy wykluczane przy sprawdzaniu nazwisk (np. „urząd”, „miasto”).

JSON jest ładowany przy importowaniu modułu `validators.Config`.
