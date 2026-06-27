#!/usr/bin/env bash
# Build Omni-Mask .app bundles for macOS (arm64 and/or x86_64).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ARCH="${1:-all}"
PYTHON_ARM="${ROOT}/.venv/bin/python3"
CONDA_INTEL="${ROOT}/.miniforge-x86_64"
PYTHON_INTEL="${CONDA_INTEL}/envs/omni-mask-intel/bin/python"

build_arch() {
    local arch="$1"
    local python="$2"
    local dist_name="dist-${arch}"

    echo "=== Building OmniMask for ${arch} ==="

    rm -rf "build-${arch}" "${dist_name}"
    env TARGET_ARCH="${arch}" \
        "${python}" -m PyInstaller \
        --noconfirm \
        --clean \
        --distpath "${dist_name}" \
        --workpath "build-${arch}" \
        omni_mask.spec

    if [[ -d "${dist_name}/OmniMask.app" ]]; then
        echo "Built: ${dist_name}/OmniMask.app"
        file "${dist_name}/OmniMask.app/Contents/MacOS/OmniMask"
    else
        echo "Build failed: ${dist_name}/OmniMask.app not found" >&2
        exit 1
    fi
}

ensure_intel_venv() {
    if [[ ! -x "${PYTHON_INTEL}" ]]; then
        if [[ ! -x "${CONDA_INTEL}/bin/conda" ]]; then
            echo "Installing Miniforge (x86_64) for Intel Mac builds..."
            installer="${ROOT}/.cache/Miniforge3-MacOSX-x86_64.sh"
            mkdir -p "${ROOT}/.cache"
            if [[ ! -f "${installer}" ]]; then
                curl -fsSL \
                    "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-x86_64.sh" \
                    -o "${installer}"
            fi
            arch -x86_64 bash "${installer}" -b -p "${CONDA_INTEL}"
        fi

        echo "Creating Intel build conda env (Python 3.12 + PyTorch)..."
        arch -x86_64 "${CONDA_INTEL}/bin/conda" create -y -n omni-mask-intel python=3.12
        arch -x86_64 "${CONDA_INTEL}/bin/conda" install -y -n omni-mask-intel -c conda-forge \
            pytorch transformers pandas openpyxl lxml pyinstaller
        arch -x86_64 "${PYTHON_INTEL}" -m pip install \
            "python-docx>=1.1.2" "PyMuPDF>=1.24.0"
        arch -x86_64 "${PYTHON_INTEL}" -m pip install \
            "llm-router-plugins @ git+https://github.com/radlab-dev-group/llm-router-plugins.git"
        arch -x86_64 "${PYTHON_INTEL}" -m pip install \
            "pii-classification @ git+https://github.com/radlab-dev-group/anonymizer-model.git"
    fi
}

case "${ARCH}" in
    arm64)
        build_arch arm64 "${PYTHON_ARM}"
        ;;
    x86_64|intel)
        ensure_intel_venv
        build_arch x86_64 "${PYTHON_INTEL}"
        ;;
    all)
        build_arch arm64 "${PYTHON_ARM}"
        ensure_intel_venv
        build_arch x86_64 "${PYTHON_INTEL}"
        ;;
    *)
        echo "Usage: $0 [arm64|x86_64|all]" >&2
        exit 1
        ;;
esac

echo "Done."
