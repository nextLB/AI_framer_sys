from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from devices.models import RobotDevice
from .models import RobotConnection, MessageLog


@login_required
def connection_list(request):
    connections = RobotConnection.objects.all()
    return render(request, 'communication/connection_list.html', {'connections': connections})


@login_required
def connection_detail(request, connection_id):
    connection = get_object_or_404(RobotConnection, id=connection_id)
    messages = connection.message_logs.all()[:100]
    
    return render(request, 'communication/connection_detail.html', {
        'connection': connection,
        'messages': messages,
    })


@login_required
def message_log_list(request):
    connection_id = request.GET.get('connection_id')
    
    messages = MessageLog.objects.all()
    if connection_id:
        messages = messages.filter(connection_id=connection_id)
    
    messages = messages.order_by('-timestamp')
    paginator = Paginator(messages, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    connections = RobotConnection.objects.all()
    
    return render(request, 'communication/message_log_list.html', {
        'page_obj': page_obj,
        'connections': connections,
    })


@login_required
def connection_status_api(request):
    connections = RobotConnection.objects.all()
    data = [{
        'id': c.id,
        'device_name': c.device.name,
        'ip_address': c.ip_address,
        'port': c.port,
        'is_connected': c.is_connected,
        'connected_at': c.connected_at.isoformat() if c.connected_at else None,
        'last_message_at': c.last_message_at.isoformat() if c.last_message_at else None,
        'message_count': c.message_count,
    } for c in connections]
    
    return JsonResponse({'connections': data})


@login_required
def device_communication_config(request, device_id):
    device = get_object_or_404(RobotDevice, id=device_id)
    
    connection, created = RobotConnection.objects.get_or_create(device=device)
    
    if request.method == 'POST':
        connection.ip_address = request.POST.get('ip_address')
        connection.port = request.POST.get('port', 8888)
        connection.save()
        
        return JsonResponse({'status': 'ok', 'message': '通信配置已更新'})
    
    return JsonResponse({
        'ip_address': connection.ip_address,
        'port': connection.port,
        'is_connected': connection.is_connected,
    })


def robot_receive_data(request):
    device_id = request.GET.get('device_id')
    
    if not device_id:
        return JsonResponse({'error': 'Missing device_id'}, status=400)
    
    try:
        device = RobotDevice.objects.get(device_id=device_id)
        connection = RobotConnection.objects.get(device=device)
        
        MessageLog.objects.create(
            connection=connection,
            direction='inbound',
            message_type=request.POST.get('type', 'data'),
            content=request.POST.get('content', '')
        )
        
        connection.message_count += 1
        connection.last_message_at = timezone.now()
        connection.save()
        
        return JsonResponse({'status': 'ok'})
    except RobotDevice.DoesNotExist:
        return JsonResponse({'error': 'Device not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


from django.utils import timezone