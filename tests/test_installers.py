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
        ignore=shutil.ignore_patterns(
            ".git",
            "__pycache__",
            ".pytest_cache",
            "dist",
            "logs",
            "*.pyc",
        ),
    )
    return destination


def build_env(tmp_path: Path) -> dict[str, str]:
    home_dir = tmp_path / "home"
    desktop_dir = home_dir / "Desktop With Space"
    config_dir = home_dir / ".config"
    home_dir.mkdir(parents=True, exist_ok=True)
    desktop_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["HOME"] = str(home_dir)
    env["XDG_DESKTOP_DIR"] = str(desktop_dir)
    env["XDG_CONFIG_HOME"] = str(config_dir)
    env["XDG_CURRENT_DESKTOP"] = "test"
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
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Готово." in result.stdout

    desktop_dir = Path(env["XDG_DESKTOP_DIR"])
    watch_launcher = desktop_dir / "vnc-watch.desktop"
    log_launcher = desktop_dir / "vnc-watch-log.desktop"
    autostart_launcher = (
        Path(env["XDG_CONFIG_HOME"]) / "autostart" / "vnc-watch.desktop"
    )
    assert watch_launcher.exists()
    assert log_launcher.exists()
    assert autostart_launcher.exists()
    assert os.access(project_dir / "sudo-askpass.sh", os.X_OK)

    launcher_text = watch_launcher.read_text(encoding="utf-8")
    assert "run.sh" in launcher_text
    assert str(project_dir) in launcher_text
    assert "Terminal=false" in launcher_text


def test_self_extracting_installer_contains_current_launch_path(
    tmp_path: Path,
) -> None:
    project_dir = copy_project(tmp_path)
    env = build_env(tmp_path)

    build_result = subprocess.run(
        ["bash", str(project_dir / "build-installer.sh")],
        cwd=project_dir,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert build_result.returncode == 0, build_result.stderr

    installer_path = project_dir / "dist" / "vnc-watch-installer.run"
    assert installer_path.exists()
    assert os.access(installer_path, os.X_OK)

    target_dir = tmp_path / "installed target with space"
    install_result = subprocess.run(
        [str(installer_path), str(target_dir)],
        cwd=project_dir,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert install_result.returncode == 0, install_result.stderr
    assert "Установка завершена" in install_result.stdout
    assert (target_dir / "sudo-askpass.sh").exists()
    assert (target_dir / "autostart.sh").exists()
    assert not (target_dir / "pkexec-journalctl.sh").exists()
    assert not (target_dir / "vnc-watch.service").exists()

    watch_launcher = Path(env["XDG_DESKTOP_DIR"]) / "vnc-watch.desktop"
    autostart_launcher = (
        Path(env["XDG_CONFIG_HOME"]) / "autostart" / "vnc-watch.desktop"
    )
    assert str(target_dir / "run.sh") in watch_launcher.read_text(
        encoding="utf-8"
    )
    assert str(target_dir / "autostart.sh") in autostart_launcher.read_text(
        encoding="utf-8"
    )

    mode = (target_dir / "setup.sh").stat().st_mode
    assert mode & stat.S_IXUSR
