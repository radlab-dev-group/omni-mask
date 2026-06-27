## 🇵🇱 Omni‑Mask – Co zawiera repozytorium

Omni‑Mask to dwuwarstwowe narzędzie do anonimizacji:

1. **Wykrywanie danych osobowych (PII)** (oparte na AI) – korzysta z
   [anonymizer‑model](https://github.com/radlab-dev-group/anonymizer-model.git) (`AnonPredictor`, model
   `radlab/pii-pl-v1.0`), aby zidentyfikować osoby, lokalizacje, organizacje itp.
2. **Maskowanie oparte na wzorcach** – wykorzystuje
   [llm‑router‑plugins FastMasker](https://github.com/radlab-dev-group/llm-router-plugins.git) (`FastMasker`,
   `FastDeanonymizer` oraz ponad 30 reguł) do wykrywania PESEL, NIP, IBAN, e‑maili, adresów IP, kart kredytowych, VIN‑ów
   i nie tylko.

### Instalacja

```shell script
git clone https://github.com/radlab-dev-group/omni-mask.git
cd omni-mask
```

2. **Utwórz i aktywuj wirtualne środowisko (zalecane)**

```shell script
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

3. **Zainstaluj wymagane pakiety**

```shell script
pip install -r requirements.txt
```

Podstawowe zależności: `pandas`, `openpyxl`, `python-docx`, `PyMuPDF`, plus zewnętrzne pakiety do anonimizacji:

- [anonymizer‑model](https://github.com/radlab-dev-group/anonymizer-model.git) (`pii-classification` — wykrywanie PII
  przy pomocy `AnonPredictor`)
- [llm‑router‑plugins](https://github.com/radlab-dev-group/llm-router-plugins.git) (`llm-router-plugins` — `FastMasker`,
  `FastDeanonymizer` i ponad 30 reguł maskujących)

*`tkinter` jest częścią standardowej dystrybucji Pythona, więc nie wymaga dodatkowych działań.*

4. **(Opcjonalnie) Zainstaluj projekt w trybie edytowalnym** – przydatne przy rozwoju

```shell script
pip install -e .
```

5. **Uruchom interfejs graficzny**

```shell script
python -m omni_mask.gui.app
```

### Budowanie aplikacji macOS (.app)

Aby spakować Omni-Mask do samodzielnej aplikacji na macOS (Apple Silicon i/lub Intel), zobacz **[BUILD-PL.md](BUILD-PL.md)**.

### Struktura pakietu

```
omni_mask/
│
├─ core/
│   ├─ __init__.py
│   └─ logic.py                # AnonMaskingCore (opakowuje FastMasker + PII), DeanonymizerCore (opakowuje FastDeanonymizer)
│
├─ gui/
│   ├─ __init__.py
│   └─ app.py                  # UI w Tkinter (klasa App)
│
├─ loaders/
│   ├─ __init__.py
│   ├─ base.py                 # abstrakcyjny BaseLoader
│   ├─ docx_loader.py          # obsługa .docx/.doc
│   ├─ excel_loader.py         # obsługa .xlsx/.xls
│   ├─ pdf_loader.py           # obsługa .pdf (tylko redakcja)
│   └─ text_loader.py          # obsługa .txt/.csv
│
├─ resources/
│   └─ config.json             # listy słów i reguły wykluczeń (legacy)
│
├─ utils/
│   ├─ __init__.py
│   └─ validators.py           # starsze wyrażenia regularne i pomocnicze funkcje walidacji
│
└─ __init__.py

fast_masker/                     # kopia FastMasker z llm-router-plugins (zewnętrzne: github.com/radlab-dev-group/llm-router-plugins)
├─ fast_masker_plugin.py         # FastMaskerPlugin – punkt wejścia
├─ core/
│   ├─ __init__.py               # FastMasker, MaskerRuleI
│   ├─ masker.py                 # FastMasker, FastDeanonymizer
│   └─ rule_interface.py         # klasa bazowa MaskerRuleI
├─ rules/                        # >30 reguł: PeselRule, NipRule, EmailRule, CreditCardRule, VinRule, itp.
└─ utils/
    └─ validators.py             # funkcje pomocnicze do walidacji sum kontrolnych
```

### Logika rdzenia (`omni_mask/core/logic.py`)

* **`AnonMaskingCore`** – opakowanie wokół `FastMasker` + predyktora PII
    * `pii_enabled` / `enabled_fastmask` – zestawy etykiet typów z `PII_TYPE_LABELS` i `ANON_TYPE_LABELS`
    * `pii_anonymize_text(text, pii_labels)` → `(masked_text, mappings)` – wywołuje `AnonPredictor`, aby znaleźć PII w
      tekście
    * `accumulate_pii_mappings(mappings)` – przechowuje mapowania PII do późniejszego eksportu
    * `_build_fastmask_rules(enabled_fastmask)` → `[Rule, …]` – wybiera reguły FastMasker według typu (PESEL, NIP,
      EMAIL, itp.)
    * własność `records` – łączy zgromadzone mapowania PII + mapowania FastMasker w jeden słownik
    * Generuje deterministyczne placeholdery, np. `[PESEL_1]`, `[EMAIL_2]`, `{{EMAIL}}`, `{{PERSON}}` itd.
    * Udostępnia `anonymize_text` oraz metody pomocnicze do wyodrębniania kontekstu (deleguje do FastMasker)

* **`DeanonymizerCore`**
    * Opakowuje `FastDeanonymizer` z `llm_router_plugins`
    * Ładuje klucz mapowania (plik Excel) utworzony przez anonimizator
    * Zastępuje pseudonimy oryginalnymi wartościami poprzez `deanonymize(text)`

### Etykiety typów PII (`PII_TYPE_LABELS`)

Typy wykrywane przez AI‑opartego `AnonPredictor` (model `radlab/pii-pl-v1.0`):

| Klucz          | Etykieta    |
|----------------|-------------|
| `LOCATION`     | Lokalizacja |
| `PERSON`       | Osoba       |
| `FACILITY`     | Obiekt      |
| `ORGANIZATION` | Organizacja |
| `PRODUCT`      | Produkt     |
| `EVENT`        | Wydarzenie  |

### Etykiety typów FastMasker (`ANON_TYPE_LABELS`)

Typy wykrywane przez reguły FastMasker:

| Klucz                 | Etykieta             |
|-----------------------|----------------------|
| `PESEL`               | PESEL                |
| `NIP`                 | NIP (ID podatkowy)   |
| `TELEFON`             | Numer telefonu       |
| `EMAIL`               | Adres e‑mail         |
| `KONTO_BANKOWE`       | Konto bankowe (IBAN) |
| `DOKUMENT_TOZSAMOSCI` | Dokument tożsamości  |
| `NAZWISKO`            | Nazwisko             |
| `ADRES`               | Adres                |

### Loadery (`omni_mask/loaders/`)

Wszystkie loadery dziedziczą po `BaseLoader` i implementują metody  
`anonymize(in_dir, out_dir, pii_enabled, enabled_fastmask)` oraz  
`deanonymize(in_dir, out_dir, key_path)`:

| Loader        | Obsługiwane rozszerzenia | `anonymize`                                                                                                                     | `deanonymize`                                                    |
|---------------|--------------------------|---------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| `DocxLoader`  | `.docx`, `.doc`          | Najpierw PII za pomocą `AnonPredictor`, potem reguły wzorcowe z `FastMasker`. Zastępuje tekst w paragrafach, runach i tabelach. | Używa `FastDeanonymizer.deanonymize()` do przywracania wartości. |
| `ExcelLoader` | `.xlsx`, `.xls`          | Ten sam podwójny potok – najpierw PII, potem FastMasker. Przetwarza każdą komórkę zawierającą tekst.                            | Używa `FastDeanonymizer.deanonymize()` do przywracania wartości. |
| `PDFLoader`   | `.pdf`                   | PII przez `AnonPredictor`, potem FastMasker przy użyciu adnotacji redakcyjnych w PyMuPDF.                                       | Rzuca `NotImplementedError` (PDF‑y nie mogą być odtwarzane).     |
| `TextLoader`  | `.txt`, `.csv`           | PII + FastMasker stosowane kolejno na całej treści pliku; zapisuje zamaskowany wynik z powrotem.                                | Używa `FastDeanonymizer.deanonymize()` do przywracania wartości. |

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
