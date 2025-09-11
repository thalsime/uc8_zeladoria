from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

def user_profile_picture_path(instance, filename):
    """Define o caminho de upload para a foto de perfil do usuário.

    Gera um caminho padronizado no formato 'profile_pics/{user_id}.jpg',
    garantindo que cada usuário tenha um nome de arquivo único e estável para
    sua foto, que será substituída a cada novo upload. A extensão é
    fixada em '.jpg' devido ao processamento da imagem antes de salvar.

    Args:
        instance (Profile): A instância do modelo de Profile sendo salva.
        filename (str): O nome original do arquivo enviado.

    Returns:
        str: O caminho completo onde o arquivo será salvo.
    """
    return f'profile_pics/{instance.user.id}.jpg'

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
        """Sobrescreve o método save para processar a foto de perfil antes de salvar.

        Se uma nova imagem de perfil for enviada, este método realiza as
        seguintes operações:
        1.  Realiza um corte quadrado central na imagem.
        2.  Redimensiona a imagem para 300x300 pixels para padronização.
        3.  Converte a imagem para o formato RGB, removendo canais de transparência.
        4.  Salva a imagem processada em formato JPEG com qualidade otimizada.

        Após o processamento, a imagem original é substituída pela versão
        tratada antes de chamar o método `save` da superclasse para
        persistir os dados no banco de dados.
        """
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

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Cria ou atualiza o perfil de um usuário ao salvar o modelo User.

    Esta função é um receptor de sinal que é acionado sempre que uma instância
    do modelo `User` é salva. Se o usuário foi recém-criado (`created` is True),
    um novo perfil é criado e associado a ele. Em todas as chamadas,
    o perfil associado é salvo para garantir a consistência.

    Args:
        sender (User): A classe do modelo que enviou o sinal.
        instance (User): A instância do usuário que foi salva.
        created (bool): Um booleano que indica se a instância foi criada.
        **kwargs: Argumentos adicionais de palavra-chave.
    """
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()