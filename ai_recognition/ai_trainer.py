import os
import threading
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from django.utils import timezone
from django.conf import settings
import yaml

logger = logging.getLogger(__name__)


class YOLOTrainer:
    def __init__(self, training_task):
        self.training_task = training_task
        self.model = None
        self.is_running = False
        self.stop_flag = threading.Event()
        
    def start_training(self):
        self.is_running = True
        self.stop_flag.clear()
        thread = threading.Thread(target=self._train)
        thread.daemon = True
        thread.start()
        
    def stop_training(self):
        self.stop_flag.set()
        self.is_running = False
        
    def _train(self):
        try:
            from ultralytics import YOLO
            from datetime import datetime
            
            self.training_task.status = 'running'
            self.training_task.started_at = timezone.now()
            self.training_task.save()
            
            output_dir = os.path.join(
                settings.MEDIA_ROOT, 
                'training_outputs',
                f"train_{self.training_task.id}_{int(time.time())}"
            )
            os.makedirs(output_dir, exist_ok=True)
            self.training_task.output_dir = output_dir
            self.training_task.save()
            
            base_model = f"{self.training_task.model_type}.pt"
            logger.info(f"Loading base model: {base_model}")
            self.model = YOLO(base_model)
            
            results = self.model.train(
                data=self.training_task.dataset_path,
                epochs=self.training_task.epochs,
                batch=self.training_task.batch_size,
                imgsz=self.training_task.image_size,
                patience=self.training_task.patience,
                project=output_dir,
                name='weights',
                device=self.training_task.device,
                optimizer=self.training_task.optimizer,
                lr0=self.training_task.learning_rate,
                lrf=0.01,
                momentum=self.training_task.momentum,
                weight_decay=self.training_task.weight_decay,
                warmup_epochs=3.0,
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
                amp=True,
                cache=True,
                workers=4,
                close_mosaic=10,
                pretrained=True,
                verbose=True,
                seed=0,
            )
            
            best_model_path = os.path.join(output_dir, 'weights', 'best.pt')
            if os.path.exists(best_model_path):
                from .models import AIModel
                
                class_names = {}
                dataset_yaml = self.training_task.dataset_path
                if os.path.exists(dataset_yaml):
                    with open(dataset_yaml, 'r', encoding='utf-8') as f:
                        dataset_info = yaml.safe_load(f)
                        class_names = dataset_info.get('names', {})
                
                trained_model = AIModel.objects.create(
                    name=f"{self.training_task.name}_trained",
                    model_type=self.training_task.model_type,
                    model_path=best_model_path,
                    num_classes=len(class_names),
                    class_names=class_names,
                    accuracy=results.results_dict.get('metrics/mAP50(B)', 0) if results else None,
                    is_active=False,
                )
                
                self.training_task.trained_model = trained_model
                self.training_task.best_map = results.results_dict.get('metrics/mAP50(B)', 0) if results else None
            
            self.training_task.status = 'completed'
            self.training_task.progress = 100
            self.training_task.current_epoch = self.training_task.epochs
            self.training_task.completed_at = timezone.now()
            self.training_task.save()
            
            self.is_running = False
            logger.info(f"Training completed: {self.training_task.name}")
            
        except Exception as e:
            logger.error(f"Training failed: {str(e)}")
            self.training_task.status = 'failed'
            self.training_task.error_message = str(e)
            self.training_task.completed_at = timezone.now()
            self.training_task.save()
            self.is_running = False
            
    def get_progress(self) -> Dict[str, Any]:
        if not self.is_running and self.training_task.status == 'completed':
            return {
                'status': 'completed',
                'progress': 100,
                'current_epoch': self.training_task.epochs,
                'best_map': self.training_task.best_map,
            }
        
        log_file = None
        if self.training_task.output_dir:
            log_file = os.path.join(self.training_task.output_dir, 'weights', 'results.csv')
        
        current_epoch = 0
        best_map = 0.0
        
        if log_file and os.path.exists(log_file):
            try:
                import pandas as pd
                df = pd.read_csv(log_file)
                if len(df) > 0:
                    current_epoch = int(df['epoch'].iloc[-1]) if 'epoch' in df.columns else 0
                    if 'metrics/mAP50(B)' in df.columns:
                        best_map = float(df['metrics/mAP50(B)'].iloc[-1])
            except:
                pass
        
        progress = int((current_epoch / self.training_task.epochs) * 100) if self.training_task.epochs > 0 else 0
        
        return {
            'status': self.training_task.status,
            'progress': progress,
            'current_epoch': current_epoch,
            'best_map': best_map,
        }


class YOLOInference:
    def __init__(self, model_path: str, confidence: float = 0.25):
        self.model_path = model_path
        self.confidence = confidence
        self.model = None
        self.class_names = []
        
    def load_model(self):
        try:
            from ultralytics import YOLO
            self.model = YOLO(self.model_path)
            self.class_names = list(self.model.names.values())
            logger.info(f"Model loaded: {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            return False
            
    def predict_image(self, image_path: str, save_dir: Optional[str] = None) -> Dict[str, Any]:
        if not self.model:
            if not self.load_model():
                return {'error': 'Failed to load model'}
        
        start_time = time.time()
        
        try:
            results = self.model.predict(
                source=image_path,
                conf=self.confidence,
                iou=0.45,
                imgsz=640,
                device=0,
                save=True,
                save_txt=False,
                show=False,
                verbose=False
            )
            
            processing_time = time.time() - start_time
            detections = []
            class_counts = {}
            
            if results and len(results) > 0:
                boxes = results[0].boxes
                if boxes is not None and len(boxes) > 0:
                    for box in boxes:
                        conf = float(box.conf[0])
                        cls_id = int(box.cls[0])
                        cls_name = self.class_names[cls_id] if cls_id < len(self.class_names) else f"class_{cls_id}"
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        
                        detections.append({
                            'class_id': cls_id,
                            'class_name': cls_name,
                            'confidence': conf,
                            'bbox': [x1, y1, x2, y2],
                        })
                        
                        class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
            
            result_image = None
            if results and len(results) > 0 and hasattr(results[0], 'plot'):
                result_image = results[0].plot()
            
            return {
                'success': True,
                'detections': detections,
                'total_detections': len(detections),
                'class_counts': class_counts,
                'processing_time': processing_time,
                'result_image': result_image,
            }
            
        except Exception as e:
            logger.error(f"Inference failed: {str(e)}")
            return {'success': False, 'error': str(e)}
            
    def predict_video(self, video_path: str, save_path: Optional[str] = None) -> Dict[str, Any]:
        if not self.model:
            if not self.load_model():
                return {'error': 'Failed to load model'}
        
        import cv2
        
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {'success': False, 'error': 'Cannot open video'}
            
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if save_path:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(save_path, fourcc, fps, (width, height))
            
            all_detections = []
            frame_idx = 0
            start_time = time.time()
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                results = self.model.predict(
                    source=frame,
                    conf=self.confidence,
                    iou=0.45,
                    imgsz=640,
                    device=0,
                    verbose=False
                )
                
                frame_detections = []
                if results and len(results) > 0:
                    boxes = results[0].boxes
                    if boxes is not None and len(boxes) > 0:
                        for box in boxes:
                            conf = float(box.conf[0])
                            cls_id = int(box.cls[0])
                            cls_name = self.class_names[cls_id] if cls_id < len(self.class_names) else f"class_{cls_id}"
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            frame_detections.append({
                                'frame': frame_idx,
                                'class_id': cls_id,
                                'class_name': cls_name,
                                'confidence': conf,
                                'bbox': [x1, y1, x2, y2],
                            })
                
                all_detections.append({
                    'frame': frame_idx,
                    'detections': frame_detections,
                })
                
                if save_path and results and len(results) > 0:
                    annotated = results[0].plot()
                    out.write(annotated)
                
                frame_idx += 1
            
            cap.release()
            if save_path:
                out.release()
            
            processing_time = time.time() - start_time
            total_det = sum(len(f['detections']) for f in all_detections)
            
            class_counts = {}
            for fd in all_detections:
                for det in fd['detections']:
                    cls_name = det['class_name']
                    class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
            
            return {
                'success': True,
                'total_frames': frame_idx,
                'total_detections': total_det,
                'class_counts': class_counts,
                'detections': all_detections,
                'processing_time': processing_time,
                'result_video': save_path,
            }
            
        except Exception as e:
            logger.error(f"Video inference failed: {str(e)}")
            return {'success': False, 'error': str(e)}
            
    def predict_camera_frame(self, frame) -> Dict[str, Any]:
        if not self.model:
            return {'error': 'Model not loaded'}
        
        try:
            results = self.model.predict(
                source=frame,
                conf=self.confidence,
                iou=0.45,
                imgsz=640,
                device=0,
                verbose=False
            )
            
            detections = []
            if results and len(results) > 0:
                boxes = results[0].boxes
                if boxes is not None and len(boxes) > 0:
                    for box in boxes:
                        conf = float(box.conf[0])
                        cls_id = int(box.cls[0])
                        cls_name = self.class_names[cls_id] if cls_id < len(self.class_names) else f"class_{cls_id}"
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        detections.append({
                            'class_id': cls_id,
                            'class_name': cls_name,
                            'confidence': conf,
                            'bbox': [x1, y1, x2, y2],
                        })
            
            annotated = None
            if results and len(results) > 0 and hasattr(results[0], 'plot'):
                annotated = results[0].plot()
            
            return {
                'success': True,
                'detections': detections,
                'annotated_frame': annotated,
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


trainer_instances: Dict[int, YOLOTrainer] = {}


def get_trainer(training_task_id: int) -> Optional[YOLOTrainer]:
    return trainer_instances.get(training_task_id)


def create_trainer(training_task) -> YOLOTrainer:
    trainer = YOLOTrainer(training_task)
    trainer_instances[training_task.id] = trainer
    return trainer


def remove_trainer(training_task_id: int):
    if training_task_id in trainer_instances:
        del trainer_instances[training_task_id]
