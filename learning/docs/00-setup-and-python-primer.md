# Phase 0 — Setup + Python primer

## Goal
A working Python project with the Anthropic SDK installed, secrets handled safely, and enough Python to follow the rest of the plan.

## Concepts
- **Virtual environment:** an isolated folder of packages for this project. `uv` creates and manages it.
- **`pyproject.toml`:** the project's manifest (name, Python version, dependencies).
- **Environment variables / `.env`:** where secrets such as `ANTHROPIC_API_KEY` live. Never in code, never in git.
- **Type hints + pydantic:** Python is dynamically typed, but this project uses hints heavily. pydantic validates data at runtime. You'll use it for tool inputs, configs, and API payloads.

## Requirements
- Python 3.12 or 3.13 managed by uv (the system has 3.15, which some libraries may not support yet).
- Docker running (`docker --version` works already).
- An Anthropic API key with a **monthly spend limit** set in the Console.

## Steps
1. `cd` into the project, run `git init`, and create `.gitignore` with: `.venv/`, `.env`, `__pycache__/`, `*.pyc`, `.pytest_cache/`.
2. `uv init --python 3.13` (or let it adopt the existing folder: `uv init --python 3.13 .`). Look at the generated `pyproject.toml` and understand each line.
3. Add dependencies: `uv add anthropic python-dotenv pydantic pydantic-settings`. Dev tools: `uv add --dev pytest ruff`.
4. Create `.env.example` listing keys with fake values (`ANTHROPIC_API_KEY=sk-ant-...`, `ANTHROPIC_MODEL=claude-opus-5-5`). Copy to `.env` and fill in the real key.
5. Create `src/policypal/config.py` with a `Settings` class (pydantic-settings `BaseSettings`) that reads those values. This is your first real module. Everything else imports settings from here.
6. Smoke test: a `scripts/hello.py` that sends "Say hi in five words" and prints the reply (the Phase 1 doc has the API details; do just this one call now). Run with `uv run python scripts/hello.py`.
7. Docker sanity check: `docker run --rm hello-world`, then write a trivial `docker-compose.yml` with one service (e.g. `redis:7`) and run `docker compose up -d`, `docker compose ps`, `docker compose down`. You will extend this file all project long.

## Python primer — learn these as you hit them
Do small exercises in a scratch file for each. Don't just read.
| Topic | Why you need it | Mini exercise |
|---|---|---|
| Functions, `*args/**kwargs`, default args | Everywhere | Write `greet(name, *, shout=False)` |
| `dict`, `list`, comprehensions | API payloads are nested dicts | Filter a list of messages by role |
| `dataclass` and pydantic `BaseModel` | Structured data | Model a `PolicyChunk(text, source, section)` |
| Type hints (`list[str]`, `str \| None`) | Readability, pydantic | Annotate your functions |
| Modules/packages, `__init__.py`, imports | Project layout | Import `settings` from another file |
| Exceptions: `try/except/finally`, custom errors | Phase 1 and 9 | Raise and catch your own `BudgetExceeded` |
| Context managers (`with`) | Files, streams, DB connections | Read a file with `with open(...)` |
| Generators / `yield` | Streaming responses | Write a generator that yields numbers lazily |
| `async`/`await` basics | FastAPI, concurrency (later) | Run two `asyncio.sleep(1)` concurrently with `gather` |
| `pathlib`, `json`, `logging` | Loading docs, logs | Load all `.md` files from a folder |
| `pytest` basics | Evals and tests | Test a pure function |
| Decorators | Retry wrappers, tool registration | Write a `@timed` decorator |

Suggested resources: the official Python tutorial (sections 3–9), then pydantic's "Models" docs page.

## Checkpoint
- [ ] `uv run python scripts/hello.py` prints a Claude reply.
- [ ] `git status` does NOT show `.env`.
- [ ] `Settings()` loads the key and model from `.env`.
- [ ] You can explain: venv, `pyproject.toml`, env var, why `.env` isn't committed.

## Stretch
Set up `ruff` (`uv run ruff check .` and `uv run ruff format .`) and run it before every commit.

## Pitfalls
- Running `python` instead of `uv run python` and using the wrong interpreter.
- Committing `.env`. If it happens, rotate the key immediately.
- Hard-coding the model string in many places. It lives in config only.
