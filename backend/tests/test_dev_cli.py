from pathlib import Path

import pytest

from tools import dev


def test_run_command_uses_resolved_venv_python(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], Path]] = []

    monkeypatch.setattr(dev, "resolve_venv_python", lambda _: Path("backend/.venv/Scripts/python.exe"))
    monkeypatch.setattr(
        dev,
        "run_command",
        lambda args, *, cwd: calls.append((args, cwd)),
    )

    dev.run_backend_command(["-m", "pytest", "backend/tests"])

    assert calls == [
        (
            ["backend/.venv/Scripts/python.exe", "-m", "pytest", "backend/tests"],
            dev.repo_root(),
        )
    ]


def test_run_command_surfaces_missing_venv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        dev,
        "resolve_venv_python",
        lambda _: (_ for _ in ()).throw(FileNotFoundError("missing venv")),
    )

    with pytest.raises(SystemExit, match="missing venv"):
        dev.run_backend_command(["-m", "pytest", "backend/tests"])


@pytest.mark.parametrize(
    ("argv", "expected_mode"),
    [
        (["setup-minimal"], "minimal"),
        (["setup-full"], "full"),
    ],
)
def test_main_dispatches_setup_commands(
    monkeypatch: pytest.MonkeyPatch,
    argv: list[str],
    expected_mode: str,
) -> None:
    calls: list[str] = []

    monkeypatch.setattr(dev, "bootstrap", lambda mode: calls.append(mode) or 0)

    exit_code = dev.main(argv)

    assert exit_code == 0
    assert calls == [expected_mode]


def test_main_dispatches_run(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    monkeypatch.setattr(
        dev,
        "run_backend_command",
        lambda args: calls.append(args) or 0,
    )

    exit_code = dev.main(["run"])

    assert exit_code == 0
    assert calls == [["-m", "uvicorn", "app.main:app", "--reload", "--app-dir", "backend"]]


def test_main_dispatches_test(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    monkeypatch.setattr(
        dev,
        "run_backend_command",
        lambda args: calls.append(args) or 0,
    )

    exit_code = dev.main(["test"])

    assert exit_code == 0
    assert calls == [["-m", "pytest", "backend/tests"]]
