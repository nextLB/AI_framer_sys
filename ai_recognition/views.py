import os
import json
import time
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, FileResponse, HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from devices.models import RobotDevice
from .models import RecognitionTask, RecognitionConfig, AIModel, TrainingTask, InferenceRecord
from .services import AIRecognitionService
from .ai_trainer import YOLOInference, create_trainer, get_trainer, remove_trainer


@login_required
def recognition_dashboard(request):
    tasks = RecognitionTask.objects.all().order_by('-created_at')[:50]
    configs = RecognitionConfig.objects.all()
    
    return render(request, 'ai_recognition/dashboard.html', {
        'tasks': tasks,
        'configs': configs,
    })


@login_required
def start_recognition(request, device_id):
    device = get_object_or_404(RobotDevice, id=device_id)
    
    if request.method == 'POST':
        task_type = request.POST.get('task_type')
        
        task = RecognitionTask.objects.create(
            device=device,
            task_type=task_type,
            status='pending'
        )
        
        return redirect('recognition_task_detail', task_id=task.id)
    
    return render(request, 'ai_recognition/start_recognition.html', {'device': device})


@login_required
def recognition_task_detail(request, task_id):
    task = get_object_or_404(RecognitionTask, id=task_id)
    return render(request, 'ai_recognition/task_detail.html', {'task': task})


@login_required
def recognition_history(request):
    device_id = request.GET.get('device_id')
    task_type = request.GET.get('task_type')
    
    tasks = RecognitionTask.objects.all()
    
    if device_id:
        tasks = tasks.filter(device_id=device_id)
    if task_type:
        tasks = tasks.filter(task_type=task_type)
    
    tasks = tasks.order_by('-created_at')
    paginator = Paginator(tasks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    devices = RobotDevice.objects.all()
    
    return render(request, 'ai_recognition/history.html', {
        'page_obj': page_obj,
        'devices': devices,
    })


@login_required
def run_recognition_api(request, task_id):
    task = get_object_or_404(RecognitionTask, id=task_id)
    
    if task.status != 'pending':
        return JsonResponse({'error': '任务已处理'}, status=400)
    
    task.status = 'processing'
    task.save()
    
    service = AIRecognitionService()
    try:
        result = service.run_recognition(task)
        task.result_json = result
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.save()
        return JsonResponse({'status': 'completed', 'result': result})
    except Exception as e:
        task.status = 'failed'
        task.save()
        return JsonResponse({'status': 'failed', 'error': str(e)}, status=500)


@login_required
def recognition_config_list(request):
    configs = RecognitionConfig.objects.all()
    return render(request, 'ai_recognition/config_list.html', {'configs': configs})


@login_required
def recognition_config_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        model_path = request.POST.get('model_path')
        confidence_threshold = request.POST.get('confidence_threshold', 0.5)
        
        RecognitionConfig.objects.create(
            name=name,
            model_path=model_path,
            confidence_threshold=confidence_threshold
        )
        messages.success(request, '配置已创建')
        return redirect('ai_recognition:recognition_config_list')
    
    return render(request, 'ai_recognition/config_form.html', {'action': '创建'})


@login_required
def recognition_config_edit(request, config_id):
    config = get_object_or_404(RecognitionConfig, id=config_id)
    
    if request.method == 'POST':
        config.name = request.POST.get('name')
        config.model_path = request.POST.get('model_path')
        config.confidence_threshold = request.POST.get('confidence_threshold', 0.5)
        config.is_active = request.POST.get('is_active') == 'on'
        config.save()
        messages.success(request, '配置已更新')
        return redirect('ai_recognition:recognition_config_list')
    
    return render(request, 'ai_recognition/config_form.html', {
        'config': config,
        'action': '编辑'
    })


@login_required
def model_list(request):
    models = AIModel.objects.all().order_by('-created_at')
    return render(request, 'ai_recognition/model_list.html', {'models': models})


@login_required
def model_upload(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        model_type = request.POST.get('model_type', 'custom')
        model_file = request.FILES.get('model_file')
        model_path = request.POST.get('model_path', '')
        description = request.POST.get('description', '')
        num_classes = int(request.POST.get('num_classes', 0))
        class_names_json = request.POST.get('class_names', '[]')
        
        try:
            class_names = json.loads(class_names_json)
        except:
            class_names = []
        
        model = AIModel.objects.create(
            name=name,
            model_type=model_type,
            model_file=model_file,
            model_path=model_path,
            description=description,
            num_classes=num_classes,
            class_names=class_names,
        )
        
        messages.success(request, f'模型 {name} 上传成功')
        return redirect('ai_recognition:model_list')
    
    return render(request, 'ai_recognition/model_upload.html')


@login_required
def model_delete(request, model_id):
    model = get_object_or_404(AIModel, id=model_id)
    model.delete()
    messages.success(request, '模型已删除')
    return redirect('ai_recognition:model_list')


@login_required
def training_list(request):
    tasks = TrainingTask.objects.all().order_by('-created_at')
    paginator = Paginator(tasks, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'ai_recognition/training_list.html', {'page_obj': page_obj})


@login_required
def training_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        model_type = request.POST.get('model_type', 'yolov8n')
        dataset_path = request.POST.get('dataset_path')
        epochs = int(request.POST.get('epochs', 100))
        batch_size = int(request.POST.get('batch_size', 8))
        image_size = int(request.POST.get('image_size', 640))
        patience = int(request.POST.get('patience', 20))
        device = request.POST.get('device', '0')
        optimizer = request.POST.get('optimizer', 'AdamW')
        learning_rate = float(request.POST.get('learning_rate', 0.001))
        weight_decay = float(request.POST.get('weight_decay', 0.0005))
        momentum = float(request.POST.get('momentum', 0.937))
        
        task = TrainingTask.objects.create(
            name=name,
            model_type=model_type,
            dataset_path=dataset_path,
            epochs=epochs,
            batch_size=batch_size,
            image_size=image_size,
            patience=patience,
            device=device,
            optimizer=optimizer,
            learning_rate=learning_rate,
            weight_decay=weight_decay,
            momentum=momentum,
            created_by=request.user,
        )
        
        messages.success(request, f'训练任务 {name} 已创建')
        return redirect('ai_recognition:training_list')
    
    return render(request, 'ai_recognition/training_create.html')


@login_required
def training_detail(request, task_id):
    task = get_object_or_404(TrainingTask, id=task_id)
    return render(request, 'ai_recognition/training_detail.html', {'task': task})


@login_required
def training_start(request, task_id):
    task = get_object_or_404(TrainingTask, id=task_id)
    
    if task.status != 'pending':
        return JsonResponse({'error': '任务状态不允许启动'}, status=400)
    
    trainer = create_trainer(task)
    trainer.start_training()
    
    return JsonResponse({'status': 'started', 'message': '训练已启动'})


@login_required
def training_stop(request, task_id):
    task = get_object_or_404(TrainingTask, id=task_id)
    trainer = get_trainer(task_id)
    
    if trainer:
        trainer.stop_training()
    
    task.status = 'paused'
    task.save()
    
    return JsonResponse({'status': 'stopped', 'message': '训练已停止'})


@login_required
def training_progress(request, task_id):
    task = get_object_or_404(TrainingTask, id=task_id)
    trainer = get_trainer(task_id)
    
    if trainer:
        progress = trainer.get_progress()
    else:
        progress = {
            'status': task.status,
            'progress': task.progress,
            'current_epoch': task.current_epoch,
            'best_map': task.best_map,
        }
    
    return JsonResponse(progress)


@login_required
def training_delete(request, task_id):
    task = get_object_or_404(TrainingTask, id=task_id)
    remove_trainer(task_id)
    task.delete()
    messages.success(request, '训练任务已删除')
    return redirect('ai_recognition:training_list')


@login_required
def inference_page(request):
    models = AIModel.objects.all()
    devices = RobotDevice.objects.all()
    return render(request, 'ai_recognition/inference.html', {
        'models': models,
        'devices': devices,
    })


@login_required
def inference_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        model_id = request.POST.get('model_id')
        confidence = float(request.POST.get('confidence', 0.25))
        image_file = request.FILES['image']
        
        model = None
        if model_id:
            model = get_object_or_404(AIModel, id=model_id)
        
        from django.conf import settings
        import cv2
        import numpy as np
        
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'inference', 'source')
        result_dir = os.path.join(settings.MEDIA_ROOT, 'inference', 'result')
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(result_dir, exist_ok=True)
        
        timestamp = int(time.time() * 1000)
        ext = os.path.splitext(image_file.name)[1]
        source_filename = f'{timestamp}{ext}'
        result_filename = f'{timestamp}_result.jpg'
        source_path = os.path.join(upload_dir, source_filename)
        result_path = os.path.join(result_dir, result_filename)
        
        with open(source_path, 'wb+') as destination:
            for chunk in image_file.chunks():
                destination.write(chunk)
        
        default_model_path = os.path.join(settings.BASE_DIR, 'vision_code', 'outputs', 'agriculture_yolov8', 'weights', 'best.pt')
        inference = YOLOInference(
            model_path=model.model_path if model and model.model_path else default_model_path,
            confidence=confidence
        )
        
        result = inference.predict_image(source_path)
        
        if result.get('result_image') is not None:
            cv2.imwrite(result_path, result['result_image'])
        
        import copy
        result_for_db = copy.deepcopy(result)
        if 'result_image' in result_for_db:
            del result_for_db['result_image']
        
        record = InferenceRecord.objects.create(
            mode='image',
            model=model,
            source_file=f'inference/source/{source_filename}',
            result_file=f'inference/result/{result_filename}',
            confidence_threshold=confidence,
            total_detections=result.get('total_detections', 0),
            detection_details=result_for_db,
            processing_time=result.get('processing_time', 0),
            created_by=request.user,
        )
        
        return render(request, 'ai_recognition/inference_result.html', {
            'result': result,
            'record': record,
        })
    
    models = AIModel.objects.all()
    return render(request, 'ai_recognition/inference_image.html', {'models': models})


@login_required
def inference_video(request):
    if request.method == 'POST' and request.FILES.get('video'):
        model_id = request.POST.get('model_id')
        confidence = float(request.POST.get('confidence', 0.25))
        video_file = request.FILES['video']
        
        model = None
        if model_id:
            model = get_object_or_404(AIModel, id=model_id)
        
        from django.conf import settings
        
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'inference', 'source')
        result_dir = os.path.join(settings.MEDIA_ROOT, 'inference', 'result')
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(result_dir, exist_ok=True)
        
        timestamp = int(time.time() * 1000)
        ext = os.path.splitext(video_file.name)[1]
        source_filename = f'{timestamp}{ext}'
        result_filename = f'{timestamp}_result.mp4'
        source_path = os.path.join(upload_dir, source_filename)
        result_path = os.path.join(result_dir, result_filename)
        
        with open(source_path, 'wb+') as destination:
            for chunk in video_file.chunks():
                destination.write(chunk)
        
        default_model_path = os.path.join(settings.BASE_DIR, 'vision_code', 'outputs', 'agriculture_yolov8', 'weights', 'best.pt')
        inference = YOLOInference(
            model_path=model.model_path if model and model.model_path else default_model_path,
            confidence=confidence
        )
        
        result = inference.predict_video(source_path, result_path)
        
        record = InferenceRecord.objects.create(
            mode='video',
            model=model,
            source_file=f'inference/source/{source_filename}',
            result_file=f'inference/result/{result_filename}',
            confidence_threshold=confidence,
            total_detections=result.get('total_detections', 0),
            detection_details=result,
            processing_time=result.get('processing_time', 0),
            created_by=request.user,
        )
        
        return render(request, 'ai_recognition/inference_video_result.html', {
            'result': result,
            'record': record,
        })
    
    models = AIModel.objects.all()
    return render(request, 'ai_recognition/inference_video.html', {'models': models})


@login_required
def inference_camera(request):
    models = AIModel.objects.all()
    return render(request, 'ai_recognition/inference_camera.html', {'models': models})


@login_required
@csrf_exempt
def camera_detect(request):
    if request.method == 'POST':
        import base64
        import numpy as np
        import cv2
        
        model_id = request.POST.get('model_id')
        confidence = float(request.POST.get('confidence', 0.25))
        image_data = request.POST.get('image_data')
        
        if not image_data:
            return JsonResponse({'error': 'No image data'}, status=400)
        
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        model = None
        if model_id:
            try:
                model = AIModel.objects.get(id=model_id)
            except AIModel.DoesNotExist:
                pass
        
        default_model_path = os.path.join(settings.BASE_DIR, 'vision_code', 'outputs', 'agriculture_yolov8', 'weights', 'best.pt')
        inference = YOLOInference(
            model_path=model.model_path if model and model.model_path else default_model_path,
            confidence=confidence
        )
        
        result = inference.predict_camera_frame(frame)
        
        if result.get('annotated_frame') is not None:
            _, buffer = cv2.imencode('.jpg', result['annotated_frame'])
            annotated_base64 = base64.b64encode(buffer).decode('utf-8')
            result['annotated_base64'] = annotated_base64
            del result['annotated_frame']
        
        return JsonResponse(result)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)


@login_required
def inference_history(request):
    records = InferenceRecord.objects.all().order_by('-created_at')
    paginator = Paginator(records, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'ai_recognition/inference_history.html', {'page_obj': page_obj})