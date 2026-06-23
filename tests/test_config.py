import textwrap

import pytest

from aio_control.config import ConfigError, load_config, parse_config
from aio_control.models import EntryType


def test_default_config_loads():
    cfg = load_config()  # bundled default
    assert cfg.categories
    ids = {c.id for c in cfg.categories}
    assert {"sdr", "gps", "lora", "usb_rail"} <= ids
    # every entry has its required fields validated already
    total = sum(len(c.entries) for c in cfg.categories)
    assert total > 10


def test_parse_minimal():
    data = {
        "meta": {"name": "T", "refresh_interval": 3},
        "categories": [
            {
                "id": "sdr",
                "title": "SDR",
                "entries": [
                    {"name": "Info", "type": "command", "cmd": "hackrf_info"},
                    {"name": "GQRX", "type": "app", "cmd": "gqrx"},
                    {
                        "name": "gpsd",
                        "type": "toggle",
                        "on": "start",
                        "off": "stop",
                        "status": "true",
                    },
                ],
            }
        ],
    }
    cfg = parse_config(data)
    assert cfg.name == "T"
    assert cfg.refresh_interval == 3
    cat = cfg.categories[0]
    assert cat.entries[0].type is EntryType.COMMAND
    assert cat.entries[2].type is EntryType.TOGGLE
    assert cat.entries[2].detail == "start"


def test_command_requires_cmd():
    data = {"categories": [{"id": "x", "entries": [{"name": "n", "type": "command"}]}]}
    with pytest.raises(ConfigError, match="requires a 'cmd'"):
        parse_config(data)


def test_toggle_requires_on_off():
    data = {
        "categories": [
            {"id": "x", "entries": [{"name": "n", "type": "toggle", "on": "go"}]}
        ]
    }
    with pytest.raises(ConfigError, match="requires both 'on' and 'off'"):
        parse_config(data)


def test_unknown_type_rejected():
    data = {"categories": [{"id": "x", "entries": [{"name": "n", "type": "bogus"}]}]}
    with pytest.raises(ConfigError, match="unknown type"):
        parse_config(data)


def test_empty_categories_rejected():
    with pytest.raises(ConfigError, match="no categories"):
        parse_config({"categories": []})


def test_load_from_file(tmp_path):
    p = tmp_path / "aio.yaml"
    p.write_text(
        textwrap.dedent(
            """
            meta:
              name: From File
            categories:
              - id: radio
                title: Radio
                entries:
                  - name: Sweep
                    type: command
                    cmd: rtl_power
            """
        )
    )
    cfg = load_config(p)
    assert cfg.name == "From File"
    assert cfg.source_path == str(p)


def test_missing_file_raises():
    with pytest.raises(ConfigError, match="not found"):
        load_config("/no/such/file.yaml")
