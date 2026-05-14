"""Interpreter tests."""

from __future__ import annotations

import pytest

from wok.errors import KitchenError, PantryError
from wok.interpreter import run
from wok.lexer import lex
from wok.parser import parse


def run_src(src: str):
    return run(parse(lex(src)))


@pytest.mark.parametrize("recipe_file", ["pad_thai.wok", "carbonara.wok", "omelette.wok"])
def test_example_recipes_execute(recipe_file, capsys):
    src = open(f"recipes/{recipe_file}").read()
    run_src(src)
    captured = capsys.readouterr().out
    # Each recipe should print at least one step line.
    assert "Serving" in captured or "Folding" in captured


def test_undeclared_ingredient_raises_pantry_error():
    src = (
        "recipe r serves 1:\n"
        "    pantry:\n"
        "        a = 1g\n"
        "    chop(mystery)\n"
    )
    with pytest.raises(PantryError) as exc_info:
        run_src(src)
    assert exc_info.value.line == 4


def test_crack_non_egg_raises_kitchen_error():
    src = (
        "recipe r serves 1:\n"
        "    pantry:\n"
        "        rice_noodles = 200g\n"
        "    crack(rice_noodles, into=wok)\n"
    )
    with pytest.raises(KitchenError):
        run_src(src)


def test_unknown_verb_raises_kitchen_error():
    src = (
        "recipe r serves 1:\n"
        "    pantry:\n"
        "        a = 1g\n"
        "    teleport(a)\n"
    )
    with pytest.raises(KitchenError):
        run_src(src)


def test_pad_thai_step_count(capsys):
    src = open("recipes/pad_thai.wok").read()
    run_src(src)
    out = capsys.readouterr().out
    # 6 numbered steps in pad_thai.
    for n in range(1, 7):
        assert f"[ {n}]" in out or f"[{n:>2}]" in out
