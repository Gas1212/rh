# jobs/forms.py
from django import forms
from .models import JobDocument
from datetime import datetime, timedelta

class JobCreationForm(forms.Form):
    """Formulaire de création d'offre d'emploi"""
    
    # Informations de base
    title = forms.CharField(
        max_length=255,
        label="Titre du poste",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': 'Ex: Développeur Full Stack Senior'
        })
    )
    
    description = forms.CharField(
        label="Description du poste",
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'rows': 8,
            'placeholder': 'Décrivez le poste, les missions, le profil recherché...'
        })
    )
    
    # Localisation
    location = forms.CharField(
        max_length=255,
        label="Localisation",
        initial="Tunisie",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
            'placeholder': 'Ex: Tunis, Tunisie'
        })
    )
    
    # Type de contrat
    contract_type = forms.ChoiceField(
        label="Type de contrat",
        choices=JobDocument._fields['contract_type'].choices,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500'
        })
    )
    
    # Mode de travail
    work_mode = forms.ChoiceField(
        label="Mode de travail",
        choices=JobDocument._fields['work_mode'].choices,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500'
        })
    )
    
    # Salaire
    salary_min = forms.DecimalField(
        required=False,
        label="Salaire minimum (TND)",
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
            'placeholder': '2500'
        })
    )
    
    salary_max = forms.DecimalField(
        required=False,
        label="Salaire maximum (TND)",
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
            'placeholder': '4000'
        })
    )
    
    salary_period = forms.ChoiceField(
        label="Période",
        choices=JobDocument._fields['salary_period'].choices,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500'
        })
    )
    
    # Compétences
    required_skills = forms.CharField(
        required=False,
        label="Compétences requises",
        help_text="Séparez les compétences par des virgules",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
            'placeholder': 'Python, Django, MongoDB, React'
        })
    )
    
    # Expérience
    experience_min = forms.IntegerField(
        label="Années d'expérience minimum",
        initial=0,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500'
        })
    )
    
    experience_max = forms.IntegerField(
        required=False,
        label="Années d'expérience maximum",
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500'
        })
    )
    
    # Niveau d'études
    education_level = forms.ChoiceField(
        required=False,
        label="Niveau d'études requis",
        choices=[('', '--- Non spécifié ---')] + list(JobDocument._fields['education_level'].choices),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500'
        })
    )
    
    # Secteur
    industry = forms.CharField(
        required=False,
        max_length=100,
        label="Secteur d'activité",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
            'placeholder': 'Ex: Technologie, Finance, Marketing'
        })
    )
    
    # Date d'expiration
    expires_in_days = forms.IntegerField(
        required=False,
        label="Expiration dans X jours (optionnel)",
        initial=30,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500',
            'placeholder': '30'
        })
    )
    
    def clean_required_skills(self):
        """Convertir la chaîne de compétences en liste"""
        skills = self.cleaned_data.get('required_skills', '')
        if skills:
            return [s.strip() for s in skills.split(',') if s.strip()]
        return []