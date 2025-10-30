from django.urls import path
from . import views

urlpatterns = [
    path('', views.all_jobs, name='all_jobs'),
    path('create/', views.create_job, name='create_job'),  # ✅ NOUVEAU

]