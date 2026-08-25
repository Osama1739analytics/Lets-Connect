from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-m+&3_!f0(0^=4(9)8@8*6#5^2_5+9=7^0=8=0(8=0(8=0(8='

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = [
    'https://lets-connect-fyp.onrender.com',
    'https://*.onrender.com',
    'https://lets-connect-production.up.railway.app',
    'https://*.up.railway.app',
]

# Application definition

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'channels',
    'social_django',
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
    'taggit',

    # Local apps
    'home.apps.HomeConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Social Auth Middleware
    'social_django.middleware.SocialAuthExceptionMiddleware',
]

ROOT_URLCONF = 'p2p.urls'

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
                
                # Social Auth Context Processors
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

# WSGI_APPLICATION = 'p2p.wsgi.application'
ASGI_APPLICATION = 'p2p.asgi.application'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Karachi'

USE_I18N = True

USE_TZ = True

# Date and Time Formatting (Explicit for Pakistan preference)
DATE_FORMAT = 'd-m-Y'
TIME_FORMAT = 'h:i A'
DATETIME_FORMAT = 'd-m-Y h:i A'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATIC_ROOT = BASE_DIR / 'staticfiles'  # <--- Add this line
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'  # <--- Add this line
# Media files (Uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication Backends
AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_USER_MODEL = 'home.CustomUser'

# Auth URLs
LOGIN_URL = 'home:login'
LOGIN_REDIRECT_URL = 'home:onboarding_setup'
LOGOUT_REDIRECT_URL = 'home:login'

# Email settings
if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RENDER'):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 465
    EMAIL_USE_TLS = False
    EMAIL_USE_SSL = True
    EMAIL_HOST_USER = 'sharyar.ali.104@gmail.com'
    EMAIL_HOST_PASSWORD = 'itsg iwri ykui wpmt'

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# social-auth settings (set your real keys in env variables)
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', 'your-client-id-here')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', 'your-secret-here')
SOCIAL_AUTH_USER_MODEL = AUTH_USER_MODEL
SOCIAL_AUTH_USER_FIELDS = ['username', 'email', 'full_name', 'age', 'user_type']

SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.settings.readonly',
]

SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_PARAMS = {
    'access_type': 'offline',
    'prompt': 'consent',
    'approval_prompt': 'force',
}

SOCIAL_AUTH_GOOGLE_OAUTH2_EXTRA_DATA = [
    ('refresh_token', 'refresh_token'),
    ('expires_in', 'expires'),
    ('access_token', 'access_token'),
]

# Pipeline to require profile confirmation before user creation
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'home.social_pipeline.check_existing_email',
    'home.social_pipeline.require_profile',
    'social_core.pipeline.user.create_user',
    'home.social_pipeline.set_password',  # Set password if provided
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'home.social_pipeline.update_calendar_status',
)

# OTP configuration
OTP_CODE_LENGTH = 6
OTP_EXPIRY_SECONDS = 300  # 5 minutes

# Daily.co Integration Key for Frictionless Online Meetings
DAILY_API_KEY = os.getenv('DAILY_API_KEY', '20618252681ba2b25e31c3438303bf04d8f62960f6762e0e0327d3e3073f6fab') # Placeholder dev key; replace with yours


# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Groq API Key for AI Assistant
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

