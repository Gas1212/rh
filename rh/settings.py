"""
Django settings for rh project.
"""

from pathlib import Path
from mongoengine import connect

# ==================== BASE DIR ====================
BASE_DIR = Path(__file__).resolve().parent.parent

# ==================== SECURITY ====================
SECRET_KEY = 'django-insecure-qaqz(fgg4s63pmxxy9m5fku7^d!45xzw^_iuy*#$snmz%la^h0'
DEBUG = True
ALLOWED_HOSTS = ['biggergas.serv00.net', 'localhost', '127.0.0.1']

# ==================== APPLICATIONS ====================
INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Apps locales
    'fiche_de_paie',   
    'file_converter',
    'jobs',
    'accounts',

    # MongoEngine
    'django_mongoengine',
    'django_mongoengine.mongo_admin',
]

# ==================== MIDDLEWARE ====================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'rh.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'rh.wsgi.application'

# ==================== DJANGO DATABASE (ORM) ====================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ==================== MONGODB DATABASES ====================
MONGODB_DATABASES = {
    'default': {  # Utilisé par django_mongoengine pour l'admin
        'name': 'RH_Platform',
        'host': 'mongodb+srv://syncro1578_db_user:ah49wIw2HpxEnKwg@jobposting.hu5w8ad.mongodb.net/RH_Platform',
        'username': 'syncro1578_db_user',
        'password': 'ah49wIw2HpxEnKwg',
        'authentication_source': 'admin',
    },
    'keejob': {  # Base Keejob
        'name': 'Keejob',
        'host': 'mongodb+srv://syncro1578_db_user:ah49wIw2HpxEnKwg@jobposting.hu5w8ad.mongodb.net/Keejob',
        'username': 'syncro1578_db_user',
        'password': 'ah49wIw2HpxEnKwg',
        'authentication_source': 'admin',
    },
    'tanit': {  # Base Tanitjob
        'name': 'Tanitjob',
        'host': 'mongodb+srv://syncro1578_db_user:ah49wIw2HpxEnKwg@jobposting.hu5w8ad.mongodb.net/Tanitjob',
        'username': 'syncro1578_db_user',
        'password': 'ah49wIw2HpxEnKwg',
        'authentication_source': 'admin',
    },
}

# ==================== MongoEngine connections pour scripts spécifiques ====================
db1 = connect(db='Keejob', alias='keejob', host=MONGODB_DATABASES['keejob']['host'], username='syncro1578_db_user', password='ah49wIw2HpxEnKwg')
db2 = connect(db='Tanitjob', alias='tanit', host=MONGODB_DATABASES['tanit']['host'], username='syncro1578_db_user', password='ah49wIw2HpxEnKwg')
db_rh = connect(db='RH_Platform', alias='default', host=MONGODB_DATABASES['default']['host'], username='syncro1578_db_user', password='ah49wIw2HpxEnKwg')

# ==================== CUSTOM USER MODEL ====================
AUTH_USER_MODEL = 'accounts.User'

# ==================== MEDIA ====================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ==================== STATIC ====================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'public' / 'static_root'

# ==================== AUTH CONFIGURATION ====================
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/accounts/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ==================== PASSWORD VALIDATION ====================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 6}},
]

# ==================== INTERNATIONALIZATION ====================
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Tunis'
USE_I18N = True
USE_TZ = True

# ==================== DEFAULT FIELD ====================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==================== FILE UPLOAD ====================
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760
ALLOWED_CV_EXTENSIONS = ['pdf', 'doc', 'docx']
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png']

# ====================MANGODB JOBS ====================
MONGO_URI = "mongodb+srv://syncro1578_db_user:ah49wIw2HpxEnKwg@jobposting.hu5w8ad.mongodb.net/"
MONGO_DATABASE_1 = "Keejob"
MONGO_DATABASE_2 = "Tanitjob"
MONGO_DATABASE_RH = "RH_Platform"
MONGO_COLLECTION = "db"
