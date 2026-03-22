import os
import argparse
from pathlib import Path
from ultralytics import YOLO
import cv2


def draw_predictions(image, results, class_names, conf_threshold=0.25):
    """在图像上绘制预测结果"""
    annotated_frame = image.copy()
    
    if len(results) == 0:
        return annotated_frame
    
    boxes = results[0].boxes
    if boxes is None or len(boxes) == 0:
        return annotated_frame
    
    for box in boxes:
        conf = float(box.conf[0])
        cls_id = int(box.cls[0])
        
        if conf < conf_threshold:
            continue
        
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        
        label = f"{class_names[cls_id]}: {conf:.2f}"
        
        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        cv2.rectangle(annotated_frame, (x1, y1 - label_size[1] - 10), 
                     (x1 + label_size[0], y1), (0, 255, 0), -1)
        cv2.putText(annotated_frame, label, (x1, y1 - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    
    return annotated_frame


def inference_image(model_path, image_path, conf=0.25, save_dir='../outputs/inference'):
    """单张图片推理"""
    model = YOLO(model_path)
    
    results = model.predict(
        source=image_path,
        conf=conf,
        iou=0.45,
        imgsz=640,
        device=0,
        save=True,
        save_txt=False,
        show=False,
        verbose=False
    )
    
    class_names = list(model.names.values())
    
    if results[0].boxes is not None and len(results[0].boxes) > 0:
        print(f"\nDetections in {os.path.basename(image_path)}:")
        for box in results[0].boxes:
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            print(f"  - {class_names[cls_id]}: {conf:.4f}")
    
    return results


def inference_folder(model_path, folder_path, conf=0.25, save_dir='../outputs/inference'):
    """批量图片推理"""
    model = YOLO(model_path)
    
    os.makedirs(save_dir, exist_ok=True)
    
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(image_extensions)]
    
    if len(image_files) == 0:
        print(f"No images found in {folder_path}")
        return
    
    print(f"Found {len(image_files)} images")
    
    results = model.predict(
        source=folder_path,
        conf=conf,
        iou=0.45,
        imgsz=640,
        device=0,
        save=True,
        save_txt=False,
        show=False,
        verbose=False
    )
    
    print(f"\nResults saved to: {save_dir}")
    
    class_names = list(model.names.values())
    for r in results:
        if r.boxes is not None and len(r.boxes) > 0:
            print(f"\n{os.path.basename(r.path)}:")
            for box in r.boxes:
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                print(f"  - {class_names[cls_id]}: {conf:.4f}")


def inference_camera(model_path, conf=0.25, camera_id=0):
    """摄像头实时推理"""
    model = YOLO(model_path)
    class_names = list(model.names.values())
    
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"Error: Cannot open camera {camera_id}")
        return
    
    print(f"Press 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        results = model.predict(
            source=frame,
            conf=conf,
            iou=0.45,
            imgsz=640,
            device=0,
            verbose=False
        )
        
        annotated_frame = draw_predictions(frame, results, class_names, conf)
        
        cv2.imshow('YOLOv8 Inference', annotated_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description='YOLOv8 Inference for Agricultural Plant Disease')
    parser.add_argument('--weights', type=str, 
                        default='./outputs/agriculture_yolov8/weights/best.pt',
                        help='Path to model weights')
    parser.add_argument('--source', type=str, 
                        default=None,
                        help='Image file, folder, or camera index')
    parser.add_argument('--conf', type=float, default=0.25,
                        help='Confidence threshold')
    parser.add_argument('--mode', type=str, 
                        default='image',
                        choices=['image', 'folder', 'camera'],
                        help='Inference mode')
    parser.add_argument('--camera-id', type=int, default=0,
                        help='Camera device ID')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.weights):
        print(f"Error: Weights file not found: {args.weights}")
        return
    
    print("=" * 60)
    print("YOLOv8 Agricultural Plant Disease Detection - Inference")
    print("=" * 60)
    
    if args.mode == 'camera':
        inference_camera(args.weights, args.conf, args.camera_id)
    elif args.mode == 'folder':
        if args.source is None:
            args.source = '../datasets/yolo_dataset/images/val'
        inference_folder(args.weights, args.source, args.conf)
    else:
        if args.source is None:
            args.source = '../datasets/yolo_dataset/images/val'
            if os.path.exists(args.source):
                files = [f for f in os.listdir(args.source) if f.endswith(('.jpg', '.png'))]
                if files:
                    args.source = os.path.join(args.source, files[0])
        
        if os.path.isfile(args.source):
            inference_image(args.weights, args.source, args.conf)
        elif os.path.isdir(args.source):
            inference_folder(args.weights, args.source, args.conf)
        else:
            print(f"Error: Source not found: {args.source}")


if __name__ == '__main__':
    main()
