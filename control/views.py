from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from devices.models import RobotDevice, DeviceOperationLog
from .models import ControlCommand, ManualControl


@login_required
def control_panel(request, device_id):
    device = get_object_or_404(RobotDevice, id=device_id)
    commands = ControlCommand.objects.filter(device=device).order_by('-created_at')[:20]
    
    try:
        manual_control = device.manual_control
    except ManualControl.DoesNotExist:
        manual_control = ManualControl.objects.create(device=device)
    
    return render(request, 'control/panel.html', {
        'device': device,
        'commands': commands,
        'manual_control': manual_control,
    })


@login_required
def send_command(request, device_id):
    device = get_object_or_404(RobotDevice, id=device_id)
    
    if request.method == 'POST':
        command_type = request.POST.get('command_type')
        parameters = request.POST.get('parameters', '{}')
        
        import json
        try:
            params = json.loads(parameters)
        except:
            params = {}
        
        command = ControlCommand.objects.create(
            device=device,
            command_type=command_type,
            parameters=params,
            sender=request.user,
            status='pending'
        )
        
        DeviceOperationLog.objects.create(
            device=device,
            operator=request.user,
            operation_type='control',
            details=f'发送命令: {command.get_command_type_display()}'
        )
        
        messages.success(request, f'命令已发送: {command.get_command_type_display()}')
        return redirect('control_panel', device_id=device.id)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def activate_manual_control(request, device_id):
    device = get_object_or_404(RobotDevice, id=device_id)
    
    manual_control, created = ManualControl.objects.get_or_create(device=device)
    manual_control.is_active = True
    manual_control.operator = request.user
    manual_control.active_since = timezone.now()
    manual_control.save()
    
    DeviceOperationLog.objects.create(
        device=device,
        operator=request.user,
        operation_type='control',
        details='激活手动控制'
    )
    
    messages.success(request, '手动控制已激活')
    return redirect('control_panel', device_id=device.id)


@login_required
def deactivate_manual_control(request, device_id):
    device = get_object_or_404(RobotDevice, id=device_id)
    
    try:
        manual_control = device.manual_control
        manual_control.is_active = False
        manual_control.joystick_x = 0
        manual_control.joystick_y = 0
        manual_control.spray_enabled = False
        manual_control.save()
        
        DeviceOperationLog.objects.create(
            device=device,
            operator=request.user,
            operation_type='control',
            details='停用手动控制'
        )
        
        messages.success(request, '手动控制已停用')
    except ManualControl.DoesNotExist:
        pass
    
    return redirect('control_panel', device_id=device.id)


@login_required
def joystick_control(request, device_id):
    device = get_object_or_404(RobotDevice, id=device_id)
    
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        
        try:
            manual_control = device.manual_control
            manual_control.joystick_x = data.get('x', 0)
            manual_control.joystick_y = data.get('y', 0)
            manual_control.save()
            
            if abs(data.get('x', 0)) > 0.1 or abs(data.get('y', 0)) > 0.1:
                device.status = 'working'
            else:
                device.status = 'online'
            device.save()
            
            return JsonResponse({'status': 'ok'})
        except ManualControl.DoesNotExist:
            return JsonResponse({'error': 'Manual control not active'}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def spray_control(request, device_id):
    device = get_object_or_404(RobotDevice, id=device_id)
    
    if request.method == 'POST':
        spray_enabled = request.POST.get('spray_enabled') == 'true'
        
        try:
            manual_control = device.manual_control
            manual_control.spray_enabled = spray_enabled
            manual_control.save()
            
            command_type = 'spray_start' if spray_enabled else 'spray_stop'
            ControlCommand.objects.create(
                device=device,
                command_type=command_type,
                sender=request.user,
                status='sent'
            )
            
            DeviceOperationLog.objects.create(
                device=device,
                operator=request.user,
                operation_type='control',
                details=f'{"开启" if spray_enabled else "关闭"}喷洒'
            )
            
            return JsonResponse({'status': 'ok', 'spray_enabled': spray_enabled})
        except ManualControl.DoesNotExist:
            return JsonResponse({'error': 'Manual control not active'}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def command_history(request, device_id):
    device = get_object_or_404(RobotDevice, id=device_id)
    commands = ControlCommand.objects.filter(device=device).order_by('-created_at')[:50]
    
    return render(request, 'control/command_history.html', {
        'device': device,
        'commands': commands,
    })