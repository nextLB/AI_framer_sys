import os
import argparse
from pathlib import Path
from ultralytics import YOLO
import matplotlib.pyplot as plt


def validate_model(model_path, data_yaml, imgsz=640, batch=16, conf=0.001, iou=0.6):
    """验证模型性能"""
    model = YOLO(model_path)
    
    print("=" * 60)
    print("YOLOv8 Model Validation")
    print("=" * 60)
    
    metrics = model.val(
        data=data_yaml,
        batch=batch,
        imgsz=imgsz,
        conf=conf,
        iou=iou,
        device=0,
        workers=4,
        plots=True,
        save_json=True,
        verbose=True
    )
    
    print("\n" + "=" * 60)
    print("Validation Results")
    print("=" * 60)
    print(f"\nmAP50: {metrics.box.map50:.4f}")
    print(f"mAP50-95: {metrics.box.map:.4f}")
    print(f"Precision: {metrics.box.mp:.4f}")
    print(f"Recall: {metrics.box.mr:.4f}")
    
    print("\nPer-Class AP:")
    if hasattr(metrics.box, 'ap50'):
        for i, ap in enumerate(metrics.box.ap50):
            print(f"  Class {i}: AP50 = {ap:.4f}")
    
    return metrics


def main():
    parser = argparse.ArgumentParser(description='Validate YOLOv8 model')
    parser.add_argument('--weights', type=str, 
                        default='./outputs/agriculture_yolov8/weights/best.pt',
                        help='Path to model weights')
    parser.add_argument('--data', type=str, 
                        default='/home/next_lb/桌面/next/基于AI的农业植保机器人监控软件系统/datasets/yolo_dataset/dataset.yaml',
                        help='Path to dataset.yaml')
    parser.add_argument('--batch', type=int, default=16,
                        help='Batch size for validation')
    parser.add_argument('--imgsz', type=int, default=640,
                        help='Image size')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.weights):
        print(f"Error: Weights file not found: {args.weights}")
        return
    
    if not os.path.exists(args.data):
        print(f"Error: dataset.yaml not found: {args.data}")
        return
    
    validate_model(args.weights, args.data, args.imgsz, args.batch)


if __name__ == '__main__':
    main()
