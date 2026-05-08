# 移动端与 GitHub YOLOv5s 检测仓库对接说明

与 **MobileNet / Yolov8fruitsclassify / yolov3friutsclassify** 相同流程：OAuth → Contents API 写入 **`incoming/`** → push 触发 Actions → 下载 **`predictions`** Artifact 或查看 Summary。

| 项 | 值 |
|----|-----|
| 仓库 | `yhlkxkzs/yolov5friutsclassify` |
| 权重 | `models/yolov5s_fruit_detect_best.pt` |
| Workflow | `Fruit detection (YOLOv5s / YOLOv5 hub)` |

检测结果 JSON 中每张图含 **`detections`**：`class_id`、`class`、`confidence`、`xyxy`。

**可选**：仓库 Secrets 配置 `FRUIT_SERVER_UPLOAD_URL`（及可选 `FRUIT_SERVER_UPLOAD_TOKEN`），Workflow 在推理前将相关图片 POST 到你的 **公网 HTTPS** 接口（字段：`file`、`path`、`commit`、`repo`）。
