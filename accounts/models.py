from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.image_utils import get_random_image_path, process_and_save_image

def user_profile_picture_path(instance, filename):
    """Gera o caminho para a foto de perfil, usando a função genérica."""
    return get_random_image_path(instance, filename, 'profile_pics')

class Profile(models.Model):
    """Modela o perfil de um usuário, estendendo o modelo padrão do Django.

    Este modelo possui uma relação um-para-um com o modelo `User` e armazena
    informações adicionais, como a foto de perfil.

    Attributes:
        user (User): A instância do usuário associada a este perfil.
        profile_picture (ImageField): O campo para upload da foto de perfil.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(
        upload_to=user_profile_picture_path,
        null=True,
        blank=True,
        verbose_name="Foto de Perfil"
    )

    def __str__(self):
        """Retorna a representação textual do perfil."""
        return f'Perfil de {self.user.username}'

    def save(self, *args, **kwargs):
        """Sobrescreve o método save para gerenciar e processar a foto de perfil."""
        old_instance = None
        if self.pk:
            try:
                # Busca a instância antiga ANTES de qualquer modificação
                old_instance = Profile.objects.get(pk=self.pk)
            except Profile.DoesNotExist:
                pass

        imagem_mudou = False
        if old_instance:
            # Verifica se uma imagem foi enviada E é diferente da antiga, OU se a imagem antiga foi removida
            if self.profile_picture != old_instance.profile_picture:
                 imagem_mudou = True
                 # Se a imagem mudou e existia uma antiga, deleta o arquivo antigo
                 if old_instance.profile_picture:
                     old_instance.profile_picture.delete(save=False)
        elif self.profile_picture: # Se é uma nova instância E tem imagem
             imagem_mudou = True

        # Só processa se a imagem mudou OU se é uma nova instância com imagem
        if imagem_mudou and self.profile_picture:
             process_and_save_image(self.profile_picture, size=(300, 300))

        super().save(*args, **kwargs)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Cria um perfil para um usuário SEMPRE QUE um novo usuário for criado.

    Este sinal agora executa apenas na criação do usuário (`created` is True)
    para evitar chamadas desnecessárias e errôneas ao Profile.save().
    """
    if created:
        Profile.objects.create(user=instance)
