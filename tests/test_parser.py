"""Parser tests."""

from __future__ import annotations

import pytest

from wok.ast_nodes import Count, Duration, Ident, Quantity
from wok.errors import SyntaxKitchenError
from wok.lexer import lex
from wok.parser import parse


def parse_src(src: str):
    return parse(lex(src))


def test_minimal_recipe():
    src = (
        "recipe r serves 1:\n"
        "    pantry:\n"
        "        a = 1g\n"
        "    chop(a)\n"
    )
    recipe = parse_src(src)
    assert recipe.name == "r"
    assert recipe.serves == 1
    assert len(recipe.pantry) == 1
    assert len(recipe.steps) == 1
    assert recipe.steps[0].verb == "chop"


def test_quantity_vs_duration_vs_count():
    src = (
        "recipe r serves 1:\n"
        "    pantry:\n"
        "        a = 1g\n"
        "        b = 30s\n"
        "        c = 3\n"
        "    chop(a)\n"
    )
    r = parse_src(src)
    by_name = {p.name: p.value for p in r.pantry}
    assert isinstance(by_name["a"], Quantity)
    assert isinstance(by_name["b"], Duration)
    assert isinstance(by_name["c"], Count)


def test_kwarg_with_connector_keyword():
    src = (
        "recipe r serves 1:\n"
        "    pantry:\n"
        "        rice = 200g\n"
        "    soak(rice, in=water, for=10min)\n"
    )
    r = parse_src(src)
    step = r.steps[0]
    kw_names = [k.name for k in step.kwargs]
    assert kw_names == ["in", "for"]


def test_positional_after_kwarg_rejected():
    src = (
        "recipe r serves 1:\n"
        "    pantry:\n"
        "        a = 1g\n"
        "    chop(in=water, a)\n"
    )
    with pytest.raises(SyntaxKitchenError):
        parse_src(src)


def test_duplicate_kwarg_rejected():
    src = (
        "recipe r serves 1:\n"
        "    pantry:\n"
        "        a = 1g\n"
        "    soak(a, in=water, in=water, for=5min)\n"
    )
    with pytest.raises(SyntaxKitchenError):
        parse_src(src)


def test_recipe_needs_steps():
    src = (
        "recipe r serves 1:\n"
        "    pantry:\n"
        "        a = 1g\n"
    )
    with pytest.raises(SyntaxKitchenError):
        parse_src(src)


def test_serves_must_be_integer():
    src = (
        "recipe r serves 1.5:\n"
        "    pantry:\n"
        "        a = 1g\n"
        "    chop(a)\n"
    )
    with pytest.raises(SyntaxKitchenError):
        parse_src(src)


def test_missing_colon():
    src = "recipe r serves 1\n    pantry:\n        a = 1g\n    chop(a)\n"
    with pytest.raises(SyntaxKitchenError):
        parse_src(src)


def test_unexpected_value_in_step():
    src = (
        "recipe r serves 1:\n"
        "    pantry:\n"
        "        a = 1g\n"
        "    chop(=)\n"
    )
    with pytest.raises(SyntaxKitchenError):
        parse_src(src)


@pytest.mark.parametrize("recipe_file", ["pad_thai.wok", "carbonara.wok", "omelette.wok"])
def test_example_recipes_parse(recipe_file):
    src = open(f"recipes/{recipe_file}").read()
    recipe = parse_src(src)
    assert recipe.steps, "should have at least one step"
    assert recipe.pantry, "should have a pantry"


def test_ident_resolution_target():
    src = (
        "recipe r serves 1:\n"
        "    pantry:\n"
        "        a = 1g\n"
        "    crack(a, into=wok)\n"
    )
    r = parse_src(src)
    step = r.steps[0]
    assert isinstance(step.args[0], Ident)
    assert step.args[0].name == "a"
