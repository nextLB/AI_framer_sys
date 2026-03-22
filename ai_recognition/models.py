import os
from django.db import models
from django.conf import settings
from devices.models import RobotDevice


class AIModel(models.Model):
    MODEL_TYPES = [
        ('yolov8n', 'YOLOv8 Nano'),
        ('yolov8s', 'YOLOv8 Small'),
        ('yolov8m', 'YOLOv8 Medium'),
        ('yolov8l', 'YOLOv8 Large'),
        ('yolov8x', 'YOLOv8 XLarge'),
        ('yolo11n', 'YOLO11 Nano'),
        ('yolo11s', 'YOLO11 Small'),
        ('yolo11m', 'YOLO11 Medium'),
        ('yolo11l', 'YOLO11 Large'),
        ('yolo11x', 'YOLO11 XLarge'),
        ('custom', '自定义模型'),
    ]
    name = models.CharField(max_length=100, verbose_name='模型名称')
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES, default='yolov8n', verbose_name='模型架构')
    model_file = models.FileField(upload_to='ai_models/', null=True, blank=True, verbose_name='模型文件')
    model_path = models.CharField(max_length=500, blank=True, verbose_name='模型路径')
    description = models.TextField(blank=True, verbose_name='模型描述')
    num_classes = models.IntegerField(default=0, verbose_name='类别数')
    class_names = models.JSONField(null=True, blank=True, verbose_name='类别名称列表')
    is_active = models.BooleanField(default=False, verbose_name='是否默认')
    accuracy = models.FloatField(null=True, blank=True, verbose_name='准确率')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = 'AI模型'
        verbose_name_plural = 'AI模型'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_model_type_display()})"
    
    @property
    def model_source(self):
        if self.model_file:
            return self.model_file.path
        elif self.model_path:
            return self.model_path
        return None


class TrainingTask(models.Model):
    STATUS_CHOICES = [
        ('pending', '等待中'),
        ('running', '训练中'),
        ('paused', '已暂停'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]
    name = models.CharField(max_length=100, verbose_name='训练任务名称')
    model_type = models.CharField(max_length=20, choices=AIModel.MODEL_TYPES, default='yolov8n', verbose_name='基础模型')
    dataset_path = models.CharField(max_length=500, verbose_name='数据集路径')
    epochs = models.IntegerField(default=100, verbose_name='训练轮数')
    batch_size = models.IntegerField(default=8, verbose_name='批次大小')
    image_size = models.IntegerField(default=640, verbose_name='图像尺寸')
    patience = models.IntegerField(default=20, verbose_name='早停耐心值')
    device = models.CharField(max_length=50, default='0', verbose_name='训练设备')
    optimizer = models.CharField(max_length=50, default='AdamW', verbose_name='优化器')
    learning_rate = models.FloatField(default=0.001, verbose_name='学习率')
    weight_decay = models.FloatField(default=0.0005, verbose_name='权重衰减')
    momentum = models.FloatField(default=0.937, verbose_name='动量')
    augment = models.BooleanField(default=True, verbose_name='数据增强')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    progress = models.IntegerField(default=0, verbose_name='训练进度(%)')
    current_epoch = models.IntegerField(default=0, verbose_name='当前轮数')
    best_map = models.FloatField(null=True, blank=True, verbose_name='最佳mAP')
    output_dir = models.CharField(max_length=500, blank=True, verbose_name='输出目录')
    trained_model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='training_tasks', verbose_name='训练好的模型')
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')

    class Meta:
        verbose_name = '训练任务'
        verbose_name_plural = '训练任务'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class InferenceRecord(models.Model):
    MODE_CHOICES = [
        ('image', '单张图片'),
        ('video', '视频文件'),
        ('camera', '实时摄像头'),
    ]
    device = models.ForeignKey(RobotDevice, on_delete=models.CASCADE, null=True, blank=True, related_name='inference_records', verbose_name='关联设备')
    model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, related_name='inference_records', verbose_name='使用的模型')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='image', verbose_name='推理模式')
    source_file = models.FileField(upload_to='inference/source/', null=True, blank=True, verbose_name='源文件')
    result_file = models.FileField(upload_to='inference/result/', null=True, blank=True, verbose_name='结果文件')
    confidence_threshold = models.FloatField(default=0.25, verbose_name='置信度阈值')
    total_detections = models.IntegerField(default=0, verbose_name='总检测数')
    detection_details = models.JSONField(null=True, blank=True, verbose_name='检测详情')
    processing_time = models.FloatField(null=True, blank=True, verbose_name='处理时间(秒)')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='操作者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='推理时间')

    class Meta:
        verbose_name = '推理记录'
        verbose_name_plural = '推理记录'
        ordering = ['-created_at']

    def __str__(self):
        return f"推理-{self.id} ({self.get_mode_display()})"


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