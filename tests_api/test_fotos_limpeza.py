"""Testes de integração para o endpoint de Fotos de Limpeza (/api/fotos_limpeza/)."""

import os
import pytest
import requests
import uuid
from pathlib import Path
from typing import Dict, Any


@pytest.fixture
def setup_fotos_para_listagem(
    api_base_url: str,
    auth_header_admin: Dict[str, str],
    auth_header_zelador: Dict[str, str],
    auth_header_assistente: Dict[str, str],
    test_image_path: Path,
) -> Dict[str, Any]:
    """
    Fixture para criar o cenário necessário para testar a listagem de fotos.

    Cria duas salas, inicia e conclui limpezas (uma por 'zelador', outra por 'assistente'),
    adicionando uma foto a cada limpeza durante o processo. Retorna os dados relevantes.
    """
    zelador1_username = os.getenv("TEST_USER_ZELADOR_USERNAME")
    zelador2_username = os.getenv("TEST_USER_ASSISTENTE_USERNAME")

    salas_criadas_uuids = []
    registros_limpeza_ids = {}
    fotos_criadas = {}

    for i in range(2):
        nome_sala = f"Sala Foto Teste {uuid.uuid4()}"
        payload_sala = {
            "nome_numero": nome_sala,
            "capacidade": 10 + i,
            "localizacao": f"Bloco Foto {i}",
            "validade_limpeza_horas": 4,
        }
        response_sala = requests.post(
            f"{api_base_url}/salas/", headers=auth_header_admin, data=payload_sala
        )
        assert response_sala.status_code == 201, f"Fixture: Falha ao criar sala {i}"
        salas_criadas_uuids.append(response_sala.json()["qr_code_id"])

    def _simular_limpeza_com_foto(
        sala_uuid: str, auth_header: Dict[str, str], zelador_username: str
    ):

        resp_iniciar = requests.post(
            f"{api_base_url}/salas/{sala_uuid}/iniciar_limpeza/", headers=auth_header
        )
        assert (
            resp_iniciar.status_code == 201
        ), f"Fixture: Falha ao iniciar limpeza por {zelador_username}"
        registro_id = resp_iniciar.json()["id"]
        registros_limpeza_ids[zelador_username] = registro_id

        with open(test_image_path, "rb") as img:
            files = {"imagem": (test_image_path.name, img, "image/png")}
            data = {"registro_limpeza": str(registro_id)}
            resp_foto = requests.post(
                f"{api_base_url}/fotos_limpeza/",
                headers=auth_header,
                data=data,
                files=files,
            )
            assert (
                resp_foto.status_code == 201
            ), f"Fixture: Falha ao adicionar foto por {zelador_username}"
            fotos_criadas[zelador_username] = resp_foto.json()["id"]

        resp_concluir = requests.post(
            f"{api_base_url}/salas/{sala_uuid}/concluir_limpeza/", headers=auth_header
        )
        assert (
            resp_concluir.status_code == 200
        ), f"Fixture: Falha ao concluir limpeza por {zelador_username}"

    _simular_limpeza_com_foto(
        salas_criadas_uuids[0], auth_header_zelador, zelador1_username
    )
    _simular_limpeza_com_foto(
        salas_criadas_uuids[1], auth_header_assistente, zelador2_username
    )

    yield {
        "zelador1": zelador1_username,
        "zelador2": zelador2_username,
        "foto_id_zelador1": fotos_criadas[zelador1_username],
        "foto_id_zelador2": fotos_criadas[zelador2_username],
        "salas_uuids": salas_criadas_uuids,
    }

    for sala_uuid in salas_criadas_uuids:

        requests.patch(
            f"{api_base_url}/salas/{sala_uuid}/",
            headers=auth_header_admin,
            data={"ativa": True},
        )
        requests.delete(f"{api_base_url}/salas/{sala_uuid}/", headers=auth_header_admin)


def test_listar_fotos_nao_autenticado_falha(api_base_url: str):
    """Verifica se acesso não autenticado é negado (401)."""
    response = requests.get(f"{api_base_url}/fotos_limpeza/")
    assert response.status_code == 401


def test_listar_fotos_como_solicitante_lista_vazia(
    api_base_url: str,
    auth_header_solicitante: Dict[str, str],
    setup_fotos_para_listagem: Dict[str, Any],
):
    """Verifica se Solicitante recebe 200 OK com uma lista vazia."""
    response = requests.get(
        f"{api_base_url}/fotos_limpeza/", headers=auth_header_solicitante
    )
    assert response.status_code == 200
    assert response.json() == []


def test_listar_fotos_como_zelador_proprio(
    api_base_url: str,
    auth_header_zelador: Dict[str, str],
    setup_fotos_para_listagem: Dict[str, Any],
):
    """Verifica se Zelador lista apenas suas próprias fotos."""
    response = requests.get(
        f"{api_base_url}/fotos_limpeza/", headers=auth_header_zelador
    )
    assert response.status_code == 200
    fotos_listadas = response.json()

    foto_id_propria = setup_fotos_para_listagem["foto_id_zelador1"]
    foto_id_outro = setup_fotos_para_listagem["foto_id_zelador2"]

    assert len(fotos_listadas) > 0

    ids_listados = {foto["id"] for foto in fotos_listadas}

    assert foto_id_propria in ids_listados
    assert foto_id_outro not in ids_listados


def test_listar_fotos_como_admin(
    api_base_url: str,
    auth_header_admin: Dict[str, str],
    setup_fotos_para_listagem: Dict[str, Any],
):
    """Verifica se Admin lista fotos de todos os zeladores."""
    response = requests.get(f"{api_base_url}/fotos_limpeza/", headers=auth_header_admin)
    assert response.status_code == 200
    fotos_listadas = response.json()

    foto_id_zelador1 = setup_fotos_para_listagem["foto_id_zelador1"]
    foto_id_zelador2 = setup_fotos_para_listagem["foto_id_zelador2"]

    assert len(fotos_listadas) >= 2

    ids_listados = {foto["id"] for foto in fotos_listadas}

    assert foto_id_zelador1 in ids_listados
    assert foto_id_zelador2 in ids_listados


# Testes de Recuperação (GET /api/fotos_limpeza/{id}/)


def test_recuperar_foto_nao_autenticado_falha(
    api_base_url: str, setup_fotos_para_listagem: Dict[str, Any]
):
    """Verifica se acesso não autenticado é negado (401)."""
    foto_id = setup_fotos_para_listagem["foto_id_zelador1"]
    response = requests.get(f"{api_base_url}/fotos_limpeza/{foto_id}/")
    assert response.status_code == 401


def test_recuperar_foto_como_solicitante_falha(
    api_base_url: str,
    auth_header_solicitante: Dict[str, str],
    setup_fotos_para_listagem: Dict[str, Any],
):
    """Verifica se Solicitante recebe 404 ao tentar ver detalhes de uma foto."""
    foto_id = setup_fotos_para_listagem["foto_id_zelador1"]
    response = requests.get(
        f"{api_base_url}/fotos_limpeza/{foto_id}/", headers=auth_header_solicitante
    )

    assert response.status_code == 404


def test_recuperar_foto_propria_como_zelador(
    api_base_url: str,
    auth_header_zelador: Dict[str, str],
    setup_fotos_para_listagem: Dict[str, Any],
):
    """Verifica se Zelador pode recuperar detalhes de sua própria foto."""
    foto_id_propria = setup_fotos_para_listagem["foto_id_zelador1"]
    response = requests.get(
        f"{api_base_url}/fotos_limpeza/{foto_id_propria}/", headers=auth_header_zelador
    )
    assert response.status_code == 200
    foto_data = response.json()
    assert foto_data["id"] == foto_id_propria
    assert "imagem" in foto_data


def test_recuperar_foto_outro_zelador_falha(
    api_base_url: str,
    auth_header_zelador: Dict[str, str],
    setup_fotos_para_listagem: Dict[str, Any],
):
    """Verifica se Zelador recebe 404 ao tentar ver foto de outro zelador."""
    foto_id_outro = setup_fotos_para_listagem["foto_id_zelador2"]
    response = requests.get(
        f"{api_base_url}/fotos_limpeza/{foto_id_outro}/", headers=auth_header_zelador
    )
    assert response.status_code == 404


def test_recuperar_foto_como_admin(
    api_base_url: str,
    auth_header_admin: Dict[str, str],
    setup_fotos_para_listagem: Dict[str, Any],
):
    """Verifica se Admin pode recuperar detalhes de qualquer foto."""
    foto_id_zelador1 = setup_fotos_para_listagem["foto_id_zelador1"]
    foto_id_zelador2 = setup_fotos_para_listagem["foto_id_zelador2"]

    response1 = requests.get(
        f"{api_base_url}/fotos_limpeza/{foto_id_zelador1}/", headers=auth_header_admin
    )
    assert response1.status_code == 200
    foto_data1 = response1.json()
    assert foto_data1["id"] == foto_id_zelador1

    response2 = requests.get(
        f"{api_base_url}/fotos_limpeza/{foto_id_zelador2}/", headers=auth_header_admin
    )
    assert response2.status_code == 200
    foto_data2 = response2.json()
    assert foto_data2["id"] == foto_id_zelador2


# Testes de Exclusão (DELETE /api/fotos_limpeza/{id}/)


def test_excluir_foto_nao_autenticado_falha(
    api_base_url: str, setup_fotos_para_listagem: Dict[str, Any]
):
    """Verifica se acesso não autenticado é negado (401)."""
    foto_id = setup_fotos_para_listagem["foto_id_zelador1"]
    response = requests.delete(f"{api_base_url}/fotos_limpeza/{foto_id}/")
    assert response.status_code == 401


def test_excluir_foto_como_solicitante_falha(
    api_base_url: str,
    auth_header_solicitante: Dict[str, str],
    setup_fotos_para_listagem: Dict[str, Any],
):
    """Verifica se Solicitante recebe 404 ao tentar excluir uma foto."""
    foto_id = setup_fotos_para_listagem["foto_id_zelador1"]
    response = requests.delete(
        f"{api_base_url}/fotos_limpeza/{foto_id}/", headers=auth_header_solicitante
    )

    assert response.status_code == 404


def test_excluir_foto_outro_zelador_falha(
    api_base_url: str,
    auth_header_zelador: Dict[str, str],
    setup_fotos_para_listagem: Dict[str, Any],
):
    """Verifica se Zelador recebe 404 ao tentar excluir foto de outro zelador."""
    foto_id_outro = setup_fotos_para_listagem["foto_id_zelador2"]
    response = requests.delete(
        f"{api_base_url}/fotos_limpeza/{foto_id_outro}/", headers=auth_header_zelador
    )
    assert response.status_code == 404


def test_excluir_foto_propria_como_zelador(
    api_base_url: str,
    auth_header_zelador: Dict[str, str],
    setup_fotos_para_listagem: Dict[str, Any],
    request,
):
    """Verifica se Zelador pode excluir sua própria foto."""
    foto_id_propria = setup_fotos_para_listagem["foto_id_zelador1"]

    response_delete = requests.delete(
        f"{api_base_url}/fotos_limpeza/{foto_id_propria}/", headers=auth_header_zelador
    )

    assert response_delete.status_code == 204

    response_get = requests.get(
        f"{api_base_url}/fotos_limpeza/{foto_id_propria}/", headers=auth_header_zelador
    )
    assert response_get.status_code == 404


def test_excluir_foto_como_admin(
    api_base_url: str,
    auth_header_admin: Dict[str, str],
    setup_fotos_para_listagem: Dict[str, Any],
    request,
):
    """Verifica se Admin pode excluir qualquer foto (ex: a do zelador2)."""
    foto_id_zelador2 = setup_fotos_para_listagem["foto_id_zelador2"]

    response_delete = requests.delete(
        f"{api_base_url}/fotos_limpeza/{foto_id_zelador2}/", headers=auth_header_admin
    )

    assert response_delete.status_code == 204

    response_get = requests.get(
        f"{api_base_url}/fotos_limpeza/{foto_id_zelador2}/", headers=auth_header_admin
    )
    assert response_get.status_code == 404


# Testes de Permissão de Criação (POST /api/fotos_limpeza/)


def test_criar_foto_nao_autenticado_falha(api_base_url: str, test_image_path: Path):
    """Verifica se não autenticado recebe 401 ao tentar criar foto."""
    payload = {"registro_limpeza": "1"}
    with open(test_image_path, "rb") as image_file:
        files = {"imagem": (test_image_path.name, image_file, "image/png")}
        response = requests.post(
            f"{api_base_url}/fotos_limpeza/", data=payload, files=files
        )
    assert response.status_code == 401


@pytest.mark.parametrize(
    "auth_fixture",
    [
        "auth_header_admin",
        "auth_header_solicitante",
    ],
)
def test_criar_foto_permissoes_invalidas_falha(
    api_base_url: str,
    request: Any,
    auth_fixture: str,
    test_image_path: Path,
    iniciar_limpeza_para_teste: Dict[str, Any],
):
    """Verifica se Admin e Solicitante recebem 403 ao tentar criar foto."""
    header = request.getfixturevalue(auth_fixture)
    registro_id = iniciar_limpeza_para_teste["id"]
    payload = {"registro_limpeza": str(registro_id)}

    with open(test_image_path, "rb") as image_file:
        files = {"imagem": (test_image_path.name, image_file, "image/png")}
        response = requests.post(
            f"{api_base_url}/fotos_limpeza/", headers=header, data=payload, files=files
        )
    assert response.status_code == 403


# Testes de Permissão de Criação (POST /api/fotos_limpeza/)


def test_criar_foto_nao_autenticado_falha(api_base_url: str, test_image_path: Path):
    """Verifica se não autenticado recebe 401 ao tentar criar foto."""
    payload = {"registro_limpeza": "1"}
    with open(test_image_path, "rb") as image_file:
        files = {"imagem": (test_image_path.name, image_file, "image/png")}
        response = requests.post(
            f"{api_base_url}/fotos_limpeza/", data=payload, files=files
        )
    assert response.status_code == 401


@pytest.mark.parametrize(
    "auth_fixture",
    [
        "auth_header_admin",
        "auth_header_solicitante",
    ],
)
def test_criar_foto_permissoes_invalidas_falha(
    api_base_url: str,
    request: Any,
    auth_fixture: str,
    test_image_path: Path,
    iniciar_limpeza_para_teste: Dict[str, Any],
):
    """Verifica se Admin e Solicitante recebem 403 ao tentar criar foto."""
    header = request.getfixturevalue(auth_fixture)
    registro_id = iniciar_limpeza_para_teste["id"]
    payload = {"registro_limpeza": str(registro_id)}

    with open(test_image_path, "rb") as image_file:
        files = {"imagem": (test_image_path.name, image_file, "image/png")}
        response = requests.post(
            f"{api_base_url}/fotos_limpeza/", headers=header, data=payload, files=files
        )
    assert response.status_code == 403
