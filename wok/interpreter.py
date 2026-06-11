"""Tree-walking interpreter for wok recipes."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel

from .ast_nodes import Count, Duration, Ident, Recipe, Step
from .errors import KitchenError, MeasureError, PantryError
from .stdlib import VERB_TABLE

console = Console()

# Bare ingredients that can show up in a recipe without being declared in
# the pantry — water, salt and the cooking vessel itself.
BUILTIN_INGREDIENTS = {"water", "salt", "pepper", "wok", "pan", "pot"}

# Bare adjectives valid as `until=` states.
BUILTIN_STATES = {"smoking", "boiling", "golden", "browned", "soft", "tender"}


class Environment:
    """The pantry — a name -> value mapping plus identity for bare ingredients."""

    def __init__(self, pantry: dict[str, Any]) -> None:
        self.pantry = pantry

    def resolve(self, ident: Ident, *, allow_states: bool = False) -> Any:
        # Idents resolve to their *name* — that's what recipes refer to.
        # The pantry quantity is inventory, not the value substituted into
        # a verb call.
        name = ident.name
        if name in self.pantry:
            return name
        if name in BUILTIN_INGREDIENTS:
            return name
        if allow_states and name in BUILTIN_STATES:
            return name
        raise PantryError(
            f"ingredient '{name}' not in pantry",
            line=ident.line,
        )


class Interpreter:
    def __init__(self, recipe: Recipe) -> None:
        self.recipe = recipe

    def run(self) -> None:
        console.rule(
            f"[bold yellow]{self.recipe.name}[/bold yellow] "
            f"[dim](serves {self.recipe.serves})[/dim]"
        )
        env = self._build_pantry()
        self._print_pantry(env)

        for idx, step in enumerate(self.recipe.steps, start=1):
            self._exec_step(step, env, idx)

        console.rule("[green]done[/green]")

    # ---- internals ------------------------------------------------------
    def _build_pantry(self) -> Environment:
        # Pantry values are always concrete — Quantity, Duration, or Count —
        # never Idents. The parser enforces this.
        return Environment({entry.name: entry.value for entry in self.recipe.pantry})

    def _print_pantry(self, env: Environment) -> None:
        lines = []
        for name, value in env.pantry.items():
            lines.append(f"  [bold]{name}[/bold] = {value}")
        console.print(Panel("\n".join(lines), title="pantry", title_align="left",
                            border_style="dim"))

    def _exec_step(self, step: Step, env: Environment, step_no: int) -> None:
        verb = VERB_TABLE.get(step.verb)
        if verb is None:
            raise KitchenError(
                f"unknown verb '{step.verb}' — try one of: "
                f"{', '.join(sorted(set(VERB_TABLE) - {'saute'}))}",
                line=step.line,
            )

        resolved_args = [self._resolve_value(v, env) for v in step.args]
        resolved_kwargs: dict[str, Any] = {}
        for kw in step.kwargs:
            resolved_kwargs[kw.name] = self._resolve_value(
                kw.value, env, allow_states=(kw.name == "until"),
            )

        self._check_units(step, resolved_args, resolved_kwargs)

        verb(resolved_args, resolved_kwargs, line=step.line, step_no=step_no)

    def _resolve_value(self, value, env: Environment, *, allow_states: bool = False) -> Any:
        if isinstance(value, Ident):
            return env.resolve(value, allow_states=allow_states)
        if isinstance(value, Count):
            return value.amount
        return value  # Quantity / Duration pass through

    def _check_units(self, step: Step, args: list[Any], kwargs: dict[str, Any]) -> None:
        # The grammar already separates Duration from Quantity, but a few
        # verbs care about the kind of value they get for specific kwargs.
        if "for" in kwargs and not isinstance(kwargs["for"], Duration):
            raise MeasureError(
                f"'for=' expects a duration, got {kwargs['for']!r}",
                line=step.line,
            )


def run(recipe: Recipe) -> None:
    Interpreter(recipe).run()
