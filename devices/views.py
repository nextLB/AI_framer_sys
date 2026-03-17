from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import RobotDevice, DeviceOperationLog
from .forms import RobotDeviceForm


@login_required
def device_list(request):
    devices = RobotDevice.objects.all().order_by('-registered_at')
    paginator = Paginator(devices, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'devices/device_list.html', {'page_obj': page_obj})


@login_required
def device_detail(request, device_id):
    device = get_object_or_404(RobotDevice, id=device_id)
    operation_logs = device.operation_logs.all()[:20]
    return render(request, 'devices/device_detail.html', {
        'device': device,
        'operation_logs': operation_logs
    })


@login_required
def device_register(request):
    if request.method == 'POST':
        form = RobotDeviceForm(request.POST)
        if form.is_valid():
            device = form.save(commit=False)
            device.owner = request.user
            device.save()
            messages.success(request, f'设备 {device.name} 注册成功')
            return redirect('device_detail', device_id=device.id)
    else:
        form = RobotDeviceForm()
    
    return render(request, 'devices/device_form.html', {'form': form, 'action': '注册'})


@login_required
def device_edit(request, device_id):
    device = get_object_or_404(RobotDevice, id=device_id)
    
    if request.method == 'POST':
        form = RobotDeviceForm(request.POST, instance=device)
        if form.is_valid():
            form.save()
            messages.success(request, '设备信息已更新')
            return redirect('device_detail', device_id=device.id)
    else:
        form = RobotDeviceForm(instance=device)
    
    return render(request, 'devices/device_form.html', {'form': form, 'action': '编辑'})


@login_required
def device_delete(request, device_id):
    device = get_object_or_404(RobotDevice, id=device_id)
    
    if request.method == 'POST':
        device.delete()
        messages.success(request, '设备已删除')
        return redirect('device_list')
    
    return render(request, 'devices/device_confirm_delete.html', {'device': device})


@login_required
def device_config(request, device_id):
    device = get_object_or_404(RobotDevice, id=device_id)
    
    if request.method == 'POST':
        device.spray_rate = request.POST.get('spray_rate', device.spray_rate)
        device.patrol_interval = request.POST.get('patrol_interval', device.patrol_interval)
        device.obstacle_avoidance_sensitivity = request.POST.get('obstacle_avoidance_sensitivity', device.obstacle_avoidance_sensitivity)
        device.run_mode = request.POST.get('run_mode', device.run_mode)
        device.save()
        
        DeviceOperationLog.objects.create(
            device=device,
            operator=request.user,
            operation_type='config',
            details='参数配置更新'
        )
        
        messages.success(request, '设备参数已更新')
        return redirect('device_detail', device_id=device.id)
    
    return render(request, 'devices/device_config.html', {'device': device})


@login_required
def device_status_api(request, device_id):
    device = get_object_or_404(RobotDevice, id=device_id)
    data = {
        'id': device.id,
        'name': device.name,
        'status': device.status,
        'battery_level': device.battery_level,
        'run_mode': device.run_mode,
        'location_lat': str(device.location_lat) if device.location_lat else None,
        'location_lng': str(device.location_lng) if device.location_lng else None,
    }
    return JsonResponse(data)