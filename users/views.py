from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.http import JsonResponse
from .models import LoginLog
from .forms import UserRegistrationForm, UserProfileForm


def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            LoginLog.objects.create(
                user=user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                status='success'
            )
            user.last_login_ip = get_client_ip(request)
            user.save()
            return redirect('dashboard')
        else:
            messages.error(request, '用户名或密码错误')
            LoginLog.objects.create(
                username=username,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                status='failed'
            )
    
    return render(request, 'users/login.html')


def user_logout(request):
    logout(request)
    return redirect('login')


def user_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '注册成功！')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '个人信息已更新')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    login_logs = LoginLog.objects.filter(user=request.user)[:10]
    return render(request, 'users/profile.html', {
        'form': form,
        'login_logs': login_logs
    })


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '密码已更新，请重新登录')
            logout(request)
            return redirect('login')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'users/change_password.html', {'form': form})


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def dashboard(request):
    from devices.models import RobotDevice
    from data_analysis.models import WorkSession
    from ai_recognition.models import RecognitionTask
    
    devices = RobotDevice.objects.all()
    total_devices = devices.count()
    online_devices = devices.filter(status__in=['online', 'working']).count()
    working_devices = devices.filter(status='working').count()
    
    recent_sessions = WorkSession.objects.filter(status='completed').order_by('-end_time')[:5]
    recent_tasks = RecognitionTask.objects.order_by('-created_at')[:5]
    
    return render(request, 'dashboard.html', {
        'total_devices': total_devices,
        'online_devices': online_devices,
        'working_devices': working_devices,
        'devices': devices,
        'recent_sessions': recent_sessions,
        'recent_tasks': recent_tasks,
    })