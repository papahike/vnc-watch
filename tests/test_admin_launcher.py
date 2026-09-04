from __future__ import annotations

import os
import subprocess
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]


def test_admin_launcher_has_valid_bash_syntax() -> None:
    for filename in (
        "run.sh",
        "sudo-askpass.sh",
        "launch-monitor.sh",
        "install-desktop-launcher.sh",
    ):
        result = subprocess.run(
            ["bash", "-n", str(PROJECT_DIR / filename)],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"{filename}: {result.stderr}"


def test_manual_launcher_uses_sudo_only_for_system_journal() -> None:
    script = (PROJECT_DIR / "run.sh").read_text(encoding="utf-8")

    assert 'SUDO_BIN="/usr/bin/sudo"' in script
    assert 'JOURNALCTL_BIN="/usr/bin/journalctl"' in script
    assert '"$SUDO_BIN" "${sudo_args[@]}"' in script
    assert '"$JOURNALCTL_BIN"' in script
    assert "-u x11vnc" in script
    assert '"$PYTHON_BIN" "$SCRIPT_DIR/vnc_tray.py" --stdin' in script
    assert "pkexec" not in script
    assert '"$SUDO_BIN" "$PYTHON_BIN"' not in script


def test_manual_launcher_supports_graphical_and_terminal_sudo() -> None:
    script = (PROJECT_DIR / "run.sh").read_text(encoding="utf-8")
    diagnostic = (PROJECT_DIR / "launch-monitor.sh").read_text(encoding="utf-8")

    assert 'export SUDO_ASKPASS="$ASKPASS_BIN"' in script
    assert "sudo_args+=(-A)" in script
    assert "sudo_args=(-k)" in script
    assert '"${1:-}" == "--terminal-auth"' in script
    assert "./run.sh --terminal-auth" in diagnostic


def test_askpass_supports_installed_graphical_helpers() -> None:
    script = (PROJECT_DIR / "sudo-askpass.sh").read_text(encoding="utf-8")

    assert "zenity" in script
    assert "--password" in script
    assert "yad" in script
    assert "--hide-text" in script


def test_askpass_returns_zenity_output_to_sudo(tmp_path) -> None:
    fake_zenity = tmp_path / "zenity"
    fake_zenity.write_text(
        "#!/usr/bin/env bash\nprintf 'test-password\\n'\n",
        encoding="utf-8",
    )
    fake_zenity.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:/usr/bin:/bin"

    result = subprocess.run(
        [str(PROJECT_DIR / "sudo-askpass.sh"), "Password:"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    assert result.stdout == "test-password\n"
    assert result.stderr == ""


def test_portable_desktop_launcher_is_graphical() -> None:
    desktop = (PROJECT_DIR / "vnc-watch.desktop").read_text(encoding="utf-8")

    assert "Terminal=false" in desktop
    assert "run.sh" in desktop
    assert "launch-monitor.sh" not in desktop
    assert "%k" in desktop
    assert "/home/" not in desktop


def test_repository_desktop_templates_do_not_contain_machine_paths() -> None:
    for filename in (
        "vnc-watch.desktop",
        "show-log.desktop",
        "vnc-watch-autostart.desktop",
    ):
        desktop = (PROJECT_DIR / filename).read_text(encoding="utf-8")
        assert "%k" in desktop
        assert "/home/" not in desktop


def test_installer_creates_launchers_and_session_autostart() -> None:
    script = (PROJECT_DIR / "install-desktop-launcher.sh").read_text(
        encoding="utf-8"
    )

    assert "run.sh" in script
    assert "sudo-askpass.sh" in script
    assert "autostart.sh" in script
    assert 'AUTOSTART_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"' in script
    assert "Terminal=false" in script
    assert "pkexec" not in script
    assert "OnlyShowIn" not in script
    assert "appindicatorsupport@rgcjonas.gmail.com" in script


def test_installer_writes_gnome_autostart_and_nonterminal_launcher(tmp_path) -> None:
    desktop_dir = tmp_path / "Desktop with spaces"
    config_dir = tmp_path / "config"
    env = os.environ.copy()
    env["XDG_DESKTOP_DIR"] = str(desktop_dir)
    env["XDG_CONFIG_HOME"] = str(config_dir)
    env["XDG_CURRENT_DESKTOP"] = "test"

    result = subprocess.run(
        ["bash", str(PROJECT_DIR / "install-desktop-launcher.sh")],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    watch_launcher = (desktop_dir / "vnc-watch.desktop").read_text(
        encoding="utf-8"
    )
    autostart = (config_dir / "autostart" / "vnc-watch.desktop").read_text(
        encoding="utf-8"
    )
    assert "Terminal=false" in watch_launcher
    assert str(PROJECT_DIR / "run.sh") in watch_launcher
    assert "Terminal=false" in autostart
    assert str(PROJECT_DIR / "autostart.sh") in autostart
    assert "OnlyShowIn" not in autostart
