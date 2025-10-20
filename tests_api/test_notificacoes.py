"""Testes de integração para o endpoint de Notificações (/api/notificacoes/)."""

import os
import pytest
from django.contrib.auth.models import User, Group
from rest_framework import status # Para verificar o status code
from rest_framework.test import APIClient
from typing import Dict, Any, List
from core.models import Notificacao


# Fixtures de conftest.py e a fixture local (setup_notificacoes)

@pytest.fixture
def api_client() -> APIClient:
    """Fixture que fornece uma instância do APIClient do DRF."""
    return APIClient()


@pytest.fixture
def setup_notificacoes(db) -> Dict[str, Any]:
    """
    Cria notificações para diferentes usuários (zelador e assistente) no banco de dados.
    Garante que os usuários e grupos necessários existam no banco de teste.
    Limpa TODAS as notificações existentes antes de criar as de teste.
    Retorna dados relevantes para os testes.
    """
    zelador1_username = os.getenv("TEST_USER_ZELADOR_USERNAME", "zelador")
    zelador2_username = os.getenv("TEST_USER_ASSISTENTE_USERNAME", "assistente")
    zeladoria_group_name = "Zeladoria"

    group_zeladoria, _ = Group.objects.get_or_create(name=zeladoria_group_name)

    user_zelador1, created1 = User.objects.get_or_create(
        username=zelador1_username, defaults={'password': 'dummy_password_test'}
    )
    if created1 or not user_zelador1.groups.filter(name=zeladoria_group_name).exists():
        user_zelador1.groups.add(group_zeladoria)

    user_zelador2, created2 = User.objects.get_or_create(
        username=zelador2_username, defaults={'password': 'dummy_password_test'}
    )
    if created2 or not user_zelador2.groups.filter(name=zeladoria_group_name).exists():
        user_zelador2.groups.add(group_zeladoria)

    # Dados das notificações a serem criadas
    notificacoes_data = {
        user_zelador1: [
            {"mensagem": "Z1 - Msg 1 (NL)", "lida": False}, # Mais antiga
            {"mensagem": "Z1 - Msg 2 (L)", "lida": True},
            {"mensagem": "Z1 - Msg 3 (NL)", "lida": False}, # Mais recente
        ],
        user_zelador2: [
            {"mensagem": "Z2 - Msg 1 (NL)", "lida": False},
        ]
    }
    created_notifications = {user_zelador1: [], user_zelador2: []}

    # Limpa TODAS as notificações antes de criar
    Notificacao.objects.all().delete()

    # Cria as novas notificações
    for user, data_list in notificacoes_data.items():
        for data in data_list:
            user.refresh_from_db()
            notificacao = Notificacao.objects.create(destinatario=user, **data)
            created_notifications[user].append(notificacao)

    ids_zelador1 = [n.id for n in created_notifications[user_zelador1]]
    ids_zelador2 = [n.id for n in created_notifications[user_zelador2]]

    if not all(ids_zelador1):
         pytest.fail("Fixture falhou ao criar notificações para zelador1 (IDs nulos/ausentes)")

    return {
        "user_zelador1": user_zelador1,
        "user_zelador2": user_zelador2,
        "ids_zelador1": ids_zelador1,
        "ids_zelador2": ids_zelador2,
        "count_zelador1": len(ids_zelador1),
        "count_zelador2": len(ids_zelador2),
        "id_nao_lida_zelador1_primeira": ids_zelador1[0],
        "id_lida_zelador1": ids_zelador1[1],
        "id_nao_lida_zelador1_ultima": ids_zelador1[2],
        "id_nao_lida_zelador2": ids_zelador2[0]
    }


# Testes de Listagem (GET /api/notificacoes/)

# Usar 'client' padrão para teste não autenticado
def test_listar_notificacoes_nao_autenticado_falha(client):
    """Verifica se acesso não autenticado é negado (401)."""
    url = "/api/notificacoes/"
    response = client.get(url)
    assert response.status_code == 401

# Usar 'api_client' para teste autenticado
def test_listar_notificacoes_proprias(
    api_client: APIClient, # <-- Usar a fixture api_client
    setup_notificacoes: Dict[str, Any]
):
    """Verifica se o usuário logado lista apenas suas próprias notificações e na ordem correta."""
    url = "/api/notificacoes/"
    user_zelador1 = setup_notificacoes["user_zelador1"] # Obter o objeto User

    # Autenticar usando force_authenticate do APIClient
    api_client.force_authenticate(user=user_zelador1)

    # Fazer a requisição com o api_client (agora autenticado)
    response = api_client.get(url) # Usar api_client
    assert response.status_code == 200

    # Acessar dados JSON da resposta
    notificacoes_listadas = response.json()
    ids_listados = [n['id'] for n in notificacoes_listadas]

    # Dados esperados da fixture (lógica inalterada)
    expected_count = setup_notificacoes["count_zelador1"]
    ids_esperados_zelador1_set = set(setup_notificacoes["ids_zelador1"])
    ids_nao_esperados_zelador2 = setup_notificacoes["ids_zelador2"]

    # 1. Verificar a contagem
    assert len(notificacoes_listadas) == expected_count, \
        (f"Falha na contagem: Esperado {expected_count}, Recebido {len(notificacoes_listadas)}. "
         f"IDs Esperados da Fixture: {setup_notificacoes['ids_zelador1']}. Resposta da API: {notificacoes_listadas}")

    # 2. Verificar se todos os IDs esperados estão presentes
    ids_listados_set = {n['id'] for n in notificacoes_listadas}
    assert ids_listados_set == ids_esperados_zelador1_set, \
        f"Falha na verificação de IDs: Esperado {ids_esperados_set}, Recebido {ids_listados_set}"

    # 3. Verificar se nenhuma notificação do outro usuário está presente
    for id_z2 in ids_nao_esperados_zelador2:
        assert id_z2 not in ids_listados_set, f"ID {id_z2} do outro usuário foi listado indevidamente"

    # 4. Verificar a ordem (mais recente primeiro)
    assert ids_listados[0] == setup_notificacoes["id_nao_lida_zelador1_ultima"], \
        "Falha na ordenação: A notificação mais recente não é a primeira."
    assert ids_listados[-1] == setup_notificacoes["id_nao_lida_zelador1_primeira"], \
        "Falha na ordenação: A notificação mais antiga não é a última."


# Testes para Marcar como Lida - Individual (POST /api/notificacoes/{id}/marcar_como_lida/)

def test_marcar_como_lida_propria_nao_lida_sucesso(
    api_client: APIClient,
    setup_notificacoes: Dict[str, Any]
):
    """
    Verifica se marcar uma notificação própria não lida como lida funciona.

    Passos:
    1. Autentica como zelador1.
    2. Envia POST para marcar uma notificação NÃO LIDA específica como lida.
    3. Verifica se o status code é 204 No Content.
    4. Verifica no banco de dados se o campo 'lida' da notificação é True.
    """
    user_zelador1 = setup_notificacoes["user_zelador1"]
    # Pegar o ID da *última* notificação não lida criada pela fixture para zelador1,
    # que é a mais recente e mais provável de ser a primeira a ser marcada como lida.
    notificacao_id_nao_lida = setup_notificacoes["id_nao_lida_zelador1_ultima"]

    # 1. Autenticar
    api_client.force_authenticate(user=user_zelador1)

    # 2. Construir URL e fazer a requisição POST
    url = f"/api/notificacoes/{notificacao_id_nao_lida}/marcar_como_lida/"
    response = api_client.post(url)

    # 3. Verificar Status Code
    assert response.status_code == status.HTTP_204_NO_CONTENT, \
        f"Esperado status 204, recebido {response.status_code}. Resposta: {response.content}"

    # 4. Verificar no banco de dados
    # Força a releitura do objeto do banco para garantir que estamos vendo o estado atualizado
    notificacao_atualizada = Notificacao.objects.get(pk=notificacao_id_nao_lida)
    assert notificacao_atualizada.lida is True, \
        f"A notificação {notificacao_id_nao_lida} deveria estar marcada como lida no banco, mas não está."

    # Opcional: Desautenticar para isolar o próximo teste (boa prática)
    api_client.logout()


def test_marcar_como_lida_propria_ja_lida_sucesso(
    api_client: APIClient,
    setup_notificacoes: Dict[str, Any]
):
    """
    Verifica a idempotência ao marcar uma notificação própria JÁ LIDA.

    Passos:
    1. Autentica como zelador1.
    2. Envia POST para marcar uma notificação JÁ LIDA como lida.
    3. Verifica se o status code é 204 No Content.
    4. Verifica no banco de dados se o campo 'lida' da notificação permanece True.
    """
    user_zelador1 = setup_notificacoes["user_zelador1"]
    # Pegar o ID da notificação que a fixture já definiu como lida
    notificacao_id_ja_lida = setup_notificacoes["id_lida_zelador1"]

    # 1. Autenticar
    api_client.force_authenticate(user=user_zelador1)

    # 2. Construir URL e fazer a requisição POST
    url = f"/api/notificacoes/{notificacao_id_ja_lida}/marcar_como_lida/"
    response = api_client.post(url)

    # 3. Verificar Status Code
    assert response.status_code == status.HTTP_204_NO_CONTENT, \
        f"Esperado status 204 ao remarcar como lida, recebido {response.status_code}. Resposta: {response.content}"

    # 4. Verificar no banco de dados
    # Garante que a notificação ainda existe e busca seu estado atual
    try:
        notificacao_apos_remarcar = Notificacao.objects.get(pk=notificacao_id_ja_lida)
        assert notificacao_apos_remarcar.lida is True, \
            f"A notificação {notificacao_id_ja_lida} deveria permanecer como lida no banco, mas seu estado é {notificacao_apos_remarcar.lida}."
    except Notificacao.DoesNotExist:
        pytest.fail(f"A notificação {notificacao_id_ja_lida}, que deveria existir, não foi encontrada no banco após tentar remarcá-la.")


    # Opcional: Desautenticar
    api_client.logout()


def test_marcar_como_lida_outra_pessoa_falha(
    api_client: APIClient,
    setup_notificacoes: Dict[str, Any]
):
    """
    Verifica se marcar notificação de OUTRO usuário falha (404).

    Passos:
    1. Autentica como zelador1.
    2. Tenta enviar POST para marcar uma notificação do zelador2 como lida.
    3. Verifica se o status code é 404 Not Found.
    4. Opcional: Verifica se o estado da notificação do zelador2 NÃO mudou.
    """
    user_zelador1 = setup_notificacoes["user_zelador1"]
    # Pegar o ID de uma notificação pertencente ao zelador2
    notificacao_id_outro_usuario = setup_notificacoes["id_nao_lida_zelador2"]

    # 1. Autenticar como zelador1
    api_client.force_authenticate(user=user_zelador1)

    # 2. Construir URL e fazer a requisição POST
    url = f"/api/notificacoes/{notificacao_id_outro_usuario}/marcar_como_lida/"
    response = api_client.post(url)

    # 3. Verificar Status Code 404
    assert response.status_code == status.HTTP_404_NOT_FOUND, \
        f"Esperado status 404 ao tentar marcar notificação de outro usuário, recebido {response.status_code}. Resposta: {response.content}"

    # 4. Opcional: Verificar se a notificação do outro usuário permanece não lida
    try:
        notificacao_outro_usuario = Notificacao.objects.get(pk=notificacao_id_outro_usuario)
        assert notificacao_outro_usuario.lida is False, \
            f"A notificação {notificacao_id_outro_usuario} do outro usuário foi marcada como lida indevidamente."
    except Notificacao.DoesNotExist:
        pytest.fail(f"A notificação {notificacao_id_outro_usuario}, que pertence a outro usuário, não foi encontrada para verificação.")


    # Opcional: Desautenticar
    api_client.logout()


def test_marcar_como_lida_inexistente_falha(
    api_client: APIClient,
    setup_notificacoes: Dict[str, Any]
):
    """
    Verifica se marcar notificação com ID inexistente falha (404).

    Passos:
    1. Autentica como zelador1.
    2. Tenta enviar POST para marcar uma notificação com ID заведомо inexistente.
    3. Verifica se o status code é 404 Not Found.
    """
    user_zelador1 = setup_notificacoes["user_zelador1"]
    id_inexistente = 99999 # Um ID que provavelmente não existirá

    # Garante que o ID realmente não existe, caso a fixture tenha criado muitos IDs.
    while Notificacao.objects.filter(pk=id_inexistente).exists():
        id_inexistente += 1

    # 1. Autenticar
    api_client.force_authenticate(user=user_zelador1)

    # 2. Construir URL e fazer a requisição POST
    url = f"/api/notificacoes/{id_inexistente}/marcar_como_lida/"
    response = api_client.post(url)

    # 3. Verificar Status Code 404
    assert response.status_code == status.HTTP_404_NOT_FOUND, \
        f"Esperado status 404 ao tentar marcar notificação inexistente ({id_inexistente}), recebido {response.status_code}. Resposta: {response.content}"

    # Opcional: Desautenticar
    api_client.logout()


def test_marcar_como_lida_nao_autenticado_falha(
    api_client: APIClient, # Usamos o cliente, mas sem autenticar
    setup_notificacoes: Dict[str, Any]
):
    """
    Verifica se marcar notificação sem autenticação falha (401).

    Passos:
    1. NÃO autentica o cliente.
    2. Tenta enviar POST para marcar uma notificação qualquer como lida.
    3. Verifica se o status code é 401 Unauthorized.
    """
    # Pegar o ID de uma notificação qualquer (só para ter uma URL válida)
    # Não importa qual notificação usamos, pois o erro 401 deve ocorrer antes
    notificacao_id_qualquer = setup_notificacoes["id_nao_lida_zelador1_primeira"]

    # 1. NÃO autenticar (api_client por padrão não está autenticado)

    # 2. Construir URL e fazer a requisição POST
    url = f"/api/notificacoes/{notificacao_id_qualquer}/marcar_como_lida/"
    response = api_client.post(url) # Requisição sem header de autorização

    # 3. Verificar Status Code 401
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
        f"Esperado status 401 ao tentar marcar notificação sem autenticação, recebido {response.status_code}. Resposta: {response.content}"

    # Não precisamos verificar o estado no banco, pois a ação não deve ter sido permitida.
    # Também não precisamos desautenticar, pois nunca autenticamos.

# Testes para Marcar Todas como Lidas (POST /api/notificacoes/marcar_todas_como_lidas/)

def test_marcar_todas_como_lidas_sucesso(
    api_client: APIClient,
    setup_notificacoes: Dict[str, Any]
):
    """
    Verifica se marcar todas as notificações não lidas como lidas funciona.

    Passos:
    1. Autentica como zelador1 (que tem notificações não lidas).
    2. Envia POST para a action 'marcar_todas_como_lidas'.
    3. Verifica se o status code é 204 No Content.
    4. Verifica no banco de dados se TODAS as notificações do zelador1 estão agora com 'lida' = True.
    """
    user_zelador1 = setup_notificacoes["user_zelador1"]
    ids_notificacoes_zelador1 = setup_notificacoes["ids_zelador1"]

    # Verificar o estado inicial (garantir que há notificações não lidas)
    notificacoes_iniciais = Notificacao.objects.filter(destinatario=user_zelador1)
    assert notificacoes_iniciais.filter(lida=False).exists(), \
        "Fixture falhou: zelador1 deveria ter notificações não lidas inicialmente para este teste."

    # 1. Autenticar
    api_client.force_authenticate(user=user_zelador1)

    # 2. Construir URL e fazer a requisição POST
    url = "/api/notificacoes/marcar_todas_como_lidas/"
    response = api_client.post(url)

    # 3. Verificar Status Code
    assert response.status_code == status.HTTP_204_NO_CONTENT, \
        f"Esperado status 204, recebido {response.status_code}. Resposta: {response.content}"

    # 4. Verificar no banco de dados
    # Busca todas as notificações do usuário novamente
    notificacoes_apos_acao = Notificacao.objects.filter(destinatario=user_zelador1)
    assert notificacoes_apos_acao.count() == len(ids_notificacoes_zelador1), \
        "O número de notificações do usuário mudou inesperadamente após a ação."

    # Verifica se TODAS elas estão marcadas como lidas
    for notificacao in notificacoes_apos_acao:
        assert notificacao.lida is True, \
            f"A notificação {notificacao.id} deveria estar marcada como lida após 'marcar_todas', mas não está."

    # Alternativamente, verificar se não existe nenhuma não lida:
    assert not notificacoes_apos_acao.filter(lida=False).exists(), \
        "Deveriam todas as notificações do usuário estar marcadas como lidas, mas ainda existem não lidas."

    # Opcional: Desautenticar
    api_client.logout()

def test_marcar_todas_como_lidas_ja_lidas_sucesso(
    api_client: APIClient,
    setup_notificacoes: Dict[str, Any]
):
    """
    Verifica a idempotência ao chamar 'marcar_todas' quando já estão lidas.

    Passos:
    1. Autentica como zelador1.
    2. Chama 'marcar_todas_como_lidas' uma primeira vez para garantir que tudo está lido.
    3. Verifica o status 204.
    4. Chama 'marcar_todas_como_lidas' uma segunda vez.
    5. Verifica novamente o status 204.
    6. Opcional: Verifica no banco se todas as notificações permanecem lidas.
    """
    user_zelador1 = setup_notificacoes["user_zelador1"]
    ids_notificacoes_zelador1 = setup_notificacoes["ids_zelador1"]

    # 1. Autenticar
    api_client.force_authenticate(user=user_zelador1)

    # 2. Chamar a action pela primeira vez
    url = "/api/notificacoes/marcar_todas_como_lidas/"
    response_primeira_chamada = api_client.post(url)

    # 3. Verificar o status da primeira chamada
    assert response_primeira_chamada.status_code == status.HTTP_204_NO_CONTENT, \
        f"Esperado status 204 na primeira chamada, recebido {response_primeira_chamada.status_code}. Resposta: {response_primeira_chamada.content}"

    # Verificar se realmente marcou todas como lidas (pré-condição para a segunda chamada)
    assert not Notificacao.objects.filter(destinatario=user_zelador1, lida=False).exists(), \
        "A primeira chamada falhou em marcar todas as notificações como lidas."

    # 4. Chamar a action pela segunda vez
    response_segunda_chamada = api_client.post(url)

    # 5. Verificar o status da segunda chamada (teste de idempotência)
    assert response_segunda_chamada.status_code == status.HTTP_204_NO_CONTENT, \
        f"Esperado status 204 na segunda chamada (idempotência), recebido {response_segunda_chamada.status_code}. Resposta: {response_segunda_chamada.content}"

    # 6. Opcional: Re-verificar no banco
    notificacoes_apos_segunda_chamada = Notificacao.objects.filter(destinatario=user_zelador1)
    assert notificacoes_apos_segunda_chamada.count() == len(ids_notificacoes_zelador1)
    assert not notificacoes_apos_segunda_chamada.filter(lida=False).exists(), \
        "Todas as notificações deveriam permanecer lidas após a segunda chamada."

    # Opcional: Desautenticar
    api_client.logout()


def test_marcar_todas_como_lidas_nao_autenticado_falha(
    api_client: APIClient # Cliente não autenticado
):
    """
    Verifica se chamar 'marcar_todas' sem autenticação falha (401).

    Passos:
    1. NÃO autentica o cliente.
    2. Envia POST para a action 'marcar_todas_como_lidas'.
    3. Verifica se o status code é 401 Unauthorized.
    """
    # 1. NÃO autenticar

    # 2. Construir URL e fazer a requisição POST
    url = "/api/notificacoes/marcar_todas_como_lidas/"
    response = api_client.post(url) # Requisição sem header de autorização

    # 3. Verificar Status Code 401
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
        f"Esperado status 401 ao chamar 'marcar_todas' sem autenticação, recebido {response.status_code}. Resposta: {response.content}"

    # Não precisamos da fixture setup_notificacoes aqui, pois o erro 401 ocorre antes
    # de qualquer interação com dados específicos.
