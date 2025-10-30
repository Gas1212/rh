# jobs/models.py
from mongoengine import Document, fields
from datetime import datetime

class JobDocument(Document):
    """
    Offre d'emploi interne (MongoDB)
    Stockée dans la base RH_Platform
    """
    
    # ==================== RELATIONS ====================
    company_id = fields.ObjectIdField(required=True)  # Référence à CompanyDocument
    company_name = fields.StringField(max_length=255)  # Dénormalisé pour performance
    recruiter_id = fields.ObjectIdField(required=True)  # Qui a publié l'offre
    
    # ==================== INFORMATIONS DE BASE ====================
    title = fields.StringField(required=True, max_length=255)  # Ex: "Développeur Full Stack"
    description = fields.StringField(required=True)  # Description complète du poste
    
    # ==================== LOCALISATION & CONTRAT ====================
    location = fields.StringField(max_length=255, default="Tunisie")  # Ville ou pays
    contract_type = fields.StringField(
        max_length=50,
        choices=[
            ('CDI', 'CDI - Contrat à Durée Indéterminée'),
            ('CDD', 'CDD - Contrat à Durée Déterminée'),
            ('FREELANCE', 'Freelance / Mission'),
            ('STAGE', 'Stage'),
            ('ALTERNANCE', 'Alternance'),
        ],
        default='CDI'
    )
    work_mode = fields.StringField(
        max_length=50,
        choices=[
            ('ON_SITE', 'Présentiel'),
            ('REMOTE', 'Télétravail complet'),
            ('HYBRID', 'Hybride'),
        ],
        default='ON_SITE'
    )
    
    # ==================== SALAIRE ====================
    salary_min = fields.DecimalField(precision=2, min_value=0)  # Salaire minimum (TND)
    salary_max = fields.DecimalField(precision=2, min_value=0)  # Salaire maximum (TND)
    salary_currency = fields.StringField(max_length=3, default='TND')  # Devise
    salary_period = fields.StringField(
        max_length=20,
        choices=[
            ('MONTHLY', 'Mensuel'),
            ('ANNUAL', 'Annuel'),
            ('HOURLY', 'Horaire'),
        ],
        default='MONTHLY'
    )
    
    # ==================== COMPÉTENCES & EXPÉRIENCE ====================
    required_skills = fields.ListField(fields.StringField())  # Compétences obligatoires
    optional_skills = fields.ListField(fields.StringField())  # Compétences souhaitées
    experience_min = fields.IntField(min_value=0, default=0)  # Années d'expérience minimales
    experience_max = fields.IntField(min_value=0)  # Années d'expérience maximales
    education_level = fields.StringField(
        max_length=50,
        choices=[
            ('BAC', 'Baccalauréat'),
            ('BAC+2', 'Bac+2'),
            ('BAC+3', 'Licence / Bac+3'),
            ('BAC+5', 'Master / Ingénieur'),
            ('DOCTORAT', 'Doctorat'),
        ]
    )
    
    # ==================== SECTEUR & FONCTION ====================
    industry = fields.StringField(max_length=100)  # Ex: "Technologie", "Finance"
    department = fields.StringField(max_length=100)  # Ex: "IT", "Marketing"
    
    # ==================== STATUT & PUBLICATION ====================
    status = fields.StringField(
        max_length=20,
        choices=[
            ('DRAFT', 'Brouillon'),
            ('PUBLISHED', 'Publiée'),
            ('PAUSED', 'En pause'),
            ('CLOSED', 'Fermée'),
            ('EXPIRED', 'Expirée'),
        ],
        default='DRAFT'
    )
    published_at = fields.DateTimeField()  # Date de publication
    expires_at = fields.DateTimeField()  # Date d'expiration (optionnelle)
    
    # ==================== STATISTIQUES ====================
    views_count = fields.IntField(default=0)  # Nombre de vues
    applications_count = fields.IntField(default=0)  # Nombre de candidatures
    
    # ==================== METADATA ====================
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)
    
    # ==================== CONFIGURATION MONGODB ====================
    meta = {
        'collection': 'jobs',  # Nom de la collection dans MongoDB
        'db_alias': 'default',  # Utilise la base RH_Platform
        'indexes': [
            'company_id',
            'recruiter_id',
            'status',
            'location',
            'contract_type',
            'industry',
            'published_at',
            'required_skills',  # Index pour recherche par compétences
        ],
        'ordering': ['-published_at']  # Trier par date décroissante
    }
    
    def __str__(self):
        return f"{self.title} chez {self.company_name}"
    
    # ==================== MÉTHODES UTILITAIRES ====================
    
    def get_salary_range(self):
        """Retourne le range salarial formaté"""
        if self.salary_min and self.salary_max:
            return f"{int(self.salary_min)}-{int(self.salary_max)} {self.salary_currency}"
        elif self.salary_min:
            return f"À partir de {int(self.salary_min)} {self.salary_currency}"
        else:
            return "Non communiqué"
    
    def is_new(self):
        """Vérifie si l'offre a moins de 3 jours"""
        if not self.published_at:
            return False
        days_ago = (datetime.now() - self.published_at).days
        return days_ago <= 3
    
    def is_expired(self):
        """Vérifie si l'offre est expirée"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    def increment_views(self):
        """Incrémenter le compteur de vues"""
        self.views_count += 1
        self.save()
    
    def increment_applications(self):
        """Incrémenter le compteur de candidatures"""
        self.applications_count += 1
        self.save()