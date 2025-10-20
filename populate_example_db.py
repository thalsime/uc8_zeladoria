"""Popula o banco de dados com um conjunto de dados iniciais.

Este script foi projetado para ser executado como um utilitário autônomo.
Ele inicializa o ambiente Django e preenche o banco de dados com dados
essenciais para o desenvolvimento e teste da aplicação, incluindo:

- Grupos de permissão padrão ('Zeladoria', 'Solicitante de Serviços').
- Um conjunto de usuários com diferentes perfis e permissões.
- Uma lista de salas com dados variados para simular um ambiente real.

O processo é idempotente: ele verifica a existência de dados antes de
criá-los para evitar duplicatas em execuções múltiplas. Toda a operação
é envolvida em uma transação atômica para garantir a integridade dos dados.

Para executar o script, use o comando:
    python populate_example_db.py
"""
import os
import django
import random
from typing import List

# Configuração inicial do Django para permitir o uso dos modelos fora do servidor.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zeladoria.settings")
django.setup()

from django.db import transaction
from django.contrib.auth.models import Group, User
from salas.models import Sala

# Define os nomes dos grupos como constantes para evitar a repetição de strings literais ("magic strings"),
# o que melhora a manutenibilidade e reduz o risco de erros de digitação.
ZELADORIA_GROUP_NAME = "Zeladoria"
SOLICITANTE_GROUP_NAME = "Solicitante de Serviços"


# Funções auxiliares para feedback no console
def print_success(message: str) -> None:
    """Exibe uma mensagem de sucesso no console com a cor verde.

    Args:
        message: A mensagem a ser exibida.
    """
    # Código de escape ANSI para cor verde.
    print(f"\033[92m{message}\033[0m")


def print_warning(message: str) -> None:
    """Exibe uma mensagem de aviso no console com a cor amarela.

    Args:
        message: A mensagem a ser exibida.
    """
    # Código de escape ANSI para cor amarela.
    print(f"\033[93m{message}\033[0m")


def print_info(message: str) -> None:
    """Exibe uma mensagem informativa no console com a cor azul.

    Args:
        message: A mensagem a ser exibida.
    """
    # Código de escape ANSI para cor azul.
    print(f"\033[94m{message}\033[0m")


def print_error(message: str) -> None:
    """Exibe uma mensagem de erro no console com a cor vermelha.

    Args:
        message: A mensagem a ser exibida.
    """
    # Código de escape ANSI para cor vermelha.
    print(f"\033[91m{message}\033[0m")


@transaction.atomic
def run_population():
    """Executa o processo principal de população do banco de dados.

    Esta função orquestra a criação de grupos, usuários e salas.
    O decorador `@transaction.atomic` garante que todas as operações
    de banco de dados dentro da função sejam executadas em uma única
    transação. Se ocorrer qualquer erro, todas as alterações serão
    revertidas, mantendo a consistência do banco de dados.
    """
    print_success("Iniciando a população do banco de dados...")
    print_info("Verificando e criando grupos...")

    # Garante que os grupos essenciais existam no banco de dados.
    # `get_or_create` é um método idempotente que evita a criação de duplicatas.
    grupo_zeladoria, _ = Group.objects.get_or_create(name=ZELADORIA_GROUP_NAME)
    grupo_solicitante, _ = Group.objects.get_or_create(name=SOLICITANTE_GROUP_NAME)
    print_success(f"Grupos '{ZELADORIA_GROUP_NAME}' e '{SOLICITANTE_GROUP_NAME}' garantidos.")

    print_info("Criando usuários...")
    senha_padrao = "Senac@098"
    usuarios_a_criar = [
        {"username": "senac", "is_superuser": True, "is_staff": True, "grupos": [grupo_zeladoria, grupo_solicitante]},
        {"username": "administrador", "is_superuser": True, "is_staff": True, "grupos": []},
        {"username": "assistente", "is_superuser": False, "is_staff": True, "grupos": [grupo_zeladoria, grupo_solicitante]},
        {"username": "zelador", "is_superuser": False, "is_staff": False, "grupos": [grupo_zeladoria]},
        {"username": "colaborador", "is_superuser": False, "is_staff": False, "grupos": [grupo_solicitante]},
        {"username": "funcionario", "is_superuser": False, "is_staff": False, "grupos": [grupo_solicitante]},
    ]
    # Itera sobre a lista de dicionários para criar cada usuário.
    for dados_usuario in usuarios_a_criar:
        username = dados_usuario["username"]
        # Verifica se o usuário já existe para evitar erros de integridade.
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username, password=senha_padrao,
                is_superuser=dados_usuario["is_superuser"], is_staff=dados_usuario["is_staff"]
            )
            # Associa o usuário aos seus respectivos grupos.
            user.groups.set(dados_usuario["grupos"])
            print(f"- Usuário '{username}' criado.")
        else:
            print_warning(f"- Usuário '{username}' já existe. Pulando.")
    print_success("Criação de usuários concluída.")

    print_info("Criando salas...")
    # Se já existirem salas, o script assume que a população já ocorreu e interrompe a execução desta etapa.
    if Sala.objects.exists():
        print_warning("Salas já existem. Pulando a criação de salas.")
        return

    # Obtém uma lista de usuários do grupo 'Zeladoria' para atribuí-los como responsáveis pelas salas.
    responsaveis = list(User.objects.filter(groups__name=ZELADORIA_GROUP_NAME))
    if not responsaveis:
        print_error("Nenhum usuário no grupo Zeladoria para ser responsável. Abortando criação de salas.")
        return

    # Dados base para geração aleatória de salas.
    nomes_base_salas = ["Laboratório de Informática", "Sala de Aula Teórica", "Auditório", "Biblioteca",
                        "Sala de Reuniões", "Estúdio de Fotografia", "Laboratório de Gastronomia",
                        "Oficina de Robótica", "Sala Multiuso", "Consultório de Psicologia"]
    instrucoes_limpeza = ["Limpeza geral, foco nos equipamentos eletrônicos.", "Higienizar todas as mesas e cadeiras.",
                          "Aspirar o carpete e limpar poltronas.", "Esvaziar lixeiras e limpar a mesa de vidro."]

    salas_a_criar = []
    salas_com_responsaveis = []

    # Cria 20 salas com dados gerados aleatoriamente.
    for i in range(1, 21):
        sala_data = {
            "nome_numero": f"{random.choice(nomes_base_salas)} {100 + i}",
            "localizacao": f"Bloco {random.choice(['A', 'B', 'C'])}, Andar {random.randint(1, 5)}",
            "capacidade": random.randint(10, 50)
        }

        responsavel_aleatorio = None
        # As primeiras 5 salas são criadas com todos os campos preenchidos para garantir dados consistentes para testes.
        if i <= 5:
            sala_data.update({
                "descricao": f"Descrição detalhada para a sala {sala_data['nome_numero']}.",
                "instrucoes": random.choice(instrucoes_limpeza),
                "ativa": True,
            })
            responsavel_aleatorio = random.choice(responsaveis)
        else:
            # As salas restantes possuem dados opcionais preenchidos de forma aleatória.
            if random.choice([True, False]):
                sala_data["descricao"] = f"Descrição opcional para a sala {sala_data['nome_numero']}."
            if random.choice([True, False]):
                sala_data["instrucoes"] = random.choice(instrucoes_limpeza)
            if random.choice([True, False]):
                responsavel_aleatorio = random.choice(responsaveis)
            sala_data["ativa"] = random.choice([True, False, True]) # Maior chance de ser `True`.

        # Instancia o objeto Sala, mas não o salva no banco de dados ainda.
        sala_obj = Sala(**sala_data)
        salas_a_criar.append(sala_obj)

        # Guarda a relação entre a sala e seu futuro responsável para atribuição posterior.
        if responsavel_aleatorio:
            salas_com_responsaveis.append((sala_obj, responsavel_aleatorio))

    # Utiliza `bulk_create` para inserir todas as salas em uma única consulta SQL,
    # o que é significativamente mais eficiente do que criar uma por uma.
    Sala.objects.bulk_create(salas_a_criar)
    print_success(f"{len(salas_a_criar)} salas criadas com sucesso.")

    print_info("Atribuindo responsáveis às salas...")
    # A atribuição de relações Many-to-Many deve ser feita após a criação dos objetos.
    for sala, responsavel in salas_com_responsaveis:
        # `set` é usado para definir a lista de responsáveis da sala.
        sala.responsaveis.set([responsavel])
    print_success("Responsáveis atribuídos.")


if __name__ == "__main__":
    run_population()
    print_success("\nBanco de dados populado com sucesso!")
