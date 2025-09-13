import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Sala(models.Model):
    """Representa uma sala física ou local gerenciável no sistema.

    Armazena informações como identificação, capacidade, localização e as
    regras de limpeza associadas, além de manter um registro de quem são os
    responsáveis por ela.

    Attributes:
        nome_numero (CharField): Identificador textual único da sala.
        capacidade (IntegerField): Número máximo de ocupantes.
        descricao (TextField): Descrição opcional da sala.
        instrucoes (TextField): Instruções específicas para a limpeza da sala.
        localizacao (CharField): Localização física da sala.
        qr_code_id (UUIDField): Identificador único para a geração de QR Codes.
        ativa (BooleanField): Indica se a sala está em uso no sistema.
        responsaveis (ManyToManyField): Usuários do grupo 'Zeladoria'
            responsáveis pela sala.
        validade_limpeza_horas (IntegerField): Período em horas que uma
            limpeza é considerada válida.
    """
    nome_numero = models.CharField(max_length=100, unique=True, verbose_name="Nome/Número")
    capacidade = models.IntegerField(
        verbose_name="Capacidade",
        validators=[
            MinValueValidator(1, message="A capacidade deve ser de no mínimo 1."),
            MaxValueValidator(2000, message="A capacidade máxima não pode exceder 2000.")
        ]
    )
    descricao = models.TextField(max_length=100, blank=True, null=True, verbose_name="Descrição")
    instrucoes = models.TextField(blank=True, null=True, verbose_name="Instruções de Limpeza")
    localizacao = models.CharField(max_length=100, verbose_name="Localização")
    qr_code_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
        verbose_name="ID para QR Code"
    )
    ativa = models.BooleanField(default=True, verbose_name="Ativa")
    responsaveis = models.ManyToManyField(
        User,
        related_name='salas_responsaveis',
        blank=True,
        verbose_name="Responsáveis pela Limpeza",
        limit_choices_to={'groups__name': 'Zeladoria'}
    )
    validade_limpeza_horas = models.IntegerField(
        default=4,
        verbose_name="Validade da Limpeza (em horas)",
        validators=[
            MinValueValidator(1, message="A validade da limpeza deve ser de no mínimo 1 hora.")
        ]
    )

    class Meta:
        """Define metadados para o modelo Sala.

        Configura os nomes de exibição no admin do Django e a ordenação
        padrão das consultas pelo campo `nome_numero`.
        """
        verbose_name = "Sala"
        verbose_name_plural = "Salas"
        ordering = ['nome_numero']

    def __str__(self):
        """Retorna a representação textual do modelo Sala."""
        return self.nome_numero


class LimpezaRegistro(models.Model):
    """Registra a ocorrência de uma limpeza em uma determinada sala.

    Armazena a qual sala o registro pertence, o funcionário que realizou a
    limpeza e o momento exato em que ela foi registrada.

    Attributes:
        sala (ForeignKey): A sala que foi limpa.
        data_hora_limpeza (DateTimeField): Data e hora em que o registro foi
            criado automaticamente.
        funcionario_responsavel (ForeignKey): O usuário que registrou a limpeza.
        observacoes (TextField): Notas adicionais sobre a limpeza.
    """
    sala = models.ForeignKey(Sala, on_delete=models.CASCADE, related_name='registros_limpeza', verbose_name="Sala")
    data_hora_limpeza = models.DateTimeField(auto_now_add=True, verbose_name="Data e Hora da Limpeza")
    funcionario_responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Funcionário Responsável")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")

    class Meta:
        """Define metadados para o modelo LimpezaRegistro.

        Configura os nomes de exibição e a ordenação padrão das consultas,
        mostrando os registros mais recentes primeiro.
        """
        verbose_name = "Registro de Limpeza"
        verbose_name_plural = "Registros de Limpeza"
        ordering = ['-data_hora_limpeza']

    def __str__(self):
        """Retorna a representação textual do registro de limpeza."""
        return f"Limpeza da {self.sala.nome_numero} em {self.data_hora_limpeza.strftime('%Y-%m-%d %H:%M:%S')}"
