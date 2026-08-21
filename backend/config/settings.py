import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("LOCALMIND_SECRET_KEY", "localmind-development-only-key")
DEBUG = os.getenv("LOCALMIND_DEBUG", "true").lower() == "true"

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",

    "core",
    "documents",
    "learning",
    "tutor",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

# LocalMind Phase 1 settings
LOCALMIND_MAX_UPLOAD_MB = int(os.getenv("LOCALMIND_MAX_UPLOAD_MB", "100"))
LOCALMIND_OLLAMA_URL = os.getenv("LOCALMIND_OLLAMA_URL", "http://127.0.0.1:11434")
LOCALMIND_OUTLINE_MODEL = os.getenv("LOCALMIND_OUTLINE_MODEL", "qwen3:4b")
LOCALMIND_TUTOR_MODEL = os.getenv("LOCALMIND_TUTOR_MODEL", "qwen3:1.7b")
LOCALMIND_USE_OLLAMA = os.getenv("LOCALMIND_USE_OLLAMA", "true").lower() == "true"

