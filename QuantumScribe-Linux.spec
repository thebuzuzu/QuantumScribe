# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [
    ('localwhisper/assets/icon.png', 'localwhisper/assets'),
    ('localwhisper/assets/tray-icon.png', 'localwhisper/assets'),
]
binaries = []
hiddenimports = [
    'huggingface_hub', 'pynput',
    'PIL._tkinter_finder', 'gi', 'gi.repository.Gtk',
    'gi.repository.AyatanaAppIndicator3',
]
tmp_ret = collect_all('faster_whisper')
datas += [item for item in tmp_ret[0] if 'silero_vad' not in str(item[0]).lower()]
binaries += tmp_ret[1]
hiddenimports += [name for name in tmp_ret[2] if 'silero_vad' not in name.lower()]
tmp_ret = collect_all('ctranslate2')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('av')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('gi')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch', 'torchaudio', 'silero_vad', 'nvidia', 'onnxruntime',
        'matplotlib', 'contourpy', 'cycler', 'fonttools', 'kiwisolver',
        'comtypes', 'uiautomation', 'hf_xet'
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='QuantumScribe',
    icon='localwhisper/assets/icon.png',
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
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='QuantumScribe',
)
