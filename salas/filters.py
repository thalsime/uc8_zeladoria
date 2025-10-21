import django_filters
from datetime import timedelta
from django.contrib.auth.models import User
from django.db.models import (
    Q, F, Exists, OuterRef, Subquery, ExpressionWrapper, DateTimeField, DurationField
)
from django.utils import timezone
from .models import Sala, LimpezaRegistro, RelatorioSalaSuja


class SalaFilter(django_filters.FilterSet):
    """Filtro para a consulta de objetos do modelo Sala.

    Permite filtrar salas por nome, localização, faixa de capacidade,
    status de ativação, pelo nome de usuário de um dos seus responsáveis,
    e pelo status de limpeza calculado.

    Filtros disponíveis:
        ativa (bool): Filtra por salas ativas ou inativas.
        nome_numero (str): Busca textual por parte do nome/número da sala.
        localizacao (str): Busca textual por parte da localização da sala.
        capacidade (Range): Filtra por faixa de capacidade (ex: capacidade_min=10).
        responsavel_username (str): Busca por nome de usuário do responsável.
        status_limpeza (str): Filtra pelo status de limpeza calculado
            ('Limpa', 'Suja', 'Em Limpeza', 'Limpeza Pendente').
    """
    nome_numero = django_filters.CharFilter(
        field_name='nome_numero', lookup_expr='icontains'
    )
    localizacao = django_filters.CharFilter(
        field_name='localizacao', lookup_expr='icontains'
    )
    capacidade = django_filters.RangeFilter()
    responsavel_username = django_filters.CharFilter(
        field_name='responsaveis__username', lookup_expr='icontains'
    )

    status_limpeza = django_filters.ChoiceFilter(
        choices=[
            ('Limpa', 'Limpa'),
            ('Suja', 'Suja'),
            ('Em Limpeza', 'Em Limpeza'),
            ('Limpeza Pendente', 'Limpeza Pendente'),
        ],
        method='filter_status_limpeza',
        label="Filtrar por status de limpeza (Limpa, Suja, Em Limpeza, Limpeza Pendente)"
    )

    class Meta:
        model = Sala
        fields = [
            'ativa', 'nome_numero', 'localizacao', 'capacidade',
            'responsavel_username', 'status_limpeza'
        ]

    def filter_status_limpeza(self, queryset, name, value):
        """
        Filtra o queryset de Salas com base no status de limpeza calculado.
        """
        now = timezone.now()

        # Subconsultas (permanecem as mesmas)
        ultima_limpeza_subquery = LimpezaRegistro.objects.filter(
            sala=OuterRef('pk'), data_hora_fim__isnull=False
        ).order_by('-data_hora_fim').values('data_hora_fim')[:1]

        ultimo_relatorio_subquery = RelatorioSalaSuja.objects.filter(
            sala=OuterRef('pk')
        ).order_by('-data_hora').values('data_hora')[:1]

        limpeza_em_andamento_subquery = LimpezaRegistro.objects.filter(
            sala=OuterRef('pk'), data_hora_fim__isnull=True
        )

        # Anotar o queryset base (permanece o mesmo)
        annotated_queryset = queryset.annotate(
            ultima_limpeza_fim=Subquery(ultima_limpeza_subquery),
            ultimo_relatorio_data=Subquery(ultimo_relatorio_subquery),
            tem_limpeza_em_andamento=Exists(limpeza_em_andamento_subquery)
        )

        # Expressão reutilizável para calcular quando a limpeza expira (permanece a mesma)
        duration_expr = ExpressionWrapper(
            F('validade_limpeza_horas') * timedelta(hours=1),
            output_field=DurationField()
        )
        cleaning_expires_at_expr = ExpressionWrapper(
            F('ultima_limpeza_fim') + duration_expr,
            output_field=DateTimeField()
        )

        if value == 'Em Limpeza':
            # Apenas argumento nomeado, sem Q objects - OK
            return annotated_queryset.filter(tem_limpeza_em_andamento=True)

        elif value == 'Suja':
            # Apenas Q objects - OK
            return annotated_queryset.filter(
                Q(ultimo_relatorio_data__isnull=False) &
                (Q(ultima_limpeza_fim__isnull=True) | Q(ultimo_relatorio_data__gt=F('ultima_limpeza_fim')))
            )

        elif value == 'Limpa':
            annotated_queryset_for_limpa = annotated_queryset.annotate(
                cleaning_expires_at=cleaning_expires_at_expr
            )
            # --- INÍCIO DA CORREÇÃO DE ORDEM ---
            # Q object PRIMEIRO, depois argumentos nomeados
            return annotated_queryset_for_limpa.filter(
                (Q(ultimo_relatorio_data__isnull=True) | Q(ultimo_relatorio_data__lt=F('ultima_limpeza_fim'))), # Q object posicional
                tem_limpeza_em_andamento=False, # Argumento nomeado
                ultima_limpeza_fim__isnull=False, # Argumento nomeado
                cleaning_expires_at__gte=now # Argumento nomeado
            )
            # --- FIM DA CORREÇÃO DE ORDEM ---

        elif value == 'Limpeza Pendente':
            annotated_queryset_for_pendente = annotated_queryset.annotate(
                cleaning_expires_at=cleaning_expires_at_expr
            )
            validade_expirada_condition = Q(cleaning_expires_at__lt=now)
            nunca_limpa_ou_expirou_condition = Q(ultima_limpeza_fim__isnull=True) | validade_expirada_condition

            # --- INÍCIO DA CORREÇÃO DE ORDEM ---
            # Q objects PRIMEIRO, depois argumentos nomeados
            return annotated_queryset_for_pendente.filter(
                (Q(ultimo_relatorio_data__isnull=True) | Q(ultimo_relatorio_data__lt=F('ultima_limpeza_fim'))), # Q object posicional (condição NÃO Suja)
                nunca_limpa_ou_expirou_condition, # Q object posicional (condição Pendente)
                tem_limpeza_em_andamento=False # Argumento nomeado
            )
            # --- FIM DA CORREÇÃO DE ORDEM ---

        return queryset


class LimpezaRegistroFilter(django_filters.FilterSet):
    """Filtro para a consulta de objetos do modelo LimpezaRegistro.
        (Esta classe permanece inalterada)
    """
    sala_uuid = django_filters.UUIDFilter(field_name='sala__qr_code_id')
    sala_nome = django_filters.CharFilter(
        field_name='sala__nome_numero', lookup_expr='icontains'
    )
    funcionario_username = django_filters.CharFilter(
        field_name='funcionario_responsavel__username', lookup_expr='icontains'
    )
    data_hora_fim_after = django_filters.DateFilter(
        field_name='data_hora_fim',
        lookup_expr='gte'
    )
    data_hora_fim_before = django_filters.DateFilter(
        field_name='data_hora_fim',
        lookup_expr='lte'
    )

    class Meta:
        model = LimpezaRegistro
        fields = [
            'sala_nome', 'sala_uuid', 'funcionario_username',
            'data_hora_fim_after', 'data_hora_fim_before',
        ]
