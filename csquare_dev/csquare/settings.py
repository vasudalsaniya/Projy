from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────────────────────────────────────
# ENVIRONMENT SWITCH
# Set ENVIRONMENT=production  →  Neon PostgreSQL + AWS S3 + DEBUG off
# Set ENVIRONMENT=development →  SQLite + local media  + DEBUG on   (default)
# ─────────────────────────────────────────────────────────────────────────────
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
IS_PRODUCTION = ENVIRONMENT == 'production'

# ─── Security ────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-gs^3$(^6ryi%4g_zg%&n(1o#kb+6o#6#bfl5qctv_0g7_#0qs#'
)
DEBUG = not IS_PRODUCTION

ALLOWED_HOSTS = [
    '.vercel.app',
    'localhost',
    '127.0.0.1',
]

# ─── Installed Apps ───────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'storages',

    # Custom Apps
    'accounts',
    'college',
    'students',
    'recruitment',
]

# ─── Middleware ───────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'csquare.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.user_notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'csquare.wsgi.application'

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE
#   production  → Neon PostgreSQL via DATABASE_URL env var
#   development → SQLite (local file)
# ─────────────────────────────────────────────────────────────────────────────
if IS_PRODUCTION and os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ─── Password Validators ──────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── i18n ─────────────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ─────────────────────────────────────────────────────────────────────────────
# STATIC FILES  (same in both environments — whitenoise serves from STATIC_ROOT)
# ─────────────────────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# ─────────────────────────────────────────────────────────────────────────────
# MEDIA / FILE STORAGE
#   production  → AWS S3
#   development → local filesystem  (served by Django dev server)
# ─────────────────────────────────────────────────────────────────────────────
if IS_PRODUCTION:
    # ── AWS S3 credentials (set these in Vercel env vars) ──────────────────
    AWS_ACCESS_KEY_ID       = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY   = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME      = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
    AWS_S3_FILE_OVERWRITE   = False          # never overwrite existing files
    AWS_DEFAULT_ACL         = 'public-read'  # files are publicly readable
    AWS_S3_CUSTOM_DOMAIN    = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

    MEDIA_URL  = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
    MEDIA_ROOT = ''

    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
            'OPTIONS': {
                'location': 'media',
                'file_overwrite': False,
                'default_acl': 'public-read',
            },
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
        },
    }

else:
    # ── Local filesystem ────────────────────────────────────────────────────
    MEDIA_URL  = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

    STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
        },
    }

# ─── Auth ─────────────────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]
