# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# 添加隐藏导入
hiddenimports = [
    'requests',
    'requests.adapters',
    'requests.auth',
    'requests.cookies',
    'requests.models',
    'requests.sessions',
    'requests.utils',
    'playwright',
    'playwright.sync_api',
    'playwright._impl',
    'playwright._impl._connection',
    'playwright._impl._page',
    'playwright._impl._browser_context',
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',
    'tkinter.scrolledtext',
    'customtkinter',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL._tkinter_finder',
    'json',
    'threading',
    'queue',
    'logging',
    'pathlib',
    'datetime',
    'time',
    'random',
    'typing',
    'base64',
]

# 数据文件
datas = [
    ('whisk_core_v2.py', '.'),
    ('whisk_window_queue.py', '.'),      # V2.1新增: 窗口队列管理
    ('whisk_queue_dialog.py', '.'),      # 批量任务对话框
    ('config_gui_v2.json', '.'),
    ('gui', 'gui'),                      # V3新增: GUI主题模块
]

# 如果存在downloads目录，也包含进去
if Path('downloads').exists():
    datas.append(('downloads', 'downloads'))

a = Analysis(
    ['whisk_gui_v3.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='跨海帆-Imager_V3',
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
    icon=None,
)
