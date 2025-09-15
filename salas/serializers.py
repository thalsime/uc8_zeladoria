from rest_framework import serializers
from .models import Sala, LimpezaRegistro, RelatorioSalaSuja, FotoLimpeza
from django.contrib.auth.models import User
from django.utils import timezone


# class BasicUserSerializer(serializers.ModelSerializer):
#     """Serializa informações básicas de um usuário.
#
#     É utilizado como um campo aninhado em outros serializers para representar
#     um usuário de forma concisa, expondo apenas seu ID e nome de usuário.
#     """
#     class Meta:
#         model = User
#         fields = ['id', 'username']


class SalaSerializer(serializers.ModelSerializer):
    """Serializa os dados do modelo Sala para a API."""
    responsaveis = serializers.SlugRelatedField(
        many=True,
        slug_field='username',  # O campo do modelo User que queremos usar
        queryset=User.objects.filter(groups__name='Zeladoria'),
        required=False
    )
    status_limpeza = serializers.SerializerMethodField()
    ultima_limpeza_data_hora = serializers.DateTimeField(source='ultima_limpeza_fim', read_only=True)
    ultima_limpeza_funcionario = serializers.CharField(source='ultimo_funcionario', read_only=True)

    class Meta:
        model = Sala
        fields = ['id', 'qr_code_id', 'nome_numero', 'capacidade', 'validade_limpeza_horas', 'descricao', 'instrucoes',
                  'localizacao', 'ativa', 'imagem',
                  'responsaveis', 'status_limpeza', 'ultima_limpeza_data_hora', 'ultima_limpeza_funcionario']
        read_only_fields = ['id', 'qr_code_id']

    # def to_representation(self, instance):
    #     """Customiza a representação de saída da sala.
    #
    #     Este método sobrescreve o comportamento padrão para substituir a lista
    #     de IDs de responsáveis por uma lista de objetos de usuário serializados
    #     com `BasicUserSerializer`.
    #
    #     Args:
    #         instance (Sala): A instância de Sala a ser representada.
    #
    #     Returns:
    #         dict: A representação customizada do objeto Sala.
    #     """
    #     representation = super().to_representation(instance)
    #     representation['responsaveis'] = BasicUserSerializer(instance.responsaveis.all(), many=True).data
    #     return representation

    def get_status_limpeza(self, obj):
        if obj.limpeza_em_andamento:
            return "Em Limpeza"

        if obj.ultimo_relatorio_suja_data and (
                not obj.ultima_limpeza_fim or obj.ultimo_relatorio_suja_data > obj.ultima_limpeza_fim):
            return "Suja"

        if obj.ultima_limpeza_fim:
            validade_em_segundos = obj.validade_limpeza_horas * 3600
            tempo_decorrido = (timezone.now() - obj.ultima_limpeza_fim).total_seconds()
            if tempo_decorrido < validade_em_segundos:
                return "Limpa"

        return "Limpeza Pendente"

    # def get_ultima_limpeza_data_hora(self, obj):
    #     """
    #     Obtém a data da última limpeza, usando o campo anotado se disponível,
    #     ou fazendo a query como fallback.
    #     """
    #     if hasattr(obj, 'ultima_limpeza_anotada'):
    #         dt = obj.ultima_limpeza_anotada
    #         return dt.isoformat().replace('+00:00', 'Z') if dt else None
    #
    #     # Fallback
    #     ultimo_registro = obj.registros_limpeza.first()
    #     if ultimo_registro:
    #         return ultimo_registro.data_hora_limpeza.isoformat() + 'Z'
    #     return None
    #
    # def get_ultima_limpeza_funcionario(self, obj):
    #     """
    #     Obtém o funcionário da última limpeza, usando o campo anotado se
    #     disponível, ou fazendo a query como fallback.
    #     """
    #     if hasattr(obj, 'funcionario_anotado'):
    #         return obj.funcionario_anotado
    #
    #     # Fallback
    #     ultimo_registro = obj.registros_limpeza.first()
    #     if ultimo_registro and ultimo_registro.funcionario_responsavel:
    #         return ultimo_registro.funcionario_responsavel.username
    #     return None


class FotoLimpezaSerializer(serializers.ModelSerializer):
    """Serializa os dados da imagem de uma limpeza."""
    registro_limpeza = serializers.PrimaryKeyRelatedField(
        queryset=LimpezaRegistro.objects.all(), write_only=True
    )

    class Meta:
        model = FotoLimpeza
        fields = ['id', 'imagem', 'timestamp', 'registro_limpeza']


class LimpezaRegistroSerializer(serializers.ModelSerializer):
    """Serializa os dados do modelo LimpezaRegistro para a API.

    Facilita a leitura dos dados ao incluir representações aninhadas para
    o funcionário responsável e o nome da sala associada ao registro.
    """
    funcionario_responsavel = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )
    sala_nome = serializers.CharField(source='sala.nome_numero', read_only=True)
    fotos = FotoLimpezaSerializer(many=True, read_only=True)
    sala = serializers.SlugRelatedField(
        slug_field='qr_code_id',
        queryset=Sala.objects.all()
    )

    class Meta:
        model = LimpezaRegistro
        fields = ['id', 'sala', 'sala_nome', 'data_hora_inicio', 'data_hora_fim',
                  'funcionario_responsavel', 'observacoes', 'fotos']
