from rest_framework import serializers
from .models import Notificacao

class RelativeImageField(serializers.ImageField):
    """
    Um campo de imagem customizado que serializa a imagem para sua URL relativa,
    em vez da URL absoluta padrão.
    """
    def to_representation(self, value):
        if not value:
            return None
        # Retorna apenas o caminho relativo (ex: /media/sala_pics/imagem.jpg)
        return value.url


class NotificacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacao
        fields = ['id', 'mensagem', 'link', 'data_criacao', 'lida']