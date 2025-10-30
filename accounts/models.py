from django.contrib.auth.models import AbstractUser
from django.db import models
from mongoengine import Document, fields, connect

# ==================== DJANGO MODELS (SQLite) ====================
# Ces models restent en SQLite pour l'authentification Django

class User(AbstractUser):
    """Utilisateur Django (SQLite) - Authentification"""
    
    ROLE_CHOICES = [
        ('candidate', 'Candidat'),
        ('recruiter', 'Recruteur'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    mongo_id = models.CharField(max_length=100, blank=True)  # Référence au doc MongoDB
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"


# ==================== MONGODB DOCUMENTS (MongoEngine) ====================
# Ces documents sont stockés dans MongoDB Atlas

class CompanyDocument(Document):
    """Entreprise (MongoDB)"""
    
    name = fields.StringField(required=True, max_length=255)
    logo_url = fields.URLField()
    description = fields.StringField()
    industry = fields.StringField(max_length=100)
    website = website = fields.StringField()
    location = fields.StringField(max_length=255)
    created_at = fields.DateTimeField()
    
    meta = {
        'collection': 'companies',
        'db_alias': 'default'  # Utilise la nouvelle base RH_Platform
    }
    
    def __str__(self):
        return self.name


class CandidateDocument(Document):
    """Candidat (MongoDB)"""
    
    user_id = fields.IntField(required=True)  # ID du User Django
    username = fields.StringField(required=True, max_length=150)
    email = fields.EmailField(required=True)
    
    # Informations personnelles
    first_name = fields.StringField(max_length=100)
    last_name = fields.StringField(max_length=100)
    phone = fields.StringField(max_length=20)
    location = fields.StringField(max_length=255)
    photo_url = fields.URLField()
    
    # CV
    cv_url = fields.URLField()
    cv_text = fields.StringField()  # Texte extrait par IA
    
    # Données IA
    skills = fields.ListField(fields.StringField())
    experience_years = fields.IntField(default=0)
    desired_position = fields.StringField(max_length=255)
    desired_salary = fields.DecimalField(precision=2)
    
    # Embeddings IA (pour matching)
    profile_embedding = fields.ListField(fields.FloatField())
    
    created_at = fields.DateTimeField()
    updated_at = fields.DateTimeField()
    
    meta = {
        'collection': 'candidates',
        'db_alias': 'default',
        'indexes': [
            'user_id',
            'email',
            'skills'
        ]
    }
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class RecruiterDocument(Document):
    """Recruteur (MongoDB)"""
    
    user_id = fields.IntField(required=True)
    username = fields.StringField(required=True, max_length=150)
    email = fields.EmailField(required=True)
    
    company_id = fields.ObjectIdField(required=True)  # Référence CompanyDocument
    company_name = fields.StringField(max_length=255)  # Dénormalisé pour perf
    
    # Informations personnelles
    first_name = fields.StringField(max_length=100)
    last_name = fields.StringField(max_length=100)
    position = fields.StringField(max_length=100)
    phone = fields.StringField(max_length=20)
    
    # Permissions
    can_post_jobs = fields.BooleanField(default=True)
    can_view_candidates = fields.BooleanField(default=True)
    
    created_at = fields.DateTimeField()
    
    meta = {
        'collection': 'recruiters',
        'db_alias': 'default',
        'indexes': [
            'user_id',
            'company_id',
            'email'
        ]
    }
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.company_name})"