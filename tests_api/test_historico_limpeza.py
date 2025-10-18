"""Testes de integração para o endpoint de Histórico de Limpeza (/api/limpezas/)."""

import os
import pytest
import requests
import uuid
from datetime import datetime, timedelta, timezone # Adicione no início do arquivo
from typing import Dict, Any
from pathlib import Path

# Fixtures de conftest.py (api_base_url, auth_header_admin, etc.) serão injetadas

# --- Testes de Permissão para Listagem (GET /api/limpezas/) ---

def test_listar_historico_como_admin(api_base_url: str, auth_header_admin: Dict[str, str]):
    """Verifica se um Admin pode listar o histórico de limpezas com sucesso (200 OK)."""
    response = requests.get(f"{api_base_url}/limpezas/", headers=auth_header_admin)
    assert response.status_code == 200
    # Verifica se a resposta é uma lista (pode estar vazia, mas deve ser uma lista)
    assert isinstance(response.json(), list)


def test_listar_historico_como_zelador(api_base_url: str, auth_header_zelador: Dict[str, str]):
    """Verifica se um Zelador pode listar o histórico de limpezas com sucesso (200 OK)."""
    response = requests.get(f"{api_base_url}/limpezas/", headers=auth_header_zelador)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    # Futuro teste: verificar se ele vê APENAS os seus registros


def test_listar_historico_como_solicitante_falha(api_base_url: str, auth_header_solicitante: Dict[str, str]):
    """Verifica se um Solicitante é proibido (403 Forbidden) de listar o histórico."""
    response = requests.get(f"{api_base_url}/limpezas/", headers=auth_header_solicitante)
    assert response.status_code == 403


def test_listar_historico_sem_autenticacao_falha(api_base_url: str):
    """Verifica se um usuário não autenticado é proibido (401 Unauthorized) de listar o histórico."""
    response = requests.get(f"{api_base_url}/limpezas/")
    assert response.status_code == 401


# --- Fixture para Criar Dados ---

@pytest.fixture
def setup_registros_multiplos_zeladores(
    api_base_url: str,
    auth_header_admin: Dict[str, str],
    auth_header_zelador: Dict[str, str],
    auth_header_assistente: Dict[str, str], # Adiciona a nova fixture
    test_image_path: Path
) -> Dict[str, Any]:
    """
    Cria duas salas e registra limpezas concluídas por dois zeladores diferentes.
    Retorna os usernames dos zeladores e os dados dos registros criados.
    """
    zelador1_username = os.getenv("TEST_USER_ZELADOR_USERNAME")
    zelador2_username = os.getenv("TEST_USER_ASSISTENTE_USERNAME") # Usando assistente como zelador2

    salas_criadas_uuids = []
    registros_zelador1 = []
    registros_zelador2 = []

    # Criar duas salas usando o admin
    for i in range(2):
        nome_sala = f"Sala Histórico Teste {uuid.uuid4()}"
        payload_sala = {
            "nome_numero": nome_sala,
            "capacidade": 10 + i,
            "localizacao": f"Bloco Histórico {i}",
            "validade_limpeza_horas": 4
        }
        response_sala = requests.post(f"{api_base_url}/salas/", headers=auth_header_admin, data=payload_sala)
        assert response_sala.status_code == 201, f"Fixture: Falha ao criar sala {i}"
        salas_criadas_uuids.append(response_sala.json()["qr_code_id"])

    # Função auxiliar para simular limpeza completa
    def _simular_limpeza_completa(sala_uuid: str, auth_header: Dict[str, str]):
        # Iniciar
        resp_iniciar = requests.post(f"{api_base_url}/salas/{sala_uuid}/iniciar_limpeza/", headers=auth_header)
        assert resp_iniciar.status_code == 201, f"Fixture: Falha ao iniciar limpeza para {sala_uuid}"
        registro_id = resp_iniciar.json()["id"]
        # Adicionar foto
        with open(test_image_path, "rb") as img:
            files = {"imagem": (test_image_path.name, img, "image/png")}
            resp_foto = requests.post(f"{api_base_url}/fotos_limpeza/", headers=auth_header, data={"registro_limpeza": str(registro_id)}, files=files)
            assert resp_foto.status_code == 201, f"Fixture: Falha ao add foto para {sala_uuid}"
        # Concluir
        resp_concluir = requests.post(f"{api_base_url}/salas/{sala_uuid}/concluir_limpeza/", headers=auth_header, json={"observacoes": f"Limpeza por {auth_header}"})
        assert resp_concluir.status_code == 200, f"Fixture: Falha ao concluir limpeza para {sala_uuid}"
        return resp_concluir.json()

    # Zelador 1 limpa a Sala 1
    registros_zelador1.append(_simular_limpeza_completa(salas_criadas_uuids[0], auth_header_zelador))

    # Zelador 2 (Assistente) limpa a Sala 2
    registros_zelador2.append(_simular_limpeza_completa(salas_criadas_uuids[1], auth_header_assistente))

    yield {
        "zelador1": zelador1_username,
        "zelador2": zelador2_username,
        "registros1": registros_zelador1,
        "registros2": registros_zelador2,
        "salas_uuids": salas_criadas_uuids
    }

    # Limpeza: deletar as salas criadas (os registros de limpeza serão deletados em cascata)
    for sala_uuid in salas_criadas_uuids:
        requests.delete(f"{api_base_url}/salas/{sala_uuid}/", headers=auth_header_admin)


def test_listar_historico_zelador_ve_apenas_seus_registros(
    api_base_url: str,
    auth_header_zelador: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any] # Usa a fixture que cria os dados
):
    """Verifica se um Zelador, ao listar, vê apenas seus próprios registros."""
    # Username do zelador que está fazendo a requisição
    zelador_logado = os.getenv("TEST_USER_ZELADOR_USERNAME")
    # Username do outro zelador (assistente) cujos registros NÃO devem aparecer
    outro_zelador = setup_registros_multiplos_zeladores["zelador2"]

    # Faz a requisição logado como o zelador principal
    response = requests.get(f"{api_base_url}/limpezas/", headers=auth_header_zelador)
    assert response.status_code == 200
    registros_retornados = response.json()

    # Verifica se a lista não está vazia (a fixture garante que ele tem pelo menos 1 registro)
    assert len(registros_retornados) > 0, "A lista de registros retornada está vazia, mas deveria conter registros do zelador logado."

    # Verifica TODOS os registros retornados
    for registro in registros_retornados:
        # Confirma que o funcionário responsável é o zelador logado
        assert registro["funcionario_responsavel"] == zelador_logado, \
            f"Registro {registro['id']} pertence a {registro['funcionario_responsavel']}, mas deveria ser de {zelador_logado}."
        # Confirma (redundante, mas seguro) que o funcionário não é o outro zelador
        assert registro["funcionario_responsavel"] != outro_zelador, \
            f"Registro {registro['id']} pertence ao outro zelador ({outro_zelador}), mas não deveria aparecer na lista do {zelador_logado}."


# --- Testes para Filtros (GET /api/limpezas/) ---

def test_filtro_sala_uuid_admin(
    api_base_url: str,
    auth_header_admin: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any]
):
    """Verifica se o Admin pode filtrar registros por sala_uuid específico."""
    sala_uuid_para_filtrar = setup_registros_multiplos_zeladores["salas_uuids"][0]
    # Esperamos encontrar o registro do zelador1 para esta sala
    zelador_esperado = setup_registros_multiplos_zeladores["zelador1"]

    params = {"sala_uuid": sala_uuid_para_filtrar}
    response = requests.get(f"{api_base_url}/limpezas/", headers=auth_header_admin, params=params)

    assert response.status_code == 200
    registros_filtrados = response.json()
    assert len(registros_filtrados) == 1 # A fixture criou 1 registro para esta sala
    assert registros_filtrados[0]["sala"] == sala_uuid_para_filtrar
    assert registros_filtrados[0]["funcionario_responsavel"] == zelador_esperado


def test_filtro_sala_uuid_zelador(
    api_base_url: str,
    auth_header_zelador: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any]
):
    """Verifica se o Zelador pode filtrar seus registros por sala_uuid."""
    sala_uuid_zelador1 = setup_registros_multiplos_zeladores["salas_uuids"][0]
    sala_uuid_zelador2 = setup_registros_multiplos_zeladores["salas_uuids"][1]
    zelador_logado = setup_registros_multiplos_zeladores["zelador1"]

    # 1. Filtra pela sala que ele limpou
    params1 = {"sala_uuid": sala_uuid_zelador1}
    response1 = requests.get(f"{api_base_url}/limpezas/", headers=auth_header_zelador, params=params1)
    assert response1.status_code == 200
    registros1 = response1.json()
    assert len(registros1) == 1
    assert registros1[0]["sala"] == sala_uuid_zelador1
    assert registros1[0]["funcionario_responsavel"] == zelador_logado

    # 2. Filtra pela sala que o OUTRO zelador limpou (não deve retornar nada)
    params2 = {"sala_uuid": sala_uuid_zelador2}
    response2 = requests.get(f"{api_base_url}/limpezas/", headers=auth_header_zelador, params=params2)
    assert response2.status_code == 200
    registros2 = response2.json()
    assert len(registros2) == 0 # Zelador 1 não limpou a sala 2


def test_filtro_sala_nome_parcial_admin(
    api_base_url: str,
    auth_header_admin: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any]
):
    """Verifica se o Admin pode filtrar registros por nome parcial da sala."""
    # A fixture cria salas com nome "Sala Histórico Teste ..."
    nome_parcial = "Histórico Teste"
    # Esperamos encontrar os 2 registros criados pela fixture
    registros_esperados = setup_registros_multiplos_zeladores["registros1"] + setup_registros_multiplos_zeladores["registros2"]
    ids_esperados = {reg["id"] for reg in registros_esperados}

    params = {"sala_nome": nome_parcial}
    response = requests.get(f"{api_base_url}/limpezas/", headers=auth_header_admin, params=params)

    assert response.status_code == 200
    registros_filtrados = response.json()
    ids_retornados = {reg["id"] for reg in registros_filtrados}

    # Verifica se todos os registros esperados foram retornados
    assert len(registros_filtrados) == len(ids_esperados)
    assert ids_retornados == ids_esperados
    for reg in registros_filtrados:
        assert nome_parcial in reg["sala_nome"]


def test_filtro_sala_nome_parcial_zelador(
    api_base_url: str,
    auth_header_zelador: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any]
):
    """Verifica se o Zelador pode filtrar seus registros por nome parcial da sala."""
    nome_parcial = "Histórico Teste" # Ambas as salas criadas pela fixture contêm isso
    zelador_logado = setup_registros_multiplos_zeladores["zelador1"]
    # Esperamos encontrar apenas o registro do zelador logado
    registro_esperado_id = setup_registros_multiplos_zeladores["registros1"][0]["id"]

    params = {"sala_nome": nome_parcial}
    response = requests.get(f"{api_base_url}/limpezas/", headers=auth_header_zelador, params=params)

    assert response.status_code == 200
    registros_filtrados = response.json()

    # Verifica se retornou apenas 1 registro e se é o correto
    assert len(registros_filtrados) == 1
    assert registros_filtrados[0]["id"] == registro_esperado_id
    assert registros_filtrados[0]["funcionario_responsavel"] == zelador_logado
    assert nome_parcial in registros_filtrados[0]["sala_nome"]


def test_filtro_sala_nome_nao_encontrado(
    api_base_url: str,
    auth_header_admin: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any]
):
    """Verifica se o filtro por nome retorna lista vazia quando nada corresponde."""
    params = {"sala_nome": "NomeInexistente"}
    response = requests.get(f"{api_base_url}/limpezas/", headers=auth_header_admin, params=params)
    assert response.status_code == 200
    assert len(response.json()) == 0


# --- Mais Testes para Filtros (GET /api/limpezas/) ---

def test_filtro_funcionario_username_admin(
    api_base_url: str,
    auth_header_admin: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any]
):
    """Verifica se o Admin pode filtrar registros pelo username do funcionário."""
    # Filtra pelo username do zelador1
    username_para_filtrar = setup_registros_multiplos_zeladores["zelador1"]
    registro_esperado_id = setup_registros_multiplos_zeladores["registros1"][0]["id"]

    params = {"funcionario_username": username_para_filtrar}
    response = requests.get(f"{api_base_url}/limpezas/", headers=auth_header_admin, params=params)

    assert response.status_code == 200
    registros_filtrados = response.json()
    assert len(registros_filtrados) >= 1 # Deve encontrar pelo menos o registro da fixture
    # Verifica se o registro específico da fixture está presente
    ids_retornados = {reg["id"] for reg in registros_filtrados}
    assert registro_esperado_id in ids_retornados
    # Verifica se todos retornados têm o funcionário correto
    for reg in registros_filtrados:
        assert reg["funcionario_responsavel"] == username_para_filtrar


def test_filtro_funcionario_username_zelador_proprio(
    api_base_url: str,
    auth_header_zelador: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any]
):
    """Verifica se o Zelador pode filtrar pelo seu próprio username."""
    zelador_logado = setup_registros_multiplos_zeladores["zelador1"]
    registro_esperado_id = setup_registros_multiplos_zeladores["registros1"][0]["id"]

    params = {"funcionario_username": zelador_logado}
    response = requests.get(f"{api_base_url}/limpezas/", headers=auth_header_zelador, params=params)

    assert response.status_code == 200
    registros_filtrados = response.json()
    assert len(registros_filtrados) == 1
    assert registros_filtrados[0]["id"] == registro_esperado_id
    assert registros_filtrados[0]["funcionario_responsavel"] == zelador_logado


def test_filtro_funcionario_username_zelador_outro_falha(
    api_base_url: str,
    auth_header_zelador: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any]
):
    """Verifica se o Zelador obtém lista vazia ao filtrar pelo username de outro zelador."""
    outro_zelador = setup_registros_multiplos_zeladores["zelador2"]

    params = {"funcionario_username": outro_zelador}
    response = requests.get(f"{api_base_url}/limpezas/", headers=auth_header_zelador, params=params)

    assert response.status_code == 200
    registros_filtrados = response.json()
    # Como o zelador1 só vê seus próprios registros, filtrar por outro zelador não deve retornar nada
    assert len(registros_filtrados) == 0


def test_filtro_data_after_admin(
    api_base_url: str,
    auth_header_admin: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any]
):
    """Verifica se o Admin pode filtrar registros após uma data."""
    # Pega a data/hora do primeiro registro e subtrai 1 segundo
    # ATENÇÃO: Os registros podem ter sido criados muito próximos no tempo.
    # Usar a data do dia anterior para garantir a filtragem
    registro1_fim_str = setup_registros_multiplos_zeladores["registros1"][0]["data_hora_fim"]
    registro1_fim_dt = datetime.fromisoformat(registro1_fim_str)
    data_filtro = (registro1_fim_dt - timedelta(days=1)).strftime('%Y-%m-%d') # Dia anterior

    params = {"data_hora_fim_after": data_filtro}
    response = requests.get(f"{api_base_url}/limpezas/", headers=auth_header_admin, params=params)

    assert response.status_code == 200
    registros_filtrados = response.json()
    assert len(registros_filtrados) >= 2 # Deve encontrar pelo menos os 2 da fixture
    ids_esperados = {reg["id"] for reg in setup_registros_multiplos_zeladores["registros1"] + setup_registros_multiplos_zeladores["registros2"]}
    ids_retornados = {reg["id"] for reg in registros_filtrados}
    assert ids_esperados.issubset(ids_retornados) # Garante que os da fixture estão lá


def test_filtro_data_before_admin(
    api_base_url: str,
    auth_header_admin: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any]
):
    """Verifica se o Admin pode filtrar registros antes de uma data."""
    # Pega a data/hora do segundo registro e adiciona 1 dia
    registro2_fim_str = setup_registros_multiplos_zeladores["registros2"][0]["data_hora_fim"]
    registro2_fim_dt = datetime.fromisoformat(registro2_fim_str)
    data_filtro = (registro2_fim_dt + timedelta(days=1)).strftime('%Y-%m-%d') # Dia seguinte

    params = {"data_hora_limpeza_before": data_filtro}
    response = requests.get(f"{api_base_url}/limpezas/", headers=auth_header_admin, params=params)

    assert response.status_code == 200
    registros_filtrados = response.json()
    assert len(registros_filtrados) >= 2 # Deve encontrar pelo menos os 2 da fixture
    ids_esperados = {reg["id"] for reg in setup_registros_multiplos_zeladores["registros1"] + setup_registros_multiplos_zeladores["registros2"]}
    ids_retornados = {reg["id"] for reg in registros_filtrados}
    assert ids_esperados.issubset(ids_retornados)


def test_filtro_data_range_zelador(
    api_base_url: str,
    auth_header_zelador: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any]
):
    """Verifica se o Zelador pode filtrar seus registros por intervalo de datas."""
    zelador_logado = setup_registros_multiplos_zeladores["zelador1"]
    registro1_fim_str = setup_registros_multiplos_zeladores["registros1"][0]["data_hora_fim"]
    registro1_fim_dt = datetime.fromisoformat(registro1_fim_str)

    data_inicio_filtro = (registro1_fim_dt - timedelta(hours=1)).strftime('%Y-%m-%d')
    data_fim_filtro = (registro1_fim_dt + timedelta(hours=1)).strftime('%Y-%m-%d')

    params = {
        "data_hora_limpeza_after": data_inicio_filtro,
        "data_hora_limpeza_before": data_fim_filtro
    }
    response = requests.get(f"{api_base_url}/limpezas/", headers=auth_header_zelador, params=params)

    assert response.status_code == 200
    registros_filtrados = response.json()

    # Deve encontrar apenas o registro do zelador1 que está dentro do intervalo
    assert len(registros_filtrados) == 1
    assert registros_filtrados[0]["id"] == setup_registros_multiplos_zeladores["registros1"][0]["id"]
    assert registros_filtrados[0]["funcionario_responsavel"] == zelador_logado


# --- Testes para Detalhes (GET /api/limpezas/{id}/) ---

def test_detalhes_limpeza_admin(
    api_base_url: str,
    auth_header_admin: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any]
):
    """Verifica se o Admin pode ver detalhes de qualquer registro de limpeza."""
    # Pega o ID do registro feito pelo zelador1
    registro_id = setup_registros_multiplos_zeladores["registros1"][0]["id"]
    sala_uuid_esperado = setup_registros_multiplos_zeladores["salas_uuids"][0]

    response = requests.get(f"{api_base_url}/limpezas/{registro_id}/", headers=auth_header_admin)

    assert response.status_code == 200
    detalhes = response.json()
    assert detalhes["id"] == registro_id
    assert detalhes["sala"] == sala_uuid_esperado
    assert detalhes["funcionario_responsavel"] == setup_registros_multiplos_zeladores["zelador1"]


def test_detalhes_limpeza_zelador_proprio(
    api_base_url: str,
    auth_header_zelador: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any]
):
    """Verifica se o Zelador pode ver detalhes do seu próprio registro."""
    registro_id = setup_registros_multiplos_zeladores["registros1"][0]["id"] # Registro do zelador1
    zelador_logado = setup_registros_multiplos_zeladores["zelador1"]

    response = requests.get(f"{api_base_url}/limpezas/{registro_id}/", headers=auth_header_zelador)

    assert response.status_code == 200
    detalhes = response.json()
    assert detalhes["id"] == registro_id
    assert detalhes["funcionario_responsavel"] == zelador_logado


def test_detalhes_limpeza_zelador_outro_falha(
    api_base_url: str,
    auth_header_zelador: Dict[str, str], # Logado como zelador1
    setup_registros_multiplos_zeladores: Dict[str, Any]
):
    """Verifica se o Zelador recebe 404 ao tentar ver detalhes de registro de outro zelador."""
    registro_id_outro = setup_registros_multiplos_zeladores["registros2"][0]["id"] # Registro do zelador2

    response = requests.get(f"{api_base_url}/limpezas/{registro_id_outro}/", headers=auth_header_zelador)

    # Esperamos 404 porque o get_queryset do ViewSet filtra antes de buscar pelo ID
    assert response.status_code == 404


def test_detalhes_limpeza_solicitante_falha(
    api_base_url: str,
    auth_header_solicitante: Dict[str, str],
    setup_registros_multiplos_zeladores: Dict[str, Any]
):
    """Verifica se o Solicitante recebe 403 ao tentar ver detalhes de qualquer registro."""
    registro_id = setup_registros_multiplos_zeladores["registros1"][0]["id"]

    response = requests.get(f"{api_base_url}/limpezas/{registro_id}/", headers=auth_header_solicitante)

    assert response.status_code == 403


def test_detalhes_limpeza_sem_autenticacao_falha(
    api_base_url: str,
    setup_registros_multiplos_zeladores: Dict[str, Any]
):
    """Verifica se usuário não autenticado recebe 401 ao tentar ver detalhes."""
    registro_id = setup_registros_multiplos_zeladores["registros1"][0]["id"]

    response = requests.get(f"{api_base_url}/limpezas/{registro_id}/")

    assert response.status_code == 401
