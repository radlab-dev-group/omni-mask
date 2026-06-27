## 🇬🇧 Omni‑Mask – What the repository actually contains

Omni‑Mask is a dual‑tier anonymization tool:

1. **PII detection** (AI‑based) – uses
   the [anonymizer-model](https://github.com/radlab-dev-group/anonymizer-model.git) (`AnonPredictor`, model
   `radlab/pii-pl-v1.0`) to identify persons, locations, organizations, etc.
2. **Pattern-based masking** – uses
   the [llm-router-plugins FastMasker](https://github.com/radlab-dev-group/llm-router-plugins.git) (`FastMasker`,
   `FastDeanonymizer` and 30+ rules) to detect PESEL, NIP, IBAN, emails, IPs, credit cards, VINs and more.

### Installation

```shell script
git clone https://github.com/radlab-dev-group/omni-mask.git
cd omni-mask
```

2. **Create and activate a virtual environment (recommended)**

```shell script
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

3. **Install the required packages**

```shell script
pip install -r requirements.txt
```

Core dependencies: `pandas`, `openpyxl`, `python-docx`, `PyMuPDF`, plus external anonymization packages:

- [anonymizer-model](https://github.com/radlab-dev-group/anonymizer-model.git) (`pii-classification` — PII detection via
  `AnonPredictor`)
- [llm-router-plugins](https://github.com/radlab-dev-group/llm-router-plugins.git) (`llm-router-plugins` — `FastMasker`,
  `FastDeanonymizer` and 30+ masking rules)

*`tkinter` comes with the standard Python distribution, so no extra step is needed.*

4. **(Optional) Install the project in editable mode** – useful for development

```shell script
pip install -e .
```

5. **Run the GUI**

```shell script
python -m omni_mask.gui.app
```

### Building macOS apps (.app)

To package Omni-Mask as a standalone macOS application (Apple Silicon and/or Intel), see **[BUILD-PL.md](BUILD-PL.md)** (Polish).

### Package layout

```
omni_mask/
│
├─ core/
│   ├─ __init__.py
│   └─ logic.py                # AnonMaskingCore (wraps FastMasker + PII), DeanonymizerCore (wraps FastDeanonymizer)
│
├─ gui/
│   ├─ __init__.py
│   └─ app.py                  # Tkinter UI (class App)
│
├─ loaders/
│   ├─ __init__.py
│   ├─ base.py                 # abstract BaseLoader
│   ├─ docx_loader.py          # .docx/.doc handling
│   ├─ excel_loader.py         # .xlsx/.xls handling
│   ├─ pdf_loader.py           # .pdf handling (redaction only)
│   └─ text_loader.py          # .txt/.csv handling
│
├─ resources/
│   └─ config.json             # word‑lists and exclusion rules (legacy)
│
├─ utils/
│   ├─ __init__.py
│   └─ validators.py           # legacy regexes & validation helpers
│
└─ __init__.py

fast_masker/                     # copy of llm-router-plugins FastMasker (external: github.com/radlab-dev-group/llm-router-plugins)
├─ fast_masker_plugin.py         # FastMaskerPlugin – entry point
├─ core/
│   ├─ __init__.py               # FastMasker, MaskerRuleI
│   ├─ masker.py                 # FastMasker, FastDeanonymizer
│   └─ rule_interface.py         # MaskerRuleI base class
├─ rules/                        # 30+ rules: PeselRule, NipRule, EmailRule, CreditCardRule, VinRule, etc.
└─ utils/
    └─ validators.py             # checksum validation helpers
```

### Core logic (`omni_mask/core/logic.py`)

* **`AnonMaskingCore`** – wrapper around `FastMasker` + PII predictor
    * `pii_enabled` / `enabled_fastmask` – sets of type labels from `PII_TYPE_LABELS` and `ANON_TYPE_LABELS`
    * `pii_anonymize_text(text, pii_labels)` → `(masked_text, mappings)` – calls `AnonPredictor` to find PII in the text
    * `accumulate_pii_mappings(mappings)` – stores PII mappings for later export
    * `_build_fastmask_rules(enabled_fastmask)` → `[Rule, …]` – selects FastMasker rules by type (PESEL, NIP, EMAIL,
      etc.)
    * `records` property – merges accumulated PII mappings + FastMasker mappings into a single dict
    * Generates deterministic placeholders like `[PESEL_1]`, `[EMAIL_2]`, `{{EMAIL}}`, `{{PERSON}}`, etc.
    * Provides `anonymize_text` and helper methods for context extraction (delegates to FastMasker)

* **`DeanonymizerCore`**
    * Wraps `FastDeanonymizer` from `llm_router_plugins`
    * Loads a mapping key (Excel file) created by the anonymiser
    * Replaces pseudonyms with original values via `deanonymize(text)`

### PII type labels (`PII_TYPE_LABELS`)

Types detected by the AI‑based `AnonPredictor` (model `radlab/pii-pl-v1.0`):

| Key            | Label       |
|----------------|-------------|
| `LOCATION`     | Lokalizacja |
| `PERSON`       | Osoba       |
| `FACILITY`     | Obiekt      |
| `ORGANIZATION` | Organizacja |
| `PRODUCT`      | Produkt     |
| `EVENT`        | Wydarzenie  |

### FastMasker type labels (`ANON_TYPE_LABELS`)

Pattern types detected by FastMasker rules:

| Key                   | Label                |
|-----------------------|----------------------|
| `PESEL`               | PESEL                |
| `NIP`                 | NIP (ID podatkowy)   |
| `TELEFON`             | Numer telefonu       |
| `EMAIL`               | Adres e-mail         |
| `KONTO_BANKOWE`       | Konto bankowe (IBAN) |
| `DOKUMENT_TOZSAMOSCI` | Dokument tożsamości  |
| `NAZWISKO`            | Nazwisko             |
| `ADRES`               | Adres                |

### Loaders (`omni_mask/loaders/`)

All loaders inherit from `BaseLoader` and implement `anonymize(in_dir, out_dir, pii_enabled, enabled_fastmask)` and
`deanonymize(in_dir, out_dir, key_path)`:

| Loader        | File extensions handled | `anonymize`                                                                                                        | `deanonymize`                                            |
|---------------|-------------------------|--------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------|
| `DocxLoader`  | `.docx`, `.doc`         | PII via `AnonPredictor` first, then pattern rules via `FastMasker`. Replaces text in paragraphs, runs, and tables. | Uses `FastDeanonymizer.deanonymize()` to restore values. |
| `ExcelLoader` | `.xlsx`, `.xls`         | Same dual pipeline – PII first, then FastMasker. Processes every cell containing a string.                         | Uses `FastDeanonymizer.deanonymize()` to restore values. |
| `PDFLoader`   | `.pdf`                  | PII via `AnonPredictor`, then FastMasker via `PyMuPDF` redaction annotations.                                      | Raises `NotImplementedError` (PDFs cannot be restored).  |
| `TextLoader`  | `.txt`, `.csv`          | PII + FastMasker applied sequentially on the whole file content; writes masked output back.                        | Uses `FastDeanonymizer.deanonymize()` to restore values. |

`BaseLoader` defines the abstract interface (`can_handle`, `anonymize`, `deanonymize`).

### GUI (`omni_mask/gui/app.py`)

* A single `App` class derived from `tk.Tk`.
* Two notebook tabs: **Anonymisation** and **De‑anonymisation**.
* UI elements for selecting input/output directories, choosing which data types to mask, and specifying the mapping key
  file for de‑anonymisation.
* **PII checkbox section** – checkboxes for each type in `PII_TYPE_LABELS` (LOCATION, PERSON, ORGANIZATION, …).
* **FastMasker checkbox section** – checkboxes for each type in `ANON_TYPE_LABELS` (PESEL, NIP, EMAIL, …).
* Background threads perform the heavy work; a `queue.Queue` delivers log messages and progress updates to the UI.
* After anonymisation it automatically writes:
    * `klucz_mapowania.xlsx` – Excel file with columns *Original value*, *Data type*, *Generated pseudonym*, *Context*.
    * An HTML audit report (`*_Raport_Zmian.html`).
