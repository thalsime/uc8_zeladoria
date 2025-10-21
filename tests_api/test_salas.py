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
from typing import Dict, Any
from pathlib import Path


# Define um dicionário com um modelo de dados válidos para a criação de uma sala.
# O nome será modificado em cada teste para garantir a unicidade.
DADOS_BASE_SALA = {
    "descricao": "Sala para testes automatizados de criação.",
    "capacidade": 15,
    "localizacao": "Corredor de Testes do Bloco Z",
    "ativa": True,
}

# Testes de Listagem (GET /api/salas/)


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


# Testes de Criação (POST /api/salas/)


def test_criar_sala_com_imagem_como_admin_sucesso(
    api_base_url, auth_header_admin, test_image_path
):
    """Verifica se um Admin pode criar uma nova sala com dados válidos e uma imagem."""
    dados_sala_unicos = DADOS_BASE_SALA.copy()
    dados_sala_unicos["nome_numero"] = f"Sala de Teste {uuid.uuid4()}"

    with open(test_image_path, "rb") as image_file:
        files = {"imagem": (test_image_path.name, image_file, "image/png")}
        response = requests.post(
            f"{api_base_url}/salas/",
            headers=auth_header_admin,
            data=dados_sala_unicos,
            files=files,
        )

    assert (
        response.status_code == 201
    ), f"Falha na criação da sala. Resposta: {response.text}"

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
    response = requests.post(
        f"{api_base_url}/salas/", headers=auth_header_zelador, data=payload
    )
    assert response.status_code == 403


def test_criar_sala_como_solicitante_falha(api_base_url, auth_header_solicitante):
    """Verifica se um Solicitante é proibido (403) de criar uma sala."""
    payload = DADOS_BASE_SALA.copy()
    payload["nome_numero"] = "Sala Teste Permissao Solicitante"
    response = requests.post(
        f"{api_base_url}/salas/", headers=auth_header_solicitante, data=payload
    )
    assert response.status_code == 403


def test_criar_sala_com_dados_invalidos_falha(api_base_url, auth_header_admin):
    """Verifica se a criação da sala falha (400) com dados inválidos (nome_numero faltando)."""
    dados_invalidos = DADOS_BASE_SALA.copy()
    # Remove a chave obrigatória
    if "nome_numero" in dados_invalidos:
        del dados_invalidos["nome_numero"]
    response = requests.post(
        f"{api_base_url}/salas/", headers=auth_header_admin, data=dados_invalidos
    )
    assert response.status_code == 400
    assert "nome_numero" in response.json()


# Testes de Atualização (PATCH /api/salas/{qr_code_id}/)


def test_atualizar_parcialmente_sala_como_admin_sucesso(
    api_base_url, auth_header_admin, sala_de_teste
):
    """Verifica se um Admin pode atualizar parcialmente uma sala (PATCH)."""
    sala_uuid = sala_de_teste["qr_code_id"]
    payload_atualizacao = {
        "descricao": "Descrição foi atualizada via PATCH.",
        "capacidade": 99,
    }

    response = requests.patch(
        f"{api_base_url}/salas/{sala_uuid}/",
        headers=auth_header_admin,
        data=payload_atualizacao,
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["descricao"] == payload_atualizacao["descricao"]
    assert response_data["capacidade"] == payload_atualizacao["capacidade"]
    assert (
        response_data["nome_numero"] == sala_de_teste["nome_numero"]
    )  # Verifica que não mudou


@pytest.mark.parametrize(
    "auth_header",
    [
        "auth_header_zelador",
        "auth_header_solicitante",
    ],
)
def test_atualizar_parcialmente_sala_outros_usuarios_falha(
    api_base_url, request, auth_header, sala_de_teste
):
    """Verifica se Zelador e Solicitante são proibidos (403) de atualizar uma sala."""
    sala_uuid = sala_de_teste["qr_code_id"]
    header = request.getfixturevalue(auth_header)  # Pega a fixture pelo nome

    response = requests.patch(
        f"{api_base_url}/salas/{sala_uuid}/",
        headers=header,
        data={"descricao": "Tentativa de atualização."},
    )

    assert response.status_code == 403


# Testes de Atualização (PUT /api/salas/{qr_code_id}/)


def test_atualizar_totalmente_sala_admin_sucesso(
    api_base_url, auth_header_admin, sala_de_teste
):
    """
    Verifica se um Admin pode atualizar totalmente uma sala (PUT),
    substituindo todos os seus dados.
    """
    sala_uuid = sala_de_teste["qr_code_id"]

    # Payload completo para a substituição do recurso.
    payload_atualizacao_completa = {
        "nome_numero": f"Sala Substituída PUT {uuid.uuid4()}",  # Garante nome único
        "descricao": "Descrição totalmente nova para o teste de PUT.",
        "capacidade": 25,
        "localizacao": "Nova Localização via PUT",
        "ativa": False,
        "instrucoes": "Instruções atualizadas via PUT.",
        "validade_limpeza_horas": 8,
        # 'imagem' e 'responsaveis' omitidos, devem ser limpos/removidos
    }

    response = requests.put(
        f"{api_base_url}/salas/{sala_uuid}/",
        headers=auth_header_admin,
        data=payload_atualizacao_completa,  # 'data' para PUT com multipart/form-data
    )

    assert response.status_code == 200, f"Erro na requisição PUT: {response.text}"

    response_data = response.json()

    # Verifica se todos os campos enviados foram atualizados
    for key, value in payload_atualizacao_completa.items():
        assert (
            response_data[key] == value
        ), f"Campo '{key}' não foi atualizado corretamente no PUT."
    # Verifica se campos omitidos foram limpos (ex: imagem)
    assert response_data["imagem"] is None, "Campo 'imagem' não foi removido no PUT."
    assert (
        response_data["responsaveis"] == []
    ), "Campo 'responsaveis' não foi limpo no PUT."


# Testes para Marcar Sala como Suja (POST /api/salas/{qr_code_id}/marcar_como_suja/)


def test_marcar_como_suja_solicitante_sucesso(
    api_base_url: str,
    auth_header_solicitante: Dict[str, str],
    sala_de_teste: Dict[str, Any],
):
    """Verifica se um Solicitante pode marcar uma sala ativa como suja (com observações)."""
    sala_uuid = sala_de_teste["qr_code_id"]
    payload = {"observacoes": "Material derramado no chão durante o evento."}

    response = requests.post(
        f"{api_base_url}/salas/{sala_uuid}/marcar_como_suja/",
        headers=auth_header_solicitante,
        json=payload,  # A action aceita JSON ou form-data
    )

    assert (
        response.status_code == 201
    ), f"Falha ao marcar sala como suja: {response.text}"
    assert (
        response.json().get("status") == "Relatório de sala suja enviado com sucesso."
    )

    # Verificar se o status da sala mudou (requer uma nova consulta)
    response_get = requests.get(
        f"{api_base_url}/salas/{sala_uuid}/", headers=auth_header_solicitante
    )
    assert response_get.status_code == 200
    sala_data = response_get.json()
    assert sala_data["status_limpeza"] == "Suja"
    assert sala_data["detalhes_suja"] is not None
    assert sala_data["detalhes_suja"]["observacoes"] == payload["observacoes"]
    assert sala_data["detalhes_suja"]["reportado_por"] == os.getenv(
        "TEST_USER_SOLICITANTE_USERNAME"
    )


def test_marcar_como_suja_solicitante_sem_observacoes_sucesso(
    api_base_url: str,
    auth_header_solicitante: Dict[str, str],
    sala_de_teste: Dict[str, Any],
):
    """Verifica se um Solicitante pode marcar uma sala ativa como suja (sem observações)."""
    sala_uuid = sala_de_teste["qr_code_id"]

    response = requests.post(
        f"{api_base_url}/salas/{sala_uuid}/marcar_como_suja/",
        headers=auth_header_solicitante,
        json={},  # Envia corpo JSON vazio
    )

    assert response.status_code == 201
    assert (
        response.json().get("status") == "Relatório de sala suja enviado com sucesso."
    )

    # Verificar se o status da sala mudou
    response_get = requests.get(
        f"{api_base_url}/salas/{sala_uuid}/", headers=auth_header_solicitante
    )
    assert response_get.status_code == 200
    sala_data = response_get.json()
    assert sala_data["status_limpeza"] == "Suja"
    assert sala_data["detalhes_suja"] is not None
    assert sala_data["detalhes_suja"]["observacoes"] in [
        None,
        "",
    ], f"Observações deveriam ser nulas ou vazias, mas foram: {sala_data['detalhes_suja']['observacoes']}"  # Verifica se observações está vazia ou nula


@pytest.mark.parametrize(
    "auth_fixture",
    [
        "auth_header_admin",
        "auth_header_zelador",
    ],
)
def test_marcar_como_suja_outros_usuarios_falha(
    api_base_url: str, request: Any, auth_fixture: str, sala_de_teste: Dict[str, Any]
):
    """Verifica se Admin e Zelador são proibidos (403) de marcar sala como suja."""
    sala_uuid = sala_de_teste["qr_code_id"]
    header = request.getfixturevalue(auth_fixture)
    response = requests.post(
        f"{api_base_url}/salas/{sala_uuid}/marcar_como_suja/", headers=header, json={}
    )
    assert response.status_code == 403


def test_marcar_como_suja_sala_inativa_falha(
    api_base_url: str,
    auth_header_admin: Dict[str, str],
    auth_header_solicitante: Dict[str, str],
    sala_de_teste: Dict[str, Any],
):
    """Verifica se falha (400) ao tentar marcar uma sala inativa como suja."""
    sala_uuid = sala_de_teste["qr_code_id"]

    response_patch = requests.patch(
        f"{api_base_url}/salas/{sala_uuid}/",
        headers=auth_header_admin,
        data={"ativa": False},  # Usa 'data' pois PATCH pode ser multipart
    )
    assert (
        response_patch.status_code == 200
    ), f"Falha ao desativar sala para o teste: {response_patch.text}"

    response_marcar = requests.post(
        f"{api_base_url}/salas/{sala_uuid}/marcar_como_suja/",
        headers=auth_header_solicitante,
        json={},
    )
    assert response_marcar.status_code == 400
    assert "Não é possível reportar uma sala inativa" in response_marcar.json().get(
        "detail", ""
    )

    # 3. Reativar a sala para não afetar outros testes (limpeza da fixture sala_de_teste)
    #    A fixture `sala_de_teste` remove e recria a sala, mas reativar aqui é seguro.
    requests.patch(
        f"{api_base_url}/salas/{sala_uuid}/",
        headers=auth_header_admin,
        data={"ativa": True},
    )


@pytest.mark.django_db(transaction=True)
def test_filtrar_salas_por_status_limpeza(
    api_base_url: str,
    auth_header_admin: Dict[str, str],  # Usaremos admin para ter visão total
    auth_header_zelador: Dict[str, str],
    auth_header_solicitante: Dict[str, str],
    test_image_path: Path,
):
    """
    Verifica se o filtro `status_limpeza` na listagem de salas funciona
    corretamente para os status: Limpa, Suja, Em Limpeza, Limpeza Pendente.
    """
    # Setup do Cenário
    # 1. Criar salas com nomes únicos
    nomes_salas = {
        "limpa": f"Sala Teste Limpa {uuid.uuid4()}",
        "suja_reportada": f"Sala Teste Suja Reportada {uuid.uuid4()}",
        "em_limpeza": f"Sala Teste Em Limpeza {uuid.uuid4()}",
        "pendente": f"Sala Teste Pendente {uuid.uuid4()}",  # Nunca limpa
        "suja_pos_limpa": f"Sala Suja Pós Limpa {uuid.uuid4()}",  # Limpa e depois reportada
        # Poderíamos adicionar um caso de 'pendente por expiração', mas requer controle de tempo
    }
    salas_criadas_uuids = {}
    salas_para_limpar = []  # Armazena UUIDs para deleção no final

    print("\n--- Iniciando Setup do Teste de Filtro de Status")  # Debug print

    try:  # Usar try/finally para garantir a limpeza
        for status_key, nome in nomes_salas.items():
            payload = {
                "nome_numero": nome,
                "capacidade": 10,
                "localizacao": f"Bloco Status {status_key}",
                "validade_limpeza_horas": 1,  # Validade curta para facilitar teste (se necessário)
            }
            print(f"Criando sala: {nome}...")  # Debug print
            response = requests.post(
                f"{api_base_url}/salas/", headers=auth_header_admin, data=payload
            )
            assert (
                response.status_code == 201
            ), f"Falha ao criar sala '{status_key}'. Resposta: {response.text}"
            sala_uuid = response.json()["qr_code_id"]
            salas_criadas_uuids[status_key] = sala_uuid
            salas_para_limpar.append(sala_uuid)  # Adiciona à lista de limpeza
            print(f"Sala criada: {nome} (UUID: {sala_uuid})")  # Debug print

        # 2. Manipular estados para criar os cenários
        print("Manipulando estados das salas...")  # Debug print

        # Sala Limpa: Iniciar + Add Foto + Concluir
        uuid_limpa = salas_criadas_uuids["limpa"]
        print(f"Configurando Sala Limpa (UUID: {uuid_limpa})...")  # Debug print
        resp_iniciar_limpa = requests.post(
            f"{api_base_url}/salas/{uuid_limpa}/iniciar_limpeza/",
            headers=auth_header_zelador,
        )
        assert (
            resp_iniciar_limpa.status_code == 201
        ), f"Falha ao iniciar limpeza da sala 'limpa': {resp_iniciar_limpa.text}"
        reg_id_limpa = resp_iniciar_limpa.json()["id"]
        # Adiciona foto
        with open(test_image_path, "rb") as img:
            files = {"imagem": ("foto_limpa.png", img, "image/png")}
            resp_foto_limpa = requests.post(
                f"{api_base_url}/fotos_limpeza/",
                headers=auth_header_zelador,
                data={"registro_limpeza": str(reg_id_limpa)},
                files=files,
            )
            assert (
                resp_foto_limpa.status_code == 201
            ), f"Falha ao adicionar foto à sala 'limpa': {resp_foto_limpa.text}"
        # Conclui
        resp_concluir_limpa = requests.post(
            f"{api_base_url}/salas/{uuid_limpa}/concluir_limpeza/",
            headers=auth_header_zelador,
        )
        assert (
            resp_concluir_limpa.status_code == 200
        ), f"Falha ao concluir limpeza da sala 'limpa': {resp_concluir_limpa.text}"
        print("Sala Limpa configurada.")  # Debug print

        # Sala Suja (Reportada): Marcar como suja
        uuid_suja_reportada = salas_criadas_uuids["suja_reportada"]
        print(
            f"Configurando Sala Suja Reportada (UUID: {uuid_suja_reportada})..."
        )  # Debug print
        resp_marcar_suja = requests.post(
            f"{api_base_url}/salas/{uuid_suja_reportada}/marcar_como_suja/",
            headers=auth_header_solicitante,
            json={"observacoes": "Reporte de sujeira inicial"},
        )
        assert (
            resp_marcar_suja.status_code == 201
        ), f"Falha ao marcar sala 'suja_reportada' como suja: {resp_marcar_suja.text}"
        print("Sala Suja Reportada configurada.")  # Debug print

        # Sala Em Limpeza: Apenas Iniciar
        uuid_em_limpeza = salas_criadas_uuids["em_limpeza"]
        print(
            f"Configurando Sala Em Limpeza (UUID: {uuid_em_limpeza})..."
        )  # Debug print
        resp_iniciar_em_limpeza = requests.post(
            f"{api_base_url}/salas/{uuid_em_limpeza}/iniciar_limpeza/",
            headers=auth_header_zelador,
        )
        assert (
            resp_iniciar_em_limpeza.status_code == 201
        ), f"Falha ao iniciar limpeza da sala 'em_limpeza': {resp_iniciar_em_limpeza.text}"
        print("Sala Em Limpeza configurada.")  # Debug print

        # Sala Pendente: Criada, mas nunca limpa (já está nesse estado)
        uuid_pendente = salas_criadas_uuids["pendente"]
        print(
            f"Sala Pendente (UUID: {uuid_pendente}) - Nenhuma ação necessária."
        )  # Debug print

        # Sala Suja Pós Limpa: Limpar e depois marcar como suja
        uuid_suja_pos_limpa = salas_criadas_uuids["suja_pos_limpa"]
        print(
            f"Configurando Sala Suja Pós Limpa (UUID: {uuid_suja_pos_limpa})..."
        )  # Debug print
        # Limpa primeiro
        resp_iniciar_spl = requests.post(
            f"{api_base_url}/salas/{uuid_suja_pos_limpa}/iniciar_limpeza/",
            headers=auth_header_zelador,
        )
        assert (
            resp_iniciar_spl.status_code == 201
        ), f"SPL: Falha ao iniciar limpeza: {resp_iniciar_spl.text}"
        reg_id_spl = resp_iniciar_spl.json()["id"]
        with open(test_image_path, "rb") as img:
            files = {"imagem": ("foto_spl.png", img, "image/png")}
            resp_foto_spl = requests.post(
                f"{api_base_url}/fotos_limpeza/",
                headers=auth_header_zelador,
                data={"registro_limpeza": str(reg_id_spl)},
                files=files,
            )
            assert (
                resp_foto_spl.status_code == 201
            ), f"SPL: Falha ao adicionar foto: {resp_foto_spl.text}"
        resp_concluir_spl = requests.post(
            f"{api_base_url}/salas/{uuid_suja_pos_limpa}/concluir_limpeza/",
            headers=auth_header_zelador,
        )
        assert (
            resp_concluir_spl.status_code == 200
        ), f"SPL: Falha ao concluir limpeza: {resp_concluir_spl.text}"
        # Marca como suja DEPOIS
        resp_marcar_spl_suja = requests.post(
            f"{api_base_url}/salas/{uuid_suja_pos_limpa}/marcar_como_suja/",
            headers=auth_header_solicitante,
            json={"observacoes": "Suja após limpeza"},
        )
        assert (
            resp_marcar_spl_suja.status_code == 201
        ), f"SPL: Falha ao marcar como suja: {resp_marcar_spl_suja.text}"
        print("Sala Suja Pós Limpa configurada.")  # Debug print

        print("--- Setup Concluído")  # Debug print

        # Testes de Filtro
        url_listagem = f"{api_base_url}/salas/"
        print("--- Iniciando Testes de Filtro")  # Debug print

        # Função auxiliar para testar um filtro
        def _testar_filtro(status_valor, uuids_esperados, uuids_nao_esperados):
            print(f"Testando filtro status_limpeza={status_valor}...")  # Debug print
            params = {"status_limpeza": status_valor}
            response = requests.get(
                url_listagem, headers=auth_header_admin, params=params
            )
            assert (
                response.status_code == 200
            ), f"Filtro '{status_valor}': Esperado 200, Recebido {response.status_code}. Resposta: {response.text}"
            salas_filtradas = response.json()
            ids_retornados = {s["qr_code_id"] for s in salas_filtradas}
            print(
                f"Filtro '{status_valor}': IDs retornados: {ids_retornados}"
            )  # Debug print

            # Verificar IDs esperados
            for uuid_esperado in uuids_esperados:
                assert (
                    uuid_esperado in ids_retornados
                ), f"Filtro '{status_valor}': Esperado encontrar UUID {uuid_esperado}, mas não encontrado."
            # Verificar IDs não esperados
            for uuid_nao_esperado in uuids_nao_esperados:
                assert (
                    uuid_nao_esperado not in ids_retornados
                ), f"Filtro '{status_valor}': UUID {uuid_nao_esperado} encontrado indevidamente."
            print(f"Filtro status_limpeza={status_valor} - OK")  # Debug print

        # Executar os testes para cada status
        _testar_filtro(
            "Limpa",
            uuids_esperados=[uuid_limpa],
            uuids_nao_esperados=[
                uuid_suja_reportada,
                uuid_em_limpeza,
                uuid_pendente,
                uuid_suja_pos_limpa,
            ],
        )
        _testar_filtro(
            "Suja",
            uuids_esperados=[
                uuid_suja_reportada,
                uuid_suja_pos_limpa,
            ],  # Ambas devem aparecer
            uuids_nao_esperados=[uuid_limpa, uuid_em_limpeza, uuid_pendente],
        )
        _testar_filtro(
            "Em Limpeza",
            uuids_esperados=[uuid_em_limpeza],
            uuids_nao_esperados=[
                uuid_limpa,
                uuid_suja_reportada,
                uuid_pendente,
                uuid_suja_pos_limpa,
            ],
        )
        _testar_filtro(
            "Limpeza Pendente",
            uuids_esperados=[uuid_pendente],  # A sala nunca limpa
            uuids_nao_esperados=[
                uuid_limpa,
                uuid_suja_reportada,
                uuid_em_limpeza,
                uuid_suja_pos_limpa,
            ],
            # Nota: Se o teste demorar mais que a validade (1h), a sala 'limpa' poderia virar 'pendente'.
            # A lógica atual do teste não cobre explicitamente a pendência por expiração,
            # apenas a pendência inicial. Para um teste mais robusto de expiração,
            # seria necessário mockar o tempo ou esperar o tempo da validade.
        )
        print("--- Testes de Filtro Concluídos")  # Debug print

    finally:
        # Limpeza
        print("--- Iniciando Limpeza do Teste")  # Debug print
        # Deletar as salas criadas, garantindo que estejam ativas primeiro
        for uuid_sala in salas_para_limpar:
            print(f"Limpando sala UUID: {uuid_sala}...")  # Debug print
            # Tentativa de reativar (ignora falha se já foi deletada ou não encontrada)
            requests.patch(
                f"{api_base_url}/salas/{uuid_sala}/",
                headers=auth_header_admin,
                data={"ativa": True},
            )
            # Tentativa de deletar
            delete_resp = requests.delete(
                f"{api_base_url}/salas/{uuid_sala}/", headers=auth_header_admin
            )
            # Verifica se foi deletado (204) ou já não existia (404)
            assert delete_resp.status_code in [
                204,
                404,
            ], f"Falha ao limpar sala {uuid_sala}. Status: {delete_resp.status_code}"
            print(
                f"Sala {uuid_sala} limpa (Status: {delete_resp.status_code})."
            )  # Debug print
        print("--- Limpeza Concluída")  # Debug print
