from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser

# ---------- MongoEngine Admin ----------
from django_mongoengine import mongo_admin
from django_mongoengine.mongo_admin import DocumentAdmin
from .models import CandidateDocument, CompanyDocument, RecruiterDocument


# ==================== DJANGO ADMIN (PostgreSQL/SQLite) ====================

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """Administration des utilisateurs Django"""
    list_display = ['username', 'email', 'role', 'first_name', 'last_name', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('role', 'mongo_id')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('role',)
        }),
    )


# ==================== MONGODB ADMIN ====================

class CandidateAdmin(DocumentAdmin):
    """Administration des candidats MongoDB"""
    list_display = ('first_name', 'last_name', 'email', 'location', 'experience_years', 'created_at')
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('experience_years', 'location')


class CompanyAdmin(DocumentAdmin):
    """Administration des entreprises MongoDB"""
    list_display = ('name', 'industry', 'location', 'created_at')
    search_fields = ('name', 'industry')
    list_filter = ('industry', 'location')


class RecruiterAdmin(DocumentAdmin):
    """Administration des recruteurs MongoDB"""
    list_display = ('first_name', 'last_name', 'email', 'position', 'created_at')
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('position',)
    
    def company_name(self, obj):
        """Récupère le nom de l'entreprise"""
        try:
            company = CompanyDocument.objects.get(id=obj.company_id)
            return company.name
        except CompanyDocument.DoesNotExist:
            return "N/A"
    
    company_name.short_description = "Entreprise"


# ---------- Register MongoEngine Models ----------
mongo_admin.site.register(CandidateDocument, CandidateAdmin)
mongo_admin.site.register(CompanyDocument, CompanyAdmin)
mongo_admin.site.register(RecruiterDocument, RecruiterAdmin)