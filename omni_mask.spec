# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Omni-Mask macOS builds."""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None
project_root = Path(SPECPATH)

datas = [
    (str(project_root / "omni_mask" / "resources"), "omni_mask/resources"),
]
binaries = []
hiddenimports = [
    "pii_classification.inference.inference",
    "llm_router_plugins.maskers.fast_masker.core.masker",
    "llm_router_plugins.maskers.fast_masker.rules.email_rule",
    "llm_router_plugins.maskers.fast_masker.rules.phone_rule",
    "llm_router_plugins.maskers.fast_masker.rules.phone_international_rule",
    "llm_router_plugins.maskers.fast_masker.rules.bank_account_rule",
    "llm_router_plugins.maskers.fast_masker.rules.passport_rule",
    "llm_router_plugins.maskers.fast_masker.rules.id_card_rule",
    "llm_router_plugins.maskers.fast_masker.rules.pesel_rule",
    "llm_router_plugins.maskers.fast_masker.rules.nip_rule",
    "fitz",
    "docx",
    "openpyxl",
    "pandas",
    "sklearn.utils._typedefs",
    "sklearn.neighbors._typedefs",
    "sklearn.neighbors._partition_nodes",
    "sklearn.tree._utils",
]

for package in ("torch", "transformers", "pii_classification", "llm_router_plugins"):
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

hiddenimports += collect_submodules("transformers")

a = Analysis(
    ["main.py"],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "IPython", "notebook", "tkinter.test"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="OmniMask",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="OmniMask",
)

app = BUNDLE(
    coll,
    name="OmniMask.app",
    icon=None,
    bundle_identifier="pl.radlab.omni-mask",
    info_plist={
        "CFBundleName": "OmniMask",
        "CFBundleDisplayName": "Omni-Mask",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "NSHighResolutionCapable": True,
    },
)
