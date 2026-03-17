from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Sum, Avg, Count
from django.utils import timezone
from datetime import timedelta
from devices.models import RobotDevice
from .models import WorkSession, StatisticalReport, DashboardMetrics
import json


@login_required
def data_dashboard(request):
    devices = RobotDevice.objects.all()
    total_devices = devices.count()
    online_devices = devices.filter(status__in=['online', 'working']).count()
    
    recent_sessions = WorkSession.objects.filter(status='completed').order_by('-end_time')[:10]
    total_work_hours = WorkSession.objects.filter(status='completed').aggregate(Sum('duration'))['duration__sum'] or 0
    total_area = WorkSession.objects.filter(status='completed').aggregate(Sum('area_covered'))['area_covered__sum'] or 0
    
    return render(request, 'data_analysis/dashboard.html', {
        'total_devices': total_devices,
        'online_devices': online_devices,
        'recent_sessions': recent_sessions,
        'total_work_hours': round(total_work_hours / 3600, 2),
        'total_area': round(total_area, 2),
    })


@login_required
def work_session_list(request):
    device_id = request.GET.get('device_id')
    sessions = WorkSession.objects.all()
    
    if device_id:
        sessions = sessions.filter(device_id=device_id)
    
    sessions = sessions.order_by('-start_time')
    paginator = Paginator(sessions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    devices = RobotDevice.objects.all()
    
    return render(request, 'data_analysis/session_list.html', {
        'page_obj': page_obj,
        'devices': devices,
    })


@login_required
def session_detail(request, session_id):
    session = get_object_or_404(WorkSession, id=session_id)
    return render(request, 'data_analysis/session_detail.html', {'session': session})


@login_required
def statistical_report_list(request):
    reports = StatisticalReport.objects.all().order_by('-generated_at')
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'data_analysis/report_list.html', {'page_obj': page_obj})


@login_required
def generate_report(request):
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        device_id = request.POST.get('device_id')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        from datetime import datetime
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        sessions = WorkSession.objects.filter(
            start_time__date__gte=start,
            start_time__date__lte=end,
            status='completed'
        )
        
        if device_id:
            sessions = sessions.filter(device_id=device_id)
        
        total_hours = sum(s.duration for s in sessions) / 3600
        total_area = sum(s.area_covered for s in sessions)
        total_pesticide = sum(s.pesticide_used for s in sessions)
        
        StatisticalReport.objects.create(
            device_id=device_id if device_id else None,
            report_type=report_type,
            start_date=start,
            end_date=end,
            total_work_hours=total_hours,
            total_area=total_area,
            total_pesticide=total_pesticide,
            pest_alert_count=0,
        )
        
        messages.success(request, '报告生成成功')
        return redirect('statistical_report_list')
    
    devices = RobotDevice.objects.all()
    return render(request, 'data_analysis/generate_report.html', {'devices': devices})


@login_required
def dashboard_metrics(request):
    days = int(request.GET.get('days', 7))
    start_date = timezone.now().date() - timedelta(days=days)
    
    metrics = DashboardMetrics.objects.filter(date__gte=start_date).order_by('date')
    
    data = [{
        'date': str(m.date),
        'total_devices': m.total_devices,
        'online_devices': m.online_devices,
        'total_work_area': m.total_work_area,
        'total_work_hours': m.total_work_hours,
        'pest_alerts': m.pest_alerts,
        'robot_utilization': m.robot_utilization,
    } for m in metrics]
    
    return JsonResponse({'metrics': data})


@login_required
def big_screen(request):
    latest_metrics = DashboardMetrics.objects.order_by('-date').first()
    devices = RobotDevice.objects.all()
    online_count = devices.filter(status__in=['online', 'working']).count()
    working_count = devices.filter(status='working').count()
    
    return render(request, 'data_analysis/big_screen.html', {
        'metrics': latest_metrics,
        'devices': devices,
        'online_count': online_count,
        'working_count': working_count,
    })


@login_required
def export_data(request):
    export_type = request.GET.get('type', 'sessions')
    format_type = request.GET.get('format', 'csv')
    
    if export_type == 'sessions':
        sessions = WorkSession.objects.all()
        data = [[
            s.id, s.device.name, s.start_time, s.end_time,
            s.duration, s.total_distance, s.area_covered, s.pesticide_used, s.status
        ] for s in sessions]
        headers = ['ID', '设备', '开始时间', '结束时间', '时长(秒)', '距离(m)', '面积(亩)', '农药(L)', '状态']
    
    return JsonResponse({'data': data, 'headers': headers})