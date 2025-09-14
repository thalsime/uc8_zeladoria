from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Sala, RelatorioSalaSuja, LimpezaRegistro
from .pdf_generator import generate_salas_pdf
from core.notification_service import criar_notificacao_para_responsaveis # Adicionar import
from django.utils import timezone

@receiver(post_save, sender=Sala)
def sala_post_save_handler(sender, instance, **kwargs):
    """Gera o PDF de salas sempre que uma instância de Sala é salva."""
    generate_salas_pdf()

@receiver(post_delete, sender=Sala)
def sala_post_delete_handler(sender, instance, **kwargs):
    """Gera o PDF de salas sempre que uma instância de Sala é deletada."""
    generate_salas_pdf()

@receiver(post_save, sender=RelatorioSalaSuja)
def notificar_sala_suja(sender, instance, created, **kwargs):
    """
    Envia notificação quando um novo relatório de sala suja é criado.
    """
    if created:
        sala = instance.sala
        mensagem = f"A sala '{sala.nome_numero}' foi reportada como suja."
        criar_notificacao_para_responsaveis(sala, mensagem)

@receiver(post_save, sender=LimpezaRegistro)
def notificar_limpeza_pendente(sender, instance, **kwargs):
    """
    Verifica se uma limpeza concluída tornou outra sala pendente e notifica.
    (Esta é uma implementação simplificada. Uma tarefa agendada seria mais robusta)
    """
    # Esta lógica pode ser complexa. Uma forma simples é verificar se o status mudou.
    # No nosso caso, vamos focar em notificar apenas quando for reportada como suja por enquanto,
    # pois verificar a transição para "Pendente" via sinais pode ser ineficiente.
    # A notificação de "Pendente" seria melhor gerenciada por uma tarefa agendada (Celery/cronjob).
    pass