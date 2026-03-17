from django.urls import path
from . import views

urlpatterns = [
    path('<int:device_id>/', views.control_panel, name='control_panel'),
    path('<int:device_id>/command/', views.send_command, name='send_command'),
    path('<int:device_id>/manual/activate/', views.activate_manual_control, name='activate_manual_control'),
    path('<int:device_id>/manual/deactivate/', views.deactivate_manual_control, name='deactivate_manual_control'),
    path('<int:device_id>/joystick/', views.joystick_control, name='joystick_control'),
    path('<int:device_id>/spray/', views.spray_control, name='spray_control'),
    path('<int:device_id>/history/', views.command_history, name='command_history'),
]