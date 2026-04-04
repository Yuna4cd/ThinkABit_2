from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


REQUIRED_FULL_ENV_VARS = ("DATABASE_URL",)

ENV_FLAG_VALUES = {
    "minimal": {
        "MINIO_UPLOAD_ENABLED": "false",
        "METASTORE_INSERT_ENABLED": "false",
    },
    "full": {
        "MINIO_UPLOAD_ENABLED": "true",
        "METASTORE_INSERT_ENABLED": "true",
    },
}

PLACEHOLDER_VALUES = {
    "DATABASE_URL": {
        "",
        "postgresql://postgres:your-password@your-project-ref.supabase.co:5432/postgres",
    },
}


def parse_env_file(env_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_path.exists():
        return values

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in raw_line:
            continue
        key, value = raw_line.split("=", 1)
        values[key.strip()] = value.strip()

    return values


def upsert_env_value(content: str, key: str, value: str) -> str:
    lines = content.splitlines()
    replaced = False
    updated_lines: list[str] = []

    for line in lines:
        if line.startswith(f"{key}="):
            updated_lines.append(f"{key}={value}")
            replaced = True
        else:
            updated_lines.append(line)

    if not replaced:
        updated_lines.append(f"{key}={value}")

    return "\n".join(updated_lines).rstrip() + "\n"


def configure_env_file(*, env_path: Path, example_path: Path, mode: str) -> None:
    if not env_path.exists():
        env_path.write_text(example_path.read_text(encoding="utf-8"), encoding="utf-8")

    content = env_path.read_text(encoding="utf-8")
    for key, value in ENV_FLAG_VALUES[mode].items():
        content = upsert_env_value(content, key, value)
    env_path.write_text(content, encoding="utf-8")


def find_missing_full_env_vars(env_path: Path) -> list[str]:
    values = parse_env_file(env_path)
    missing: list[str] = []

    for key in REQUIRED_FULL_ENV_VARS:
        value = values.get(key, "").strip()
        if value in PLACEHOLDER_VALUES[key]:
            missing.append(key)

    return missing


def require_command(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(
            f"Missing required command: {name}. Install it and rerun this setup."
        )


def run_command(args: list[str], *, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def backend_root() -> Path:
    return repo_root() / "backend"


def resolve_venv_python(venv_path: Path) -> Path:
    candidates = (
        venv_path / "bin" / "python",
        venv_path / "Scripts" / "python.exe",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        f"Virtual environment python not found under {venv_path}."
    )


def ensure_virtualenv(venv_path: Path) -> None:
    if venv_path.exists():
        return
    run_command([sys.executable, "-m", "venv", str(venv_path)], cwd=venv_path.parent)


def install_requirements(*, venv_python: Path, requirements_path: Path, cwd: Path) -> None:
    run_command([str(venv_python), "-m", "pip", "install", "-r", str(requirements_path)], cwd=cwd)


def start_minio(*, repo_root: Path) -> None:
    run_command(
        [
            "docker",
            "compose",
            "-f",
            "backend/docker-compose.minio.yml",
            "up",
            "-d",
        ],
        cwd=repo_root,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bootstrap ThinkABit backend development environments."
    )
    parser.add_argument("mode", choices=("minimal", "full"))
    return parser


def bootstrap(mode: str) -> int:
    root = repo_root()
    backend_dir = backend_root()
    env_path = backend_dir / ".env"
    example_path = backend_dir / ".env.example"
    venv_path = backend_dir / ".venv"
    requirements_path = backend_dir / "requirements.txt"

    try:
        ensure_virtualenv(venv_path)
        venv_python = resolve_venv_python(venv_path)
        install_requirements(
            venv_python=venv_python,
            requirements_path=requirements_path,
            cwd=root,
        )
        configure_env_file(env_path=env_path, example_path=example_path, mode=mode)

        if mode == "minimal":
            print("Minimal backend setup complete.")
            print("Next steps:")
            print("  make backend-run")
            print("  make backend-test")
            print("  python backend/tools/dev.py run")
            print("  python backend/tools/dev.py test")
            return 0

        require_command("docker")
        run_command(["docker", "compose", "version"], cwd=root)
        start_minio(repo_root=root)

        missing_vars = find_missing_full_env_vars(env_path)
        if missing_vars:
            print("Full backend setup is incomplete.")
            print(
                "MinIO is running, but these backend/.env values still need real values:"
            )
            for key in missing_vars:
                print(f"  - {key}")
            return 1

        print("Full backend setup complete.")
        print("Next steps:")
        print("  make backend-run")
        print("  make backend-test")
        print("  python backend/tools/dev.py run")
        print("  python backend/tools/dev.py test")
        return 0
    except subprocess.CalledProcessError as exc:
        print(
            "Setup command failed:",
            " ".join(str(part) for part in exc.cmd),
            file=sys.stderr,
        )
        return exc.returncode or 1


def main() -> int:
    args = build_parser().parse_args()
    return bootstrap(args.mode)


if __name__ == "__main__":
    raise SystemExit(main())
