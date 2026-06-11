"""`wok` command-line entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from . import __version__
from .errors import WokError
from .interpreter import run as run_recipe
from .lexer import lex
from .parser import parse

console = Console()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="wok",
        description="Run .wok recipe files. A tiny recipe-as-language.",
    )
    p.add_argument("--version", action="version", version=f"wok {__version__}")
    sub = p.add_subparsers(dest="command", metavar="command")

    run = sub.add_parser("run", help="Execute a .wok recipe file")
    run.add_argument("path", type=Path, help="Path to a .wok file")

    return p


def _render_error(err: WokError, source: str, path: Path) -> None:
    """Pretty-print a WokError with the offending source line."""
    body_lines = [f"[bold red]{err.kind()}[/bold red]: {err.message}"]
    if err.line is not None:
        src_lines = source.split("\n")
        if 0 < err.line <= len(src_lines):
            snippet = src_lines[err.line - 1]
            body_lines.append("")
            body_lines.append(f"[dim]{path.name}:{err.line}[/dim]")
            body_lines.append(f"  [yellow]{err.line:>3}[/yellow] │ {snippet}")
            body_lines.append(f"        │ [red]{'^' * max(1, len(snippet.lstrip()))}[/red]")
    console.print(Panel("\n".join(body_lines), border_style="red", title="kitchen mishap",
                        title_align="left"))


def cmd_run(path: Path) -> int:
    if not path.exists():
        console.print(f"[red]error[/red]: file not found: {path}")
        return 2
    source = path.read_text(encoding="utf-8")
    try:
        tokens = lex(source)
        recipe = parse(tokens)
        recipe.source = source
        run_recipe(recipe)
    except WokError as err:
        _render_error(err, source, path)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        return cmd_run(args.path)

    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
