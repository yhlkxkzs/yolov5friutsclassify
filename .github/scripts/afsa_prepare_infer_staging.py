#!/usr/bin/env python3
"""仅为 fruit_category 图片建立推理暂存目录（符号链接）。"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

STAGING = Path("/tmp/afsa_infer_staging")
ROUTING = Path("out/afsa_routing.json")


def main() -> int:
    if not ROUTING.is_file():
        print(f"缺少 {ROUTING}", file=sys.stderr)
        return 1

    routing = json.loads(ROUTING.read_text(encoding="utf-8"))
    paths: list[str] = routing.get("fruit_category") or []

    if STAGING.exists():
        shutil.rmtree(STAGING)
    STAGING.mkdir(parents=True, exist_ok=True)

    for rel in paths:
        src = Path(rel)
        if not src.is_file():
            print(f"::warning::图片不存在，跳过: {rel}", file=sys.stderr)
            continue
        dst = STAGING / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.symlink_to(src.resolve())

    print(f"staging={STAGING.as_posix()} count={len(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
