## 🇬🇧 Omni‑Mask – What the repository actually contains

### Installation

1. **Clone the repository**

```shell script
git clone https://github.com/your-org/omni-mask.git
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

*`tkinter` comes with the standard Python distribution, so no extra step is needed.*

4. **(Optional) Install the project in editable mode** – useful for development

```shell script
pip install -e .
```

5. **Run the GUI**

```shell script
python -m omni_mask.gui.app
```

### Package layout

```
omni_mask/
│
├─ core/
│   ├─ __init__.py
│   └─ logic.py                # AnonymizerCore, DeanonymizerCore
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
│   └─ config.json             # word‑lists and exclusion rules
│
├─ utils/
│   ├─ __init__.py
│   └─ validators.py           # regexes, validation helpers, config loader,
│                              # ANON_TYPE_LABELS dictionary
│
└─ __init__.py
```

### Core logic (`omni_mask/core/logic.py`)

* **`AnonymizerCore`**
    * Keeps a mapping of original values → pseudonyms.
    * Generates deterministic placeholders like `[PESEL_1]`, `[NIP_2]`, etc.
    * Provides `extract_matches`, `anonymize_text`, and helper methods for context extraction.
    * Uses the regexes and validation functions from `utils.validators`.

* **`DeanonymizerCore`**
    * Loads a mapping key (Excel file) created by the anonymiser.
    * Builds a compiled regex that matches all pseudonyms.
    * Replaces pseudonyms with the original values in a given text.

### Validation utilities (`omni_mask/utils/validators.py`)

* Regular expressions for PESEL, NIP, phone, address, name, e‑mail, IBAN, identity‑card.
* Functions: `is_valid_pesel`, `is_valid_nip`, `is_likely_person_name`.
* `load_exclusions()` reads the default exclusions from the JSON config and an optional `nie_koduj.txt`.
* `ANON_TYPE_LABELS` maps internal type keys to human‑readable labels.

### Loaders (`omni_mask/loaders/`)

All loaders inherit from `BaseLoader` and implement three methods:

| Loader        | File extensions handled | `anonymize`                                                                                                      | `deanonymize`                                           |
|---------------|-------------------------|------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------|
| `DocxLoader`  | `.docx`, `.doc`         | Reads a `python-docx` document, replaces text in paragraphs, runs, and tables.                                   | Reverses the replacement.                               |
| `ExcelLoader` | `.xlsx`, `.xls`         | Opens with `openpyxl`, processes every cell containing a string.                                                 | Reverses the replacement.                               |
| `PDFLoader`   | `.pdf`                  | Uses PyMuPDF (`fitz`). Finds matches, creates redaction annotations with the pseudonym, then applies redactions. | Raises `NotImplementedError` (PDFs cannot be restored). |
| `TextLoader`  | `.txt`, `.csv`          | Reads the whole file as UTF‑8 text, runs `core.anonymize_text`, writes back.                                     | Runs `core.deanonymize_text` similarly.                 |

`BaseLoader` defines the abstract interface (`can_handle`, `anonymize`, `deanonymize`).

### GUI (`omni_mask/gui/app.py`)

* A single `App` class derived from `tk.Tk`.
* Two notebook tabs: **Anonymisation** and **De‑anonymisation**.
* UI elements for selecting input/output directories, choosing which data types to mask, and specifying the mapping key
  file for de‑anonymisation.
* Background threads perform the heavy work; a `queue.Queue` delivers log messages and progress updates to the UI.
* After anonymisation it automatically writes:
    * `klucz_mapowania.xlsx` – Excel file with columns *Original value*, *Data type*, *Generated pseudonym*, *Context*.
    * An HTML audit report (`*_Raport_Zmian.html`).

### Configuration (`omni_mask/resources/config.json`)

Contains four lists used by the name‑validation logic:

* `non_name_words` – words that must not be treated as personal names.
* `blocked_name_bigrams` – pairs of words that, when occurring together, are excluded as names.
* `non_name_suffixes` – suffixes indicating a word is not a surname.
* `default_exclusions` – generic terms excluded from name detection.

The JSON is loaded by `validators.Config` at import time.
