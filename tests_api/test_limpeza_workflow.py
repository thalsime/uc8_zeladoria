"""Testes de integração para o fluxo completo de limpeza."""

import pytest
import requests
import uuid
from typing import Dict, Any # Para type hints
import os
from pathlib import Path

# Fixtures de conftest.py serão injetadas automaticamente pelo pytest

# --- Fixture Auxiliar ---

@pytest.fixture
def iniciar_limpeza_para_teste(api_base_url: str, auth_header_zelador: Dict[str, str], sala_de_teste: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fixture auxiliar que inicia uma limpeza para uma sala de teste
    e retorna os dados do registro de limpeza criado.
    """
    sala_uuid = sala_de_teste["qr_code_id"]
    response = requests.post(
        f"{api_base_url}/salas/{sala_uuid}/iniciar_limpeza/",
        headers=auth_header_zelador
    )
    assert response.status_code == 201, f"Falha ao iniciar limpeza na fixture: {response.text}"
    registro_limpeza = response.json()
    # Adiciona o UUID da sala ao dicionário retornado para facilitar o uso nos testes
    registro_limpeza['sala_uuid_test'] = sala_uuid
    return registro_limpeza


# --- Testes para Iniciar Limpeza ---

def test_iniciar_limpeza_zelador_sucesso(api_base_url: str, auth_header_zelador: Dict[str, str], sala_de_teste: Dict[str, Any]):
    """Verifica se um Zelador pode iniciar a limpeza de uma sala ativa."""
    sala_uuid = sala_de_teste["qr_code_id"]
    response = requests.post(
        f"{api_base_url}/salas/{sala_uuid}/iniciar_limpeza/",
        headers=auth_header_zelador
    )
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["sala"] == sala_uuid
    assert response_data["data_hora_inicio"] is not None
    assert response_data["data_hora_fim"] is None
    assert response_data["funcionario_responsavel"] == os.getenv("TEST_USER_ZELADOR_USERNAME") # Verifica se o zelador correto foi associado


@pytest.mark.parametrize(
    "auth_fixture",
    [
        "auth_header_admin",
        "auth_header_solicitante",
    ],
)
def test_iniciar_limpeza_outros_usuarios_falha(api_base_url: str, request: Any, auth_fixture: str, sala_de_teste: Dict[str, Any]):
    """Verifica se Admin e Solicitante são proibidos (403) de iniciar limpeza."""
    sala_uuid = sala_de_teste["qr_code_id"]
    header = request.getfixturevalue(auth_fixture) # Pega a fixture pelo nome
    response = requests.post(
        f"{api_base_url}/salas/{sala_uuid}/iniciar_limpeza/",
        headers=header
    )
    assert response.status_code == 403


def test_iniciar_limpeza_ja_em_andamento_falha(api_base_url: str, auth_header_zelador: Dict[str, str], iniciar_limpeza_para_teste: Dict[str, Any]):
    """Verifica se falha (400) ao tentar iniciar limpeza em sala que já está sendo limpa."""
    # A fixture 'iniciar_limpeza_para_teste' já iniciou a limpeza
    sala_uuid = iniciar_limpeza_para_teste["sala_uuid_test"]
    response = requests.post(
        f"{api_base_url}/salas/{sala_uuid}/iniciar_limpeza/",
        headers=auth_header_zelador
    )
    assert response.status_code == 400
    assert "já está em processo de limpeza" in response.json().get("detail", "")


def test_iniciar_limpeza_sala_inativa_falha(api_base_url: str, auth_header_admin: Dict[str, str], auth_header_zelador: Dict[str, str], sala_de_teste: Dict[str, Any]):
    """Verifica se falha (400) ao tentar iniciar limpeza em sala inativa."""
    sala_uuid = sala_de_teste["qr_code_id"]

    # 1. Desativar a sala (usando o admin)
    response_patch = requests.patch(
        f"{api_base_url}/salas/{sala_uuid}/",
        headers=auth_header_admin,
        data={"ativa": False}
    )
    assert response_patch.status_code == 200, f"Falha ao desativar sala para o teste: {response_patch.text}"
    assert not response_patch.json()["ativa"]

    # 2. Tentar iniciar a limpeza com o zelador
    response_iniciar = requests.post(
        f"{api_base_url}/salas/{sala_uuid}/iniciar_limpeza/",
        headers=auth_header_zelador
    )
    assert response_iniciar.status_code == 400
    assert "Salas inativas não podem ter a limpeza iniciada" in response_iniciar.json().get("detail", "")

    # 3. Reativar a sala para não afetar outros testes (limpeza da fixture sala_de_teste)
    #    Embora a fixture sala_de_teste recrie a sala, é boa prática limpar o estado modificado.
    requests.patch(f"{api_base_url}/salas/{sala_uuid}/", headers=auth_header_admin, data={"ativa": True})


# --- Testes para Adicionar Foto de Limpeza ---

def test_adicionar_foto_zelador_sucesso(api_base_url: str, auth_header_zelador: Dict[str, str], iniciar_limpeza_para_teste: Dict[str, Any], test_image_path: Path):
    """Verifica se um Zelador pode adicionar uma foto a uma limpeza em andamento."""
    registro_id = iniciar_limpeza_para_teste["id"]
    payload = {"registro_limpeza": str(registro_id)}

    with open(test_image_path, "rb") as image_file:
        files = {"imagem": (test_image_path.name, image_file, "image/png")}
        response = requests.post(
            f"{api_base_url}/fotos_limpeza/",
            headers=auth_header_zelador,
            data=payload,
            files=files
        )

    assert response.status_code == 201, f"Falha ao adicionar foto: {response.text}"
    response_data = response.json()
    assert "imagem" in response_data
    assert response_data["imagem"] is not None
    assert "timestamp" in response_data


def test_adicionar_mais_de_tres_fotos_falha(api_base_url: str, auth_header_zelador: Dict[str, str], iniciar_limpeza_para_teste: Dict[str, Any], test_image_path: Path):
    """Verifica se falha (400) ao tentar adicionar mais de 3 fotos."""
    registro_id = iniciar_limpeza_para_teste["id"]
    payload = {"registro_limpeza": str(registro_id)}

    # Adiciona 3 fotos com sucesso primeiro
    for i in range(3):
        with open(test_image_path, "rb") as image_file:
            files = {"imagem": (f"test_{i}.png", image_file, "image/png")}
            response_add = requests.post(f"{api_base_url}/fotos_limpeza/", headers=auth_header_zelador, data=payload, files=files)
            assert response_add.status_code == 201, f"Falha ao adicionar foto {i+1}: {response_add.text}"

    # Tenta adicionar a quarta foto
    with open(test_image_path, "rb") as image_file:
        files = {"imagem": ("test_4.png", image_file, "image/png")}
        response_fourth = requests.post(
            f"{api_base_url}/fotos_limpeza/",
            headers=auth_header_zelador,
            data=payload,
            files=files
        )

    assert response_fourth.status_code == 400
    assert "Limite de 3 fotos" in response_fourth.json().get("detail", "")


@pytest.mark.parametrize(
    "auth_fixture",
    [
        "auth_header_admin",
        "auth_header_solicitante",
    ],
)
def test_adicionar_foto_outros_usuarios_falha(api_base_url: str, request: Any, auth_fixture: str, iniciar_limpeza_para_teste: Dict[str, Any], test_image_path: Path):
    """Verifica se Admin e Solicitante são proibidos (403) de adicionar fotos."""
    registro_id = iniciar_limpeza_para_teste["id"]
    header = request.getfixturevalue(auth_fixture)
    payload = {"registro_limpeza": str(registro_id)}

    with open(test_image_path, "rb") as image_file:
        files = {"imagem": (test_image_path.name, image_file, "image/png")}
        response = requests.post(
            f"{api_base_url}/fotos_limpeza/",
            headers=header,
            data=payload,
            files=files
        )
    assert response.status_code == 403


# --- Testes para Concluir Limpeza ---

def test_concluir_limpeza_zelador_com_foto_sucesso(api_base_url: str, auth_header_zelador: Dict[str, str], iniciar_limpeza_para_teste: Dict[str, Any], test_image_path: Path):
    """Verifica se um Zelador pode concluir a limpeza após adicionar uma foto."""
    registro_id = iniciar_limpeza_para_teste["id"]
    sala_uuid = iniciar_limpeza_para_teste["sala_uuid_test"]

    # 1. Adicionar uma foto
    payload_foto = {"registro_limpeza": str(registro_id)}
    with open(test_image_path, "rb") as image_file:
        files = {"imagem": (test_image_path.name, image_file, "image/png")}
        response_add_foto = requests.post(f"{api_base_url}/fotos_limpeza/", headers=auth_header_zelador, data=payload_foto, files=files)
        assert response_add_foto.status_code == 201

    # 2. Concluir a limpeza
    payload_concluir = {"observacoes": "Limpeza concluída via teste."}
    response_concluir = requests.post(
        f"{api_base_url}/salas/{sala_uuid}/concluir_limpeza/",
        headers=auth_header_zelador,
        json=payload_concluir # Envia como JSON agora
    )

    assert response_concluir.status_code == 200, f"Falha ao concluir limpeza: {response_concluir.text}"
    response_data = response_concluir.json()
    assert response_data["id"] == registro_id
    assert response_data["data_hora_fim"] is not None
    assert response_data["observacoes"] == payload_concluir["observacoes"]
    assert len(response_data["fotos"]) == 1 # Verifica se a foto está associada


def test_concluir_limpeza_sem_foto_falha(api_base_url: str, auth_header_zelador: Dict[str, str], iniciar_limpeza_para_teste: Dict[str, Any]):
    """Verifica se falha (400) ao tentar concluir limpeza sem adicionar fotos."""
    sala_uuid = iniciar_limpeza_para_teste["sala_uuid_test"]

    response = requests.post(
        f"{api_base_url}/salas/{sala_uuid}/concluir_limpeza/",
        headers=auth_header_zelador,
        json={} # Corpo JSON vazio
    )
    assert response.status_code == 400
    assert "enviar pelo menos uma foto" in response.json().get("detail", "")


def test_concluir_limpeza_sem_iniciar_falha(api_base_url: str, auth_header_zelador: Dict[str, str], sala_de_teste: Dict[str, Any]):
    """Verifica se falha (400) ao tentar concluir limpeza que não foi iniciada."""
    sala_uuid = sala_de_teste["qr_code_id"]
    response = requests.post(
        f"{api_base_url}/salas/{sala_uuid}/concluir_limpeza/",
        headers=auth_header_zelador,
        json={}
    )
    assert response.status_code == 400
    assert "Nenhuma limpeza foi iniciada" in response.json().get("detail", "")


@pytest.mark.parametrize(
    "auth_fixture",
    [
        "auth_header_admin",
        "auth_header_solicitante",
    ],
)
def test_concluir_limpeza_outros_usuarios_falha(api_base_url: str, request: Any, auth_fixture: str, sala_de_teste: Dict[str, Any]):
    """Verifica se Admin e Solicitante são proibidos (403) de concluir limpeza."""
    sala_uuid = sala_de_teste["qr_code_id"]
    header = request.getfixturevalue(auth_fixture)
    response = requests.post(
        f"{api_base_url}/salas/{sala_uuid}/concluir_limpeza/",
        headers=header,
        json={}
    )
    assert response.status_code == 403
