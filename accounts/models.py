from django.contrib.auth.models import AbstractUser
from django.db import models
from mongoengine import (
    Document,
    StringField,
    EmailField,
    IntField,
    ListField,
    DictField,
    DateTimeField,
    FloatField,
    ReferenceField,
    PULL
)
from datetime import datetime


# ==================== MODÈLE DJANGO (PostgreSQL) ====================
class CustomUser(AbstractUser):
    """Utilisateur personnalisé stocké dans PostgreSQL"""
    ROLE_CHOICES = [
        ('candidate', 'Candidat'),
        ('recruiter', 'Recruteur'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='candidate')
    mongo_id = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# ==================== MODÈLES MONGODB ====================

class CompanyDocument(Document):
    """Entreprise dans MongoDB"""
    name = StringField(required=True, max_length=200)
    industry = StringField(max_length=100)
    size = StringField(max_length=50)
    website = StringField(max_length=200)
    description = StringField()
    location = StringField(max_length=100)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    meta = {
        'collection': 'companies',
        'strict': False,
        'indexes': [
            {'fields': ['name'], 'name': 'company_name_idx'}
        ]
    }
    
    def __str__(self):
        return self.name


class RecruiterDocument(Document):
    """Recruteur dans MongoDB"""
    user_id = IntField(required=True, unique=True)
    username = StringField(required=True, unique=True)
    first_name = StringField(max_length=100)
    last_name = StringField(max_length=100)
    email = EmailField(required=True, unique=True)
    phone = StringField(max_length=20)
    position = StringField(max_length=100)
    company_id = StringField(required=True)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    meta = {
        'collection': 'recruiters',
        'strict': False,
        'indexes': [
            {'fields': ['email'], 'unique': True, 'name': 'recruiter_email_idx'},
            {'fields': ['user_id'], 'unique': True, 'name': 'recruiter_user_idx'},
            {'fields': ['username'], 'unique': True, 'name': 'recruiter_username_idx'},
            {'fields': ['company_id'], 'name': 'recruiter_company_idx'}
        ]
    }
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class CandidateDocument(Document):
    """Candidat dans MongoDB"""
    # Relation avec Django User
    user_id = IntField(required=True, unique=True)
    username = StringField(required=True, unique=True)
    
    # Informations personnelles
    first_name = StringField(max_length=100)
    last_name = StringField(max_length=100)
    email = EmailField(required=True, unique=True)
    phone = StringField(max_length=20)
    location = StringField(max_length=100)
    
    # Expérience
    experience_years = IntField(default=0)
    
    # Compétences (liste de strings)
    skills = ListField(StringField(), default=list)
    
    # Expérience professionnelle (liste de dictionnaires)
    experience = ListField(DictField(), default=list)
    
    # Formation (liste de dictionnaires)
    education = ListField(DictField(), default=list)
    
    # Objectifs professionnels
    desired_position = StringField(max_length=200)
    desired_salary = IntField(default=0)
    
    # URL du CV (optionnel)
    cv_url = StringField(max_length=500)
    
    # Embedding IA pour matching avancé
    profile_embedding = ListField(FloatField(), default=list)
    
    # Métadonnées
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    meta = {
        'collection': 'candidates',
        'strict': False,
        'indexes': [
            {'fields': ['email'], 'unique': True, 'name': 'candidate_email_idx'},
            {'fields': ['user_id'], 'unique': True, 'name': 'candidate_user_idx'},
            {'fields': ['username'], 'unique': True, 'name': 'candidate_username_idx'},
            {'fields': ['skills'], 'name': 'candidate_skills_idx'},
            {'fields': ['location'], 'name': 'candidate_location_idx'}
        ]
    }
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"