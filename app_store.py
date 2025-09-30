"""Simple App Store

Reads `ProStore.txt` to discover available apps. Supports listing apps and "downloading"
an app by copying its script into a `downloads/` directory.

Usage:
    python app_store.py list
    python app_store.py download "Calculator"
"""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).parent
PRO_STORE = ROOT / "ProStore.txt"
DOWNLOADS = ROOT / "downloads"

# mapping from app title to script filename
APP_MAP = {
    "Calculator": "calculator.py",
    "Text Editor": "text_editor.py",
    "Browser": "browser.py",
}


def read_store() -> list[str]:
    if not PRO_STORE.exists():
        return []
    text = PRO_STORE.read_text(encoding="utf-8")
    # naive parse: lines with non-empty text
    apps = [line.strip() for line in text.splitlines() if line.strip()]
    return apps


def list_apps() -> None:
    apps = read_store()
    if not apps:
        print("No apps available")
        return
    print("Available apps:")
    for a in apps:
        print(" -", a)


def download_app(app_name: str) -> None:
    apps = read_store()
    if app_name not in apps:
        print(f"App not found in store: {app_name}")
        return
    script = APP_MAP.get(app_name)
    if not script:
        print(f"No script mapped for app: {app_name}")
        return
    src = ROOT / script
    if not src.exists():
        print(f"App script missing: {src}")
        return
    DOWNLOADS.mkdir(exist_ok=True)
    dest = DOWNLOADS / src.name
    shutil.copy2(src, dest)
    print(f"Downloaded {app_name} -> {dest}")


def main() -> None:
    p = argparse.ArgumentParser(description="Mini App Store")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("list")
    d = sub.add_parser("download")
    d.add_argument("app", help="App name exactly as in ProStore.txt")

    args = p.parse_args()
    if args.cmd == "list":
        list_apps()
    elif args.cmd == "download":
        download_app(args.app)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
