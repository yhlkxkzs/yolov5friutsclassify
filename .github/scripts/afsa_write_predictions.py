#!/usr/bin/env python3
"""
合并推理结果并写出 App 可匹配的 predictions.json。

契约见：GitHub流水线对接说明_给仓库维护者.md
- image / github_path 必须与 sidecar.image_path 一致
- afsa_detection_id 来自 sidecar
- predicted_class、confidence 必填（confidence 0～1）
"""
from __future__ import annotations

import json
from pathlib import Path

ROUTING = Path("out/afsa_routing.json")
PARTIAL = Path("output/predictions_partial.json")
OUTPUT = Path("output/predictions.json")
REPO_KIND = Path("out/afsa_repo_kind.txt")


def normalize_confidence(value: object) -> float:
    try:
        c = float(value)
    except (TypeError, ValueError):
        return 0.0
    if c > 1.0:
        return c / 100.0
    return max(0.0, min(1.0, c))


def index_entries(routing: dict) -> dict[str, dict]:
    """按文件名与 repo 路径索引 routing entry。"""
    idx: dict[str, dict] = {}
    for ent in routing.get("entries") or []:
        repo_p = ent.get("repo_image_path", "")
        gh = ent.get("github_path", repo_p)
        for key in {repo_p, gh, Path(repo_p).name, Path(gh).name}:
            if key:
                idx[key] = ent
    return idx


def detection_top_label(partial_row: dict) -> tuple[str, float]:
    dets = partial_row.get("detections") or []
    if not dets:
        return "", 0.0
    best = max(dets, key=lambda d: float(d.get("confidence") or 0))
    return str(best.get("class") or ""), normalize_confidence(best.get("confidence", 0))


def app_row_from_infer(partial_row: dict, ent: dict) -> dict:
    gh = ent.get("github_path") or ent.get("repo_image_path", "")
    raw = partial_row.get("raw_class") or partial_row.get("predicted_class") or ""
    conf = partial_row.get("confidence")
    if not raw and partial_row.get("detections"):
        raw, conf = detection_top_label(partial_row)
    display = partial_row.get("predicted_class") or raw
    conf = normalize_confidence(conf if conf is not None else 0)

    row: dict = {
        "image": gh,
        "github_path": gh,
        "afsa_detection_id": ent.get("afsa_detection_id"),
        "predicted_class": raw or display,
        "confidence": conf,
        "status": "ok",
        "task_type": ent.get("task_type", "fruit_category"),
        "detection_type": ent.get("detection_type", "category"),
    }
    if display and display != row["predicted_class"]:
        row["predicted_class_display"] = display
    if partial_row.get("top5"):
        row["top5"] = partial_row["top5"]
    return row


def skipped_row(ent: dict, repo_kind: str) -> dict:
    gh = ent.get("github_path") or ent.get("repo_image_path", "")
    tt = ent.get("task_type", "unknown")
    dt = ent.get("detection_type", "unknown")
    return {
        "image": gh,
        "github_path": gh,
        "afsa_detection_id": ent.get("afsa_detection_id"),
        "predicted_class": None,
        "confidence": None,
        "status": "skipped_wrong_pipeline",
        "task_type": tt,
        "detection_type": dt,
        "client_preset": ent.get("client_preset"),
        "message": (
            f"本仓库为水果{'分类' if repo_kind == 'classify' else '检测'}模型，"
            f"不处理 task_type={tt}。请为 growth/disease 配置专用 GitHub 仓。"
        ),
    }


def match_entry(partial_row: dict, idx: dict[str, dict]) -> dict | None:
    img = str(partial_row.get("image", ""))
    p = Path(img)
    for key in (img, p.name, p.as_posix().split("/incoming/", 1)[-1] if "/incoming/" in img else ""):
        if key and key in idx:
            return idx[key]
    # staging: /tmp/afsa_infer_staging/incoming/category/uploads/foo.jpg
    parts = p.parts
    if "incoming" in parts:
        i = parts.index("incoming")
        rel = "/".join(parts[i:])
        if rel in idx:
            return idx[rel]
    return None


def main() -> int:
    repo_kind = REPO_KIND.read_text(encoding="utf-8").strip() if REPO_KIND.is_file() else "classify"
    routing: dict = {}
    if ROUTING.is_file():
        routing = json.loads(ROUTING.read_text(encoding="utf-8"))

    idx = index_entries(routing)
    predictions: list[dict] = []
    matched_repo_paths: set[str] = set()
    weights = None

    if PARTIAL.is_file():
        partial = json.loads(PARTIAL.read_text(encoding="utf-8"))
        weights = partial.get("weights")
        for prow in partial.get("predictions") or []:
            ent = match_entry(prow, idx)
            if ent is None:
                gh = prow.get("image", "")
                if "/incoming/" in gh:
                    gh = "incoming/" + gh.split("/incoming/", 1)[1]
                predictions.append(
                    {
                        "image": gh,
                        "github_path": gh,
                        "afsa_detection_id": None,
                        "predicted_class": prow.get("raw_class") or prow.get("predicted_class"),
                        "confidence": normalize_confidence(prow.get("confidence")),
                        "status": "ok",
                        "task_type": "fruit_category",
                        "detection_type": "category",
                        "warning": "no_sidecar_match",
                    }
                )
                continue
            predictions.append(app_row_from_infer(prow, ent))
            matched_repo_paths.add(ent.get("repo_image_path", ""))

    for ent in routing.get("growth") or []:
        predictions.append(skipped_row(ent, repo_kind))
    for ent in routing.get("disease") or []:
        predictions.append(skipped_row(ent, repo_kind))

    # category 在 routing 中但推理未产出（空 staging 等）
    for repo_path in routing.get("fruit_category") or []:
        if repo_path in matched_repo_paths:
            continue
        ent = idx.get(repo_path) or idx.get(Path(repo_path).name)
        if not ent:
            continue
        predictions.append(
            {
                "image": ent["github_path"],
                "github_path": ent["github_path"],
                "afsa_detection_id": ent.get("afsa_detection_id"),
                "predicted_class": None,
                "confidence": None,
                "status": "inference_missing",
                "task_type": ent.get("task_type"),
                "detection_type": ent.get("detection_type"),
            }
        )

    payload = {
        "predictions": predictions,
    }
    if weights:
        payload["weights"] = weights

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
