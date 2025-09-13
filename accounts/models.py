import uuid
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

def user_profile_picture_path(instance, filename):
    """
    Define o caminho e um nome de arquivo aleatório para a foto de perfil.

    Gera um nome de arquivo único universal (UUID) para evitar problemas de
    cache. A extensão é fixada em '.jpg' devido ao processamento da
    imagem no método save().
    """
    random_filename = f'{uuid.uuid4()}.jpg'
    return f'profile_pics/{random_filename}'

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
        """Sobrescreve o método save para gerenciar e processar a foto de perfil.

        Antes de salvar a instância no banco de dados, este método executa duas
        operações principais. Primeiramente, se uma foto de perfil existente
        estiver sendo substituída, o arquivo de imagem antigo é deletado do
        armazenamento para evitar acúmulo de arquivos e garantir a substituição.

        Em seguida, se uma nova imagem for enviada, ela é processada para
        padronização: é cortada em um formato quadrado, redimensionada para
        300x300 pixels e convertida para o formato JPEG para otimizar seu
        tamanho antes de ser salva.
        """
        if self.pk:
            try:
                old_instance = Profile.objects.get(pk=self.pk)
                if old_instance.profile_picture and old_instance.profile_picture != self.profile_picture:
                    old_instance.profile_picture.delete(save=False)
            except Profile.DoesNotExist:
                pass

        if self.profile_picture:
            img = Image.open(self.profile_picture)

            width, height = img.size
            if width != height:
                min_dim = min(width, height)
                left = (width - min_dim) / 2
                top = (height - min_dim) / 2
                right = (width + min_dim) / 2
                bottom = (height + min_dim) / 2
                img = img.crop((left, top, right, bottom))

            img = img.resize((300, 300), Image.Resampling.LANCZOS)

            if img.mode != 'RGB':
                img = img.convert('RGB')

            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=70)

            file_name = self.profile_picture.name
            self.profile_picture.save(file_name, ContentFile(buffer.getvalue()), save=False)

        super().save(*args, **kwargs)


# --- INÍCIO DA CORREÇÃO ---
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Cria um perfil para um usuário SEMPRE QUE um novo usuário for criado.

    Este sinal agora executa apenas na criação do usuário (`created` is True)
    para evitar chamadas desnecessárias e errôneas ao Profile.save().
    """
    if created:
        Profile.objects.create(user=instance)
