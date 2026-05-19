#!/usr/bin/env python3
"""兼容旧 workflow 步骤名；逻辑与 afsa_write_predictions.py 相同。"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "afsa_write_predictions",
    Path(__file__).with_name("afsa_write_predictions.py"),
)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)

if __name__ == "__main__":
    raise SystemExit(_mod.main())
