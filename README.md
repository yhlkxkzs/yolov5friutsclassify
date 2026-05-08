# yolov5friutsclassify

GitHub 侧用于存放**水果检测**推理权重（**YOLOv5s**，与同一流水线 **v5** 一路一致），供 Actions 或本地脚本使用。

权重为 **Ultralytics YOLOv5 仓库**格式的 checkpoint，推理使用 **`torch.hub.load('ultralytics/yolov5', 'custom', path=...)`**，见 `scripts/infer_fruit_detect.py`。

**移动端对接**：见 **[docs/MOBILE_APP_INTEGRATION.md](docs/MOBILE_APP_INTEGRATION.md)**。  
可选 Secrets：`FRUIT_SERVER_UPLOAD_URL`、`FRUIT_SERVER_UPLOAD_TOKEN`（与 MobileNet / YOLOv8 / yolov3friutsclassify 一致）。

## 当前权重

| 文件 | 说明 |
|------|------|
| `models/yolov5s_fruit_detect_best.pt` | **YOLOv5s** 检测 `best.pt` |

- **类别数**：6  
- **类别名**：见 `models/classes.json`  
- **来源 run**：`fruit_detection_formal100_20260430_164036`（与 v3 / v8 / v11 同批 formal100）  
- **本地原路径**：`YOLO/versions/v5/runs/train/fruit_detection_formal100_20260430_164036/weights/best.pt`  
- **训练起点**（`opt.yaml`）：`yolov5s.pt`

## 本地推理

```bash
pip install torch torchvision
pip install -r requirements.txt
python scripts/infer_fruit_detect.py --device cpu incoming/your.jpg
```

首次运行会从 PyTorch Hub 拉取 **`ultralytics/yolov5`**（需联网）。

## GitHub Actions

向 **`incoming/`** 推送图片触发 **Fruit detection (YOLOv5s / YOLOv5 hub)**，或 **Run workflow**。

## 克隆

```bash
git clone git@github.com:yhlkxkzs/yolov5friutsclassify.git
```
