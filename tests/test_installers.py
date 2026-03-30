from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def copy_project(tmp_path: Path) -> Path:
    destination = tmp_path / "vnc watch copy"
    shutil.copytree(
        PROJECT_ROOT,
        destination,
        ignore=shutil.ignore_patterns("__pycache__", "dist", "logs", "*.pyc"),
    )
    return destination


def build_env(tmp_path: Path) -> dict[str, str]:
    home_dir = tmp_path / "home"
    desktop_dir = home_dir / "Desktop With Space"
    home_dir.mkdir(parents=True, exist_ok=True)
    desktop_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["HOME"] = str(home_dir)
    env["XDG_DESKTOP_DIR"] = str(desktop_dir)
    return env


def test_setup_script_marks_files_and_creates_launchers(tmp_path: Path) -> None:
    project_dir = copy_project(tmp_path)
    env = build_env(tmp_path)

    result = subprocess.run(
        ["bash", str(project_dir / "setup.sh")],
        cwd=project_dir,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "Готово." in result.stdout

    desktop_dir = Path(env["XDG_DESKTOP_DIR"])
    watch_launcher = desktop_dir / "vnc-watch.desktop"
    log_launcher = desktop_dir / "vnc-watch-log.desktop"
    assert watch_launcher.exists()
    assert log_launcher.exists()

    launch_monitor = project_dir / "launch-monitor.sh"
    assert launch_monitor.exists()
    assert os.access(launch_monitor, os.X_OK)

    launcher_text = watch_launcher.read_text(encoding="utf-8")
    assert "launch-monitor.sh" in launcher_text
    assert str(project_dir) in launcher_text


def test_self_extracting_installer_unpacks_and_runs_setup(tmp_path: Path) -> None:
    project_dir = copy_project(tmp_path)
    env = build_env(tmp_path)

    subprocess.run(
        ["bash", str(project_dir / "build-installer.sh")],
        cwd=project_dir,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )

    installer_path = project_dir / "dist" / "vnc-watch-installer.run"
    assert installer_path.exists()
    assert os.access(installer_path, os.X_OK)

    target_dir = tmp_path / "installed target with space"
    result = subprocess.run(
        [str(installer_path), str(target_dir)],
        cwd=project_dir,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "Установка завершена" in result.stdout
    assert (target_dir / "setup.sh").exists()
    assert (target_dir / "build-installer.sh").exists()

    desktop_dir = Path(env["XDG_DESKTOP_DIR"])
    watch_launcher = desktop_dir / "vnc-watch.desktop"
    assert watch_launcher.exists()
    launcher_text = watch_launcher.read_text(encoding="utf-8")
    assert str(target_dir) in launcher_text

    mode = (target_dir / "setup.sh").stat().st_mode
    assert mode & stat.S_IXUSR
