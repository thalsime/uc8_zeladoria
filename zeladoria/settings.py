"""
Configurações do projeto Django 'zeladoria'.

Este arquivo define todas as configurações globais para a aplicação,
incluindo configurações de segurança, aplicações instaladas, middleware,
banco de dados, validação de senha, configurações do Django REST Framework,
internacionalização e arquivos estáticos.

Muitas configurações são carregadas a partir de variáveis de ambiente
usando a biblioteca `decouple` para maior flexibilidade e segurança em diferentes ambientes.
"""

from decouple import config
from pathlib import Path

# Diretório base do projeto.
# :ivar BASE_DIR: :class:`~pathlib.Path` Representa o caminho absoluto para o diretório raiz do projeto Django.
BASE_DIR = Path(__file__).resolve().parent.parent


# Configurações de desenvolvimento rápido - inadequadas para produção.
# Consulte https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/ para mais informações.

# Configurações de segurança.
# Estas configurações são cruciais para a segurança da aplicação.

# AVISO DE SEGURANÇA: mantenha a chave secreta usada em produção em segredo!
# :ivar SECRET_KEY: :class:`str` Uma chave secreta usada para fins criptográficos e de segurança,
#                  como hash de senhas e tokens de sessão. Carregada de variáveis de ambiente.
SECRET_KEY = config("SECRET_KEY")

# AVISO DE SEGURANÇA: não execute com o modo de depuração ativado em produção!
# :ivar DEBUG: :class:`bool` Flag de modo de depuração. `True` em desenvolvimento, `False` em produção.
#             Controla a exibição de erros detalhados e o recarregamento automático do código.
DEBUG = config("DEBUG", default=False, cast=bool)

# :ivar ALLOWED_HOSTS: :class:`list` Lista de strings que definem os hosts/domínios que podem servir a aplicação.
#                     É uma medida de segurança para evitar ataques de cabeçalho HTTP Host.
ALLOWED_HOSTS = ['*']


# Definição das aplicações.
# Lista de todas as aplicações Django (incluindo as built-in, de terceiros e customizadas)
# que estão ativas neste projeto.
# :ivar INSTALLED_APPS: :class:`list` Lista de strings, cada uma representando uma aplicação instalada.
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "accounts",
    "salas",
    "core",
]

# Classes de middleware.
# :ivar MIDDLEWARE: :class:`list` Uma lista de strings que especificam as classes de middleware a serem usadas.
#                  Componentes que processam requisições e respostas HTTP, executando tarefas como
#                  segurança, autenticação e gerenciamento de sessões.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Configuração de URL principal do projeto.
# :ivar ROOT_URLCONF: :class:`str` O caminho completo do módulo de URL principal do projeto.
ROOT_URLCONF = "zeladoria.urls"

# Configurações de templates.
# Define como o Django encontrará e renderizará os templates.
# :ivar TEMPLATES: :class:`list` Uma lista de dicionários, cada um configurando um motor de templates.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True, # Permite que o Django procure templates dentro dos diretórios 'templates' de cada app.
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Aplicação WSGI.
# :ivar WSGI_APPLICATION: :class:`str` O ponto de entrada para servidores web compatíveis com WSGI.
WSGI_APPLICATION = "zeladoria.wsgi.application"


# Configurações de banco de dados.
# Consulte https://docs.djangoproject.com/en/5.2/ref/settings/#databases para mais informações.
# Define os detalhes da conexão com o banco de dados.
# :ivar DATABASES: :class:`dict` Um dicionário que define as configurações de conexão para cada banco de dados.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3", # Caminho para o arquivo do banco de dados SQLite.
    }
}


# Validadores de senha.
# Consulte https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators para mais informações.
# :ivar AUTH_PASSWORD_VALIDATORS: :class:`list` Lista de dicionários, cada um especificando um validador de senha.
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

# Configurações do Django REST Framework (DRF).
# :ivar REST_FRAMEWORK: :class:`dict` Dicionário que define comportamentos padrão para
#                      renderizadores, parsers, permissões e autenticação da API.
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer", # Renderiza a saída da API como JSON.
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser", # Analisa a entrada da API como JSON.
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated", # Permissão padrão: apenas usuários autenticados.
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication", # Autenticação baseada em token.
    ]
}

# Configurações de internacionalização (i18n) e localização.
# Consulte https://docs.djangoproject.com/en/5.2/topics/i18n/ para mais informações.

# :ivar LANGUAGE_CODE: :class:`str` O código de idioma padrão para esta instalação do Django.
#                     Carregado de variáveis de ambiente.
LANGUAGE_CODE = config("LANGUAGE_CODE")

# :ivar TIME_ZONE: :class:`str` O fuso horário padrão para esta instalação do Django.
#                 Carregado de variáveis de ambiente.
TIME_ZONE = config("TIME_ZONE")

# :ivar USE_I18N: :class:`bool` Um booleano que especifica se o sistema de tradução do Django deve ser habilitado.
#                Carregado de variáveis de ambiente.
USE_I18N =  config("USE_I18N", default=True, cast=bool)

# :ivar USE_TZ: :class:`bool` Um booleano que especifica se datetimes serão timezone-aware por padrão.
#              Carregado de variáveis de ambiente.
USE_TZ = config("USE_TZ", default=True, cast=bool)


# Arquivos estáticos (CSS, JavaScript, Imagens).
# Consulte https://docs.djangoproject.com/en/5.2/howto/static-files/ para mais informações.
# :ivar STATIC_URL: :class:`str` URL para servir arquivos estáticos.
STATIC_URL = "static/"

# Tipo de campo de chave primária padrão.
# Consulte https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field para mais informações.
# :ivar DEFAULT_AUTO_FIELD: :class:`str` Define o tipo de campo automático para chaves primárias em novos modelos.
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"