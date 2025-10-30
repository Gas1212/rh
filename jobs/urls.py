from django.urls import path
from . import views

urlpatterns = [
    path('', views.all_jobs, name='all_jobs'),
    path('create/', views.create_job, name='create_job'),  # ✅ NOUVEAU
    path('<str:job_id>/', views.job_detail, name='job_detail'),
    path('<str:job_id>/apply/', views.apply_to_job, name='apply_to_job'),

]