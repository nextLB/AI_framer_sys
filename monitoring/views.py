from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from devices.models import RobotDevice
from .models import SensorData, GPSLocation


@login_required
def monitoring_dashboard(request):
    devices = RobotDevice.objects.all()
    online_count = devices.filter(status='online').count()
    working_count = devices.filter(status='working').count()
    offline_count = devices.filter(status='offline').count()
    
    return render(request, 'monitoring/dashboard.html', {
        'devices': devices,
        'online_count': online_count,
        'working_count': working_count,
        'offline_count': offline_count,
    })


@login_required
def device_monitoring(request, device_id):
    device = get_object_or_404(RobotDevice, id=device_id)
    latest_sensor = SensorData.objects.filter(device=device).first()
    recent_locations = GPSLocation.objects.filter(device=device).order_by('-recorded_at')[:100]
    
    return render(request, 'monitoring/device_monitoring.html', {
        'device': device,
        'latest_sensor': latest_sensor,
        'recent_locations': recent_locations,
    })


@login_required
def sensor_data_api(request, device_id):
    device = get_object_or_404(RobotDevice, id=device_id)
    limit = int(request.GET.get('limit', 50))
    sensor_data = SensorData.objects.filter(device=device).order_by('-recorded_at')[:limit]
    
    data = [{
        'id': s.id,
        'temperature': s.temperature,
        'humidity': s.humidity,
        'light_intensity': s.light_intensity,
        'soil_moisture': s.soil_moisture,
        'latitude': str(s.latitude) if s.latitude else None,
        'longitude': str(s.longitude) if s.longitude else None,
        'speed': s.speed,
        'heading': s.heading,
        'recorded_at': s.recorded_at.isoformat(),
    } for s in sensor_data]
    
    return JsonResponse({'data': data})


@login_required
def gps_data_api(request, device_id):
    device = get_object_or_404(RobotDevice, id=device_id)
    locations = GPSLocation.objects.filter(device=device).order_by('-recorded_at')[:200]
    
    data = [{
        'lat': float(loc.latitude),
        'lng': float(loc.longitude),
        'altitude': loc.altitude,
        'accuracy': loc.accuracy,
        'timestamp': loc.recorded_at.isoformat(),
    } for loc in locations]
    
    return JsonResponse({'locations': data})


@login_required
def all_devices_status(request):
    devices = RobotDevice.objects.all()
    data = [{
        'id': d.id,
        'name': d.name,
        'status': d.status,
        'battery_level': d.battery_level,
        'lat': float(d.location_lat) if d.location_lat else None,
        'lng': float(d.location_lng) if d.location_lng else None,
    } for d in devices]
    
    return JsonResponse({'devices': data})