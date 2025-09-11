import django_filters
from django.contrib.auth.models import User
from .models import Sala, LimpezaRegistro


class SalaFilter(django_filters.FilterSet):
    """
    Filtro para buscas avançadas no modelo Sala.
    """
    # Filtro para buscar por parte do nome/número (case-insensitive)
    nome_numero = django_filters.CharFilter(field_name='nome_numero', lookup_expr='icontains')

    # Filtro para buscar por parte da localização (case-insensitive)
    localizacao = django_filters.CharFilter(field_name='localizacao', lookup_expr='icontains')

    # Filtro por faixa de capacidade
    capacidade = django_filters.RangeFilter()

    # Filtro pelo username do responsável (relacionamento ManyToMany)
    responsavel_username = django_filters.CharFilter(
        field_name='responsaveis__username', lookup_expr='icontains'
    )

    class Meta:
        model = Sala
        fields = ['ativa', 'nome_numero', 'localizacao', 'capacidade', 'responsavel_username']


class LimpezaRegistroFilter(django_filters.FilterSet):
    """
    Filtro para buscas avançadas nos registros de limpeza.
    """
    # Filtro para buscar por data/hora (antes, depois ou no dia)
    data_hora_limpeza = django_filters.DateFromToRangeFilter()

    # Filtro pelo nome da sala (relacionamento ForeignKey)
    sala_nome = django_filters.CharFilter(
        field_name='sala__nome_numero', lookup_expr='icontains'
    )

    # Filtro pelo username do funcionário (relacionamento ForeignKey)
    funcionario_username = django_filters.CharFilter(
        field_name='funcionario_responsavel__username', lookup_expr='icontains'
    )

    class Meta:
        model = LimpezaRegistro
        fields = ['sala', 'sala_nome', 'data_hora_limpeza', 'funcionario_username']