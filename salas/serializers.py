from rest_framework import serializers
from .models import Sala, LimpezaRegistro
from django.contrib.auth.models import User
from django.utils import timezone


class BasicUserSerializer(serializers.ModelSerializer):
    """Serializa informações básicas de um usuário.

    É utilizado como um campo aninhado em outros serializers para representar
    um usuário de forma concisa, expondo apenas seu ID e nome de usuário.
    """
    class Meta:
        model = User
        fields = ['id', 'username']


class SalaSerializer(serializers.ModelSerializer):
    """Serializa os dados do modelo Sala para a API."""
    responsaveis = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.filter(groups__name='Zeladoria'),
        required=False
    )
    status_limpeza = serializers.SerializerMethodField()
    ultima_limpeza_data_hora = serializers.DateTimeField(source='ultima_limpeza_fim', read_only=True)
    ultima_limpeza_funcionario = serializers.CharField(source='ultimo_funcionario', read_only=True)

    class Meta:
        model = Sala
        fields = ['id', 'qr_code_id', 'nome_numero', 'capacidade', 'validade_limpeza_horas', 'descricao', 'instrucoes',
                  'localizacao', 'ativa',
                  'responsaveis', 'status_limpeza', 'ultima_limpeza_data_hora', 'ultima_limpeza_funcionario']
        read_only_fields = ['id', 'qr_code_id']

    def to_representation(self, instance):
        """Customiza a representação de saída da sala.

        Este método sobrescreve o comportamento padrão para substituir a lista
        de IDs de responsáveis por uma lista de objetos de usuário serializados
        com `BasicUserSerializer`.

        Args:
            instance (Sala): A instância de Sala a ser representada.

        Returns:
            dict: A representação customizada do objeto Sala.
        """
        representation = super().to_representation(instance)
        representation['responsaveis'] = BasicUserSerializer(instance.responsaveis.all(), many=True).data
        return representation

    def get_status_limpeza(self, obj):
        """Calcula o status da limpeza com base no último registro."""
        if hasattr(obj, 'limpeza_em_andamento'):
            if obj.limpeza_em_andamento:
                return "Em Limpeza"

            ultimo_fim_limpeza = obj.ultima_limpeza_fim
        else:  # Fallback
            ultimo_registro = obj.registros_limpeza.first()
            if ultimo_registro and not ultimo_registro.data_hora_fim:
                return "Em Limpeza"
            ultimo_fim_limpeza = ultimo_registro.data_hora_fim if ultimo_registro else None

        if ultimo_fim_limpeza:
            validade_em_segundos = obj.validade_limpeza_horas * 3600
            tempo_decorrido = (timezone.now() - ultimo_fim_limpeza).total_seconds()
            if tempo_decorrido < validade_em_segundos:
                return "Limpa"
        return "Limpeza Pendente"

    def get_ultima_limpeza_data_hora(self, obj):
        """
        Obtém a data da última limpeza, usando o campo anotado se disponível,
        ou fazendo a query como fallback.
        """
        if hasattr(obj, 'ultima_limpeza_anotada'):
            dt = obj.ultima_limpeza_anotada
            return dt.isoformat().replace('+00:00', 'Z') if dt else None

        # Fallback
        ultimo_registro = obj.registros_limpeza.first()
        if ultimo_registro:
            return ultimo_registro.data_hora_limpeza.isoformat() + 'Z'
        return None

    def get_ultima_limpeza_funcionario(self, obj):
        """
        Obtém o funcionário da última limpeza, usando o campo anotado se
        disponível, ou fazendo a query como fallback.
        """
        if hasattr(obj, 'funcionario_anotado'):
            return obj.funcionario_anotado

        # Fallback
        ultimo_registro = obj.registros_limpeza.first()
        if ultimo_registro and ultimo_registro.funcionario_responsavel:
            return ultimo_registro.funcionario_responsavel.username
        return None



class LimpezaRegistroSerializer(serializers.ModelSerializer):
    """Serializa os dados do modelo LimpezaRegistro para a API.

    Facilita a leitura dos dados ao incluir representações aninhadas para
    o funcionário responsável e o nome da sala associada ao registro.
    """
    funcionario_responsavel = BasicUserSerializer(read_only=True)
    sala_nome = serializers.CharField(source='sala.nome_numero', read_only=True)

    class Meta:
        model = LimpezaRegistro
        # --- Campos atualizados para refletir o modelo ---
        fields = ['id', 'sala', 'sala_nome', 'data_hora_inicio', 'data_hora_fim', 'funcionario_responsavel',
                  'observacoes']
        # read_only_fields = ['data_hora_limpeza', 'funcionario_responsavel']