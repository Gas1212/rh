from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, CandidateDocument, RecruiterDocument, CompanyDocument
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
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = 'candidate'
        if commit:
            user.save()
            candidate_doc = CandidateDocument(
                user_id=user.id,
                username=user.username,
                email=user.email,
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                phone=self.cleaned_data.get('phone', ''),
                location=self.cleaned_data.get('location', ''),
                skills=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            candidate_doc.save()
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
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_company_website(self):
        website = self.cleaned_data.get('company_website', '').strip()
        if website:
            # Valide uniquement format example.com ou sub.example.com
            if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', website):
                raise ValidationError("Le format du site web est invalide. Exemple : example.com")
        return website

    # Dans accounts/forms.py, méthode save()
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
                                    created_at=datetime.now()
                                    )
          company.save()
          
          # ✅ CRÉER LE RECRUTEUR AVEC company_id
          recruiter_doc = RecruiterDocument(
                                            user_id=user.id,
                                            username=user.username,
                                            email=user.email,
                                            company_id=company.id,  # ✅ CORRECT
                                            company_name=company.name,
                                            first_name=self.cleaned_data['first_name'],
                                            last_name=self.cleaned_data['last_name'],
                                            phone=self.cleaned_data.get('phone', ''),
                                            position=self.cleaned_data.get('position', ''),
                                            created_at=datetime.now()
                                            )
          recruiter_doc.save()
          
          user.mongo_id = str(recruiter_doc.id)
          user.save()
        return user


# ==================== PROFILE FORMS ====================
class CandidateProfileForm(forms.Form):
    first_name = forms.CharField(max_length=100, label="Prénom")
    last_name = forms.CharField(max_length=100, label="Nom")
    phone = forms.CharField(max_length=20, required=False, label="Téléphone")
    location = forms.CharField(max_length=255, required=False, label="Ville")
    experience_years = forms.IntegerField(min_value=0, label="Années d'expérience")
    desired_position = forms.CharField(max_length=255, required=False, label="Poste recherché")
    desired_salary = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label="Salaire souhaité")
    cv_file = forms.FileField(required=False, label="CV (PDF)")
    photo = forms.ImageField(required=False, label="Photo")


class RecruiterProfileForm(forms.Form):
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
