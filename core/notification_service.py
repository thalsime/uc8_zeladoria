from django.contrib.auth.models import User
from .models import Notificacao

def criar_notificacao_para_responsaveis(sala, mensagem):
    """
    Cria uma notificação para todos os zeladores responsáveis por uma sala.
    """
    responsaveis = sala.responsaveis.all()
    if not responsaveis.exists():
        # Se a sala não tem responsáveis, notifica todos os membros do grupo Zeladoria
        responsaveis = User.objects.filter(groups__name='Zeladoria')

    for usuario in responsaveis:
        Notificacao.objects.create(
            destinatario=usuario,
            mensagem=mensagem,
            link=f"/salas/{sala.qr_code_id}/"
        )
