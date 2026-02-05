"""Tests for src/config.py - configuration management."""

import json
import os

from src.config import (
    _get_nested,
    _set_nested,
    delete_config_override,
    flatten_config,
    load_config,
    load_yaml,
    set_config_override,
)
from src.db import connect, init_schema


def test_load_yaml_reads_file(tmp_path):
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text("key: value\nnested:\n  a: 1\n")
    data = load_yaml(yaml_file)
    assert data["key"] == "value"
    assert data["nested"]["a"] == 1


def test_load_yaml_missing_file(tmp_path):
    data = load_yaml(tmp_path / "missing.yaml")
    assert data == {}


def test_set_nested_simple():
    d: dict = {}
    _set_nested(d, "voice.speed", 0.95)
    assert d == {"voice": {"speed": 0.95}}


def test_set_nested_deep():
    d: dict = {}
    _set_nested(d, "a.b.c.d", "value")
    assert d["a"]["b"]["c"]["d"] == "value"


def test_get_nested_simple():
    d = {"voice": {"speed": 0.95}}
    assert _get_nested(d, "voice.speed") == 0.95


def test_get_nested_missing():
    d = {"voice": {"speed": 0.95}}
    assert _get_nested(d, "voice.missing", "default") == "default"


def test_get_nested_top_level():
    d = {"key": "value"}
    assert _get_nested(d, "key") == "value"


def test_flatten_config():
    config = {
        "voice": {"speed": 0.95, "provider": "elevenlabs"},
        "video": {"fps": 30},
    }
    flat = flatten_config(config)
    assert ("voice.speed", 0.95) in flat
    assert ("voice.provider", "elevenlabs") in flat
    assert ("video.fps", 30) in flat


def test_flatten_config_empty():
    assert flatten_config({}) == []


def test_set_and_get_config_override(tmp_path):
    db_path = str(tmp_path / "test.db")
    os.environ["DB_PATH"] = db_path
    try:
        conn = connect(db_path)
        init_schema(conn)
        conn.close()

        set_config_override("voice.speed", 0.8, db_path)

        conn = connect(db_path)
        cur = conn.execute(
            "SELECT value FROM config_overrides WHERE key = 'voice.speed'"
        )
        row = cur.fetchone()
        assert row is not None
        assert json.loads(row["value"]) == 0.8
        conn.close()
    finally:
        os.environ.pop("DB_PATH", None)


def test_delete_config_override(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    conn.close()

    set_config_override("voice.speed", 0.8, db_path)
    assert delete_config_override("voice.speed", db_path) is True
    assert delete_config_override("nonexistent", db_path) is False


def test_load_config_merges_overrides(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    init_schema(conn)
    conn.close()

    set_config_override("voice.speed", 0.8, db_path)
    config = load_config(db_path)
    # The default.yaml has voice.speed: 0.95, override should win
    assert config.get("voice", {}).get("speed") == 0.8
