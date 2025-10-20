"""Testes de integração para o endpoint de Histórico de Limpeza (/api/limpezas/)."""

import os
import pytest
import requests
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from pathlib import Path


# Testes de Permissão para Listagem (GET /api/limpezas/)


def test_listar_historico_como_admin(
    api_base_url: str, auth_header_admin: Dict[str, str]
):
    """Verifica se um Admin pode listar o histórico de limpezas com sucesso (200 OK)."""
    response = requests.get(f"{api_base_url}/limpezas/", headers=auth_header_admin)
    assert response.status_code == 200

    assert isinstance(response.json(), list)


def test_listar_historico_como_zelador(
    api_base_url: str, auth_header_zelador: Dict[str, str]
):
    """Verifica se um Zelador pode listar o histórico de limpezas com sucesso (200 OK)."""
    response = requests.get(f"{api_base_url}/limpezas/", headers=auth_header_zelador)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_listar_historico_como_solicitante_falha(
    api_base_url: str, auth_header_solicitante: Dict[str, str]
):
    """Verifica se um Solicitante é proibido (403 Forbidden) de listar o histórico."""
    response = requests.get(
        f"{api_base_url}/limpezas/", headers=auth_header_solicitante
    )
    assert response.status_code == 403


def test_listar_historico_sem_autenticacao_falha(api_base_url: str):
    """Verifica se um usuário não autenticado é proibido (401 Unauthorized) de listar o histórico."""
    response = requests.get(f"{api_base_url}/limpezas/")
    assert response.status_code == 401


@pytest.fixture
def setup_registros_multiplos_zeladores(
    api_base_url: str,
    auth_header_admin: Dict[str, str],
    auth_header_zelador: Dict[str, str],
    auth_header_assistente: Dict[str, str],
    test_image_path: Path,
) -> Dict[str, Any]:
    """
    Cria duas salas e registra limpezas concluídas por dois zeladores diferentes.
    Retorna os usernames dos zeladores e os dados dos registros criados.
    """
    zelador1_username = os.getenv("TEST_USER_ZELADOR_USERNAME")
    zelador2_username = os.getenv("TEST_USER_ASSISTENTE_USERNAME")

    salas_criadas_uuids = []
    registros_zelador1 = []
    registros_zelador2 = []

    for i in range(2):
        nome_sala = f"Sala Histórico Teste {uuid.uuid4()}"
        payload_sala = {
            "nome_numero": nome_sala,
            "capacidade": 10 + i,
            "localizacao": f"Bloco Histórico {i}",
            "validade_limpeza_horas": 4,
        }
        response_sala = requests.post(
            f"{api_base_url}/salas/", headers=auth_header_admin, data=payload_sala
        )
        assert response_sala.status_code == 201, f"Fixture: Falha ao criar sala {i}"
        salas_criadas_uuids.append(response_sala.json()["qr_code_id"])

    def _simular_limpeza_completa(sala_uuid: str, auth_header: Dict[str, str]):

        resp_iniciar = requests.post(
            f"{api_base_url}/salas/{sala_uuid}/iniciar_limpeza/", headers=auth_header
        )
        assert (
            resp_iniciar.status_code == 201
        ), f"Fixture: Falha ao iniciar limpeza para {sala_uuid}"
        registro_id = resp_iniciar.json()["id"]

        with open(test_image_path, "rb") as img:
            files = {"imagem": (test_image_path.name, img, "image/png")}
            resp_foto = requests.post(
                f"{api_base_url}/fotos_limpeza/",
                headers=auth_header,
                data={"registro_limpeza": str(registro_id)},
                files=files,
            )
            assert (
                resp_foto.status_code == 201
            ), f"Fixture: Falha ao add foto para {sala_uuid}"

        resp_concluir = requests.post(
            f"{api_base_url}/salas/{sala_uuid}/concluir_limpeza/",
            headers=auth_header,
            json={"observacoes": f"Limpeza por {auth_header}"},
        )
        assert (
            resp_concluir.status_code == 200
        ), f"Fixture: Falha ao concluir limpeza para {sala_uuid}"
        return resp_concluir.json()

    registros_zelador1.append(
        _simular_limpeza_completa(salas_criadas_uuids[0], auth_header_zelador)
    )

    registros_zelador2.append(
        _simular_limpeza_completa(salas_criadas_uuids[1], auth_header_assistente)
    )

    yield {
        "zelador1": zelador1_username,
        "zelador2": zelador2_username,
        "registros1": registros_zelador1,
        "registros2": registros_zelador2,
        "salas_uuids": salas_criadas_uuids,
    }

    for sala_uuid in salas_criadas_uuids:
        requests.delete(f"{api_base_url}/salas/{sala_uuid}/", headers=auth_header_admin)


def test_listar_historico_zelador_ve_apenas_seus_registros(
    api_base_url: str,
    auth_header_zelador: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any],
):
    """Verifica se um Zelador, ao listar, vê apenas seus próprios registros."""

    zelador_logado = os.getenv("TEST_USER_ZELADOR_USERNAME")

    outro_zelador = setup_registros_multiplos_zeladores["zelador2"]

    response = requests.get(f"{api_base_url}/limpezas/", headers=auth_header_zelador)
    assert response.status_code == 200
    registros_retornados = response.json()

    assert (
        len(registros_retornados) > 0
    ), "A lista de registros retornada está vazia, mas deveria conter registros do zelador logado."

    for registro in registros_retornados:

        assert (
            registro["funcionario_responsavel"] == zelador_logado
        ), f"Registro {registro['id']} pertence a {registro['funcionario_responsavel']}, mas deveria ser de {zelador_logado}."

        assert (
            registro["funcionario_responsavel"] != outro_zelador
        ), f"Registro {registro['id']} pertence ao outro zelador ({outro_zelador}), mas não deveria aparecer na lista do {zelador_logado}."


# Testes para Filtros (GET /api/limpezas/)


def test_filtro_sala_uuid_admin(
    api_base_url: str,
    auth_header_admin: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any],
):
    """Verifica se o Admin pode filtrar registros por sala_uuid específico."""
    sala_uuid_para_filtrar = setup_registros_multiplos_zeladores["salas_uuids"][0]

    zelador_esperado = setup_registros_multiplos_zeladores["zelador1"]

    params = {"sala_uuid": sala_uuid_para_filtrar}
    response = requests.get(
        f"{api_base_url}/limpezas/", headers=auth_header_admin, params=params
    )

    assert response.status_code == 200
    registros_filtrados = response.json()
    assert len(registros_filtrados) == 1
    assert registros_filtrados[0]["sala"] == sala_uuid_para_filtrar
    assert registros_filtrados[0]["funcionario_responsavel"] == zelador_esperado


def test_filtro_sala_uuid_zelador(
    api_base_url: str,
    auth_header_zelador: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any],
):
    """Verifica se o Zelador pode filtrar seus registros por sala_uuid."""
    sala_uuid_zelador1 = setup_registros_multiplos_zeladores["salas_uuids"][0]
    sala_uuid_zelador2 = setup_registros_multiplos_zeladores["salas_uuids"][1]
    zelador_logado = setup_registros_multiplos_zeladores["zelador1"]

    params1 = {"sala_uuid": sala_uuid_zelador1}
    response1 = requests.get(
        f"{api_base_url}/limpezas/", headers=auth_header_zelador, params=params1
    )
    assert response1.status_code == 200
    registros1 = response1.json()
    assert len(registros1) == 1
    assert registros1[0]["sala"] == sala_uuid_zelador1
    assert registros1[0]["funcionario_responsavel"] == zelador_logado

    params2 = {"sala_uuid": sala_uuid_zelador2}
    response2 = requests.get(
        f"{api_base_url}/limpezas/", headers=auth_header_zelador, params=params2
    )
    assert response2.status_code == 200
    registros2 = response2.json()
    assert len(registros2) == 0


def test_filtro_sala_nome_parcial_admin(
    api_base_url: str,
    auth_header_admin: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any],
):
    """Verifica se o Admin pode filtrar registros por nome parcial da sala."""

    nome_parcial = "Histórico Teste"

    registros_esperados = (
        setup_registros_multiplos_zeladores["registros1"]
        + setup_registros_multiplos_zeladores["registros2"]
    )
    ids_esperados = {reg["id"] for reg in registros_esperados}

    params = {"sala_nome": nome_parcial}
    response = requests.get(
        f"{api_base_url}/limpezas/", headers=auth_header_admin, params=params
    )

    assert response.status_code == 200
    registros_filtrados = response.json()
    ids_retornados = {reg["id"] for reg in registros_filtrados}

    assert len(registros_filtrados) == len(ids_esperados)
    assert ids_retornados == ids_esperados
    for reg in registros_filtrados:
        assert nome_parcial in reg["sala_nome"]


def test_filtro_sala_nome_parcial_zelador(
    api_base_url: str,
    auth_header_zelador: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any],
):
    """Verifica se o Zelador pode filtrar seus registros por nome parcial da sala."""
    nome_parcial = "Histórico Teste"
    zelador_logado = setup_registros_multiplos_zeladores["zelador1"]

    registro_esperado_id = setup_registros_multiplos_zeladores["registros1"][0]["id"]

    params = {"sala_nome": nome_parcial}
    response = requests.get(
        f"{api_base_url}/limpezas/", headers=auth_header_zelador, params=params
    )

    assert response.status_code == 200
    registros_filtrados = response.json()

    assert len(registros_filtrados) == 1
    assert registros_filtrados[0]["id"] == registro_esperado_id
    assert registros_filtrados[0]["funcionario_responsavel"] == zelador_logado
    assert nome_parcial in registros_filtrados[0]["sala_nome"]


def test_filtro_sala_nome_nao_encontrado(
    api_base_url: str,
    auth_header_admin: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any],
):
    """Verifica se o filtro por nome retorna lista vazia quando nada corresponde."""
    params = {"sala_nome": "NomeInexistente"}
    response = requests.get(
        f"{api_base_url}/limpezas/", headers=auth_header_admin, params=params
    )
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_filtro_funcionario_username_admin(
    api_base_url: str,
    auth_header_admin: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any],
):
    """Verifica se o Admin pode filtrar registros pelo username do funcionário."""

    username_para_filtrar = setup_registros_multiplos_zeladores["zelador1"]
    registro_esperado_id = setup_registros_multiplos_zeladores["registros1"][0]["id"]

    params = {"funcionario_username": username_para_filtrar}
    response = requests.get(
        f"{api_base_url}/limpezas/", headers=auth_header_admin, params=params
    )

    assert response.status_code == 200
    registros_filtrados = response.json()
    assert len(registros_filtrados) >= 1

    ids_retornados = {reg["id"] for reg in registros_filtrados}
    assert registro_esperado_id in ids_retornados

    for reg in registros_filtrados:
        assert reg["funcionario_responsavel"] == username_para_filtrar


def test_filtro_funcionario_username_zelador_proprio(
    api_base_url: str,
    auth_header_zelador: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any],
):
    """Verifica se o Zelador pode filtrar pelo seu próprio username."""
    zelador_logado = setup_registros_multiplos_zeladores["zelador1"]
    registro_esperado_id = setup_registros_multiplos_zeladores["registros1"][0]["id"]

    params = {"funcionario_username": zelador_logado}
    response = requests.get(
        f"{api_base_url}/limpezas/", headers=auth_header_zelador, params=params
    )

    assert response.status_code == 200
    registros_filtrados = response.json()
    assert len(registros_filtrados) == 1
    assert registros_filtrados[0]["id"] == registro_esperado_id
    assert registros_filtrados[0]["funcionario_responsavel"] == zelador_logado


def test_filtro_funcionario_username_zelador_outro_falha(
    api_base_url: str,
    auth_header_zelador: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any],
):
    """Verifica se o Zelador obtém lista vazia ao filtrar pelo username de outro zelador."""
    outro_zelador = setup_registros_multiplos_zeladores["zelador2"]

    params = {"funcionario_username": outro_zelador}
    response = requests.get(
        f"{api_base_url}/limpezas/", headers=auth_header_zelador, params=params
    )

    assert response.status_code == 200
    registros_filtrados = response.json()

    assert len(registros_filtrados) == 0


def test_filtro_data_after_admin(
    api_base_url: str,
    auth_header_admin: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any],
):
    """Verifica se o Admin pode filtrar registros após uma data."""

    registro1_fim_str = setup_registros_multiplos_zeladores["registros1"][0][
        "data_hora_fim"
    ]
    registro1_fim_dt = datetime.fromisoformat(registro1_fim_str)
    data_filtro = (registro1_fim_dt - timedelta(days=1)).strftime("%Y-%m-%d")

    params = {"data_hora_fim_after": data_filtro}
    response = requests.get(
        f"{api_base_url}/limpezas/", headers=auth_header_admin, params=params
    )

    assert response.status_code == 200
    registros_filtrados = response.json()
    assert len(registros_filtrados) >= 2
    ids_esperados = {
        reg["id"]
        for reg in setup_registros_multiplos_zeladores["registros1"]
        + setup_registros_multiplos_zeladores["registros2"]
    }
    ids_retornados = {reg["id"] for reg in registros_filtrados}
    assert ids_esperados.issubset(ids_retornados)


def test_filtro_data_before_admin(
    api_base_url: str,
    auth_header_admin: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any],
):
    """Verifica se o Admin pode filtrar registros antes de uma data."""

    registro2_fim_str = setup_registros_multiplos_zeladores["registros2"][0][
        "data_hora_fim"
    ]
    registro2_fim_dt = datetime.fromisoformat(registro2_fim_str)
    data_filtro = (registro2_fim_dt + timedelta(days=1)).strftime("%Y-%m-%d")

    params = {"data_hora_limpeza_before": data_filtro}
    response = requests.get(
        f"{api_base_url}/limpezas/", headers=auth_header_admin, params=params
    )

    assert response.status_code == 200
    registros_filtrados = response.json()
    assert len(registros_filtrados) >= 2
    ids_esperados = {
        reg["id"]
        for reg in setup_registros_multiplos_zeladores["registros1"]
        + setup_registros_multiplos_zeladores["registros2"]
    }
    ids_retornados = {reg["id"] for reg in registros_filtrados}
    assert ids_esperados.issubset(ids_retornados)


def test_filtro_data_range_zelador(
    api_base_url: str,
    auth_header_zelador: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any],
):
    """Verifica se o Zelador pode filtrar seus registros por intervalo de datas."""
    zelador_logado = setup_registros_multiplos_zeladores["zelador1"]
    registro1_fim_str = setup_registros_multiplos_zeladores["registros1"][0][
        "data_hora_fim"
    ]
    registro1_fim_dt = datetime.fromisoformat(registro1_fim_str)

    data_inicio_filtro = (registro1_fim_dt - timedelta(hours=1)).strftime("%Y-%m-%d")
    data_fim_filtro = (registro1_fim_dt + timedelta(hours=1)).strftime("%Y-%m-%d")

    params = {
        "data_hora_limpeza_after": data_inicio_filtro,
        "data_hora_limpeza_before": data_fim_filtro,
    }
    response = requests.get(
        f"{api_base_url}/limpezas/", headers=auth_header_zelador, params=params
    )

    assert response.status_code == 200
    registros_filtrados = response.json()

    assert len(registros_filtrados) == 1
    assert (
        registros_filtrados[0]["id"]
        == setup_registros_multiplos_zeladores["registros1"][0]["id"]
    )
    assert registros_filtrados[0]["funcionario_responsavel"] == zelador_logado


# Testes para Detalhes (GET /api/limpezas/{id}/)


def test_detalhes_limpeza_admin(
    api_base_url: str,
    auth_header_admin: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any],
):
    """Verifica se o Admin pode ver detalhes de qualquer registro de limpeza."""

    registro_id = setup_registros_multiplos_zeladores["registros1"][0]["id"]
    sala_uuid_esperado = setup_registros_multiplos_zeladores["salas_uuids"][0]

    response = requests.get(
        f"{api_base_url}/limpezas/{registro_id}/", headers=auth_header_admin
    )

    assert response.status_code == 200
    detalhes = response.json()
    assert detalhes["id"] == registro_id
    assert detalhes["sala"] == sala_uuid_esperado
    assert (
        detalhes["funcionario_responsavel"]
        == setup_registros_multiplos_zeladores["zelador1"]
    )


def test_detalhes_limpeza_zelador_proprio(
    api_base_url: str,
    auth_header_zelador: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any],
):
    """Verifica se o Zelador pode ver detalhes do seu próprio registro."""
    registro_id = setup_registros_multiplos_zeladores["registros1"][0]["id"]
    zelador_logado = setup_registros_multiplos_zeladores["zelador1"]

    response = requests.get(
        f"{api_base_url}/limpezas/{registro_id}/", headers=auth_header_zelador
    )

    assert response.status_code == 200
    detalhes = response.json()
    assert detalhes["id"] == registro_id
    assert detalhes["funcionario_responsavel"] == zelador_logado


def test_detalhes_limpeza_zelador_outro_falha(
    api_base_url: str,
    auth_header_zelador: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any],
):
    """Verifica se o Zelador recebe 404 ao tentar ver detalhes de registro de outro zelador."""
    registro_id_outro = setup_registros_multiplos_zeladores["registros2"][0]["id"]

    response = requests.get(
        f"{api_base_url}/limpezas/{registro_id_outro}/", headers=auth_header_zelador
    )

    assert response.status_code == 404


def test_detalhes_limpeza_solicitante_falha(
    api_base_url: str,
    auth_header_solicitante: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any],
):
    """Verifica se o Solicitante recebe 403 ao tentar ver detalhes de qualquer registro."""
    registro_id = setup_registros_multiplos_zeladores["registros1"][0]["id"]

    response = requests.get(
        f"{api_base_url}/limpezas/{registro_id}/", headers=auth_header_solicitante
    )

    assert response.status_code == 403


def test_detalhes_limpeza_sem_autenticacao_falha(
    api_base_url: str, setup_registros_multiplos_zeladores: Dict[str, Any]
):
    """Verifica se usuário não autenticado recebe 401 ao tentar ver detalhes."""
    registro_id = setup_registros_multiplos_zeladores["registros1"][0]["id"]

    response = requests.get(f"{api_base_url}/limpezas/{registro_id}/")

    assert response.status_code == 401
