from __future__ import annotations

import subprocess
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]


def test_autostart_script_has_valid_bash_syntax() -> None:
    result = subprocess.run(
        ["bash", "-n", str(PROJECT_DIR / "autostart.sh")],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_autostart_uses_actual_journal_access_without_sudo() -> None:
    script = (PROJECT_DIR / "autostart.sh").read_text(encoding="utf-8")

    assert "sudo" not in script
    assert "systemd-journal" not in script
    assert '"$JOURNALCTL_BIN" -q -u x11vnc -n 1' in script
    assert "vnc_tray.py\" --stdin" in script


def test_autostart_retries_unexpected_reader_failure() -> None:
    script = (PROJECT_DIR / "autostart.sh").read_text(encoding="utf-8")

    assert "MAX_RESTARTS=3" in script
    assert "restart_count=$((restart_count + 1))" in script
    assert 'if [[ "$tray_status" -eq 0 ]]' in script
    assert 'sleep "$RESTART_DELAY_SECONDS"' in script


def test_gnome_and_mate_autostart_entry_runs_without_terminal() -> None:
    desktop = (PROJECT_DIR / "vnc-watch-autostart.desktop").read_text(
        encoding="utf-8"
    )

    assert "Terminal=false" in desktop
    assert "OnlyShowIn" not in desktop
    assert "X-GNOME-Autostart-enabled=true" in desktop
    assert "X-MATE-Autostart-Delay=5" in desktop
    assert "autostart.sh" in desktop


def test_obsolete_user_service_is_not_distributed() -> None:
    assert not (PROJECT_DIR / "vnc-watch.service").exists()
