"""Hand-written recursive-descent parser for wok.

Grammar (informal):
    recipe   := "recipe" IDENT "serves" NUMBER ":" NEWLINE INDENT pantry step+ DEDENT
    pantry   := "pantry" ":" NEWLINE INDENT (IDENT "=" value NEWLINE)+ DEDENT
    step     := IDENT "(" arglist? ")" NEWLINE
    arglist  := arg ("," arg)*
    arg      := kwarg | value
    kwarg    := IDENT "=" value
    value    := quantity | duration | count | IDENT
"""

from __future__ import annotations

from .ast_nodes import (
    Count,
    Duration,
    Ident,
    KwArg,
    PantryEntry,
    Quantity,
    Recipe,
    Step,
    Value,
)
from .errors import SyntaxKitchenError
from .lexer import Token

DURATION_UNITS = {"min", "s"}


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    # ---- token helpers --------------------------------------------------
    def peek(self, offset: int = 0) -> Token:
        return self.tokens[self.pos + offset]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, kind: str) -> Token:
        tok = self.peek()
        if tok.kind != kind:
            raise SyntaxKitchenError(
                f"expected {kind}, got {tok.kind} ({tok.value!r})",
                line=tok.line,
            )
        return self.advance()

    def match(self, *kinds: str) -> bool:
        return self.peek().kind in kinds

    # ---- grammar --------------------------------------------------------
    def parse_recipe(self) -> Recipe:
        kw = self.expect("RECIPE")
        name = self.expect("IDENT").value
        self.expect("SERVES")
        serves_tok = self.expect("NUMBER")
        try:
            serves = int(serves_tok.value)
        except ValueError:
            raise SyntaxKitchenError(
                f"'serves' must be an integer, got {serves_tok.value!r}",
                line=serves_tok.line,
            )
        self.expect("COLON")
        self.expect("NEWLINE")
        self.expect("INDENT")

        pantry = self.parse_pantry()

        steps: list[Step] = []
        while not self.match("DEDENT", "EOF"):
            steps.append(self.parse_step())

        if not steps:
            raise SyntaxKitchenError(
                "recipe has no steps — a recipe needs at least one verb",
                line=kw.line,
            )

        if self.match("DEDENT"):
            self.advance()

        return Recipe(name=name, serves=serves, pantry=pantry, steps=steps, line=kw.line)

    def parse_pantry(self) -> list[PantryEntry]:
        self.expect("PANTRY")
        self.expect("COLON")
        self.expect("NEWLINE")
        self.expect("INDENT")

        entries: list[PantryEntry] = []
        while not self.match("DEDENT", "EOF"):
            ident = self.expect("IDENT")
            self.expect("EQUALS")
            value = self.parse_value()
            self.expect("NEWLINE")
            entries.append(PantryEntry(name=ident.value, value=value, line=ident.line))

        self.expect("DEDENT")
        if not entries:
            raise SyntaxKitchenError("pantry is empty", line=self.peek().line)
        return entries

    def parse_step(self) -> Step:
        verb_tok = self.expect("IDENT")
        self.expect("LPAREN")
        args: list[Value] = []
        kwargs: list[KwArg] = []

        if not self.match("RPAREN"):
            self._parse_arg(args, kwargs)
            while self.match("COMMA"):
                self.advance()
                self._parse_arg(args, kwargs)

        self.expect("RPAREN")
        self.expect("NEWLINE")
        return Step(verb=verb_tok.value, args=args, kwargs=kwargs, line=verb_tok.line)

    def _parse_arg(self, args: list[Value], kwargs: list[KwArg]) -> None:
        # A kwarg is either `IDENT "=" value` or one of the reserved
        # connector keywords (in/into/for/until/with/sauce/garnish)
        # followed by "=".
        tok = self.peek()
        connector_kinds = {"IN", "INTO", "FOR", "UNTIL", "WITH", "SAUCE", "GARNISH"}

        if (tok.kind == "IDENT" or tok.kind in connector_kinds) and self.peek(1).kind == "EQUALS":
            name_tok = self.advance()
            self.expect("EQUALS")
            value = self.parse_value()
            if kwargs and any(k.name == name_tok.value for k in kwargs):
                raise SyntaxKitchenError(
                    f"duplicate keyword argument '{name_tok.value}'",
                    line=name_tok.line,
                )
            kwargs.append(KwArg(name=name_tok.value, value=value, line=name_tok.line))
            return

        if kwargs:
            raise SyntaxKitchenError(
                "positional argument after keyword argument",
                line=tok.line,
            )
        args.append(self.parse_value())

    def parse_value(self) -> Value:
        tok = self.peek()
        if tok.kind == "NUMBER":
            num_tok = self.advance()
            amount = float(num_tok.value)
            if self.match("UNIT"):
                unit_tok = self.advance()
                if unit_tok.value in DURATION_UNITS:
                    return Duration(amount=amount, unit=unit_tok.value, line=num_tok.line)
                return Quantity(amount=amount, unit=unit_tok.value, line=num_tok.line)
            # bare number — a count (e.g. "eggs = 2")
            if amount != int(amount):
                raise SyntaxKitchenError(
                    f"bare number must be an integer count, got {num_tok.value}",
                    line=num_tok.line,
                )
            return Count(amount=int(amount), line=num_tok.line)

        if tok.kind == "IDENT":
            self.advance()
            return Ident(name=tok.value, line=tok.line)

        raise SyntaxKitchenError(
            f"expected a value, got {tok.kind} ({tok.value!r})",
            line=tok.line,
        )


def parse(tokens: list[Token]) -> Recipe:
    """Top-level entry: parse a token stream into a Recipe AST."""
    p = Parser(tokens)
    recipe = p.parse_recipe()
    if p.peek().kind != "EOF":
        tok = p.peek()
        raise SyntaxKitchenError(
            f"unexpected token after recipe: {tok.kind} ({tok.value!r})",
            line=tok.line,
        )
    return recipe
