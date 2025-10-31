from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, CandidateDocument, RecruiterDocument, CompanyDocument
from datetime import datetime
from django.core.exceptions import ValidationError
import re


# ==================== REGISTER FORMS ====================
class CandidateRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(max_length=100, required=True, label="Prénom")
    last_name = forms.CharField(max_length=100, required=True, label="Nom")
    phone = forms.CharField(max_length=20, required=False, label="Téléphone")
    location = forms.CharField(max_length=255, required=False, label="Ville")

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = 'candidate'
        
        if commit:
            user.save()
            
            # ✅ Vérifier si un document existe déjà pour éviter les doublons
            candidate_doc = CandidateDocument.objects.filter(user_id=user.id).first()
            
            if not candidate_doc:
                # Créer le document seulement s'il n'existe pas
                candidate_doc = CandidateDocument(
                    user_id=user.id,
                    username=user.username,
                    email=user.email,
                    first_name=self.cleaned_data['first_name'],
                    last_name=self.cleaned_data['last_name'],
                    phone=self.cleaned_data.get('phone', ''),
                    location=self.cleaned_data.get('location', ''),
                    skills=[],
                    experience=[],
                    education=[],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                candidate_doc.save()
            
            # Associer le mongo_id
            user.mongo_id = str(candidate_doc.id)
            user.save()
        
        return user


class RecruiterRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(max_length=100, required=True, label="Prénom")
    last_name = forms.CharField(max_length=100, required=True, label="Nom")
    phone = forms.CharField(max_length=20, required=False, label="Téléphone")
    position = forms.CharField(max_length=100, required=False, label="Poste")
    company_name = forms.CharField(max_length=255, required=True, label="Nom de l'entreprise")
    company_website = forms.CharField(
        max_length=255,
        required=False,
        label="Site web",
        help_text="Exemple : example.com (sans http:// ni https://)"
    )
    company_location = forms.CharField(max_length=255, required=False, label="Localisation")

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

    def clean_company_website(self):
        website = self.cleaned_data.get('company_website', '').strip()
        if website:
            # Valide uniquement format example.com ou sub.example.com
            if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', website):
                raise ValidationError("Le format du site web est invalide. Exemple : example.com")
        return website

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = 'recruiter'
        
        if commit:
            user.save()
            
            # ✅ CRÉER OU RÉCUPÉRER L'ENTREPRISE
            company_name = self.cleaned_data['company_name']
            company = CompanyDocument.objects(name=company_name).first()
            
            if not company:
                company = CompanyDocument(
                    name=company_name,
                    website=self.cleaned_data.get('company_website', ''),
                    location=self.cleaned_data.get('company_location', ''),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                company.save()
            
            # ✅ Vérifier si un recruteur existe déjà pour éviter les doublons
            recruiter_doc = RecruiterDocument.objects.filter(user_id=user.id).first()
            
            if not recruiter_doc:
                # Créer le recruteur seulement s'il n'existe pas
                recruiter_doc = RecruiterDocument(
                    user_id=user.id,
                    username=user.username,
                    email=user.email,
                    company_id=str(company.id),  # ✅ Convertir en string
                    first_name=self.cleaned_data['first_name'],
                    last_name=self.cleaned_data['last_name'],
                    phone=self.cleaned_data.get('phone', ''),
                    position=self.cleaned_data.get('position', ''),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                recruiter_doc.save()
            
            # Associer le mongo_id
            user.mongo_id = str(recruiter_doc.id)
            user.save()
        
        return user


# ==================== PROFILE FORMS ====================
class CandidateProfileForm(forms.Form):
    """Formulaire de profil candidat (optionnel - on utilise des champs directs dans le template)"""
    first_name = forms.CharField(max_length=100, label="Prénom")
    last_name = forms.CharField(max_length=100, label="Nom")
    phone = forms.CharField(max_length=20, required=False, label="Téléphone")
    location = forms.CharField(max_length=255, required=False, label="Ville")
    experience_years = forms.IntegerField(min_value=0, label="Années d'expérience")
    desired_position = forms.CharField(max_length=255, required=False, label="Poste recherché")
    desired_salary = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label="Salaire souhaité")


class RecruiterProfileForm(forms.Form):
    """Formulaire de profil recruteur"""
    first_name = forms.CharField(max_length=100, label="Prénom")
    last_name = forms.CharField(max_length=100, label="Nom")
    phone = forms.CharField(max_length=20, required=False, label="Téléphone")
    position = forms.CharField(max_length=100, required=False, label="Poste")
    company_name = forms.CharField(max_length=255, required=False, label="Entreprise")
    company_website = forms.CharField(
        max_length=255,
        required=False,
        label="Site web",
        help_text="Exemple : example.com (sans http:// ni https://)"
    )
    company_location = forms.CharField(max_length=255, required=False, label="Localisation")

    def clean_company_website(self):
        website = self.cleaned_data.get('company_website', '').strip()
        if website:
            if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', website):
                raise ValidationError("Le format du site web est invalide. Exemple : example.com")
        return website