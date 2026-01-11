# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for QuantVision Backend
"""

import os
import sys

block_cipher = None

# Get the backend directory
backend_dir = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['run_server.py'],
    pathex=[backend_dir],
    binaries=[],
    datas=[
        ('app', 'app'),
        ('.env', '.'),
        ('alembic', 'alembic'),
        ('alembic.ini', '.'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'httptools',
        'dotenv',
        'pydantic',
        'pydantic_settings',
        'sqlalchemy',
        'sqlalchemy.dialects.postgresql',
        'asyncpg',
        'redis',
        'httpx',
        'structlog',
        'fastapi',
        'starlette',
        'anyio',
        'sniffio',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='QuantVisionBackend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Show console for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
