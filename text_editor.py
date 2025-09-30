"""Text Editor app (very small)

Usage:
    python text_editor.py view file.txt
    python text_editor.py write file.txt "some text"
"""
from __future__ import annotations
import argparse
from pathlib import Path


def view(path: Path) -> None:
    if not path.exists():
        print(f"File not found: {path}")
        return
    print(path.read_text(encoding="utf-8"))


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    print(f"Wrote to {path}")


def main() -> None:
    p = argparse.ArgumentParser(description="Tiny Text Editor")
    p.add_argument("cmd", choices=["view", "write"], help="command")
    p.add_argument("file", help="file path")
    p.add_argument("text", nargs="?", help="text to write")
    args = p.parse_args()

    path = Path(args.file)
    if args.cmd == "view":
        view(path)
    else:
        write(path, args.text or "")


if __name__ == "__main__":
    main()
