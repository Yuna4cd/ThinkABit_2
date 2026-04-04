from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.bootstrap_env import bootstrap, repo_root, resolve_venv_python, run_command


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cross-platform backend development commands."
    )
    parser.add_argument(
        "command",
        choices=("setup-minimal", "setup-full", "run", "test"),
    )
    return parser


def backend_venv_path() -> Path:
    return repo_root() / "backend" / ".venv"


def run_backend_command(args: list[str]) -> int:
    try:
        venv_python = resolve_venv_python(backend_venv_path())
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc

    run_command([str(venv_python), *args], cwd=repo_root())
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "setup-minimal":
        return bootstrap("minimal")
    if args.command == "setup-full":
        return bootstrap("full")
    if args.command == "run":
        return run_backend_command(
            ["-m", "uvicorn", "app.main:app", "--reload", "--app-dir", "backend"]
        )
    return run_backend_command(["-m", "pytest", "backend/tests"])


if __name__ == "__main__":
    raise SystemExit(main())
