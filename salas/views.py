from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from django.db.models import OuterRef, Subquery, Exists
from .models import Sala, LimpezaRegistro
from .filters import SalaFilter, LimpezaRegistroFilter
from .serializers import SalaSerializer, LimpezaRegistroSerializer
from core.permissions import IsAdminUser, IsZeladorUser, IsCorpoDocenteUser


class SalaViewSet(viewsets.ModelViewSet):
    """Gerencia as operações CRUD para o modelo Sala.

    Fornece endpoints para criar, ler, atualizar e deletar salas, com
    permissões de acesso granulares e uma ação customizada para registrar
    a limpeza.
    """
    queryset = Sala.objects.all().order_by('nome_numero')
    serializer_class = SalaSerializer
    filterset_class = SalaFilter
    lookup_field = 'qr_code_id'
    lookup_value_regex = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

    def get_permissions(self):
        """Define as permissões de acesso dinamicamente por ação.

        Restringe as operações de escrita (`create`, `update`, `destroy`) a
        administradores, a ação de `marcar_como_limpa` ao grupo 'Zeladoria',
        e permite a leitura (`list`, `retrieve`) a qualquer usuário autenticado.

        Returns:
            list: Uma lista de instâncias de classes de permissão.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        elif self.action in ['iniciar_limpeza', 'concluir_limpeza']:
            permission_classes = [IsZeladorUser]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Otimiza a consulta principal do ViewSet para evitar o problema N+1."""
        ultimos_registros = LimpezaRegistro.objects.filter(
            sala=OuterRef('pk')
        ).order_by('-data_hora_inicio')

        queryset = Sala.objects.prefetch_related('responsaveis').annotate(
            ultima_limpeza_fim=Subquery(
                ultimos_registros.values('data_hora_fim')[:1]
            ),
            ultimo_funcionario=Subquery(
                ultimos_registros.values('funcionario_responsavel__username')[:1]
            ),
            limpeza_em_andamento=Exists(
                LimpezaRegistro.objects.filter(sala=OuterRef('pk'), data_hora_fim__isnull=True)
            )
        )
        return queryset

    @action(detail=True, methods=['post'], permission_classes=[IsZeladorUser])
    def iniciar_limpeza(self, request, qr_code_id=None):
        """Cria um novo registro para marcar o início de uma limpeza."""
        with transaction.atomic():  # Garante a atomicidade da operação
            sala = Sala.objects.select_for_update().get(qr_code_id=qr_code_id)

            if not sala.ativa:
                return Response(
                    {'detail': 'Salas inativas não podem ter a limpeza iniciada.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if LimpezaRegistro.objects.filter(sala=sala, data_hora_fim__isnull=True).exists():
                return Response({'detail': 'Esta sala já está em processo de limpeza.'},
                                status=status.HTTP_400_BAD_REQUEST)

            registro = LimpezaRegistro.objects.create(sala=sala, funcionario_responsavel=request.user,
                                                      data_hora_inicio=timezone.now())
            serializer = LimpezaRegistroSerializer(registro)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsZeladorUser])
    def concluir_limpeza(self, request, qr_code_id=None):
        """Atualiza um registro de limpeza existente, marcando sua conclusão."""
        sala = self.get_object()

        if not sala.ativa:
            return Response(
                {'detail': 'Salas inativas não podem ter a limpeza concluída.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        registro_aberto = LimpezaRegistro.objects.filter(sala=sala, data_hora_fim__isnull=True).order_by(
            '-data_hora_inicio').first()

        if not registro_aberto:
            return Response({'detail': 'Nenhuma limpeza foi iniciada para esta sala.'},
                            status=status.HTTP_400_BAD_REQUEST)

        registro_aberto.data_hora_fim = timezone.now()
        registro_aberto.observacoes = request.data.get('observacoes', registro_aberto.observacoes)
        registro_aberto.save()

        serializer = LimpezaRegistroSerializer(registro_aberto)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """Sobrescreve o método de exclusão para adicionar uma regra de negócio.

        Impede a exclusão de uma sala se ela estiver marcada como inativa,
        retornando um erro 400. A sala deve ser reativada antes de poder
        ser excluída.
        """
        sala = self.get_object()
        if not sala.ativa:
            return Response(
                {'detail': 'Salas inativas não podem ser excluídas. Ative a sala primeiro.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)


class LimpezaRegistroViewSet(viewsets.ReadOnlyModelViewSet):
    """Fornece endpoints de apenas leitura para os registros de limpeza.

    Permite que administradores consultem o histórico de limpezas de todas
    as salas, com suporte a filtros.
    """
    queryset = LimpezaRegistro.objects.all()
    serializer_class = LimpezaRegistroSerializer
    permission_classes = [IsAdminUser]
    filterset_class = LimpezaRegistroFilter

    def get_queryset(self):
        """Otimiza a consulta principal para evitar o problema N+1.

        Pré-carrega os dados da sala e do funcionário responsável associados
        a cada registro para tornar a listagem mais eficiente.

        Returns:
            QuerySet: O conjunto de dados otimizado para o ViewSet.
        """
        return LimpezaRegistro.objects.select_related('sala', 'funcionario_responsavel').all()