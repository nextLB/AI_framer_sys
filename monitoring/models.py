from django.db import models
from devices.models import RobotDevice


class SensorData(models.Model):
    device = models.ForeignKey(RobotDevice, on_delete=models.CASCADE, related_name='sensor_data', verbose_name='设备')
    temperature = models.FloatField(null=True, blank=True, verbose_name='温度(°C)')
    humidity = models.FloatField(null=True, blank=True, verbose_name='湿度(%)')
    light_intensity = models.FloatField(null=True, blank=True, verbose_name='光照强度(lux)')
    soil_moisture = models.FloatField(null=True, blank=True, verbose_name='土壤墒情(%)')
    latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True, verbose_name='纬度')
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True, verbose_name='经度')
    speed = models.FloatField(default=0, verbose_name='速度(m/s)')
    heading = models.FloatField(default=0, verbose_name='航向角(度)')
    recorded_at = models.DateTimeField(auto_now_add=True, verbose_name='记录时间')

    class Meta:
        verbose_name = '传感器数据'
        verbose_name_plural = '传感器数据'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['device', '-recorded_at']),
        ]

    def __str__(self):
        return f"{self.device.name} - {self.recorded_at}"


class VideoStream(models.Model):
    device = models.OneToOneField(RobotDevice, on_delete=models.CASCADE, related_name='video_stream', verbose_name='设备')
    stream_url = models.URLField(verbose_name='视频流地址')
    status = models.CharField(max_length=20, choices=[('active', '活跃'), ('inactive', '不活跃')], default='inactive', verbose_name='状态')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    last_frame_time = models.DateTimeField(null=True, blank=True, verbose_name='最后帧时间')

    class Meta:
        verbose_name = '视频流'
        verbose_name_plural = '视频流'

    def __str__(self):
        return f"{self.device.name} - {self.get_status_display()}"


class GPSLocation(models.Model):
    device = models.ForeignKey(RobotDevice, on_delete=models.CASCADE, related_name='gps_locations', verbose_name='设备')
    latitude = models.DecimalField(max_digits=10, decimal_places=6, verbose_name='纬度')
    longitude = models.DecimalField(max_digits=10, decimal_places=6, verbose_name='经度')
    altitude = models.FloatField(null=True, blank=True, verbose_name='海拔(m)')
    accuracy = models.FloatField(null=True, blank=True, verbose_name='精度(m)')
    recorded_at = models.DateTimeField(auto_now_add=True, verbose_name='记录时间')

    class Meta:
        verbose_name = 'GPS位置'
        verbose_name_plural = 'GPS位置'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['device', '-recorded_at']),
        ]

    def __str__(self):
        return f"{self.device.name} - ({self.latitude}, {self.longitude})"