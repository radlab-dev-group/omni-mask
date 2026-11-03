#!/usr/bin/env bash
set -euo pipefail

# Directory of this script (project root)
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# Resolve Python executable (prefer virtual environments if present)
PYTHON_EXEC=""
if [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/python" ]]; then
    PYTHON_EXEC="${VIRTUAL_ENV}/bin/python"
elif [[ -x "${ROOT}/.venv/bin/python" ]]; then
    PYTHON_EXEC="${ROOT}/.venv/bin/python"
elif [[ -x "${ROOT}/.venv-new/bin/python" ]]; then
    PYTHON_EXEC="${ROOT}/.venv-new/bin/python"
elif [[ -x "${ROOT}/venv/bin/python" ]]; then
    PYTHON_EXEC="${ROOT}/venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_EXEC="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_EXEC="python"
else
    echo "Błąd: Nie znaleziono interpretera Pythona." >&2
    exit 1
fi

# Set PYTHONPATH to include project root and local development packages if available
EXTRA_PATHS=("$ROOT")
if [[ -d "${ROOT}/../llm-router-plugins" ]]; then
    EXTRA_PATHS+=("$(cd "${ROOT}/../llm-router-plugins" && pwd)")
fi
if [[ -d "${ROOT}/../anonymizer-model" ]]; then
    EXTRA_PATHS+=("$(cd "${ROOT}/../anonymizer-model" && pwd)")
fi

PYTHONPATH_ADD="$(IFS=:; echo "${EXTRA_PATHS[*]}")"
export PYTHONPATH="${PYTHONPATH_ADD}${PYTHONPATH:+:${PYTHONPATH}}"

echo "Uruchamianie Omni-Mask (${PYTHON_EXEC})..."
exec "${PYTHON_EXEC}" "${ROOT}/main.py" "$@"
