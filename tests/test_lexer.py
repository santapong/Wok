"""Lexer tests."""

from __future__ import annotations

import pytest

from wok.errors import SyntaxKitchenError
from wok.lexer import lex


def kinds(source: str) -> list[str]:
    return [t.kind for t in lex(source)]


def test_empty_source():
    assert kinds("") == ["EOF"]


def test_blank_and_comment_lines_skipped():
    src = "\n# a comment\n   \n"
    assert kinds(src) == ["EOF"]


def test_keywords_recognised():
    src = "recipe x serves 2:\n"
    assert kinds(src) == ["RECIPE", "IDENT", "SERVES", "NUMBER", "COLON", "NEWLINE", "EOF"]


def test_quantity_attached():
    toks = lex("    rice = 200g\n")
    kinds_ = [t.kind for t in toks]
    assert "NUMBER" in kinds_ and "UNIT" in kinds_
    num = next(t for t in toks if t.kind == "NUMBER")
    unit = next(t for t in toks if t.kind == "UNIT")
    assert num.value == "200" and unit.value == "g"


def test_quantity_with_space():
    toks = lex("    sugar = 2 tbsp\n")
    units = [t for t in toks if t.kind == "UNIT"]
    assert len(units) == 1 and units[0].value == "tbsp"


def test_indent_dedent_balanced():
    src = "recipe x serves 1:\n    pantry:\n        a = 1g\n"
    ks = kinds(src)
    assert ks.count("INDENT") == ks.count("DEDENT") == 2


def test_punctuation():
    toks = [t.kind for t in lex("step(a, b=1)\n")]
    assert "LPAREN" in toks and "RPAREN" in toks
    assert "COMMA" in toks and "EQUALS" in toks


def test_decimal_number():
    toks = lex("    a = 2.5g\n")
    num = next(t for t in toks if t.kind == "NUMBER")
    assert num.value == "2.5"


def test_unknown_unit_after_number():
    with pytest.raises(SyntaxKitchenError):
        lex("    a = 5xyz\n")


def test_unexpected_character():
    with pytest.raises(SyntaxKitchenError):
        lex("recipe @\n")


def test_tabs_rejected():
    with pytest.raises(SyntaxKitchenError):
        lex("recipe x serves 1:\n\tpantry:\n")


def test_identifier_with_underscore():
    toks = lex("rice_noodles = 1g\n")
    ident = next(t for t in toks if t.kind == "IDENT")
    assert ident.value == "rice_noodles"


def test_real_recipe_lexes():
    src = open("recipes/pad_thai.wok").read()
    toks = lex(src)
    assert toks[-1].kind == "EOF"
    # opening 'recipe' keyword present
    assert toks[0].kind == "RECIPE"
