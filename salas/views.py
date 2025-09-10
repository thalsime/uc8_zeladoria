"""
Módulo de Views para a aplicação Salas.

Define os ViewSets que lidam com as operações da API para salas e registros de limpeza.
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Sala, LimpezaRegistro
from .serializers import SalaSerializer, LimpezaRegistroSerializer
from core.permissions import IsAdminUser, IsZeladorUser, IsCorpoDocenteUser

class SalaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para a API de Salas.

    Fornece operações CRUD (Criar, Ler, Atualizar, Deletar) para salas,
    além de ações personalizadas como marcar uma sala como limpa.

    :ivar queryset: :class:`~django.db.models.QuerySet` O conjunto de objetos :class:`~salas.models.Sala`
                    a serem utilizados pelo ViewSet, ordenados por nome/número.
    :ivar serializer_class: :class:`~rest_framework.serializers.Serializer` O serializer padrão
                            para o ViewSet (:class:`~salas.serializers.SalaSerializer`).
    """
    queryset = Sala.objects.all().order_by('nome_numero')
    serializer_class = SalaSerializer
    # A linha 'permission_classes = [IsAuthenticated]' foi removida daqui,
    # pois as permissões agora são definidas dinamicamente no método get_permissions.

    def get_permissions(self):
        """
        Define as permissões de acesso para cada ação do ViewSet de forma granular
        baseado em grupos de usuários.

        Permissões:
            - Apenas administradores (`IsAdminUser`) podem criar (`create`), atualizar
              (`update`, `partial_update`) ou deletar (`destroy`) salas.
            - Apenas usuários do grupo Zeladoria (`IsZeladorUser`) podem marcar uma
              sala como limpa (`marcar_como_limpa`).
            - Qualquer usuário autenticado (`IsAuthenticated`) pode listar (`list`) e
              recuperar detalhes (`retrieve`) de salas.

        :returns: Uma lista de instâncias de classes de permissão.
        :rtype: list
        """
        # Ações de escrita e gerenciamento de salas são restritas a Admins.
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]

        # A ação principal da equipe de limpeza.
        elif self.action == 'marcar_como_limpa':
            permission_classes = [IsZeladorUser]

        # Ações de leitura são permitidas para qualquer usuário logado.
        elif self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]

        # Como padrão, para qualquer outra ação futura, exigimos permissão de Admin.
        # Isso garante que novos endpoints não fiquem abertos acidentalmente.
        else:
            permission_classes = [IsAdminUser]

        return [permission() for permission in permission_classes]


    def get_queryset(self):
        """
        Sobrescreve o queryset base para permitir filtragem de salas.

        Permite filtrar as salas por localização exata e por status de limpeza,
        conforme determinado por uma lógica de tempo no serializador.

        :param self: A instância do ViewSet.
        :type self: :class:`SalaViewSet`
        :query_param localizacao: Opcional. Filtra salas por uma localização exata (case-insensitive).
        :type localizacao: str
        :query_param status_limpeza: Opcional. Filtra salas por status de limpeza ('Limpa' ou 'Limpeza Pendente').
        :type status_limpeza: str
        :returns: Um QuerySet de objetos :class:`~salas.models.Sala` filtrados.
        :rtype: :class:`~django.db.models.QuerySet`
        """
        queryset = super().get_queryset()
        localizacao = self.request.query_params.get('localizacao')
        status_limpeza_filter = self.request.query_params.get('status_limpeza')

        if localizacao:
            queryset = queryset.filter(localizacao__iexact=localizacao)

        if status_limpeza_filter:
            # Reavalia o status de limpeza para cada sala no queryset
            # Pode ser ineficiente para muitos registros, considerar otimização se necessário.
            if status_limpeza_filter.lower() == 'limpa':
                return [sala for sala in queryset if sala.status_limpeza == "Limpa"]
            elif status_limpeza_filter.lower() == 'limpeza pendente':
                return [sala for sala in queryset if sala.status_limpeza == "Limpeza Pendente"]
            else:
                # Retorna queryset vazio ou erro se o status for inválido
                return []
        return queryset

    # A linha 'permission_classes=[IsAuthenticated]' foi removida do decorador @action,
    # pois a permissão agora é gerenciada centralmente em get_permissions.
    @action(detail=True, methods=['post'])
    def marcar_como_limpa(self, request, pk=None):
        """
        Marca uma sala específica como limpa, criando um novo registro de limpeza.

        O registro associa a limpeza à sala e ao usuário autenticado que a realizou,
        com a opção de adicionar observações.

        :param request: O objeto da requisição HTTP, contendo dados como o usuário autenticado e observações.
        :type request: :class:`~rest_framework.request.Request`
        :param pk: A chave primária (ID) da sala a ser marcada como limpa.
        :type pk: int
        :returns: Uma resposta HTTP contendo os dados do novo registro de limpeza e um status 201 Created.
        :rtype: :class:`~rest_framework.response.Response`
        :raises Http404: Se a sala com o `pk` fornecido não for encontrada.
        :payload { "observacoes": "string" }: Corpo da requisição opcional contendo observações sobre a limpeza.
        :payloadtype observacoes: str
        """
        sala = self.get_object()

        if not sala.ativa:
            return Response(
                {'detail': 'Esta sala não está ativa e não pode ser marcada como limpa.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        observacoes = request.data.get('observacoes', '')

        # O `data_hora_limpeza` é definido automaticamente pelo modelo (auto_now_add=True)
        registro_limpeza = LimpezaRegistro.objects.create(
            sala=sala,
            funcionario_responsavel=request.user,
            observacoes=observacoes
        )
        serializer = LimpezaRegistroSerializer(registro_limpeza)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



    def destroy(self, request, *args, **kwargs):
        """
        Impede a exclusão de salas que não estão ativas.
        """
        sala = self.get_object()
        if not sala.ativa:
            return Response(
                {'detail': 'Salas inativas não podem ser excluídas. Ative a sala primeiro.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

class LimpezaRegistroViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para a API de Registros de Limpeza.

    Fornece operações de leitura (Listar, Recuperar) para registros históricos de limpeza.
    O acesso a este ViewSet é restrito apenas a usuários administradores.

    :ivar queryset: :class:`~django.db.models.QuerySet` O conjunto de objetos :class:`~salas.models.LimpezaRegistro`
                    a serem utilizados pelo ViewSet.
    :ivar serializer_class: :class:`~rest_framework.serializers.Serializer` O serializer padrão
                            para o ViewSet (:class:`~salas.serializers.LimpezaRegistroSerializer`).
    :ivar permission_classes: :class:`list` Lista de classes de permissão que controlam o acesso (apenas :class:`~rest_framework.permissions.IsAdminUser`).
    """
    queryset = LimpezaRegistro.objects.all()
    serializer_class = LimpezaRegistroSerializer
    permission_classes = [IsAdminUser] # Apenas administradores podem ver registros de limpeza

    def get_queryset(self):
        """
        Sobrescreve o queryset base para permitir filtragem de registros de limpeza por sala.

        Permite buscar registros de limpeza associados a uma sala específica através
        de um parâmetro de query.

        :param self: A instância do ViewSet.
        :type self: :class:`LimpezaRegistroViewSet`
        :query_param sala_id: Opcional. O ID da sala para filtrar os registros de limpeza.
        :type sala_id: int
        :returns: Um QuerySet de objetos :class:`~salas.models.LimpezaRegistro` filtrados.
        :rtype: :class:`~django.db.models.QuerySet`
        """
        queryset = super().get_queryset()
        sala_id = self.request.query_params.get('sala_id')
        if sala_id:
            queryset = queryset.filter(sala__id=sala_id)
        return queryset