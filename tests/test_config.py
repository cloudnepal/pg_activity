from __future__ import annotations

from pathlib import Path
from typing import Any

import attr
import pytest

from pgactivity.config import Configuration, Flag, UISection


def test_flag():
    f = Flag(3)
    assert f == Flag.APPNAME | Flag.DATABASE
    assert f | Flag.CLIENT == Flag.CLIENT | Flag.APPNAME | Flag.DATABASE
    f ^= Flag.APPNAME
    assert f == Flag.DATABASE


def test_flag_load():
    options = {
        "noappname": False,
        "noclient": False,
        "nocpu": False,
        "nodb": False,
        "nomem": False,
        "nopid": False,
        "noread": False,
        "notime": False,
        "nouser": False,
        "nowait": False,
        "nowrite": False,
    }
    flag = Flag.load(None, is_local=True, **options)
    assert (
        flag
        == Flag.PID
        | Flag.IOWAIT
        | Flag.MODE
        | Flag.TYPE
        | Flag.RELATION
        | Flag.WAIT
        | Flag.TIME
        | Flag.WRITE
        | Flag.READ
        | Flag.MEM
        | Flag.CPU
        | Flag.USER
        | Flag.CLIENT
        | Flag.APPNAME
        | Flag.DATABASE
    )
    cfg = Configuration(pid=UISection(hidden=True), relation=UISection(hidden=False))
    flag = Flag.load(cfg, is_local=False, **options)
    assert (
        flag
        == Flag.MODE
        | Flag.TYPE
        | Flag.RELATION
        | Flag.WAIT
        | Flag.TIME
        | Flag.USER
        | Flag.CLIENT
        | Flag.APPNAME
        | Flag.DATABASE
    )
    options["nodb"] = True
    options["notime"] = True
    options["nopid"] = True
    cfg = Configuration(
        database=UISection(hidden=False), relation=UISection(hidden=True)
    )
    flag = Flag.load(cfg, is_local=False, **options)
    assert (
        flag
        == Flag.MODE | Flag.TYPE | Flag.WAIT | Flag.USER | Flag.CLIENT | Flag.APPNAME
    )


def test_lookup(tmp_path: Path) -> None:
    def asdict(cfg: Configuration) -> dict[str, Any]:
        return {k: attr.asdict(v) for k, v in cfg.items()}

    cfg = Configuration.lookup(None, user_config_home=tmp_path)
    assert cfg is None

    (tmp_path / "pg_activity.conf").write_text(
        "\n".join(
            [
                "[client]",
                "width=5",
                "[header]",
                "show_instance=no",
            ]
        )
    )
    cfg = Configuration.lookup(None, user_config_home=tmp_path)
    assert cfg is not None and asdict(cfg) == {
        "client": {"hidden": False, "width": 5},
        "header": {"show_instance": False, "show_system": True, "show_workers": True},
    }

    (tmp_path / "pg_activity").mkdir()
    (tmp_path / "pg_activity" / "x.conf").write_text(
        "\n".join(
            ["[database]", "hidden= on", "width = 3 ", "[header]", "show_workers=no"]
        )
    )
    cfg = Configuration.lookup("x", user_config_home=tmp_path)
    assert cfg is not None and asdict(cfg) == {
        "database": {"hidden": True, "width": 3},
        "header": {"show_instance": True, "show_system": True, "show_workers": False},
    }

    with pytest.raises(FileNotFoundError):
        Configuration.lookup("y", user_config_home=tmp_path)
