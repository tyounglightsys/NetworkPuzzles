# NetworkPuzzles

NetworkPuzzles is a simple program for teaching network principles. It was inspired by watching a number of people struggling with PacketTracer in an attempt to undestand IP addresses, subnets, and gateways. Most of their struggles were with understanding how to configure an IP on each device; they never got around to learning about how the subnets worked.

NetworkPuzzles is geared to take all the complexity away, and let you visualize the network and packet flow in a very simple way. It has proven itself already, as a great tool for teaching in lab-settings in Africa.

It is also set up to be a tool for self-teaching; If you can solve all the built-in puzzles, you should be well on your way to mastering networking.

## Development

This project uses [uv](https://docs.astral.sh/uv/) to manage Python, the
virtual environment ("venv"), and dependencies. You do **not** need to install
Python yourself, create a venv, or "activate" anything — uv does all of that.

### 1. Install uv (one time per computer)

Linux:
```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Close and reopen your terminal, then check it worked: `uv --version`

### 2. Get the code and set up the environment

```shell
git clone https://github.com/tyounglightsys/NetworkPuzzles.git
cd NetworkPuzzles
uv sync
```

`uv sync` downloads the right Python version (see `.python-version`), creates a
`.venv` folder, and installs everything listed in `uv.lock`. Re-run `uv sync`
any time you pull changes — it's fast and safe to run often.

The build translation files (needed for the tests and for French):
```shell
uv run ./scripts/compile-locales.py
```
Rerun this after pulling changes to any `.po` file.

### 3. Run things with `uv run`

Put `uv run` in front of any command that needs the project's Python. It always
uses the project's `.venv`, so you never need to activate it.
These commands work the same in bash and PowerShell:

| Task | Command |
|---|---|
| Run the GUI app | `uv run python src/main.py` |
| Run the CLI app | `uv run python -m network_puzzles` |
| Lint / format | `uv run ruff check` / `uv run ruff format` |

The helper scripts in `scripts/` are bash scripts. On Linux run them directly
through uv; on Windows run them from **Git Bash** (installed with Git for Windows):

```shell
uv run ./scripts/run-tests.sh      # unit tests (add -v for verbose output)
uv run ./scripts/test-puzzles.sh   # puzzle solution tests
uv run ./scripts/run-mobile.sh     # GUI with a phone-sized window
```

Example test output:
```
$ uv run ./scripts/run-tests.sh
....ss........................
----------------------------------------------------------------------
Ran 30 tests in 0.054s

OK (skipped=2)
```

### Adding or removing dependencies

Don't use `pip install` — it changes the venv without recording anything, so
nobody else gets the change. Instead:

```shell
uv add some-package            # app dependency (needed to run the app)
uv add --dev some-package      # developer-only tool (e.g. linters)
uv remove some-package
```

These update `pyproject.toml` **and** `uv.lock`. Commit both files.

### Build tools (rarely needed)

PyInstaller (Windows EXE) and Buildozer (Android APK, Linux only) are in an
optional group:

```shell
uv sync --group build
```

Builds normally happen in GitHub Actions, so most contributors can skip this.

### Troubleshooting

- **"command not found: uv"** — reopen your terminal after installing uv.
- **Something seems broken/out of date** — run `uv sync` again.
- **Still broken** — delete the `.venv` folder and run `uv sync`; it will be rebuilt.
- **Using an editor (VS Code, etc.)** — point it at the interpreter in `.venv`
  (`.venv/bin/python` on Linux, `.venv\Scripts\python.exe` on Windows).

## Prerequisites

Ubuntu (more specifically Wayland) requires the installation of the `xsel`
package for selection and clipboard features to work (Kivy runs under XWayland).