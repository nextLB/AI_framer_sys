from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', '管理员'),
        ('operator', '操作员'),
        ('viewer', '查看者'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer', verbose_name='角色')
    phone = models.CharField(max_length=20, blank=True, verbose_name='手机号')
    avatar = models.ImageField(upload_to='avatars/', blank=True, verbose_name='头像')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    last_login_ip = models.GenericIPAddressField(blank=True, null=True, verbose_name='最后登录IP')

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __str__(self):
        return self.username


class LoginLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_logs', verbose_name='用户')
    login_time = models.DateTimeField(auto_now_add=True, verbose_name='登录时间')
    ip_address = models.GenericIPAddressField(verbose_name='IP地址')
    user_agent = models.CharField(max_length=255, blank=True, verbose_name='用户代理')
    status = models.CharField(max_length=20, choices=[('success', '成功'), ('failed', '失败')], verbose_name='状态')

    class Meta:
        verbose_name = '登录日志'
        verbose_name_plural = '登录日志'
        ordering = ['-login_time']

    def __str__(self):
        return f"{self.user.username} - {self.login_time}"