# ===================== admin.py =====================

# ---------- Django Admin ----------
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'is_staff', 'created_at']
    list_filter = ['role', 'is_staff', 'is_active']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations supplémentaires', {'fields': ('role',)}),
    )


# ---------- MongoEngine Admin ----------
from django_mongoengine import mongo_admin
from django_mongoengine.mongo_admin import DocumentAdmin
from .models import CandidateDocument, CompanyDocument, RecruiterDocument

# ----- Candidate -----
class CandidateAdmin(DocumentAdmin):
    list_display = ('first_name', 'last_name', 'email', 'location', 'experience_years', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'skills')
    list_filter = ('experience_years', 'location')

# ----- Company -----
class CompanyAdmin(DocumentAdmin):
    list_display = ('name', 'industry', 'location', 'created_at')
    search_fields = ('name', 'industry')
    list_filter = ('industry', 'location')

# ----- Recruiter -----
class RecruiterAdmin(DocumentAdmin):
    list_display = ('first_name', 'last_name', 'company_name', 'position', 'created_at')
    search_fields = ('first_name', 'last_name', 'company_name', 'email')
    list_filter = ('company_name', 'can_post_jobs')

# ---------- Register MongoEngine Models ----------
mongo_admin.site.register(CandidateDocument, CandidateAdmin)
mongo_admin.site.register(CompanyDocument, CompanyAdmin)
mongo_admin.site.register(RecruiterDocument, RecruiterAdmin)
