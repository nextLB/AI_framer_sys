from django.urls import path
from . import views

app_name = 'data_analysis'

urlpatterns = [
    path('', views.data_dashboard, name='data_dashboard'),
    path('sessions/', views.work_session_list, name='work_session_list'),
    path('session/<int:session_id>/', views.session_detail, name='session_detail'),
    path('reports/', views.statistical_report_list, name='statistical_report_list'),
    path('reports/generate/', views.generate_report, name='generate_report'),
    path('metrics/', views.dashboard_metrics, name='dashboard_metrics'),
    path('big-screen/', views.big_screen, name='big_screen'),
    path('export/', views.export_data, name='export_data'),
]