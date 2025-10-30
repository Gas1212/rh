# jobs/admin.py
from django_mongoengine import mongo_admin
from django_mongoengine.mongo_admin import DocumentAdmin
from .models import JobDocument, ApplicationDocument

class JobAdmin(DocumentAdmin):
    list_display = (
        'title', 
        'company_name', 
        'location', 
        'contract_type', 
        'status',
        'views_count',
        'applications_count',
        'published_at'
    )
    search_fields = ('title', 'company_name', 'location', 'required_skills')
    list_filter = ('status', 'contract_type', 'work_mode', 'industry', 'location')
    ordering = ['-published_at']

# Enregistrement dans l'admin MongoDB
mongo_admin.site.register(JobDocument, JobAdmin)


class ApplicationAdmin(DocumentAdmin):
    list_display = (
        'candidate_name',
        'job_title',
        'company_name',
        'ai_match_score',
        'status',
        'applied_at'
    )
    search_fields = ('candidate_name', 'candidate_email', 'job_title', 'company_name')
    list_filter = ('status', 'ai_match_score', 'applied_at')
    ordering = ['-ai_match_score', '-applied_at']

# Enregistrement
mongo_admin.site.register(ApplicationDocument, ApplicationAdmin)