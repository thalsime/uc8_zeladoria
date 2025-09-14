from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from decouple import config
from accounts.views import AuthViewSet
from salas.views import SalaViewSet, LimpezaRegistroViewSet
from core.views import NotificacaoViewSet


"""Configuração de URLs para o projeto 'zeladoria'.

Este arquivo é o ponto de entrada para o roteamento de todas as requisições
HTTP, mapeando os padrões de URL para as views correspondentes, incluindo a
interface de administração e os endpoints da API.
"""


"""Instancia o roteador padrão do Django REST Framework.

O roteador gera automaticamente as rotas da API para os ViewSets registrados,
simplificando a configuração dos endpoints CRUD.
"""
router = DefaultRouter()
router.register(r'accounts', AuthViewSet, basename='accounts')
router.register(r'salas', SalaViewSet)
router.register(r'limpezas', LimpezaRegistroViewSet)
router.register(r'notificacoes', NotificacaoViewSet, basename='notificacoes')


"""Define a lista principal de padrões de URL para o projeto.

Inclui o caminho para a interface de administração, carregado de forma segura
a partir de variáveis de ambiente, e todas as rotas da API geradas pelo
roteador sob o prefixo 'api/'.
"""
urlpatterns = [
    path(config('URI_ADMIN'), admin.site.urls),
    path('api/', include(router.urls)),
]


"""Adiciona as URLs para servir arquivos de mídia durante o desenvolvimento.

Esta configuração não é adequada para produção e deve ser substituída por
uma estratégia de serviço de arquivos estáticos/mídia mais robusta.
"""
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)