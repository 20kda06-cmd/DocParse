"""Command line entry point:  python -m docparse invoice.pdf [more files] [--out DIR]"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import anthropic

from .extractor import extract_invoice


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="docparse", description="Extract structured data from invoices.")
    parser.add_argument("files", nargs="+", type=Path, help="PDF or image files")
    parser.add_argument("--out", type=Path, help="write <name>.json files here instead of printing")
    args = parser.parse_args(argv)

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)

    client = anthropic.Anthropic()
    exit_code = 0
    for path in args.files:
        try:
            invoice = extract_invoice(path, client)
        except Exception as exc:  # report and continue with the next file
            print(f"[error] {path}: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        payload = invoice.model_dump_json(indent=2)
        if args.out:
            (args.out / f"{path.stem}.json").write_text(payload, encoding="utf-8")
            print(f"[ok] {path} -> {args.out / (path.stem + '.json')}", file=sys.stderr)
        else:
            print(payload)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
