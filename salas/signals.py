from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Sala
from .pdf_generator import generate_salas_pdf

@receiver(post_save, sender=Sala)
def sala_post_save_handler(sender, instance, **kwargs):
    """Gera o PDF de salas sempre que uma instância de Sala é salva."""
    generate_salas_pdf()

@receiver(post_delete, sender=Sala)
def sala_post_delete_handler(sender, instance, **kwargs):
    """Gera o PDF de salas sempre que uma instância de Sala é deletada."""
    generate_salas_pdf()