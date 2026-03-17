from django.db import models
from devices.models import RobotDevice


class RobotConnection(models.Model):
    device = models.OneToOneField(RobotDevice, on_delete=models.CASCADE, related_name='connection', verbose_name='设备')
    ip_address = models.GenericIPAddressField(verbose_name='机器人IP地址')
    port = models.IntegerField(default=8888, verbose_name='端口号')
    is_connected = models.BooleanField(default=False, verbose_name='是否连接')
    connected_at = models.DateTimeField(null=True, blank=True, verbose_name='连接时间')
    disconnected_at = models.DateTimeField(null=True, blank=True, verbose_name='断开时间')
    last_message_at = models.DateTimeField(null=True, blank=True, verbose_name='最后消息时间')
    message_count = models.IntegerField(default=0, verbose_name='消息计数')

    class Meta:
        verbose_name = '机器人连接'
        verbose_name_plural = '机器人连接'

    def __str__(self):
        return f"{self.device.name} - {self.ip_address}:{self.port}"


class MessageLog(models.Model):
    MESSAGE_DIRECTION = [
        ('inbound', '接收'),
        ('outbound', '发送'),
    ]
    connection = models.ForeignKey(RobotConnection, on_delete=models.CASCADE, related_name='message_logs', verbose_name='连接')
    direction = models.CharField(max_length=20, choices=MESSAGE_DIRECTION, verbose_name='方向')
    message_type = models.CharField(max_length=50, verbose_name='消息类型')
    content = models.TextField(verbose_name='内容')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='时间戳')

    class Meta:
        verbose_name = '消息日志'
        verbose_name_plural = '消息日志'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['connection', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.connection.device.name} - {self.get_direction_display()}"