"""
Build script to compile rocket_mcp_proxy.py into a standalone binary.

Usage:
    python build_proxy.py

Output:
    dist/rocket_mcp_proxy       (Linux/macOS)
    dist/rocket_mcp_proxy.exe   (Windows)

Prerequisites:
    pip install pyinstaller fastmcp

The compiled binary has the URL allowlist baked in and cannot be edited
without access to the source and rebuild toolchain.
"""

import subprocess
import sys
import os


def main():
    base_dir = sys.path[0] or "."

    # Generate a .spec file that works around the Python 3.10.0 dis.py bug
    # by excluding 'rich' from bytecode analysis but including it as source files
    spec_content = generate_spec(base_dir)
    spec_path = os.path.join(base_dir, "rocket_mcp_proxy.spec")
    with open(spec_path, "w") as f:
        f.write(spec_content)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",                            # Clean build cache
        "--noconfirm",                        # Overwrite without prompt
        spec_path,
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=base_dir)
    if result.returncode == 0:
        print("\nBuild successful! Binary is in dist/rocket_mcp_proxy")
    else:
        print("\nBuild failed.", file=sys.stderr)
        sys.exit(1)


def generate_spec(base_dir):
    """Generate a PyInstaller .spec that bundles rich as source to avoid dis.py bug."""
    script_path = os.path.join(base_dir, "rocket_mcp_proxy.py").replace(os.sep, "/")
    return f'''# -*- mode: python ; coding: utf-8 -*-
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
    ['{script_path}'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['mcp', 'mcp.types', 'mcp.shared', 'mcp.client', 'mcp.server', 'mcp.client.sse', 'fastmcp.client.auth', 'fastmcp.client.auth.oauth', 'fastmcp.client.oauth_callback', 'fastmcp.server.providers.proxy'],
    hookspath=[],
    hooksconfig={{}},
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
'''


if __name__ == "__main__":
    main()
