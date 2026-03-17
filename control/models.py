from django.db import models
from django.conf import settings
from devices.models import RobotDevice


class ControlCommand(models.Model):
    COMMAND_TYPES = [
        ('forward', '前进'),
        ('backward', '后退'),
        ('left', '左转'),
        ('right', '右转'),
        ('stop', '停止'),
        ('spray_start', '开始喷洒'),
        ('spray_stop', '停止喷洒'),
        ('speed_set', '设置速度'),
        ('mode_change', '切换模式'),
    ]
    COMMAND_STATUS = [
        ('pending', '等待中'),
        ('sent', '已发送'),
        ('executing', '执行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]
    device = models.ForeignKey(RobotDevice, on_delete=models.CASCADE, related_name='control_commands', verbose_name='设备')
    command_type = models.CharField(max_length=20, choices=COMMAND_TYPES, verbose_name='命令类型')
    parameters = models.JSONField(null=True, blank=True, verbose_name='命令参数')
    status = models.CharField(max_length=20, choices=COMMAND_STATUS, default='pending', verbose_name='状态')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='发送者')
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='发送时间')
    executed_at = models.DateTimeField(null=True, blank=True, verbose_name='执行时间')
    response = models.TextField(blank=True, verbose_name='响应信息')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '控制命令'
        verbose_name_plural = '控制命令'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.device.name} - {self.get_command_type_display()}"


class ManualControl(models.Model):
    device = models.OneToOneField(RobotDevice, on_delete=models.CASCADE, related_name='manual_control', verbose_name='设备')
    is_active = models.BooleanField(default=False, verbose_name='是否激活手动控制')
    joystick_x = models.FloatField(default=0, verbose_name='摇杆X轴')
    joystick_y = models.FloatField(default=0, verbose_name='摇杆Y轴')
    spray_enabled = models.BooleanField(default=False, verbose_name='喷洒启用')
    active_since = models.DateTimeField(null=True, blank=True, verbose_name='激活时间')
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='操作员')

    class Meta:
        verbose_name = '手动控制状态'
        verbose_name_plural = '手动控制状态'

    def __str__(self):
        return f"{self.device.name} - {'激活' if self.is_active else '未激活'}"