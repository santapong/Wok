# Contributing to wok

Thanks for stopping by the kitchen. wok is a pedagogical project: a
complete language pipeline small enough to hold in your head. That goal
shapes what contributions fit.

## Ground rules

- **Stay under 800 lines** in `wok/` (`wc -l wok/*.py`). If a change
  pushes past that, shrink the change — the limit is the feature.
- **No new dependencies.** Runtime is stdlib + `rich`; tests use
  `pytest`. No parser generators, no CLI frameworks.
- **No new infrastructure.** No VM, no bytecode, no plugins, no config
  files. See [ARCHITECTURE.md](ARCHITECTURE.md) for how the pieces fit.

## Great first contributions

- **A new example recipe** in `recipes/` — international dishes
  especially welcome. It must run cleanly with the existing ten verbs.
- **A new verb** in `wok/stdlib.py` — one function plus one `VERB_TABLE`
  entry (e.g. `simmer`, `whisk`, `knead`). Keep the signature style and
  add a test.
- **Better error messages** — anything that makes a `SyntaxKitchenError`
  or `KitchenError` friendlier to a beginner.
- **Tests** for edge cases in the lexer or parser.

## Development setup

```
git clone https://github.com/santapong/Wok
cd Wok
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
pytest
```

The full suite runs in well under a second. Please make sure `pytest`
passes and all three example recipes still run before opening a PR:

```
for r in recipes/*.wok; do wok run "$r"; done
```

## Pull requests

- One change per PR, with a test alongside it.
- If you're unsure whether something fits the project's scope, open an
  issue first — saves everyone time.
