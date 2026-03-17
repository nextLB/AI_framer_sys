from django.db import models
from django.conf import settings
from devices.models import RobotDevice


class WorkSession(models.Model):
    device = models.ForeignKey(RobotDevice, on_delete=models.CASCADE, related_name='work_sessions', verbose_name='设备')
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='操作员')
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    duration = models.IntegerField(default=0, verbose_name='持续时长(秒)')
    total_distance = models.FloatField(default=0, verbose_name='总行驶距离(m)')
    area_covered = models.FloatField(default=0, verbose_name='作业面积(亩)')
    pesticide_used = models.FloatField(default=0, verbose_name='农药使用量(L)')
    status = models.CharField(max_length=20, choices=[('in_progress', '进行中'), ('completed', '已完成'), ('cancelled', '已取消')], default='in_progress', verbose_name='状态')
    notes = models.TextField(blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '作业会话'
        verbose_name_plural = '作业会话'
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.device.name} - {self.start_time}"


class StatisticalReport(models.Model):
    REPORT_TYPES = [
        ('daily', '日报'),
        ('weekly', '周报'),
        ('monthly', '月报'),
        ('yearly', '年报'),
    ]
    device = models.ForeignKey(RobotDevice, on_delete=models.CASCADE, related_name='reports', verbose_name='设备', null=True, blank=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, verbose_name='报告类型')
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(verbose_name='结束日期')
    total_work_hours = models.FloatField(default=0, verbose_name='总工作时间(小时)')
    total_area = models.FloatField(default=0, verbose_name='总作业面积(亩)')
    total_pesticide = models.FloatField(default=0, verbose_name='总农药用量(L)')
    pest_alert_count = models.IntegerField(default=0, verbose_name='病虫害预警数')
    crop_health_score = models.FloatField(null=True, blank=True, verbose_name='作物健康评分')
    data_json = models.JSONField(null=True, blank=True, verbose_name='详细数据JSON')
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name='生成时间')

    class Meta:
        verbose_name = '统计报告'
        verbose_name_plural = '统计报告'
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.get_report_type_display()} - {self.start_date} ~ {self.end_date}"


class DashboardMetrics(models.Model):
    date = models.DateField(unique=True, verbose_name='日期')
    total_devices = models.IntegerField(default=0, verbose_name='设备总数')
    online_devices = models.IntegerField(default=0, verbose_name='在线设备数')
    total_work_area = models.FloatField(default=0, verbose_name='总作业面积(亩)')
    total_work_hours = models.FloatField(default=0, verbose_name='总工作时间(小时)')
    pest_alerts = models.IntegerField(default=0, verbose_name='病虫害预警')
    robot_utilization = models.FloatField(default=0, verbose_name='机器人利用率(%)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '大屏指标'
        verbose_name_plural = '大屏指标'
        ordering = ['-date']

    def __str__(self):
        return str(self.date)