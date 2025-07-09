"""
Configurações de URLS para a aplicação principal Zeladoria.

Define os padrões de URL para o projeto, incluindo a interface administrativa do Django,
e os endpoints da API RESTful gerenciados pelo Django REST Framework.
Utiliza um roteador padrão para organizar as URLs dos ViewSets.
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter # Importe DefaultRouter aqui
from decouple import config

# Importe todos os seus ViewSets diretamente aqui
from accounts.views import AuthViewSet
from salas.views import SalaViewSet, LimpezaRegistroViewSet

# Instanciação do roteador padrão do Django REST Framework.
# Este roteador é responsável por gerar automaticamente os padrões de URL
# para os ViewSets registrados, simplificando a configuração das rotas da API.
router = DefaultRouter()

# Registro dos ViewSets com o roteador.
# Cada chamada a :func:`router.register` associa um ViewSet a um prefixo de URL,
# a partir do qual as rotas para as operações CRUD e ações personalizadas são geradas.
#
# :param prefix: O segmento inicial da URL para este ViewSet (ex: 'accounts', 'salas').
# :param viewset: A classe do ViewSet (ex: :class:`~accounts.views.AuthViewSet`).
# :param basename: Opcional. Usado para nomear as rotas geradas (ex: 'accounts-list').
#                  Necessário se o ViewSet não tiver um `queryset` definido ou `model` no `serializer_class`.
router.register(r'accounts', AuthViewSet, basename='accounts')
router.register(r'salas', SalaViewSet)
router.register(r'limpezas', LimpezaRegistroViewSet)

# Padrões de URL raiz do projeto.
# Esta lista contém todas as URLs da aplicação, incluindo a interface administrativa
# e os endpoints da API RESTful.
urlpatterns = [
    path(config('URI_ADMIN'), admin.site.urls),
    # Inclui as URLs geradas automaticamente pelo roteador, todas sob o prefixo 'api/'.
    path('api/', include(router.urls)),
]