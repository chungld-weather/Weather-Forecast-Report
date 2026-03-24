# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['Weather_Reporter_v3.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('weather_icon.ico', '.'),
        ('NotoSans-Regular.ttf', '.'),
        ('NotoSans-Bold.ttf', '.'),
        ('icons', 'icons'),
        ('Pictures', 'Pictures'),
    ],
    hiddenimports=[
        # jaraco sub-packages required by pkg_resources (setuptools >= 67)
        'jaraco',
        'jaraco.text',
        'jaraco.functools',
        'jaraco.context',
        'jaraco.classes',
        'jaraco.collections',
        # pkg_resources internals
        'pkg_resources',
        'pkg_resources.extern',
        'pkg_resources._vendor',
        'pkg_resources._vendor.jaraco',
        'pkg_resources._vendor.jaraco.text',
        'pkg_resources._vendor.jaraco.functools',
        'pkg_resources._vendor.jaraco.context',
        # Other commonly missed imports
        'PIL._tkinter_finder',
        'matplotlib.backends.backend_agg',
        'matplotlib.backends.backend_pdf',
        'reportlab',
        'xlsxwriter',
        'pytz',
        'urllib3',
        'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='WeatherReporter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='weather_icon.ico',
)
