"""
Arquivo de configuração central para a suíte de testes da API.
Define fixtures reutilizáveis para toda a sessão de testes.
"""

import os
import pytest
import requests
import uuid
from dotenv import load_dotenv
from pathlib import Path
from PIL import Image
from typing import Dict, Any


dotenv_path = Path(__file__).parent / ".env.test"
load_dotenv(dotenv_path=dotenv_path)


class TokenManager:
    """Gerencia e armazena em cache os tokens para a sessão de testes."""

    _tokens = {}

    @classmethod
    def get_token(cls, base_url, username_env, password_env):
        """Obtém um token, fazendo login apenas uma vez por tipo de usuário."""
        if username_env in cls._tokens:
            return cls._tokens[username_env]

        username = os.getenv(username_env)
        password = os.getenv(password_env)

        if not username or not password:
            pytest.fail(f"Credenciais para {username_env} não definidas no .env.test")

        try:
            response = requests.post(
                f"{base_url}/accounts/login/",
                json={"username": username, "password": password},
            )
            response.raise_for_status()
            response_data = response.json()

            token = response_data.get("token")

            if not token:
                pytest.fail(
                    "Token ('token') não encontrado na resposta de login.\n"
                    f"Resposta recebida da API: {response_data}"
                )

            cls._tokens[username_env] = token
            return token
        except requests.RequestException as e:
            pytest.fail(
                f"Falha ao obter token para {username}: {e}\nResposta: {e.response.text if e.response else 'N/A'}"
            )


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Fixture que fornece a URL base da API (com /api) a partir do .env.test."""
    url = os.getenv("API_BASE_URL")
    if not url:
        pytest.fail("A variável API_BASE_URL não está definida no .env.test")
    return f"{url}/api"


@pytest.fixture(scope="session")
def auth_header_admin(api_base_url) -> dict:
    """Fornece um cabeçalho de autorização para um usuário Admin."""
    token = TokenManager.get_token(
        api_base_url, "TEST_USER_ADMIN_USERNAME", "TEST_USER_ADMIN_PASSWORD"
    )
    return {"Authorization": f"Token {token}"}


@pytest.fixture(scope="session")
def auth_header_zelador(api_base_url) -> dict:
    """Fornece um cabeçalho de autorização para um usuário Zelador."""
    token = TokenManager.get_token(
        api_base_url, "TEST_USER_ZELADOR_USERNAME", "TEST_USER_ZELADOR_PASSWORD"
    )
    return {"Authorization": f"Token {token}"}


@pytest.fixture(scope="session")
def auth_header_solicitante(api_base_url) -> dict:
    """Fornece um cabeçalho de autorização para um usuário Solicitante."""
    token = TokenManager.get_token(
        api_base_url, "TEST_USER_SOLICITANTE_USERNAME", "TEST_USER_SOLICITANTE_PASSWORD"
    )
    return {"Authorization": f"Token {token}"}


@pytest.fixture
def test_image_path(tmp_path):
    """Cria uma imagem de teste temporária e retorna seu caminho."""
    image = Image.new("RGB", (10, 10), color="blue")
    file_path = tmp_path / "test_image.png"
    image.save(file_path)
    return file_path


@pytest.fixture
def sala_de_teste(api_base_url, auth_header_admin):
    """
    Fixture que cria uma sala de teste antes de cada teste que a utiliza
    e a remove ao final, garantindo o isolamento dos testes.
    """

    DADOS_BASE_SALA = {
        "descricao": "Sala fixture para testes automatizados.",
        "capacidade": 15,
        "localizacao": "Corredor Fixture Bloco T",
    }

    dados_criacao = DADOS_BASE_SALA.copy()

    dados_criacao["nome_numero"] = f"Sala Fixture {uuid.uuid4()}"

    response = requests.post(
        f"{api_base_url}/salas/", headers=auth_header_admin, data=dados_criacao
    )

    assert (
        response.status_code == 201
    ), f"Falha ao CRIAR sala na fixture sala_de_teste. Status: {response.status_code}, Resposta: {response.text}"
    sala_criada = response.json()

    yield sala_criada

    sala_uuid = sala_criada.get("qr_code_id")
    if sala_uuid:
        response_delete = requests.delete(
            f"{api_base_url}/salas/{sala_uuid}/", headers=auth_header_admin
        )


@pytest.fixture(scope="session")
def auth_header_assistente(api_base_url) -> dict:
    """Fornece um cabeçalho de autorização para um usuário Assistente (Zeladoria)."""

    token = TokenManager.get_token(
        api_base_url, "TEST_USER_ASSISTENTE_USERNAME", "TEST_USER_ASSISTENTE_PASSWORD"
    )
    return {"Authorization": f"Token {token}"}


@pytest.fixture
def iniciar_limpeza_para_teste(
    api_base_url: str,
    auth_header_zelador: Dict[str, str],
    sala_de_teste: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Fixture auxiliar que inicia uma limpeza para uma sala de teste
    e retorna os dados do registro de limpeza criado.
    Agora definida em conftest.py para ser acessível globalmente nos testes.
    """
    sala_uuid = sala_de_teste["qr_code_id"]
    response = requests.post(
        f"{api_base_url}/salas/{sala_uuid}/iniciar_limpeza/",
        headers=auth_header_zelador,
    )

    assert (
        response.status_code == 201
    ), f"Fixture 'iniciar_limpeza_para_teste': Falha ao iniciar limpeza: {response.text}"
    registro_limpeza = response.json()

    registro_limpeza["sala_uuid_test"] = sala_uuid
    return registro_limpeza
