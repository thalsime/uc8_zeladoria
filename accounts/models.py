from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    """
    Modelo de Perfil do Usuário.

    Armazena informações adicionais relacionadas a um usuário, como a foto de perfil.
    Este modelo tem uma relação um-para-um com o modelo User padrão do Django.

    :ivar user: :class:`~django.db.models.OneToOneField` A relação com o usuário.
    :ivar profile_picture: :class:`~django.db.models.ImageField` A foto de perfil do usuário.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        null=True,
        blank=True,
        verbose_name="Foto de Perfil"
    )

    def __str__(self):
        return f'Perfil de {self.user.username}'

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Cria um perfil para um novo usuário ou apenas salva o perfil se o usuário for atualizado.
    """
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
