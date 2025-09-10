from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

def user_profile_picture_path(instance, filename):
    """
    Gera um caminho padronizado para a foto de perfil do usuário.
    O arquivo será salvo como 'profile_pics/{user_id}.jpg'.
    Isso garante que cada usuário tenha apenas uma foto, que será substituída
    a cada novo upload.
    """
    # Usa o ID do usuário para criar um nome de arquivo único e estável.
    # Força a extensão para .jpg, pois converteremos todas as imagens.
    return f'profile_pics/{instance.user.id}.jpg'

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
        upload_to=user_profile_picture_path,
        null=True,
        blank=True,
        verbose_name="Foto de Perfil"
    )

    def __str__(self):
        return f'Perfil de {self.user.username}'

    def save(self, *args, **kwargs):

        if self.profile_picture:
            # Abre a imagem em memória usando Pillow
            img = Image.open(self.profile_picture)

            # Corte Quadrado Central
            width, height = img.size
            if width != height:
                # Encontra o menor lado para definir o tamanho do quadrado
                min_dim = min(width, height)

                # Calcula as coordenadas para o corte central
                left = (width - min_dim) / 2
                top = (height - min_dim) / 2
                right = (width + min_dim) / 2
                bottom = (height + min_dim) / 2

                # Realiza o corte
                img = img.crop((left, top, right, bottom))

            # Redimensiona a imagem para 300x300 pixels
            img = img.resize((300, 300), Image.Resampling.LANCZOS)

            # Converte para RGB caso seja uma imagem com canal de transparência (PNG)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Cria um buffer de bytes em memória para salvar a nova imagem
            buffer = BytesIO()
            # Salva a imagem no buffer no formato JPEG com 70% de qualidade
            img.save(buffer, format='JPEG', quality=70)

            # O nome do arquivo é pego do próprio campo, que já usou a função
            # user_profile_picture_path para definir o nome correto.
            file_name = self.profile_picture.name

            # Substitui a imagem original pela imagem processada em memória
            self.profile_picture.save(file_name, ContentFile(buffer.getvalue()), save=False)

        super().save(*args, **kwargs)

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Cria um perfil para um novo usuário ou apenas salva o perfil se o usuário for atualizado.
    """
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
