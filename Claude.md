## Environment
- Managed with uv; Python pinned to 3.12 in `.python-version`. Kivy is the reason.
- Run everything through `uv run` (e.g. `uv run ./scripts/run-tests.sh`). Never `pip install`.
- Add deps with `uv add` / `uv add --dev`; commit `pyproject.toml` and `uv.lock` together.
- Build tools (pyinstaller, buildozer) are in the `build` dependency group.

## Development
- Do not edit, create, or delete files in this repo. Humans will make all project edits.
  Work in plan mode: investigate, then give the exact changes for the human to apply.
- Do not commit, push, or open PRs.

## Testing
- Unit tests: `uv run ./scripts/run-tests.sh` (add `-v` for verbose)
- Puzzle solution tests: `uv run ./scripts/test-puzzles.sh`

## Conventions
- Ruff is set to keep existing quote style because xgettext doesn't recognize `_('text')`
  strings. Don't change quote styles in translatable strings.
- APK/buildozer workflows still use pip on purpose; only run-tests and the EXE build use uv.
