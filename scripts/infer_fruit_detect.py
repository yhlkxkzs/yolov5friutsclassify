#!/usr/bin/env python3
"""YOLOv5s 检测推理：权重为 YOLOv5 仓库导出的 .pt，经 torch.hub.load('ultralytics/yolov5', 'custom') 加载。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WEIGHTS = REPO_ROOT / "models" / "yolov5s_fruit_detect_best.pt"
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".ppm", ".tif", ".tiff"}


def collect_images(incoming: Path) -> list[Path]:
    if not incoming.exists():
        return []
    out: list[Path] = []
    for p in sorted(incoming.rglob("*")):
        if p.is_file() and p.suffix.lower() in IMAGE_EXT:
            out.append(p)
    return out


def load_model(weights: Path, device: str):
    m = torch.hub.load(
        "ultralytics/yolov5",
        "custom",
        path=str(weights),
        trust_repo=True,
        device=device,
        _verbose=False,
    )
    return m


def predict_one(model, image_path: Path, imgsz: int, conf: float) -> dict:
    model.conf = conf
    results = model(str(image_path), size=imgsz)
    names = results.names
    dets: list[dict] = []
    pred0 = results.pred[0]
    if pred0 is not None and len(pred0):
        for det in pred0:
            x1, y1, x2, y2, c, cls = det.tolist()
            cid = int(cls)
            label = names[cid] if isinstance(names, dict) else names[cid]
            dets.append(
                {
                    "class_id": cid,
                    "class": label,
                    "confidence": float(c),
                    "xyxy": [float(x1), float(y1), float(x2), float(y2)],
                }
            )
    return {"image": str(image_path.as_posix()), "detections": dets}


def main() -> int:
    p = argparse.ArgumentParser(description="YOLOv5s（YOLOv5 hub）水果检测推理")
    p.add_argument("--weights", type=Path, default=DEFAULT_WEIGHTS, help="检测权重 .pt")
    p.add_argument("--imgsz", type=int, default=640, help="推理尺寸（与训练 imgsz 一致）")
    p.add_argument("--conf", type=float, default=0.25, help="置信度阈值")
    p.add_argument(
        "--device",
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="cpu 或 cuda（默认自动）",
    )
    p.add_argument("--incoming", type=Path, default=REPO_ROOT / "incoming", help="待检测图片目录")
    p.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "output" / "predictions.json",
        help="预测结果 JSON",
    )
    p.add_argument("images", nargs="*", type=Path, help="可选：图片路径；留空则扫描 --incoming")
    args = p.parse_args()

    weights = args.weights if args.weights.is_absolute() else REPO_ROOT / args.weights
    if not weights.exists():
        print(f"权重不存在: {weights}", file=sys.stderr)
        return 1

    if args.images:
        paths = []
        for x in args.images:
            xp = x if x.is_absolute() else REPO_ROOT / x
            if not xp.exists():
                print(f"图片不存在: {xp}", file=sys.stderr)
                return 1
            paths.append(xp)
    else:
        paths = collect_images(args.incoming)

    if not paths:
        print("未找到图片：请将图片放入 incoming/ 或通过参数传入路径。", file=sys.stderr)
        return 0

    model = load_model(weights, args.device)
    results = [predict_one(model, im, args.imgsz, args.conf) for im in paths]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "weights": str(weights),
        "backend": "torch.hub ultralytics/yolov5 custom",
        "imgsz": args.imgsz,
        "conf": args.conf,
        "device": args.device,
        "count": len(results),
        "predictions": results,
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
