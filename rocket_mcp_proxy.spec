# -*- mode: python ; coding: utf-8 -*-
import os

def get_rich_source_datas():
    """Collect all rich .py files as data to bypass bytecode analysis."""
    import rich
    rich_dir = os.path.dirname(rich.__file__)
    datas = []
    for root, dirs, files in os.walk(rich_dir):
        for fname in files:
            if fname.endswith(('.py', '.pyi')):
                full_path = os.path.join(root, fname)
                dest = os.path.join('rich', os.path.relpath(root, rich_dir))
                datas.append((full_path, dest))
    return datas

# Collect fastmcp and mcp metadata
from PyInstaller.utils.hooks import copy_metadata
datas = copy_metadata('fastmcp') + copy_metadata('mcp')
datas += get_rich_source_datas()

a = Analysis(
    ['C:/Work/AI_Repos/personal/rashmith-18m/mcp-http-proxy/rocket_mcp_proxy.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['mcp', 'mcp.types', 'mcp.shared', 'mcp.client', 'mcp.server', 'mcp.client.sse', 'fastmcp.client.auth', 'fastmcp.client.auth.oauth', 'fastmcp.client.oauth_callback', 'fastmcp.server.providers.proxy'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['mcp.cli', 'rich'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='rocket_mcp_proxy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
