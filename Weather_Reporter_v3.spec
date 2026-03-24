# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['Weather_Reporter_v3.py'],
    pathex=[],
    binaries=[],
    datas=[('weather_icon.ico', '.'), ('config.json', '.'), ('NotoSans-Regular.ttf', '.'), ('NotoSans-Bold.ttf', '.'), ('icons', 'icons'), ('Pictures', 'Pictures')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Weather_Reporter_v3',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['weather_icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Weather_Reporter_v3',
)
