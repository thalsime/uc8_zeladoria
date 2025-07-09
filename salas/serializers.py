"""
Módulo de Serializers para a aplicação de gerenciamento de salas.

Define os serializadores que convertem objetos Python (modelos) em formatos de dados
(JSON, XML, etc.) e vice-versa para a API RESTful. Inclui serializadores para
usuários básicos, salas e registros de limpeza, com campos calculados e aninhados.
"""

from rest_framework import serializers
from .models import Sala, LimpezaRegistro
from django.contrib.auth.models import User
from django.utils import timezone

class BasicUserSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para o modelo User.

    Utilizado para representar informações básicas de um usuário, como ID e username,
    em outros serializadores, evitando a exposição de dados sensíveis ou desnecessários.

    :ivar id: ID único do usuário.
    :ivar username: Nome de usuário do usuário.
    """
    class Meta:
        model = User
        fields = ['id', 'username']

class SalaSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Sala.

    Converte instâncias do modelo Sala em representações JSON e permite a criação/atualização.
    Inclui campos personalizados para status de limpeza, data/hora da última limpeza
    e o funcionário responsável pela última limpeza, que são calculados dinamicamente.

    :ivar status_limpeza: Estado atual da limpeza da sala ("Limpa" ou "Limpeza Pendente").
    :ivar ultima_limpeza_data_hora: Data e hora do último registro de limpeza.
    :ivar ultima_limpeza_funcionario: Nome de usuário do funcionário que realizou a última limpeza.
    """
    status_limpeza = serializers.SerializerMethodField()
    ultima_limpeza_data_hora = serializers.SerializerMethodField()
    ultima_limpeza_funcionario = serializers.SerializerMethodField()

    class Meta:
        model = Sala
        fields = ['id', 'nome_numero', 'capacidade', 'descricao', 'localizacao',
                  'status_limpeza', 'ultima_limpeza_data_hora', 'ultima_limpeza_funcionario']

    def get_status_limpeza(self, obj):
        """
        Calcula e retorna o status de limpeza de uma sala.

        A lógica atual define a sala como "Limpa" se o último registro de limpeza
        tiver ocorrido há menos de 4 horas (14400 segundos). Caso contrário,
        a sala é considerada "Limpeza Pendente".

        :param obj: A instância :class:`Sala` da qual obter o status.
        :type obj: :class:`~salas.models.Sala`
        :returns: O status de limpeza da sala ("Limpa" ou "Limpeza Pendente").
        :rtype: str
        """
        ultimo_registro = obj.registros_limpeza.first()
        if ultimo_registro:
            # TODO: Revisar lógica de tempo para determinar "pendente"
            # Se intervalo entre agora e ultima limpeza menor que 4 horas, Limpa.
            if (timezone.now() - ultimo_registro.data_hora_limpeza).seconds < 14400:
                return "Limpa"
        return "Limpeza Pendente"

    def get_ultima_limpeza_data_hora(self, obj):
        """
        Retorna a data e hora do último registro de limpeza da sala.

        A data e hora são retornadas no formato ISO 8601 com o sufixo 'Z' para indicar UTC.

        :param obj: A instância :class:`Sala` da qual obter a data/hora da última limpeza.
        :type obj: :class:`~salas.models.Sala`
        :returns: Data e hora da última limpeza como string ISO 8601 (UTC), ou :obj:`None` se não houver registros.
        :rtype: str or None
        """
        ultimo_registro = obj.registros_limpeza.first()
        if ultimo_registro:
            # Apenas retorna o objeto datetime, DRF o serializará para ISO 8601 (UTC) por padrão.
            # Não precisa de strftime aqui se você quer o formato ISO 8601 padrão do DRF.
            # Se quiser manter o strftime para um formato específico, use:
            return ultimo_registro.data_hora_limpeza.isoformat() + 'Z' # Para garantir 'Z' para UTC
            # Ou o formato anterior, mas ciente de que será o horário UTC:
            #return ultimo_registro.data_hora_limpeza.strftime('%Y-%m-%d %H:%M:%S')  # <-- Este será o horário UTC
        return None

    def get_ultima_limpeza_funcionario(self, obj):
        """
        Retorna o nome de usuário do funcionário responsável pela última limpeza da sala.

        :param obj: A instância :class:`Sala` da qual obter o funcionário da última limpeza.
        :type obj: :class:`~salas.models.Sala`
        :returns: Nome de usuário do funcionário, ou :obj:`None` se não houver registro ou funcionário associado.
        :rtype: str or None
        """
        ultimo_registro = obj.registros_limpeza.first()
        if ultimo_registro and ultimo_registro.funcionario_responsavel:
            return ultimo_registro.funcionario_responsavel.username
        return None

class LimpezaRegistroSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo LimpezaRegistro.

    Converte instâncias do modelo LimpezaRegistro em representações JSON.
    Inclui campos aninhados para o funcionário responsável e um campo derivado
    para o nome da sala, facilitando a leitura dos registros.

    :ivar funcionario_responsavel: Serializer aninhado para o funcionário que realizou a limpeza.
    :ivar sala_nome: Nome e número da sala associada ao registro de limpeza.
    """
    funcionario_responsavel = BasicUserSerializer(read_only=True)
    sala_nome = serializers.CharField(source='sala.nome_numero', read_only=True)

    class Meta:
        model = LimpezaRegistro
        fields = ['id', 'sala', 'sala_nome', 'data_hora_limpeza', 'funcionario_responsavel', 'observacoes']
        read_only_fields = ['data_hora_limpeza', 'funcionario_responsavel']

    # def to_representation(self, instance):
    #     representation = super().to_representation(instance)
    #     # Converte para o fuso horário local antes de formatar, se for timezone-aware
    #     if instance.data_hora_limpeza and timezone.is_aware(instance.data_hora_limpeza):
    #         local_time = timezone.localtime(instance.data_hora_limpeza)
    #         representation['data_hora_limpeza'] = local_time.strftime('%Y-%m-%d %H:%M:%S')
    #     return representation