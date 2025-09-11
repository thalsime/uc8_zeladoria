from decouple import config, Csv
from pathlib import Path


"""Configuração central do projeto Django 'zeladoria'.

Este arquivo define as configurações globais da aplicação, carregando valores
sensíveis ou específicos de ambiente a partir de variáveis de ambiente para
maior segurança e flexibilidade.
"""

BASE_DIR = Path(__file__).resolve().parent.parent


"""Configurações de segurança.

SECRET_KEY é a chave criptográfica do projeto.
DEBUG ativa ou desativa o modo de depuração com mensagens de erro detalhadas.
ALLOWED_HOSTS e CSRF_TRUSTED_ORIGINS são listas de domínios permitidos.
"""
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', cast=Csv())


"""Lista de todas as aplicações Django ativas neste projeto.

A ordem é relevante для templates, estáticos e comandos de gerenciamento.
"""
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "accounts",
    "salas",
    "core",
]


"""Define os middlewares que processam as requisições e respostas.

Executados em ordem, aplicam lógicas de segurança, sessão, autenticação, etc.
"""
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


"""Aponta para o módulo Python que contém a configuração de URLs principal."""
ROOT_URLCONF = "zeladoria.urls"


"""Configura o sistema de templates do Django."""
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


"""Define o caminho para a aplicação WSGI, utilizada por servidores web."""
WSGI_APPLICATION = "zeladoria.wsgi.application"


"""Configura a conexão com o banco de dados."""
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


"""Lista de validadores para verificar a força das senhas dos usuários."""
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


"""Configurações globais para o Django REST Framework.

Define os comportamentos padrão para autenticação, permissões, renderização
e filtros da API.
"""
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
}


"""Configurações de internacionalização e localização."""
LANGUAGE_CODE = config("LANGUAGE_CODE")
TIME_ZONE = config("TIME_ZONE")
USE_I18N =  config("USE_I18N", default=True, cast=bool)
USE_TZ = config("USE_TZ", default=True, cast=bool)


"""URL base para servir arquivos estáticos (CSS, JavaScript, imagens)."""
STATIC_URL = "static/"


"""Configurações para o armazenamento e acesso a arquivos de mídia.

MEDIA_URL é a URL pública, e MEDIA_ROOT é o diretório no sistema de arquivos.
"""
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


"""Define o tipo de campo padrão para chaves primárias automáticas."""
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"