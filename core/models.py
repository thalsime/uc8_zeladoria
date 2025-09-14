from django.db import models
from django.contrib.auth.models import User


class Notificacao(models.Model):
    """
    Armazena uma notificação direcionada a um usuário específico.
    """
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificacoes', verbose_name="Destinatário")
    mensagem = models.TextField(verbose_name="Mensagem")
    link = models.CharField(max_length=255, blank=True, null=True, verbose_name="Link de Acesso")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    lida = models.BooleanField(default=False, db_index=True, verbose_name="Lida")

    class Meta:
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"
        ordering = ['-data_criacao']

    def __str__(self):
        return f"Notificação para {self.destinatario.username}: {self.mensagem[:30]}..."
