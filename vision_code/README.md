# YOLOv8 农业植物病害检测训练系统

基于 YOLOv8 的农业植保机器人监控软件系统的深度学习目标检测模块。

## 数据集说明

本项目使用的数据集为 PlantVillage 公开数据集的子集，包含以下 15 个类别：

| 类别 ID | 类别名称 |
|--------|----------|
| 0 | Pepper__bell___Bacterial_spot |
| 1 | Pepper__bell___healthy |
| 2 | Potato___Early_blight |
| 3 | Potato___healthy |
| 4 | Potato___Late_blight |
| 5 | Tomato__Target_Spot |
| 6 | Tomato__Tomato_mosaic_virus |
| 7 | Tomato__Tomato_YellowLeaf__Curl_Virus |
| 8 | Tomato_Bacterial_spot |
| 9 | Tomato_Early_blight |
| 10 | Tomato_healthy |
| 11 | Tomato_Late_blight |
| 12 | Tomato_Leaf_Mold |
| 13 | Tomato_Septoria_leaf_spot |
| 14 | Tomato_Spider_mites_Two_spotted_spider_mite |

## 快速开始

### 1. 环境配置

参考 `../document/env_setup_guide.md` 配置 conda 环境：

```bash
conda create -n yolov8_agriculture python=3.10
conda activate yolov8_agriculture
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu118
pip install ultralytics opencv-python pillow pandas matplotlib seaborn tqdm pyyaml
```

### 2. 数据集转换

将原始分类格式转换为 YOLO 格式：

```bash
python 1_dataset_converter.py
```

参数说明：
- `--dataset`: 原始数据集路径（默认: `../datasets`）
- `--output`: YOLO 格式输出路径（默认: `../datasets/yolo_dataset`）
- `--train-ratio`: 训练集比例（默认: 0.7）
- `--val-ratio`: 验证集比例（默认: 0.2）

### 3. 模型训练

```bash
python 2_train_yolov8.py
```

参数说明：
- `--data`: 数据集配置文件路径
- `--model`: 模型大小（n/s/m/l/x，默认: yolov8n.pt）
- `--epochs`: 训练轮数（默认: 100）
- `--batch`: 批量大小（RTX 3060 推荐: 8-16）
- `--imgsz`: 输入图像尺寸（默认: 640）

### 4. 模型验证

```bash
python 3_validate.py
```

### 5. 推理测试

```bash
# 单张图片
python 4_inference.py --mode image --source path/to/image.jpg

# 文件夹批量推理
python 4_inference.py --mode folder --source path/to/folder

# 摄像头实时推理
python 4_inference.py --mode camera --camera-id 0
```

## RTX 3060 (12GB) 显存优化建议

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| batch | 8-16 | 根据实际情况调整 |
| imgsz | 640 | 可降低到 416/320 |
| workers | 4 | 数据加载线程数 |
| amp | True | 启用混合精度训练 |

## 输出目录结构

```
outputs/
├── agriculture_yolov8/
│   ├── weights/
│   │   ├── best.pt      # 最佳模型
│   │   └── last.pt      # 最终模型
│   ├── args.yaml        # 训练配置
│   └── results.csv      # 训练指标
└── inference/           # 推理结果
```

## 模型性能指标

训练完成后可查看：
- `results.png`: 训练损失曲线
- `confusion_matrix.png`: 混淆矩阵
- `F1_curve.png`: F1 分数曲线
- `PR_curve.png`: PR 曲线
- `labels.jpg`: 标注分布图
