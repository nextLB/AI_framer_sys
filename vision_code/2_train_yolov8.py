import os
import yaml
import argparse
from pathlib import Path
from ultralytics import YOLO


def get_dataset_info(dataset_yaml):
    """获取数据集信息"""
    with open(dataset_yaml, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data


def main():
    parser = argparse.ArgumentParser(description='Train YOLOv8 for Agricultural Plant Disease Detection')
    parser.add_argument('--data', type=str, 
                        default='/home/next_lb/桌面/next/基于AI的农业植保机器人监控软件系统/datasets/yolo_dataset/dataset.yaml',
                        help='Path to dataset.yaml')
    parser.add_argument('--model', type=str, 
                        default='yolov8n.pt',
                        choices=['yolov8n.pt', 'yolov8s.pt', 'yolov8m.pt', 'yolov8l.pt', 'yolov8x.pt'],
                        help='YOLOv8 model size')
    parser.add_argument('--epochs', type=int, default=100,
                        help='Number of training epochs')
    parser.add_argument('--batch', type=int, default=8,
                        help='Batch size (RTX 3060 12GB: recommended 8-16)')
    parser.add_argument('--imgsz', type=int, default=640,
                        help='Image size for training')
    parser.add_argument('--patience', type=int, default=20,
                        help='Early stopping patience')
    parser.add_argument('--project', type=str, 
                        default='/home/next_lb/桌面/next/基于AI的农业植保机器人监控软件系统/outputs/',
                        help='Project directory')
    parser.add_argument('--name', type=str, 
                        default='agriculture_yolov8',
                        help='Experiment name')
    parser.add_argument('--resume', type=str, 
                        default=None,
                        help='Resume from a checkpoint')
    parser.add_argument('--device', type=str, 
                        default='0',
                        help='GPU device (0 for single GPU)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.data):
        print(f"Error: dataset.yaml not found at {args.data}")
        print("Please run 1_dataset_converter.py first")
        return
    
    print("=" * 60)
    print("YOLOv8 Agricultural Plant Disease Detection Training")
    print("=" * 60)
    
    print(f"\nConfiguration:")
    print(f"  Dataset: {args.data}")
    print(f"  Model: {args.model}")
    print(f"  Epochs: {args.epochs}")
    print(f"  Batch size: {args.batch}")
    print(f"  Image size: {args.imgsz}")
    print(f"  Device: CUDA:{args.device}")
    
    dataset_info = get_dataset_info(args.data)
    print(f"\nDataset Info:")
    print(f"  Classes ({dataset_info['nc']}): {dataset_info['names']}")
    
    print("\n[1/1] Starting training...")
    print("-" * 60)
    
    os.makedirs(args.project, exist_ok=True)
    
    model = YOLO(args.model)
    
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        patience=args.patience,
        project=args.project,
        name=args.name,
        resume=args.resume,
        device=args.device,
        
        optimizer='AdamW',
        lr0=0.001,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        
        warmup_epochs=3.0,
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,
        
        box=7.5,
        cls=0.5,
        dfl=1.5,
        
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=10.0,
        translate=0.1,
        scale=0.5,
        shear=0.0,
        perspective=0.0,
        flipud=0.0,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.0,
        copy_paste=0.0,
        
        amp=True,
        cache=True,
        workers=4,
        close_mosaic=10,
        
        pretrained=True,
        verbose=True,
        seed=0,
    )
    
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print(f"Best model: {results.save_dir}/weights/best.pt")
    print(f"Last model: {results.save_dir}/weights/last.pt")
    
    print("\nNext step: python 3_validate.py")


if __name__ == '__main__':
    main()
