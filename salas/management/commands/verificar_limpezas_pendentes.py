from django.core.management.base import BaseCommand
from django.utils import timezone
from salas.models import Sala
from core.notification_service import criar_notificacao_para_responsaveis


class Command(BaseCommand):
    """
    Comando de gerenciamento para verificar salas cuja limpeza expirou e
    criar notificações para a equipe de zeladoria.
    """
    help = 'Verifica as limpezas concluídas e cria notificações para as que expiraram.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Iniciando verificação de limpezas pendentes...'))

        # Filtra apenas salas ativas que possuem pelo menos uma limpeza concluída
        salas_ativas = Sala.objects.filter(ativa=True, registros_limpeza__data_hora_fim__isnull=False).distinct()

        salas_notificadas = 0
        for sala in salas_ativas:
            # Pega o último registro de limpeza CONCLUÍDO
            ultimo_registro = sala.registros_limpeza.filter(data_hora_fim__isnull=False).latest('data_hora_fim')

            # Pega o último relatório de sujeira, se houver
            ultimo_relatorio_suja = sala.relatorios_suja.first()

            # Se a sala foi marcada como suja após a última limpeza, não faz nada aqui.
            # A notificação de "suja" já foi enviada pelo sinal.
            if ultimo_relatorio_suja and ultimo_relatorio_suja.data_hora > ultimo_registro.data_hora_fim:
                continue

            # Calcula se o tempo de validade da limpeza expirou
            validade_em_segundos = sala.validade_limpeza_horas * 3600
            tempo_decorrido = (timezone.now() - ultimo_registro.data_hora_fim).total_seconds()

            if tempo_decorrido >= validade_em_segundos:
                if sala.data_notificacao_pendencia and sala.data_notificacao_pendencia >= ultimo_registro.data_hora_fim:
                    continue  # Já notificado, pular para a próxima sala

                mensagem = f"A limpeza da sala '{sala.nome_numero}' expirou e está pendente."
                criar_notificacao_para_responsaveis(sala, mensagem)

                sala.data_notificacao_pendencia = timezone.now()
                sala.save(update_fields=['data_notificacao_pendencia'])

                salas_notificadas += 1

        if salas_notificadas > 0:
            self.stdout.write(self.style.SUCCESS(f'{salas_notificadas} sala(s) notificada(s) sobre limpeza pendente.'))
        else:
            self.stdout.write(self.style.SUCCESS('Nenhuma nova limpeza pendente encontrada.'))