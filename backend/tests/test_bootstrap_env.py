from pathlib import Path

from tools.bootstrap_env import (
    REQUIRED_FULL_ENV_VARS,
    configure_env_file,
    find_missing_full_env_vars,
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
