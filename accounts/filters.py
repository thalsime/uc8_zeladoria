import django_filters
from django.contrib.auth.models import User


class UserFilter(django_filters.FilterSet):
    """Filtro para a consulta de objetos do modelo User.

    Esta classe permite a filtragem de usuários com base em correspondências
    parciais e insensíveis a maiúsculas para os campos de username e email,
    e por nome exato de grupo.

    Filtros disponíveis:
        username (str): Busca por parte do nome de usuário (icontains).
        email (str): Busca por parte do email do usuário (icontains).
        is_superuser (bool): Filtra por usuários que são ou não superusuários.
        group (str): Filtra por usuários pertencentes a um grupo com nome exato (iexact).
    """
    username = django_filters.CharFilter(field_name='username', lookup_expr='icontains')
    email = django_filters.CharFilter(field_name='email', lookup_expr='icontains')
    group = django_filters.CharFilter(field_name='groups__name', lookup_expr='iexact')

    class Meta:
        model = User
        fields = ['username', 'email', 'is_superuser', 'group']