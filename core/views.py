from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Notificacao
from .serializers import NotificacaoSerializer

class NotificacaoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para listar e gerenciar notificações do usuário logado.
    """
    serializer_class = NotificacaoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retorna apenas as notificações do usuário autenticado."""
        return self.request.user.notificacoes.all()

    @action(detail=False, methods=['post'])
    def marcar_todas_como_lidas(self, request):
        """Marca todas as notificações não lidas do usuário como lidas."""
        self.get_queryset().filter(lida=False).update(lida=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def marcar_como_lida(self, request, pk=None):
        """Marca uma notificação específica como lida."""
        notificacao = self.get_object()
        notificacao.lida = True
        notificacao.save(update_fields=['lida'])
        return Response(status=status.HTTP_204_NO_CONTENT)