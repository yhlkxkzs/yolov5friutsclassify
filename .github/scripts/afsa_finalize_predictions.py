#!/usr/bin/env python3
"""合并模型推理结果 + growth/disease 跳过说明，输出 App 可读的 predictions.json。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROUTING = Path("out/afsa_routing.json")
PARTIAL = Path("output/predictions_partial.json")
OUTPUT = Path("output/predictions.json")
REPO_KIND = Path("out/afsa_repo_kind.txt")  # classify | detect


def skipped_record(ent: dict, repo_kind: str) -> dict:
    tt = ent.get("task_type", "unknown")
    dt = ent.get("detection_type", "unknown")
    return {
        "image": ent.get("image"),
        "task_type": tt,
        "detection_type": dt,
        "client_preset": ent.get("client_preset"),
        "afsa_detection_id": ent.get("afsa_detection_id"),
        "status": "skipped_wrong_pipeline",
        "predicted_class": None,
        "raw_class": None,
        "confidence": None,
        "message": (
            f"本仓库为水果{'分类' if repo_kind == 'classify' else '检测'}模型，"
            f"不处理 task_type={tt}（detection_type={dt}）。"
            "请在 App 的 github_fruit_classification_targets 中为 growth/disease 配置专用仓。"
        ),
    }


def main() -> int:
    repo_kind = "classify"
    if REPO_KIND.is_file():
        repo_kind = REPO_KIND.read_text(encoding="utf-8").strip() or repo_kind

    routing = {"fruit_category": [], "growth": [], "disease": []}
    if ROUTING.is_file():
        routing = json.loads(ROUTING.read_text(encoding="utf-8"))

    predictions: list[dict] = []
    weights = None
    if PARTIAL.is_file():
        partial = json.loads(PARTIAL.read_text(encoding="utf-8"))
        weights = partial.get("weights")
        for row in partial.get("predictions") or []:
            row = dict(row)
            row.setdefault("status", "ok")
            row.setdefault("task_type", "fruit_category")
            row.setdefault("detection_type", "category")
            predictions.append(row)

    for ent in routing.get("growth") or []:
        predictions.append(skipped_record(ent, repo_kind))
    for ent in routing.get("disease") or []:
        predictions.append(skipped_record(ent, repo_kind))

    payload = {
        "schema_version": 1,
        "repo_kind": repo_kind,
        "weights": weights,
        "count": len(predictions),
        "routed": {
            "fruit_category": len(routing.get("fruit_category") or []),
            "growth": len(routing.get("growth") or []),
            "disease": len(routing.get("disease") or []),
        },
        "predictions": predictions,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
