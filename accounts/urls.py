from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # ==================== Home ====================
    path('', views.home, name='home'),

    # ==================== Auth ====================
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # ==================== Register ====================
    path('register/', views.register_choice, name='register_choice'),
    path('register/candidate/', views.register_candidate, name='register_candidate'),
    path('register/recruiter/', views.register_recruiter, name='register_recruiter'),

    # ==================== Dashboards ====================
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('dashboard/candidate/', views.candidate_dashboard, name='candidate_dashboard'),
    path('dashboard/recruiter/', views.recruiter_dashboard, name='recruiter_dashboard'),

    # ==================== Profiles ====================
    path('profile/candidate/', views.candidate_profile, name='candidate_profile'),
    path('profile/recruiter/', views.recruiter_profile, name='recruiter_profile'),
]
