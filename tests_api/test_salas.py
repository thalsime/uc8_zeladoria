"""Testes de integração para o endpoint de Salas da API de Zeladoria.
Esta suíte de testes valida o comportamento do CRUD de Salas, verificando:
- Controle de acesso (permissões) para diferentes perfis de usuário.
- Validação de dados na criação e atualização de salas.
- Sucesso no upload de imagens associadas a uma sala.
"""
import os
import uuid
import pytest
import requests

# Define um dicionário com um modelo de dados válidos para a criação de uma sala.
# O nome será modificado em cada teste para garantir a unicidade.
DADOS_BASE_SALA = {
    "descricao": "Sala para testes automatizados de criação.",
    "capacidade": 15,
    "localizacao": "Corredor de Testes do Bloco Z",
    "ativa": True,
}

# --- Testes de Listagem (GET /api/salas/) ---

def test_listar_salas_como_admin(api_base_url, auth_header_admin):
    """Verifica se um Admin pode listar as salas com sucesso (200 OK)."""
    response = requests.get(f"{api_base_url}/salas/", headers=auth_header_admin)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_listar_salas_como_zelador(api_base_url, auth_header_zelador):
    """Verifica se um Zelador pode listar as salas com sucesso (200 OK)."""
    response = requests.get(f"{api_base_url}/salas/", headers=auth_header_zelador)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_listar_salas_como_solicitante(api_base_url, auth_header_solicitante):
    """Verifica se um Solicitante pode listar as salas com sucesso (200 OK)."""
    response = requests.get(f"{api_base_url}/salas/", headers=auth_header_solicitante)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_listar_salas_sem_autenticacao(api_base_url):
    """Verifica se o acesso é negado (401) ao listar salas sem autenticação."""
    response = requests.get(f"{api_base_url}/salas/")
    assert response.status_code == 401


# --- Testes de Criação (POST /api/salas/) ---

def test_criar_sala_com_imagem_como_admin_sucesso(api_base_url, auth_header_admin, test_image_path):
    """Verifica se um Admin pode criar uma nova sala com dados válidos e uma imagem."""
    dados_sala_unicos = DADOS_BASE_SALA.copy()
    dados_sala_unicos["nome_numero"] = f"Sala de Teste {uuid.uuid4()}"

    with open(test_image_path, "rb") as image_file:
        files = {"imagem": (test_image_path.name, image_file, "image/png")}
        response = requests.post(
            f"{api_base_url}/salas/",
            headers=auth_header_admin,
            data=dados_sala_unicos,
            files=files
        )

    assert response.status_code == 201, f"Falha na criação da sala. Resposta: {response.text}"

    response_data = response.json()
    assert response_data["nome_numero"] == dados_sala_unicos["nome_numero"]
    assert "imagem" in response_data
    assert response_data["imagem"] is not None

    sala_uuid = response_data["qr_code_id"]
    requests.delete(f"{api_base_url}/salas/{sala_uuid}/", headers=auth_header_admin)

def test_criar_sala_como_zelador_falha(api_base_url, auth_header_zelador):
    """Verifica se um Zelador é proibido (403) de criar uma sala."""
    payload = DADOS_BASE_SALA.copy()
    payload["nome_numero"] = "Sala Teste Permissao Zelador"
    response = requests.post(f"{api_base_url}/salas/", headers=auth_header_zelador, data=payload)
    assert response.status_code == 403

def test_criar_sala_como_solicitante_falha(api_base_url, auth_header_solicitante):
    """Verifica se um Solicitante é proibido (403) de criar uma sala."""
    payload = DADOS_BASE_SALA.copy()
    payload["nome_numero"] = "Sala Teste Permissao Solicitante"
    response = requests.post(f"{api_base_url}/salas/", headers=auth_header_solicitante, data=payload)
    assert response.status_code == 403

def test_criar_sala_com_dados_invalidos_falha(api_base_url, auth_header_admin):
    """Verifica se a criação da sala falha (400) com dados inválidos (nome_numero faltando)."""
    dados_invalidos = DADOS_BASE_SALA.copy()
    response = requests.post(f"{api_base_url}/salas/", headers=auth_header_admin, data=dados_invalidos)
    assert response.status_code == 400
    assert "nome_numero" in response.json()


# --- Testes de Atualização (PATCH /api/salas/{qr_code_id}/) ---

def test_atualizar_parcialmente_sala_como_admin_sucesso(api_base_url, auth_header_admin, sala_de_teste):
    """Verifica se um Admin pode atualizar parcialmente uma sala (PATCH)."""
    sala_uuid = sala_de_teste["qr_code_id"]
    payload_atualizacao = {
        "descricao": "Descrição foi atualizada via PATCH.",
        "capacidade": 99
    }

    response = requests.patch(
        f"{api_base_url}/salas/{sala_uuid}/",
        headers=auth_header_admin,
        data=payload_atualizacao
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["descricao"] == payload_atualizacao["descricao"]
    assert response_data["capacidade"] == payload_atualizacao["capacidade"]
    assert response_data["nome_numero"] == sala_de_teste["nome_numero"]  # Verifica que não mudou

@pytest.mark.parametrize(
    "auth_header",
    [
        "auth_header_zelador",
        "auth_header_solicitante",
    ],
)
def test_atualizar_parcialmente_sala_outros_usuarios_falha(api_base_url, request, auth_header, sala_de_teste):
    """Verifica se Zelador e Solicitante são proibidos (403) de atualizar uma sala."""
    sala_uuid = sala_de_teste["qr_code_id"]
    header = request.getfixturevalue(auth_header) # Pega a fixture pelo nome

    response = requests.patch(
        f"{api_base_url}/salas/{sala_uuid}/",
        headers=header,
        data={"descricao": "Tentativa de atualização."}
    )

    assert response.status_code == 403


# --- Testes de Atualização (PUT /api/salas/{qr_code_id}/) ---

def test_atualizar_totalmente_sala_admin_sucesso(api_base_url, auth_header_admin, sala_de_teste):
    """
    Verifica se um Admin pode atualizar totalmente uma sala (PUT),
    substituindo todos os seus dados.
    """
    sala_uuid = sala_de_teste["qr_code_id"]

    # Payload completo para a substituição do recurso.
    # CORREÇÃO: Garante que o nome seja único para evitar falha na validação.
    payload_atualizacao_completa = {
        "nome_numero": f"Sala Substituída PUT {uuid.uuid4()}",
        "descricao": "Descrição totalmente nova para o teste de PUT.",
        "capacidade": 25,
        "localizacao": "Nova Localização via PUT",
        "ativa": False,
        "instrucoes": "Instruções atualizadas via PUT.",
        "validade_limpeza_horas": 8
    }

    response = requests.put(
        f"{api_base_url}/salas/{sala_uuid}/",
        headers=auth_header_admin,
        data=payload_atualizacao_completa
    )

    assert response.status_code == 200, f"Erro na requisição: {response.text}"

    response_data = response.json()

    # Verifica se todos os campos foram atualizados conforme o payload
    for key, value in payload_atualizacao_completa.items():
        assert response_data[key] == value


# --- Testes para Marcar Sala como Suja (POST /api/salas/{qr_code_id}/marcar_como_suja/) ---

def test_marcar_como_suja_solicitante_sucesso(api_base_url: str, auth_header_solicitante: Dict[str, str], sala_de_teste: Dict[str, Any]):
    """Verifica se um Solicitante pode marcar uma sala ativa como suja (com observações)."""
    sala_uuid = sala_de_teste["qr_code_id"]
    payload = {"observacoes": "Material derramado no chão durante o evento."}

    response = requests.post(
        f"{api_base_url}/salas/{sala_uuid}/marcar_como_suja/",
        headers=auth_header_solicitante,
        json=payload # A action aceita JSON ou form-data
    )

    assert response.status_code == 201, f"Falha ao marcar sala como suja: {response.text}"
    assert response.json().get("status") == "Relatório de sala suja enviado com sucesso."

    # Verificar se o status da sala mudou (requer uma nova consulta)
    response_get = requests.get(f"{api_base_url}/salas/{sala_uuid}/", headers=auth_header_solicitante)
    assert response_get.status_code == 200
    sala_data = response_get.json()
    assert sala_data["status_limpeza"] == "Suja"
    assert sala_data["detalhes_suja"] is not None
    assert sala_data["detalhes_suja"]["observacoes"] == payload["observacoes"]
    assert sala_data["detalhes_suja"]["reportado_por"] == os.getenv("TEST_USER_SOLICITANTE_USERNAME")


def test_marcar_como_suja_solicitante_sem_observacoes_sucesso(api_base_url: str, auth_header_solicitante: Dict[str, str], sala_de_teste: Dict[str, Any]):
    """Verifica se um Solicitante pode marcar uma sala ativa como suja (sem observações)."""
    sala_uuid = sala_de_teste["qr_code_id"]

    response = requests.post(
        f"{api_base_url}/salas/{sala_uuid}/marcar_como_suja/",
        headers=auth_header_solicitante,
        json={} # Envia corpo JSON vazio
    )

    assert response.status_code == 201
    assert response.json().get("status") == "Relatório de sala suja enviado com sucesso."

    # Verificar se o status da sala mudou
    response_get = requests.get(f"{api_base_url}/salas/{sala_uuid}/", headers=auth_header_solicitante)
    assert response_get.status_code == 200
    sala_data = response_get.json()
    assert sala_data["status_limpeza"] == "Suja"
    assert sala_data["detalhes_suja"] is not None
    assert sala_data["detalhes_suja"]["observacoes"] in [None, ""] # Verifica se observações está vazia ou nula


@pytest.mark.parametrize(
    "auth_fixture",
    [
        "auth_header_admin",
        "auth_header_zelador",
    ],
)
def test_marcar_como_suja_outros_usuarios_falha(api_base_url: str, request: Any, auth_fixture: str, sala_de_teste: Dict[str, Any]):
    """Verifica se Admin e Zelador são proibidos (403) de marcar sala como suja."""
    sala_uuid = sala_de_teste["qr_code_id"]
    header = request.getfixturevalue(auth_fixture)
    response = requests.post(
        f"{api_base_url}/salas/{sala_uuid}/marcar_como_suja/",
        headers=header,
        json={}
    )
    assert response.status_code == 403


def test_marcar_como_suja_sala_inativa_falha(api_base_url: str, auth_header_admin: Dict[str, str], auth_header_solicitante: Dict[str, str], sala_de_teste: Dict[str, Any]):
    """Verifica se falha (400) ao tentar marcar uma sala inativa como suja."""
    sala_uuid = sala_de_teste["qr_code_id"]

    # 1. Desativar a sala (usando o admin)
    response_patch = requests.patch(
        f"{api_base_url}/salas/{sala_uuid}/",
        headers=auth_header_admin,
        data={"ativa": False} # Usa 'data' pois PATCH pode ser multipart
    )
    assert response_patch.status_code == 200, f"Falha ao desativar sala para o teste: {response_patch.text}"

    # 2. Tentar marcar como suja com o solicitante
    response_marcar = requests.post(
        f"{api_base_url}/salas/{sala_uuid}/marcar_como_suja/",
        headers=auth_header_solicitante,
        json={}
    )
    assert response_marcar.status_code == 400
    assert "Não é possível reportar uma sala inativa" in response_marcar.json().get("detail", "")

    # 3. Reativar a sala (opcional, boa prática)
    requests.patch(f"{api_base_url}/salas/{sala_uuid}/", headers=auth_header_admin, data={"ativa": True})
