"""Configuration management: YAML defaults + database overrides."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from src.db import connect, now_utc

CONFIG_DIR = Path("config")
DEFAULT_CONFIG_PATH = CONFIG_DIR / "default.yaml"


def load_yaml(path: Path | str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    with open(p) as f:
        return yaml.safe_load(f) or {}


def load_defaults() -> dict[str, Any]:
    return load_yaml(DEFAULT_CONFIG_PATH)


def load_db_overrides(db_path: str | None = None) -> dict[str, Any]:
    """Load config overrides from the config_overrides table."""
    try:
        conn = connect(db_path)
        cur = conn.execute("SELECT key, value FROM config_overrides")
        overrides: dict[str, Any] = {}
        for row in cur.fetchall():
            key, value = row["key"], row["value"]
            try:
                overrides[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                overrides[key] = value
        conn.close()
        return overrides
    except Exception:
        return {}


def _set_nested(d: dict[str, Any], dotted_key: str, value: Any) -> None:
    """Set a nested dict value using a dotted key like 'voice.speed'."""
    keys = dotted_key.split(".")
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = value


def _get_nested(d: dict[str, Any], dotted_key: str, default: Any = None) -> Any:
    """Get a nested dict value using a dotted key like 'voice.speed'."""
    keys = dotted_key.split(".")
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
        if d is default:
            return default
    return d


def load_config(db_path: str | None = None) -> dict[str, Any]:
    """Load merged config: YAML defaults + DB overrides."""
    config = load_defaults()
    overrides = load_db_overrides(db_path)
    for key, value in overrides.items():
        _set_nested(config, key, value)
    return config


def get_config_value(
    key: str, default: Any = None, db_path: str | None = None
) -> Any:
    """Get a single config value by dotted key."""
    config = load_config(db_path)
    return _get_nested(config, key, default)


def set_config_override(
    key: str, value: Any, db_path: str | None = None
) -> None:
    """Set a config override in the database."""
    conn = connect(db_path)
    from src.db import init_schema

    init_schema(conn)
    json_value = json.dumps(value)
    conn.execute(
        """
        INSERT INTO config_overrides (key, value, updated_at)
        VALUES (:key, :value, :updated_at)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = excluded.updated_at
        """,
        {"key": key, "value": json_value, "updated_at": now_utc()},
    )
    conn.commit()
    conn.close()


def delete_config_override(key: str, db_path: str | None = None) -> bool:
    """Delete a config override. Returns True if a row was deleted."""
    conn = connect(db_path)
    cur = conn.execute("DELETE FROM config_overrides WHERE key = ?", (key,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted


def flatten_config(
    d: dict[str, Any], prefix: str = ""
) -> list[tuple[str, Any]]:
    """Flatten nested config dict into list of (dotted_key, value) pairs."""
    items: list[tuple[str, Any]] = []
    for k, v in d.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            items.extend(flatten_config(v, full_key))
        else:
            items.append((full_key, v))
    return items
