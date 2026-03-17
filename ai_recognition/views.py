from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from devices.models import RobotDevice
from .models import RecognitionTask, RecognitionConfig
from .services import AIRecognitionService


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
        return redirect('recognition_config_list')
    
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
        return redirect('recognition_config_list')
    
    return render(request, 'ai_recognition/config_form.html', {
        'config': config,
        'action': '编辑'
    })