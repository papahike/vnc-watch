from __future__ import annotations

from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]


def test_tray_prefers_appindicator_with_gtk_fallback() -> None:
    script = (PROJECT_DIR / "vnc_tray.py").read_text(encoding="utf-8")

    assert 'gi.require_version("AppIndicator3", "0.1")' in script
    assert "AppIndicator3.Indicator.new" in script
    assert "AppIndicator3.IndicatorStatus.ACTIVE" in script
    assert "Gtk.StatusIcon.new_from_icon_name" in script
