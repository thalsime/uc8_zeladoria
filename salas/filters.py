import django_filters
from django.contrib.auth.models import User
from .models import Sala, LimpezaRegistro


class SalaFilter(django_filters.FilterSet):
    """Filtro para a consulta de objetos do modelo Sala.

    Permite filtrar salas por nome, localização, faixa de capacidade,
    status de ativação e pelo nome de usuário de um dos seus responsáveis.

    Filtros disponíveis:
        ativa (bool): Filtra por salas ativas ou inativas.
        nome_numero (str): Busca textual por parte do nome/número da sala.
        localizacao (str): Busca textual por parte da localização da sala.
        capacidade (Range): Filtra por faixa de capacidade (ex: capacidade_min=10).
        responsavel_username (str): Busca por nome de usuário do responsável.
    """
    nome_numero = django_filters.CharFilter(field_name='nome_numero', lookup_expr='icontains')
    localizacao = django_filters.CharFilter(field_name='localizacao', lookup_expr='icontains')
    capacidade = django_filters.RangeFilter()
    responsavel_username = django_filters.CharFilter(
        field_name='responsaveis__username', lookup_expr='icontains'
    )

    class Meta:
        model = Sala
        fields = ['ativa', 'nome_numero', 'localizacao', 'capacidade', 'responsavel_username']


class LimpezaRegistroFilter(django_filters.FilterSet):
    """Filtro para a consulta de objetos do modelo LimpezaRegistro.

    Permite filtrar registros de limpeza por sala (ID ou nome), por nome
    de usuário do funcionário responsável e por um intervalo de datas.

    Filtros disponíveis:
        sala (int): Filtra pelo ID exato da sala.
        sala_nome (str): Busca textual pelo nome da sala associada.
        data_hora_limpeza (Date Range): Filtra por intervalo de datas
            (ex: data_hora_limpeza_after=2025-09-10).
        funcionario_username (str): Busca por nome de usuário do funcionário.
    """
    sala_uuid = django_filters.UUIDFilter(field_name='sala__qr_code_id')
    data_hora_fim = django_filters.DateFromToRangeFilter(field_name='data_hora_fim')
    sala_nome = django_filters.CharFilter(
        field_name='sala__nome_numero', lookup_expr='icontains'
    )
    funcionario_username = django_filters.CharFilter(
        field_name='funcionario_responsavel__username', lookup_expr='icontains'
    )

    class Meta:
        model = LimpezaRegistro
        fields = ['sala_nome', 'sala_uuid', 'data_hora_fim', 'funcionario_username']
