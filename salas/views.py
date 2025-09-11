from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
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
        elif self.action == 'marcar_como_limpa':
            permission_classes = [IsZeladorUser]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Otimiza a consulta principal do ViewSet para evitar o problema N+1.

        Pré-carrega os dados relacionados dos registros de limpeza e dos
        responsáveis para reduzir o número de acessos ao banco de dados ao
        listar as salas.

        Returns:
            QuerySet: O conjunto de dados otimizado para o ViewSet.
        """
        return Sala.objects.prefetch_related('registros_limpeza__funcionario_responsavel', 'responsaveis').all()

    @action(detail=True, methods=['post'])
    def marcar_como_limpa(self, request, qr_code_id=None):
        """Cria um novo registro de limpeza para uma sala específica.

        Esta ação é acionada via POST e está disponível apenas para o grupo
        'Zeladoria'. A sala deve estar ativa para que a limpeza seja registrada.

        Args:
            request (Request): O objeto da requisição HTTP.
            qr_code_id (str): O UUID da sala a ser marcada como limpa.

        Returns:
            Response: Uma resposta com os dados do novo registro de limpeza
                ou uma mensagem de erro.
        """
        sala = self.get_object()
        if not sala.ativa:
            return Response(
                {'detail': 'Esta sala não está ativa e não pode ser marcada como limpa.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        observacoes = request.data.get('observacoes', '')
        registro_limpeza = LimpezaRegistro.objects.create(
            sala=sala,
            funcionario_responsavel=request.user,
            observacoes=observacoes
        )
        serializer = LimpezaRegistroSerializer(registro_limpeza)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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