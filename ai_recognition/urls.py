from django.urls import path
from . import views

app_name = 'ai_recognition'

urlpatterns = [
    path('', views.recognition_dashboard, name='recognition_dashboard'),
    path('start/<int:device_id>/', views.start_recognition, name='start_recognition'),
    path('task/<int:task_id>/', views.recognition_task_detail, name='recognition_task_detail'),
    path('task/<int:task_id>/run/', views.run_recognition_api, name='run_recognition_api'),
    path('history/', views.recognition_history, name='recognition_history'),
    path('config/', views.recognition_config_list, name='recognition_config_list'),
    path('config/create/', views.recognition_config_create, name='recognition_config_create'),
    path('config/<int:config_id>/edit/', views.recognition_config_edit, name='recognition_config_edit'),
    
    path('models/', views.model_list, name='model_list'),
    path('models/upload/', views.model_upload, name='model_upload'),
    path('models/<int:model_id>/delete/', views.model_delete, name='model_delete'),
    
    path('training/', views.training_list, name='training_list'),
    path('training/create/', views.training_create, name='training_create'),
    path('training/<int:task_id>/', views.training_detail, name='training_detail'),
    path('training/<int:task_id>/start/', views.training_start, name='training_start'),
    path('training/<int:task_id>/stop/', views.training_stop, name='training_stop'),
    path('training/<int:task_id>/progress/', views.training_progress, name='training_progress'),
    path('training/<int:task_id>/delete/', views.training_delete, name='training_delete'),
    
    path('inference/', views.inference_page, name='inference_page'),
    path('inference/image/', views.inference_image, name='inference_image'),
    path('inference/video/', views.inference_video, name='inference_video'),
    path('inference/camera/', views.inference_camera, name='inference_camera'),
    path('inference/camera/detect/', views.camera_detect, name='camera_detect'),
    path('inference/history/', views.inference_history, name='inference_history'),
]