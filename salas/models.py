"""
Módulo de Modelos para a aplicação Salas.

Define as estruturas de dados para salas e registros de limpeza,
interagindo com o banco de dados.
"""

from django.db import models
from django.contrib.auth.models import User

class Sala(models.Model):
    """
    Representa uma sala física no sistema.

    Gerencia informações como nome, capacidade e localização, e
    mantém um histórico de registros de limpeza associados.

    :ivar nome_numero: :class:`str` Nome ou número único que identifica a sala (Ex: 'Sala 101', 'Auditório Principal').
    :ivar capacidade: :class:`int` Número máximo de pessoas que a sala pode acomodar.
    :ivar descricao: :class:`str` Uma descrição opcional e detalhada sobre a sala.
    :ivar localizacao: :class:`str` Onde a sala está situada fisicamente (Ex: 'Bloco A', 'Campus Central').
    :ivar registros_limpeza: :class:`~django.db.models.fields.related.ReverseManyToOneDescriptor` Relação reversa com os
                             registros de limpeza (:class:`~salas.models.LimpezaRegistro`) associados a esta sala.
    """
    nome_numero = models.CharField(max_length=100, unique=True, verbose_name="Nome/Número")
    capacidade = models.IntegerField(verbose_name="Capacidade")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    localizacao = models.CharField(max_length=100, verbose_name="Localização")

    class Meta:
        """
        Metadados para o modelo Sala.

        Define o nome legível no plural e singular e a ordem padrão
        dos objetos :class:`Sala` nas consultas.
        """
        verbose_name = "Sala"
        verbose_name_plural = "Salas"
        ordering = ['nome_numero']

    def __str__(self):
        """
        Retorna a representação em string do objeto Sala.

        :returns: O nome/número da sala.
        :rtype: str
        """
        return self.nome_numero

class LimpezaRegistro(models.Model):
    """
    Representa um registro de uma ação de limpeza em uma sala.

    Armazena detalhes sobre quando uma sala foi limpa, por qual funcionário,
    e quaisquer observações relevantes.

    :ivar sala: :class:`~django.db.models.ForeignKey` A sala à qual este registro de limpeza está associado.
    :ivar data_hora_limpeza: :class:`~django.db.models.DateTimeField` O timestamp exato em que a limpeza foi registrada.
                             É preenchido automaticamente na criação do registro.
    :ivar funcionario_responsavel: :class:`~django.db.models.ForeignKey` O usuário (:class:`~django.contrib.auth.models.User`)
                                   que registrou a limpeza. Pode ser nulo se o funcionário for removido.
    :ivar observacoes: :class:`str` Quaisquer notas ou detalhes adicionais sobre a limpeza realizada.
    """
    sala = models.ForeignKey(Sala, on_delete=models.CASCADE, related_name='registros_limpeza', verbose_name="Sala")
    data_hora_limpeza = models.DateTimeField(auto_now_add=True, verbose_name="Data e Hora da Limpeza")
    funcionario_responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Funcionário Responsável")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")

    class Meta:
        """
        Metadados para o modelo LimpezaRegistro.

        Define o nome legível no plural e singular e a ordem padrão
        dos registros de limpeza nas consultas (do mais recente para o mais antigo).
        """
        verbose_name = "Registro de Limpeza"
        verbose_name_plural = "Registros de Limpeza"
        ordering = ['-data_hora_limpeza'] # Ordena pelos mais recentes primeiro

    def __str__(self):
        """
        Retorna a representação em string do objeto LimpezaRegistro.

        :returns: Uma string formatada contendo o nome/número da sala e a data/hora da limpeza.
        :rtype: str
        """
        return f"Limpeza da {self.sala.nome_numero} em {self.data_hora_limpeza.strftime('%Y-%m-%d %H:%M:%S')}"