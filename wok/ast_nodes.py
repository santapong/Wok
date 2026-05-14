"""AST node dataclasses for wok programs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union


@dataclass
class Ident:
    name: str
    line: int


@dataclass
class Quantity:
    amount: float
    unit: str
    line: int

    def __str__(self) -> str:
        amt = int(self.amount) if self.amount == int(self.amount) else self.amount
        return f"{amt}{self.unit}"


@dataclass
class Duration:
    amount: float
    unit: str  # "min" or "s"
    line: int

    def __str__(self) -> str:
        amt = int(self.amount) if self.amount == int(self.amount) else self.amount
        return f"{amt}{self.unit}"


@dataclass
class Count:
    amount: int
    line: int

    def __str__(self) -> str:
        return str(self.amount)


Value = Union[Quantity, Duration, Count, Ident]


@dataclass
class KwArg:
    name: str
    value: Value
    line: int


@dataclass
class Step:
    verb: str
    args: list[Value]
    kwargs: list[KwArg]
    line: int


@dataclass
class PantryEntry:
    name: str
    value: Value
    line: int


@dataclass
class Recipe:
    name: str
    serves: int
    pantry: list[PantryEntry]
    steps: list[Step]
    line: int = 1
    source: str = field(default="")
