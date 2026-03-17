from django.db import models
from devices.models import RobotDevice


class RecognitionTask(models.Model):
    TASK_TYPES = [
        ('crop_weed', '作物与杂草识别'),
        ('pest_disease', '病虫害检测'),
        ('maturity', '成熟度判断'),
    ]
    TASK_STATUS = [
        ('pending', '等待中'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]
    device = models.ForeignKey(RobotDevice, on_delete=models.CASCADE, related_name='recognition_tasks', verbose_name='设备')
    task_type = models.CharField(max_length=20, choices=TASK_TYPES, verbose_name='任务类型')
    status = models.CharField(max_length=20, choices=TASK_STATUS, default='pending', verbose_name='状态')
    image = models.ImageField(upload_to='recognition/images/', null=True, blank=True, verbose_name='分析图像')
    result_json = models.JSONField(null=True, blank=True, verbose_name='识别结果JSON')
    confidence = models.FloatField(null=True, blank=True, verbose_name='置信度')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')

    class Meta:
        verbose_name = '识别任务'
        verbose_name_plural = '识别任务'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.device.name} - {self.get_task_type_display()}"


class CropWeedDetection(models.Model):
    task = models.ForeignKey(RecognitionTask, on_delete=models.CASCADE, related_name='crop_weed_results', verbose_name='任务')
    crop_count = models.IntegerField(default=0, verbose_name='作物数量')
    weed_count = models.IntegerField(default=0, verbose_name='杂草数量')
    density_map = models.JSONField(null=True, blank=True, verbose_name='密度分布图')
    detection_boxes = models.JSONField(null=True, blank=True, verbose_name='检测框数据')

    class Meta:
        verbose_name = '作物杂草检测结果'
        verbose_name_plural = '作物杂草检测结果'


class PestDiseaseDetection(models.Model):
    DISEASE_TYPES = [
        ('healthy', '健康'),
        ('powdery_mildew', '白粉病'),
        ('rust', '锈病'),
        ('blight', '枯萎病'),
        ('leaf_spot', '叶斑病'),
        ('other', '其他'),
    ]
    PEST_TYPES = [
        ('no_pest', '无虫害'),
        ('aphid', '蚜虫'),
        ('beetle', '甲虫'),
        ('caterpillar', '毛虫'),
        ('mite', '螨虫'),
        ('other', '其他'),
    ]
    task = models.ForeignKey(RecognitionTask, on_delete=models.CASCADE, related_name='pest_disease_results', verbose_name='任务')
    disease_type = models.CharField(max_length=20, choices=DISEASE_TYPES, default='healthy', verbose_name='病害类型')
    disease_confidence = models.FloatField(null=True, blank=True, verbose_name='病害置信度')
    pest_type = models.CharField(max_length=20, choices=PEST_TYPES, default='no_pest', verbose_name='虫害类型')
    pest_confidence = models.FloatField(null=True, blank=True, verbose_name='虫害置信度')
    detection_boxes = models.JSONField(null=True, blank=True, verbose_name='检测框数据')

    class Meta:
        verbose_name = '病虫害检测结果'
        verbose_name_plural = '病虫害检测结果'


class MaturityDetection(models.Model):
    MATURITY_LEVELS = [
        ('immature', '未成熟'),
        ('semi_mature', '半成熟'),
        ('mature', '成熟'),
        ('over_mature', '过熟'),
    ]
    task = models.ForeignKey(RecognitionTask, on_delete=models.CASCADE, related_name='maturity_results', verbose_name='任务')
    maturity_level = models.CharField(max_length=20, choices=MATURITY_LEVELS, verbose_name='成熟度等级')
    maturity_percentage = models.FloatField(null=True, blank=True, verbose_name='成熟度百分比')
    fruit_count = models.IntegerField(default=0, verbose_name='果实数量')
    detection_boxes = models.JSONField(null=True, blank=True, verbose_name='检测框数据')

    class Meta:
        verbose_name = '成熟度检测结果'
        verbose_name_plural = '成熟度检测结果'


class RecognitionConfig(models.Model):
    name = models.CharField(max_length=100, verbose_name='配置名称')
    model_path = models.CharField(max_length=255, blank=True, verbose_name='模型路径')
    confidence_threshold = models.FloatField(default=0.5, verbose_name='置信度阈值')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '识别配置'
        verbose_name_plural = '识别配置'

    def __str__(self):
        return self.name