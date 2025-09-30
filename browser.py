"""Browser app (toy) - opens URLs by printing them or launching default browser

Usage:
    python browser.py open https://example.com
"""
from __future__ import annotations
import argparse
import webbrowser


def open_url(url: str) -> None:
    print(f"Opening: {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        print("Could not open URL:", e)


def main() -> None:
    p = argparse.ArgumentParser(description="Toy Browser app")
    p.add_argument("cmd", choices=["open"], help="command")
    p.add_argument("url", help="URL to open")
    args = p.parse_args()

    if args.cmd == "open":
        open_url(args.url)


if __name__ == "__main__":
    main()
