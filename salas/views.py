from rest_framework import viewsets, status, parsers, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from django.db.models import OuterRef, Subquery, Exists
from .models import Sala, LimpezaRegistro, RelatorioSalaSuja, FotoLimpeza
from .filters import SalaFilter, LimpezaRegistroFilter
from .serializers import SalaSerializer, LimpezaRegistroSerializer, FotoLimpezaSerializer
from core.permissions import IsAdminUser, IsZeladorUser, IsSolicitanteServicosUser


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
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

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
        elif self.action == 'marcar_como_suja':
            permission_classes = [IsSolicitanteServicosUser]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Otimiza a consulta principal do ViewSet para evitar o problema N+1."""

        ultimos_registros_concluidos = LimpezaRegistro.objects.filter(
            sala=OuterRef('pk'),
            data_hora_fim__isnull=False
        ).order_by('-data_hora_fim')

        ultimos_relatorios_suja = RelatorioSalaSuja.objects.filter(
            sala=OuterRef('pk')
        ).order_by('-data_hora')

        queryset = Sala.objects.prefetch_related('responsaveis').annotate(
            ultima_limpeza_fim=Subquery(
                ultimos_registros_concluidos.values('data_hora_fim')[:1]
            ),
            ultimo_funcionario=Subquery(
                ultimos_registros_concluidos.values('funcionario_responsavel__username')[:1]
            ),
            limpeza_em_andamento=Exists(
                LimpezaRegistro.objects.filter(sala=OuterRef('pk'), data_hora_fim__isnull=True)
            ),
            ultimo_relatorio_suja_data=Subquery(
                ultimos_relatorios_suja.values('data_hora')[:1]
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

        # Regra de negócio: Verifica se pelo menos uma foto foi enviada
        if not registro_aberto.fotos.exists():
            return Response({'detail': 'É necessário enviar pelo menos uma foto antes de concluir a limpeza.'},
                            status=status.HTTP_400_BAD_REQUEST)

        registro_aberto.data_hora_fim = timezone.now()
        registro_aberto.observacoes = request.data.get('observacoes', registro_aberto.observacoes)
        registro_aberto.save()

        if sala.data_notificacao_pendencia:
            sala.data_notificacao_pendencia = None
            sala.save(update_fields=['data_notificacao_pendencia'])

        serializer = LimpezaRegistroSerializer(registro_aberto)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsSolicitanteServicosUser], parser_classes=[parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser])
    def marcar_como_suja(self, request, qr_code_id=None):
        """Cria um relatório de sala suja para uma sala específica."""
        sala = self.get_object()
        if not sala.ativa:
            return Response(
                {'detail': 'Não é possível reportar uma sala inativa.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        relatorio = RelatorioSalaSuja.objects.create(
            sala=sala,
            reportado_por=request.user,
            observacoes=request.data.get('observacoes', '')
        )
        return Response(
            {'status': 'Relatório de sala suja enviado com sucesso.'},
            status=status.HTTP_201_CREATED
        )

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
        """
        Otimiza a consulta principal para evitar o problema N+1, pré-carregando
        os dados da sala, do funcionário e das fotos associadas.
        """
        return LimpezaRegistro.objects.select_related(
            'sala', 'funcionario_responsavel'
        ).prefetch_related('fotos')


class FotoLimpezaViewSet(mixins.CreateModelMixin,
                         mixins.ListModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.DestroyModelMixin,
                         viewsets.GenericViewSet):
    """
    ViewSet para gerenciar fotos de limpeza.
    - Zeladores podem criar (fazer upload) de novas fotos.
    - Zeladores podem listar, ver e deletar APENAS as suas próprias fotos.
    - Administradores podem listar, ver e deletar TODAS as fotos.
    """
    serializer_class = FotoLimpezaSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get_permissions(self):
        """Define permissões mais granulares por ação."""
        if self.action == 'create':
            # Apenas zeladores podem criar fotos
            return [IsZeladorUser()]
        # Para outras ações (list, retrieve, destroy), administradores ou o próprio zelador podem
        return [IsAuthenticated()]  # A lógica de quem pode ver o quê fica no get_queryset

    def get_queryset(self):
        """
        Filtra o queryset:
        - Se for admin, retorna todas as fotos.
        - Se não for, retorna apenas as fotos do usuário autenticado.
        """
        user = self.request.user
        if user.is_superuser:
            return FotoLimpeza.objects.all()  # Admin vê tudo

        # Zelador comum vê apenas o que é seu
        return FotoLimpeza.objects.filter(registro_limpeza__funcionario_responsavel=user)

    def create(self, request, *args, **kwargs):
        """
        Cria uma nova foto associada a um registro de limpeza em aberto.
        """
        registro_id = request.data.get('registro_limpeza')
        imagem = request.data.get('imagem')

        if not registro_id or not imagem:
            return Response({'detail': 'Os campos "registro_limpeza" (ID) e "imagem" são obrigatórios.'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            registro = LimpezaRegistro.objects.get(pk=registro_id, funcionario_responsavel=request.user)
        except LimpezaRegistro.DoesNotExist:
            return Response({'detail': 'Registro de limpeza não encontrado ou não pertence a você.'},
                            status=status.HTTP_404_NOT_FOUND)

        if registro.data_hora_fim is not None:
            return Response({'detail': 'Esta limpeza já foi concluída e não aceita mais fotos.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if registro.fotos.count() >= 3:
            return Response({'detail': 'Limite de 3 fotos por registro de limpeza atingido.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Prepara os dados para o serializador
        serializer_data = {
            'registro_limpeza': registro.id,
            'imagem': imagem
        }
        serializer = self.get_serializer(data=serializer_data)
        serializer.is_valid(raise_exception=True)
        # O serializer.save() agora tem todos os dados necessários
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
