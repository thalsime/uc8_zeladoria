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
    """Serializa os dados do modelo Sala para a API.

    Além dos campos do modelo, inclui campos calculados em tempo real, como
    o status da limpeza, a data do último registro e o funcionário responsável,
    e customiza a representação dos responsáveis.
    """
    status_limpeza = serializers.SerializerMethodField()
    ultima_limpeza_data_hora = serializers.SerializerMethodField()
    ultima_limpeza_funcionario = serializers.SerializerMethodField()
    responsaveis = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.filter(groups__name='Zeladoria'),
        required=False
    )

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
        """Calcula o status de limpeza da sala com base no último registro.

        Compara o tempo decorrido desde a última limpeza com o campo
        `validade_limpeza_horas` da própria sala para determinar seu estado.

        Args:
            obj (Sala): A instância de Sala a ser avaliada.

        Returns:
            str: "Limpa" ou "Limpeza Pendente".
        """
        ultimo_registro = obj.registros_limpeza.first()
        if ultimo_registro:
            validade_em_segundos = obj.validade_limpeza_horas * 3600
            tempo_decorrido = (timezone.now() - ultimo_registro.data_hora_limpeza).total_seconds()
            if tempo_decorrido < validade_em_segundos:
                return "Limpa"
        return "Limpeza Pendente"

    def get_ultima_limpeza_data_hora(self, obj):
        """Obtém a data e hora do último registro de limpeza da sala.

        Args:
            obj (Sala): A instância de Sala a ser avaliada.

        Returns:
            str or None: A data como uma string no formato ISO 8601 (UTC) ou
            `None` se não houver registros.
        """
        ultimo_registro = obj.registros_limpeza.first()
        if ultimo_registro:
            return ultimo_registro.data_hora_limpeza.isoformat() + 'Z'
        return None

    def get_ultima_limpeza_funcionario(self, obj):
        """Obtém o nome de usuário do funcionário do último registro de limpeza.

        Args:
            obj (Sala): A instância de Sala a ser avaliada.

        Returns:
            str or None: O `username` do funcionário ou `None` se não houver
            registro ou funcionário associado.
        """
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
        fields = ['id', 'sala', 'sala_nome', 'data_hora_limpeza', 'funcionario_responsavel', 'observacoes']
        read_only_fields = ['data_hora_limpeza', 'funcionario_responsavel']