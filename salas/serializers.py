from rest_framework import serializers
from .models import Sala, LimpezaRegistro, FotoLimpeza, RelatorioSalaSuja
from django.contrib.auth.models import User
from django.utils import timezone
from core.serializers import RelativeImageField


class RelatorioSalaSujaSerializer(serializers.ModelSerializer):
    """
    Serializa os dados essenciais de um relatório de sala suja para aninhamento.
    """
    reportado_por = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = RelatorioSalaSuja
        fields = ['data_hora', 'reportado_por', 'observacoes']


class SalaSerializer(serializers.ModelSerializer):
    """Serializa os dados do modelo Sala para a API."""
    responsaveis = serializers.SlugRelatedField(
        many=True,
        slug_field='username',
        queryset=User.objects.filter(groups__name='Zeladoria'),
        required=False
    )
    status_limpeza = serializers.SerializerMethodField()
    ultima_limpeza_data_hora = serializers.DateTimeField(source='ultima_limpeza_fim', read_only=True)
    ultima_limpeza_funcionario = serializers.CharField(source='ultimo_funcionario', read_only=True)
    ativa = serializers.BooleanField(required=False, allow_null=True, default=None)
    imagem = RelativeImageField(required=False, allow_null=True)
    detalhes_suja = serializers.SerializerMethodField()

    class Meta:
        model = Sala
        fields = [
            'id', 'qr_code_id', 'nome_numero', 'capacidade', 'validade_limpeza_horas', 'descricao', 'instrucoes',
            'localizacao', 'ativa', 'imagem', 'responsaveis', 'status_limpeza', 'ultima_limpeza_data_hora',
            'ultima_limpeza_funcionario', 'detalhes_suja'
        ]
        read_only_fields = [
            'id', 'qr_code_id', 'status_limpeza', 'ultima_limpeza_data_hora', 'ultima_limpeza_funcionario',
            'detalhes_suja'
        ]

    def to_internal_value(self, data):
        """
        Sobrescreve o método de conversão de dados para tratar o caso de
        remoção de todos os responsáveis via multipart/form-data.

        Quando um campo `responsaveis` é enviado com um valor vazio em uma
        requisição form-data, ele é interpretado como `['']`. Este método
        intercepta essa condição específica e a converte para uma lista vazia `[]`,
        permitindo que a validação prossiga e a relação ManyToMany seja limpa
        corretamente.

        Args:
            data (QueryDict): Os dados brutos da requisição.

        Returns:
            dict: Os dados processados e prontos para validação.
        """
        if 'responsaveis' in data:
            responsaveis_list = data.getlist('responsaveis')

            if len(responsaveis_list) == 1 and responsaveis_list[0] == '':
                mutable_data = data.copy()
                mutable_data.setlist('responsaveis', [])
                data = mutable_data

        return super().to_internal_value(data)

    def create(self, validated_data):
        """
        Customiza a criação da Sala para lidar com o campo 'ativa'.
        Se 'ativa' não for explicitamente enviado (resultando em None),
        removemos a chave para permitir que o modelo Django aplique o valor padrão.
        """
        ativa_value = validated_data.get('ativa')

        if ativa_value is None:
            validated_data.pop('ativa', None)

        return super().create(validated_data)

    def get_status_limpeza(self, obj):
        if hasattr(obj, 'limpeza_em_andamento'):
            if obj.limpeza_em_andamento:
                return "Em Limpeza"
        elif obj.registros_limpeza.filter(data_hora_fim__isnull=True).exists():
            return "Em Limpeza"

        ultima_limpeza_fim = getattr(obj, 'ultima_limpeza_fim',
                                     obj.registros_limpeza.filter(data_hora_fim__isnull=False).order_by(
                                         '-data_hora_fim').values_list('data_hora_fim', flat=True).first())

        ultimo_relatorio_suja_data = getattr(obj, 'ultimo_relatorio_suja_data',
                                             obj.relatorios_suja.order_by('-data_hora').values_list('data_hora',
                                                                                                    flat=True).first())

        if ultimo_relatorio_suja_data and (not ultima_limpeza_fim or ultimo_relatorio_suja_data > ultima_limpeza_fim):
            return "Suja"

        if ultima_limpeza_fim:
            validade_em_segundos = obj.validade_limpeza_horas * 3600
            tempo_decorrido = (timezone.now() - ultima_limpeza_fim).total_seconds()
            if tempo_decorrido < validade_em_segundos:
                return "Limpa"

        return "Limpeza Pendente"

    # ========= INÍCIO DA CORREÇÃO =========
    def get_detalhes_suja(self, obj: Sala) -> dict | None:
        """
        Retorna os detalhes do último relatório de sujeira se a sala estiver
        efetivamente no estado 'SUJA'. Caso contrário, retorna null.
        """
        # Replicamos a mesma lógica de consulta de 'get_status_limpeza'
        # para garantir consistência sem causar erros.
        ultima_limpeza_fim = getattr(obj, 'ultima_limpeza_fim',
                                     obj.registros_limpeza.filter(data_hora_fim__isnull=False).order_by(
                                         '-data_hora_fim').values_list('data_hora_fim', flat=True).first())

        ultimo_relatorio_suja = obj.relatorios_suja.order_by('-data_hora').first()

        if ultimo_relatorio_suja:
            ultimo_relatorio_suja_data = ultimo_relatorio_suja.data_hora
            # A condição exata que define o status "Suja".
            if not ultima_limpeza_fim or ultimo_relatorio_suja_data > ultima_limpeza_fim:
                # Se a condição for atendida, serializamos e retornamos os detalhes.
                return RelatorioSalaSujaSerializer(ultimo_relatorio_suja).data

        # Para qualquer outra condição, o valor é null.
        return None
    # ========= FIM DA CORREÇÃO =========


class FotoLimpezaSerializer(serializers.ModelSerializer):
    """Serializa os dados da imagem de uma limpeza."""
    registro_limpeza = serializers.PrimaryKeyRelatedField(
        queryset=LimpezaRegistro.objects.all(), write_only=True
    )
    imagem = RelativeImageField()

    class Meta:
        model = FotoLimpeza
        fields = ['id', 'imagem', 'timestamp', 'registro_limpeza']


class LimpezaRegistroSerializer(serializers.ModelSerializer):
    """Serializa os dados do modelo LimpezaRegistro para a API."""
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
