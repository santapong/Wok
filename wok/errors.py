"""Kitchen-themed errors raised by the wok interpreter."""

from __future__ import annotations


class WokError(Exception):
    """Base class for all wok errors."""

    def __init__(self, message: str, line: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.line = line

    def __str__(self) -> str:
        if self.line is not None:
            return f"{self.kind()} (line {self.line}): {self.message}"
        return f"{self.kind()}: {self.message}"

    def kind(self) -> str:
        return type(self).__name__


class SyntaxKitchenError(WokError):
    """Raised by the lexer/parser when a recipe is malformed."""


class PantryError(WokError):
    """An ingredient is missing from the pantry."""


class KitchenError(WokError):
    """A verb was applied incorrectly (wrong target, wrong state)."""


class MeasureError(WokError):
    """Incompatible units used together."""
