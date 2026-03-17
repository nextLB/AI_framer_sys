from django.db import models
from django.conf import settings


class RobotDevice(models.Model):
    STATUS_CHOICES = [
        ('online', '在线'),
        ('offline', '离线'),
        ('working', '工作中'),
        ('charging', '充电中'),
        ('error', '故障'),
    ]
    RUN_MODE_CHOICES = [
        ('auto', '自动模式'),
        ('manual', '手动模式'),
        ('scheduled', '定时任务模式'),
    ]
    device_id = models.CharField(max_length=100, unique=True, verbose_name='设备唯一标识')
    name = models.CharField(max_length=100, verbose_name='设备名称')
    model = models.CharField(max_length=100, blank=True, verbose_name='型号')
    manufacturer = models.CharField(max_length=100, blank=True, verbose_name='制造商')
    serial_number = models.CharField(max_length=100, blank=True, verbose_name='序列号')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline', verbose_name='状态')
    run_mode = models.CharField(max_length=20, choices=RUN_MODE_CHOICES, default='auto', verbose_name='运行模式')
    battery_level = models.IntegerField(default=0, verbose_name='电量百分比')
    location_lat = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True, verbose_name='纬度')
    location_lng = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True, verbose_name='经度')
    spray_rate = models.FloatField(default=1.0, verbose_name='喷洒速率(L/min)')
    patrol_interval = models.IntegerField(default=60, verbose_name='巡检间隔(分钟)')
    obstacle_avoidance_sensitivity = models.IntegerField(default=50, verbose_name='避障灵敏度')
    last_heartbeat = models.DateTimeField(null=True, blank=True, verbose_name='最后心跳时间')
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name='注册时间')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_devices', verbose_name='所有者')

    class Meta:
        verbose_name = '机器人设备'
        verbose_name_plural = '机器人设备'
        ordering = ['-registered_at']

    def __str__(self):
        return f"{self.name} ({self.device_id})"


class DeviceOperationLog(models.Model):
    OPERATION_TYPES = [
        ('start', '启动'),
        ('stop', '停止'),
        ('pause', '暂停'),
        ('resume', '恢复'),
        ('config', '配置修改'),
        ('control', '遥控操作'),
    ]
    device = models.ForeignKey(RobotDevice, on_delete=models.CASCADE, related_name='operation_logs', verbose_name='设备')
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='操作人')
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPES, verbose_name='操作类型')
    details = models.TextField(blank=True, verbose_name='操作详情')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='操作时间')

    class Meta:
        verbose_name = '设备操作日志'
        verbose_name_plural = '设备操作日志'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.device.name} - {self.get_operation_type_display()}"