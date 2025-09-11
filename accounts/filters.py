import django_filters
from django.contrib.auth.models import User


class UserFilter(django_filters.FilterSet):
    """
    Filtro para buscas avançadas no modelo User.
    """
    username = django_filters.CharFilter(field_name='username', lookup_expr='icontains')
    email = django_filters.CharFilter(field_name='email', lookup_expr='icontains')

    # Filtra usuários por nome do grupo
    group = django_filters.CharFilter(field_name='groups__name', lookup_expr='iexact')

    class Meta:
        model = User
        fields = ['username', 'email', 'is_superuser', 'group']