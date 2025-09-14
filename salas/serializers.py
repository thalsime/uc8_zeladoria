from rest_framework import serializers
from .models import Sala, LimpezaRegistro, RelatorioSalaSuja
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
                  'localizacao', 'ativa', 'imagem',
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

    # --- LÓGICA DE STATUS COMPLETAMENTE ATUALIZADA ---
    def get_status_limpeza(self, obj):
        """
        Calcula o status da limpeza com base na ordem dos eventos.
        A lógica de status segue a seguinte prioridade:
        1. Se um relatório de "suja" é o evento mais recente, o status é "Suja".
        2. Se uma limpeza está em andamento, o status é "Em Limpeza".
        3. Se a última limpeza concluída ainda é válida, o status é "Limpa".
        4. Caso contrário, o status é "Limpeza Pendente".
        """
        # Usa os valores pré-calculados (anotados) da view se disponíveis
        if hasattr(obj, 'limpeza_em_andamento'):
            limpeza_em_andamento = obj.limpeza_em_andamento
            ultimo_fim_limpeza = obj.ultima_limpeza_fim
            ultimo_relatorio_suja = obj.ultimo_relatorio_suja_data
        else:  # Fallback para create/update/retrieve (menos performático)
            ultimo_registro = obj.registros_limpeza.first()
            limpeza_em_andamento = ultimo_registro and not ultimo_registro.data_hora_fim
            ultimo_fim_limpeza = ultimo_registro.data_hora_fim if ultimo_registro else None
            ultimo_relatorio_obj = obj.relatorios_suja.first()
            ultimo_relatorio_suja = ultimo_relatorio_obj.data_hora if ultimo_relatorio_obj else None

        # Lógica de prioridade
        if limpeza_em_andamento:
            return "Em Limpeza"

        # Compara a data do último relatório sujo com a da última limpeza concluída
        if ultimo_relatorio_suja and (not ultimo_fim_limpeza or ultimo_relatorio_suja > ultimo_fim_limpeza):
            return "Suja"

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