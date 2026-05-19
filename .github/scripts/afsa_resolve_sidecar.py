#!/usr/bin/env python3
"""解析本次 push 下 incoming/ 图片及同名 .afsa.json（与 AFSA App 契约一致）。"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def all_incoming_images() -> list[str]:
    root = Path("incoming")
    if not root.is_dir():
        return []
    return [
        p.as_posix()
        for p in sorted(root.rglob("*"))
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    ]


def changed_images() -> list[str]:
    if os.environ.get("AFSA_SCAN_ALL") == "1":
        return all_incoming_images()
    r = subprocess.run(
        ["git", "diff", "--name-only", "HEAD^", "HEAD", "--", "incoming/"],
        capture_output=True,
        text=True,
        check=False,
    )
    return [p.strip() for p in r.stdout.splitlines() if p.strip() and Path(p).suffix.lower() in IMAGE_EXTS]


def load_sidecar(image_path: str) -> dict | None:
    p = Path(image_path)
    for sidecar in (p.with_suffix(".afsa.json"), p.parent / f"{p.stem}.afsa.json"):
        if sidecar.is_file():
            with sidecar.open(encoding="utf-8") as f:
                return json.load(f)
    return None


def github_path_for(meta: dict | None, repo_image_path: str) -> str:
    """App 匹配键：优先 sidecar.image_path，与上传路径完全一致。"""
    if meta:
        ip = str(meta.get("image_path", "") or "").strip()
        if ip:
            return ip.replace("\\", "/")
    return repo_image_path.replace("\\", "/")


def bucket_task(meta: dict | None) -> str:
    if not meta:
        return "fruit_category"
    tt = str(meta.get("task_type", "") or "").strip()
    dt = str(meta.get("detection_type", "") or "").strip().lower()
    if tt.startswith("growth_") or dt == "growth":
        return "growth"
    if tt.startswith("disease_") or dt == "disease":
        return "disease"
    return "fruit_category"


def entry_from(meta: dict | None, repo_image_path: str, bucket: str) -> dict:
    gh = github_path_for(meta, repo_image_path)
    return {
        "repo_image_path": repo_image_path,
        "github_path": gh,
        "image_path_sidecar": (meta or {}).get("image_path"),
        "bucket": bucket,
        "task_type": (meta or {}).get("task_type", "fruit_category"),
        "detection_type": (meta or {}).get("detection_type", "category"),
        "client_preset": (meta or {}).get("client_preset"),
        "afsa_detection_id": (meta or {}).get("afsa_detection_id"),
        "github_model_target_id": (meta or {}).get("github_model_target_id"),
        "sidecar_missing": meta is None,
    }


def main() -> int:
    routing: dict = {
        "schema_version": 1,
        "fruit_category": [],
        "growth": [],
        "disease": [],
        "entries": [],
    }

    for img in changed_images():
        meta = load_sidecar(img)
        bucket = bucket_task(meta)
        ent = entry_from(meta, img, bucket)
        routing["entries"].append(ent)
        if bucket == "fruit_category":
            routing["fruit_category"].append(img)
        elif bucket == "growth":
            routing["growth"].append(ent)
        else:
            routing["disease"].append(ent)

    out_dir = Path("out")
    out_dir.mkdir(parents=True, exist_ok=True)
    routing_path = out_dir / "afsa_routing.json"
    routing_path.write_text(json.dumps(routing, ensure_ascii=False, indent=2), encoding="utf-8")

    task_types = sorted({str(e.get("task_type", "")) for e in routing["entries"]})
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"image_count={len(routing['entries'])}\n")
            f.write(f"category_count={len(routing['fruit_category'])}\n")
            f.write(f"growth_count={len(routing['growth'])}\n")
            f.write(f"disease_count={len(routing['disease'])}\n")
            f.write(f"task_types={','.join(task_types)}\n")
            f.write(f"routing_path={routing_path.as_posix()}\n")

    print(json.dumps(routing, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
