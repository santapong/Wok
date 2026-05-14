"""The 10 cooking verbs. Each prints a Rich status line and validates args."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from rich.console import Console

from .ast_nodes import Duration, Quantity
from .errors import KitchenError

console = Console()

# Cracking is reserved for things that come in a shell.
CRACKABLE = {"egg", "eggs", "coconut", "walnut", "walnuts"}


@dataclass
class VerbResult:
    name: str
    consumed: list[str]


def _fmt(val: Any) -> str:
    if isinstance(val, (Quantity, Duration)):
        return str(val)
    return str(val)


def _print(step_no: int, body: str) -> None:
    console.print(f"[cyan][{step_no:>2}][/cyan] {body}")


def _require(name: str, kwargs: dict, *required: str, line: int) -> None:
    missing = [k for k in required if k not in kwargs]
    if missing:
        raise KitchenError(
            f"{name}() missing required argument(s): {', '.join(missing)}",
            line=line,
        )


def _no_extra(name: str, kwargs: dict, allowed: set[str], line: int) -> None:
    extra = set(kwargs) - allowed
    if extra:
        raise KitchenError(
            f"{name}() got unexpected argument(s): {', '.join(sorted(extra))}",
            line=line,
        )


def verb_soak(args, kwargs, *, line, step_no):
    _no_extra("soak", kwargs, {"in", "for"}, line)
    _require("soak", kwargs, "in", "for", line=line)
    if len(args) != 1:
        raise KitchenError("soak() needs exactly one ingredient", line=line)
    _print(step_no, f"🌊 Soaking [bold]{args[0]}[/bold] in {_fmt(kwargs['in'])} "
                    f"for {_fmt(kwargs['for'])}...")
    return VerbResult("soak", [str(args[0])])


def verb_heat(args, kwargs, *, line, step_no):
    _no_extra("heat", kwargs, {"until", "for"}, line)
    if len(args) != 1:
        raise KitchenError("heat() needs exactly one target (e.g. wok)", line=line)
    if "until" not in kwargs and "for" not in kwargs:
        raise KitchenError("heat() needs either 'until=' or 'for='", line=line)
    target = args[0]
    if "until" in kwargs:
        _print(step_no, f"🔥 Heating [bold]{target}[/bold] until {_fmt(kwargs['until'])}...")
    else:
        _print(step_no, f"🔥 Heating [bold]{target}[/bold] for {_fmt(kwargs['for'])}...")
    return VerbResult("heat", [])


def verb_saute(args, kwargs, *, line, step_no):
    _no_extra("sauté", kwargs, {"in", "for"}, line)
    _require("sauté", kwargs, "in", "for", line=line)
    if len(args) != 1:
        raise KitchenError("sauté() needs exactly one ingredient", line=line)
    _print(step_no, f"🧄 Sautéing [bold]{args[0]}[/bold] in {_fmt(kwargs['in'])} "
                    f"for {_fmt(kwargs['for'])}...")
    return VerbResult("sauté", [str(args[0])])


def verb_crack(args, kwargs, *, line, step_no):
    _no_extra("crack", kwargs, {"into"}, line)
    _require("crack", kwargs, "into", line=line)
    if len(args) != 1:
        raise KitchenError("crack() needs exactly one ingredient", line=line)
    ingredient = str(args[0])
    base = ingredient.rstrip("s").lower()
    if ingredient.lower() not in CRACKABLE and base not in CRACKABLE:
        raise KitchenError(
            f"can't crack {ingredient} — only eggs can be cracked",
            line=line,
        )
    _print(step_no, f"🥚 Cracking [bold]{ingredient}[/bold] into {_fmt(kwargs['into'])}...")
    return VerbResult("crack", [ingredient])


def verb_fold(args, kwargs, *, line, step_no):
    _no_extra("fold", kwargs, {"sauce"}, line)
    if len(args) != 1:
        raise KitchenError("fold() needs exactly one ingredient", line=line)
    sauce = kwargs.get("sauce")
    if sauce is None:
        _print(step_no, f"🥢 Folding [bold]{args[0]}[/bold]...")
    else:
        _print(step_no, f"🥢 Folding [bold]{args[0]}[/bold] with {_fmt(sauce)}...")
    return VerbResult("fold", [str(args[0])])


def verb_boil(args, kwargs, *, line, step_no):
    _no_extra("boil", kwargs, {"in", "for"}, line)
    _require("boil", kwargs, "in", "for", line=line)
    if len(args) != 1:
        raise KitchenError("boil() needs exactly one ingredient", line=line)
    _print(step_no, f"♨️  Boiling [bold]{args[0]}[/bold] in {_fmt(kwargs['in'])} "
                    f"for {_fmt(kwargs['for'])}...")
    return VerbResult("boil", [str(args[0])])


def verb_chop(args, kwargs, *, line, step_no):
    _no_extra("chop", kwargs, set(), line)
    if len(args) != 1:
        raise KitchenError("chop() needs exactly one ingredient", line=line)
    _print(step_no, f"🔪 Chopping [bold]{args[0]}[/bold]...")
    return VerbResult("chop", [str(args[0])])


def verb_season(args, kwargs, *, line, step_no):
    _no_extra("season", kwargs, {"with"}, line)
    _require("season", kwargs, "with", line=line)
    if len(args) != 1:
        raise KitchenError("season() needs exactly one target", line=line)
    _print(step_no, f"🧂 Seasoning [bold]{args[0]}[/bold] with {_fmt(kwargs['with'])}...")
    return VerbResult("season", [str(args[0])])


def verb_wait(args, kwargs, *, line, step_no):
    _no_extra("wait", kwargs, set(), line)
    if len(args) != 1:
        raise KitchenError("wait() needs exactly one duration", line=line)
    duration = args[0]
    if not isinstance(duration, Duration):
        raise KitchenError(
            f"wait() expects a duration (e.g. 30s, 5min), got {duration!r}",
            line=line,
        )
    _print(step_no, f"⏳ Waiting [bold]{_fmt(duration)}[/bold]...")
    return VerbResult("wait", [])


def verb_serve(args, kwargs, *, line, step_no):
    _no_extra("serve", kwargs, {"garnish"}, line)
    if args:
        raise KitchenError("serve() takes no positional arguments", line=line)
    if "garnish" in kwargs:
        _print(step_no, f"🍽️  Serving, garnished with [bold]{_fmt(kwargs['garnish'])}[/bold].")
    else:
        _print(step_no, "🍽️  Serving.")
    return VerbResult("serve", [])


VERB_TABLE: dict[str, Callable[..., VerbResult]] = {
    "soak": verb_soak,
    "heat": verb_heat,
    "sauté": verb_saute,
    "saute": verb_saute,
    "crack": verb_crack,
    "fold": verb_fold,
    "boil": verb_boil,
    "chop": verb_chop,
    "season": verb_season,
    "wait": verb_wait,
    "serve": verb_serve,
}
