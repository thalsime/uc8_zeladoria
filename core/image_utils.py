import uuid
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

def get_random_image_path(instance, filename, upload_to_dir):
    """
    Gera um caminho de arquivo único e aleatório para uma imagem.

    Args:
        instance: A instância do modelo sendo salva.
        filename (str): O nome original do arquivo.
        upload_to_dir (str): O subdiretório dentro de 'media/' onde a imagem será salva.

    Returns:
        str: O caminho completo para o novo arquivo (ex: 'profile_pics/uuid.jpg').
    """
    random_filename = f'{uuid.uuid4()}.jpg'
    return f'{upload_to_dir}/{random_filename}'

def process_and_save_image(image_field, size=(300, 300), quality=70):
    """
    Processa uma imagem (corta, redimensiona, converte) e a salva no campo.

    Args:
        image_field: O campo ImageField da instância do modelo (ex: self.profile_picture).
        size (tuple): A dimensão final da imagem (largura, altura).
        quality (int): A qualidade do JPEG a ser salvo (0-100).
    """
    if not image_field:
        return

    img = Image.open(image_field)

    # Corta a imagem para ficar quadrada (crop central)
    width, height = img.size
    if width != height:
        min_dim = min(width, height)
        left = (width - min_dim) / 2
        top = (height - min_dim) / 2
        right = (width + min_dim) / 2
        bottom = (height + min_dim) / 2
        img = img.crop((left, top, right, bottom))

    # Redimensiona para o tamanho padrão
    img = img.resize(size, Image.Resampling.LANCZOS)

    # Converte para RGB para garantir compatibilidade
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Salva a imagem processada em um buffer em memória
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=quality)

    # Salva o conteúdo do buffer de volta no campo da imagem, sem salvar o modelo ainda
    file_name = image_field.name
    image_field.save(file_name, ContentFile(buffer.getvalue()), save=False)
