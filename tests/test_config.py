"""Config load/save and autostart handling, against a temporary XDG home."""

import importlib
import json

import pytest


@pytest.fixture()
def conf(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    import prayertimes.config as module
    return importlib.reload(module)


def test_load_returns_defaults_when_nothing_is_stored(conf):
    cfg = conf.load()
    assert cfg["configured"] is False
    assert set(conf.DEFAULTS) <= set(cfg)


def test_save_then_load_round_trips(conf):
    cfg = conf.load()
    cfg.update(configured=True, city="مكة المكرمة", latitude=21.3891,
               method="Makkah")
    conf.save(cfg)
    assert conf.load()["city"] == "مكة المكرمة"
    assert conf.load()["method"] == "Makkah"


def test_unknown_keys_from_older_versions_do_not_break_load(conf, tmp_path):
    path = tmp_path / "prayer-times" / "config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"city": "الرياض", "legacy_key": 1}),
                    encoding="utf-8")
    cfg = conf.load()
    assert cfg["city"] == "الرياض"
    assert cfg["method"] == conf.DEFAULTS["method"]   # filled from defaults


def test_corrupt_file_falls_back_to_defaults(conf, tmp_path):
    path = tmp_path / "prayer-times" / "config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{ not json", encoding="utf-8")
    assert conf.load()["configured"] is False


def test_autostart_can_be_enabled_and_disabled(conf, tmp_path):
    assert conf.autostart_enabled() is False
    conf.set_autostart(True)
    desktop = tmp_path / "autostart" / "prayer-times.desktop"
    assert desktop.exists()
    assert "Exec=" in desktop.read_text(encoding="utf-8")
    assert conf.autostart_enabled() is True
    conf.set_autostart(False)
    assert not desktop.exists()
    assert conf.autostart_enabled() is False
