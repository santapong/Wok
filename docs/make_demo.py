"""Regenerate docs/demo.svg from recipes/pad_thai.wok.

Usage: python docs/make_demo.py
"""

from pathlib import Path

from rich.console import Console

from wok import cli, interpreter, stdlib
from wok.lexer import lex
from wok.parser import parse

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    console = Console(record=True, width=78, force_terminal=True)
    interpreter.console = console
    stdlib.console = console
    cli.console = console

    path = ROOT / "recipes" / "pad_thai.wok"
    console.print(f"[bold green]$[/bold green] wok run recipes/{path.name}")
    recipe = parse(lex(path.read_text(encoding="utf-8")))
    interpreter.run(recipe)

    out = ROOT / "docs" / "demo.svg"
    console.save_svg(str(out), title="wok")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
