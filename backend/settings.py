"""Environment-based settings. PostgreSQL is the application database."""
import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'local-development-only-change-before-deploying')
DEBUG = os.environ.get('DJANGO_DEBUG', '0') == '1'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')
INSTALLED_APPS = ['django.contrib.auth', 'django.contrib.contenttypes', 'operations']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'django.middleware.common.CommonMiddleware']
ROOT_URLCONF = 'urls'
USE_TZ = True
TIME_ZONE = 'Asia/Kolkata'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': os.environ.get('PGDATABASE', 'miseops'), 'USER': os.environ.get('PGUSER', 'miseops'), 'PASSWORD': os.environ.get('PGPASSWORD', ''), 'HOST': os.environ.get('PGHOST', 'localhost'), 'PORT': os.environ.get('PGPORT', '5432'), 'CONN_MAX_AGE': 60, 'CONN_HEALTH_CHECKS': True, 'OPTIONS': {'connect_timeout': 10, 'sslmode': os.environ.get('PGSSLMODE', 'prefer')}}}
if os.environ.get('TEST_SQLITE') == '1':
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'test.sqlite3'}}
