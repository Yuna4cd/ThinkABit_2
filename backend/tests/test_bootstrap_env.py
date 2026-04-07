from pathlib import Path

import pytest

from tools.bootstrap_env import (
    REQUIRED_FULL_ENV_VARS,
    bootstrap,
    configure_env_file,
    find_missing_full_env_vars,
    resolve_venv_python,
)


def test_configure_env_file_creates_minimal_env_from_example(tmp_path: Path) -> None:
    example_path = tmp_path / ".env.example"
    env_path = tmp_path / ".env"

    example_path.write_text(
        "\n".join(
            [
                "MINIO_UPLOAD_ENABLED=true",
                "METASTORE_INSERT_ENABLED=true",
                "SUPABASE_URL=https://your-project-ref.supabase.co",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    configure_env_file(env_path=env_path, example_path=example_path, mode="minimal")

    assert env_path.exists()
    content = env_path.read_text(encoding="utf-8")
    assert "MINIO_UPLOAD_ENABLED=false" in content
    assert "METASTORE_INSERT_ENABLED=false" in content
    assert "SUPABASE_URL=https://your-project-ref.supabase.co" in content


def test_configure_env_file_switches_existing_env_to_full_mode(tmp_path: Path) -> None:
    example_path = tmp_path / ".env.example"
    env_path = tmp_path / ".env"

    example_path.write_text("MINIO_UPLOAD_ENABLED=false\n", encoding="utf-8")
    env_path.write_text(
        "\n".join(
            [
                "MINIO_UPLOAD_ENABLED=false",
                "METASTORE_INSERT_ENABLED=false",
                "CUSTOM_FLAG=kept",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    configure_env_file(env_path=env_path, example_path=example_path, mode="full")

    content = env_path.read_text(encoding="utf-8")
    assert "MINIO_UPLOAD_ENABLED=true" in content
    assert "METASTORE_INSERT_ENABLED=true" in content
    assert "CUSTOM_FLAG=kept" in content


def test_find_missing_full_env_vars_flags_blank_and_placeholder_values(
    tmp_path: Path,
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SUPABASE_URL=https://your-project-ref.supabase.co",
                "SUPABASE_SERVICE_ROLE_KEY=",
                "DATABASE_URL=postgresql://postgres:your-password@your-project-ref.supabase.co:5432/postgres",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    missing = find_missing_full_env_vars(env_path)

    assert missing == ["DATABASE_URL"]


def test_find_missing_full_env_vars_accepts_realistic_values(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SUPABASE_URL=https://your-project-ref.supabase.co",
                "SUPABASE_SERVICE_ROLE_KEY=",
                "DATABASE_URL=postgresql://postgres:encoded%24pass@db.example.com:5432/postgres",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert find_missing_full_env_vars(env_path) == []


def test_resolve_venv_python_prefers_posix_layout(tmp_path: Path) -> None:
    venv_path = tmp_path / ".venv"
    posix_python = venv_path / "bin" / "python"
    posix_python.parent.mkdir(parents=True)
    posix_python.write_text("", encoding="utf-8")

    assert resolve_venv_python(venv_path) == posix_python


def test_resolve_venv_python_prefers_windows_layout(tmp_path: Path) -> None:
    venv_path = tmp_path / ".venv"
    windows_python = venv_path / "Scripts" / "python.exe"
    windows_python.parent.mkdir(parents=True)
    windows_python.write_text("", encoding="utf-8")

    assert resolve_venv_python(venv_path) == windows_python


def test_resolve_venv_python_errors_when_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Virtual environment python not found"):
        resolve_venv_python(tmp_path / ".venv")


def test_bootstrap_upgrades_packaging_tools_before_installing_requirements(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo_root_path = tmp_path
    backend_root_path = repo_root_path / "backend"
    venv_path = backend_root_path / ".venv"
    venv_python = venv_path / "Scripts" / "python.exe"
    requirements_path = backend_root_path / "requirements.txt"
    env_path = backend_root_path / ".env"
    example_path = backend_root_path / ".env.example"
    call_order: list[str] = []

    venv_python.parent.mkdir(parents=True)
    venv_python.write_text("", encoding="utf-8")
    requirements_path.parent.mkdir(parents=True, exist_ok=True)
    requirements_path.write_text("pytest==8.4.2\n", encoding="utf-8")
    example_path.write_text("MINIO_UPLOAD_ENABLED=false\n", encoding="utf-8")

    monkeypatch.setattr("tools.bootstrap_env.repo_root", lambda: repo_root_path)
    monkeypatch.setattr("tools.bootstrap_env.backend_root", lambda: backend_root_path)
    monkeypatch.setattr(
        "tools.bootstrap_env.ensure_virtualenv",
        lambda path: call_order.append(f"ensure:{path}"),
    )
    monkeypatch.setattr(
        "tools.bootstrap_env.upgrade_packaging_tools",
        lambda *, venv_python, cwd: call_order.append(
            f"upgrade:{venv_python}:{cwd}"
        ),
    )
    monkeypatch.setattr(
        "tools.bootstrap_env.install_requirements",
        lambda *, venv_python, requirements_path, cwd: call_order.append(
            f"install:{venv_python}:{requirements_path}:{cwd}"
        ),
    )
    monkeypatch.setattr(
        "tools.bootstrap_env.configure_env_file",
        lambda *, env_path, example_path, mode: call_order.append(
            f"configure:{env_path}:{example_path}:{mode}"
        ),
    )

    exit_code = bootstrap("minimal")

    assert exit_code == 0
    assert call_order == [
        f"ensure:{venv_path}",
        f"upgrade:{venv_python}:{repo_root_path}",
        f"install:{venv_python}:{requirements_path}:{repo_root_path}",
        f"configure:{env_path}:{example_path}:minimal",
    ]
