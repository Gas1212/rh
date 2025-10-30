# jobs/admin.py
from django_mongoengine import mongo_admin
from django_mongoengine.mongo_admin import DocumentAdmin
from .models import JobDocument

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