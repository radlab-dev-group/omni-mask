# Budowanie aplikacji macOS (Omni-Mask)

Instrukcja pakowania Omni-Mask do samodzielnych aplikacji `.app` na macOS.

## Wymagania

- macOS (zalecany Mac z Apple Silicon do budowania obu wersji)
- Python 3.13 (do wersji **Apple Silicon**)
- Połączenie z internetem (instalacja zależności, pobieranie modelu PII przy pierwszym uruchomieniu aplikacji)
- ~5 GB wolnego miejsca na dysku (środowiska build + wygenerowane aplikacje)

## Pliki buildowe w repozytorium

| Plik | Opis |
|------|------|
| `omni_mask.spec` | Konfiguracja PyInstaller |
| `app-build-scripts/build_mac.sh` | Skrypt budujący `.app` |
| `omni_mask/resources/config.json` | Dane pakowane do aplikacji |

Artefakty buildu (`dist-*`, `build-*`, `.miniforge-x86_64/`) **nie trafiają do repozytorium** — są w `.gitignore`.

## Szybki start

### 1. Przygotuj środowisko dla Apple Silicon (arm64)

```bash
git clone https://github.com/radlab-dev-group/omni-mask.git
cd omni-mask

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pyinstaller
```

### 2. Zbuduj aplikacje

```bash
chmod +x app-build-scripts/build_mac.sh
./app-build-scripts/build_mac.sh all
```

Dostępne warianty:

```bash
./app-build-scripts/build_mac.sh arm64    # tylko Apple Silicon
./app-build-scripts/build_mac.sh x86_64   # tylko Intel
./app-build-scripts/build_mac.sh all      # obie wersje (domyślnie)
```

### 3. Wynik buildu

| Wersja | Ścieżka | Docelowe Maci |
|--------|---------|---------------|
| Apple Silicon | `dist-arm64/OmniMask.app` | M1, M2, M3, M4… |
| Intel | `dist-x86_64/OmniMask.app` | Maci z procesorem Intel |

Szacowany rozmiar aplikacji: **~700 MB** (arm64), **~1.7 GB** (Intel).

## Wersja Intel (x86_64) — szczegóły

PyTorch nie udostępnia wheeli dla **macOS Intel + Python 3.13**, dlatego build Intel wymaga osobnego środowiska:

- **Miniforge x86_64** (instalowany automatycznie do `.miniforge-x86_64/`)
- **Python 3.12** + PyTorch z **conda-forge**

Przy pierwszym `./app-build-scripts/build_mac.sh x86_64` lub `all` skrypt sam:

1. pobierze Miniforge (x86_64, przez Rosettę),
2. utworzy środowisko conda `omni-mask-intel`,
3. zainstaluje zależności,
4. zbuduje aplikację.

Kolejne buildy Intel są znacznie szybsze — środowisko conda zostaje na dysku.

## Uruchamianie zbudowanej aplikacji

1. Skopiuj `OmniMask.app` do folderu **Aplikacje** (lub uruchom bezpośrednio z `dist-*`).
2. Przy pierwszym uruchomieniu macOS może zablokować aplikację (brak podpisu deweloperskiego):
   - **Ustawienia systemowe → Prywatność i bezpieczeństwo → Otwórz mimo to**
3. Przy pierwszym użyciu detekcji PII aplikacja pobierze model `radlab/pii-pl-v1.0` z Hugging Face (wymaga internetu). Maskowanie wzorcowe (PESEL, NIP, e-mail itd.) działa bez tego pobierania.

## Rozwiązywanie problemów

### `ModuleNotFoundError` przy buildzie arm64

Upewnij się, że środowisko `.venv` ma wszystkie zależności:

```bash
source .venv/bin/activate
pip install -r requirements.txt pyinstaller
```

### Build Intel — błąd instalacji conda / sieci

Spróbuj ponownie. Jeśli środowisko conda jest uszkodzone, usuń je i zbuduj od nowa:

```bash
rm -rf .miniforge-x86_64 .cache
./app-build-scripts/build_mac.sh x86_64
```

### Aplikacja się nie uruchamia po skopiowaniu

Sprawdź architekturę — na Macu Apple Silicon używaj `dist-arm64/`, na Intel `dist-x86_64/`:

```bash
file dist-arm64/OmniMask.app/Contents/MacOS/OmniMask
# oczekiwane: arm64

file dist-x86_64/OmniMask.app/Contents/MacOS/OmniMask
# oczekiwane: x86_64
```

### Ponowny build od zera

```bash
rm -rf build-arm64 build-x86_64 dist-arm64 dist-x86_64
./app-build-scripts/build_mac.sh all
```

## Dystrybucja

Zbudowane `.app` można spakować do `.zip` lub `.dmg` i udostępnić poza GitHubem (aplikacje są zbyt duże na repozytorium).

Do publicznej dystrybucji warto rozważyć **podpisywanie kodu** i **notaryzację** Apple — bez tego użytkownicy mogą widzieć ostrzeżenia Gatekeepera.
