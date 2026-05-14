"""Lexer: source text -> stream of tokens.

Significant whitespace is tracked Python-style with INDENT/DEDENT tokens.
Numbers and units are emitted as separate NUMBER/UNIT tokens so the parser
can build Quantity / Duration nodes.
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import SyntaxKitchenError

KEYWORDS = {
    "recipe", "serves", "pantry",
    "in", "into", "for", "until", "with", "sauce", "garnish",
}

UNITS = {"g", "ml", "tbsp", "tsp", "cup", "min", "s"}

SINGLE_PUNCT = {
    ":": "COLON",
    ",": "COMMA",
    "(": "LPAREN",
    ")": "RPAREN",
    "=": "EQUALS",
}


@dataclass
class Token:
    kind: str
    value: str
    line: int
    col: int

    def __repr__(self) -> str:
        return f"Token({self.kind}, {self.value!r}, line={self.line}, col={self.col})"


def lex(source: str) -> list[Token]:
    tokens: list[Token] = []
    indent_stack: list[int] = [0]
    lines = source.split("\n")

    for line_no, raw in enumerate(lines, start=1):
        stripped = raw.lstrip(" ")
        # Blank lines and full-line comments are ignored — no NEWLINE emitted,
        # so they don't affect indent tracking.
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(raw) - len(stripped)
        if "\t" in raw[:indent]:
            raise SyntaxKitchenError("tabs are not allowed for indentation", line=line_no)

        # Emit INDENT / DEDENT tokens relative to the indent stack.
        if indent > indent_stack[-1]:
            indent_stack.append(indent)
            tokens.append(Token("INDENT", "", line_no, 1))
        else:
            while indent < indent_stack[-1]:
                indent_stack.pop()
                tokens.append(Token("DEDENT", "", line_no, 1))
            if indent != indent_stack[-1]:
                raise SyntaxKitchenError("inconsistent indentation", line=line_no)

        col = indent + 1
        i = indent
        line_len = len(raw)
        while i < line_len:
            ch = raw[i]
            if ch == " ":
                i += 1
                col += 1
                continue
            if ch == "#":
                break  # rest of line is a comment

            if ch in SINGLE_PUNCT:
                tokens.append(Token(SINGLE_PUNCT[ch], ch, line_no, col))
                i += 1
                col += 1
                continue

            if ch.isdigit() or (ch == "." and i + 1 < line_len and raw[i + 1].isdigit()):
                start = i
                start_col = col
                seen_dot = False
                while i < line_len and (raw[i].isdigit() or (raw[i] == "." and not seen_dot)):
                    if raw[i] == ".":
                        seen_dot = True
                    i += 1
                    col += 1
                tokens.append(Token("NUMBER", raw[start:i], line_no, start_col))
                # An immediately-attached unit (200g) becomes its own UNIT token.
                if i < line_len and raw[i].isalpha():
                    u_start = i
                    u_col = col
                    while i < line_len and raw[i].isalpha():
                        i += 1
                        col += 1
                    word = raw[u_start:i]
                    if word not in UNITS:
                        raise SyntaxKitchenError(
                            f"unknown unit '{word}' after number", line=line_no,
                        )
                    tokens.append(Token("UNIT", word, line_no, u_col))
                continue

            if ch.isalpha() or ch == "_":
                start = i
                start_col = col
                while i < line_len and (raw[i].isalnum() or raw[i] == "_"):
                    i += 1
                    col += 1
                word = raw[start:i]
                if word in KEYWORDS:
                    tokens.append(Token(word.upper(), word, line_no, start_col))
                elif word in UNITS:
                    tokens.append(Token("UNIT", word, line_no, start_col))
                else:
                    tokens.append(Token("IDENT", word, line_no, start_col))
                continue

            raise SyntaxKitchenError(
                f"unexpected character {ch!r}", line=line_no,
            )

        tokens.append(Token("NEWLINE", "", line_no, col))

    # Close any remaining open indents at end-of-file.
    final_line = len(lines)
    while len(indent_stack) > 1:
        indent_stack.pop()
        tokens.append(Token("DEDENT", "", final_line, 1))
    tokens.append(Token("EOF", "", final_line, 1))
    return tokens
