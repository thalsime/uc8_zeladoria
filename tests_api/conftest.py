"""Arquivo de configuração central para a suíte de testes da API.

Define fixtures reutilizáveis para toda a sessão de testes, como:
- Carregamento de variáveis de ambiente.
- URL base da API.
- Gestão de tokens de autenticação (com cache) para diferentes perfis.
- Criação de ativos de teste, como imagens temporárias.
"""
import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
import pytest
import requests
from PIL import Image

# Carrega as variáveis de ambiente do arquivo .env.test de forma robusta
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

            # CORREÇÃO FINAL: A API retorna a chave como 'token', não 'key'.
            token = response_data.get("token")

            if not token:
                pytest.fail(
                    "Token ('token') não encontrado na resposta de login.\n"
                    f"Resposta recebida da API: {response_data}"
                )

            cls._tokens[username_env] = token
            return token
        except requests.RequestException as e:
            pytest.fail(f"Falha ao obter token para {username}: {e}\nResposta: {e.response.text if e.response else 'N/A'}")

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
    token = TokenManager.get_token(api_base_url, "TEST_USER_ADMIN_USERNAME", "TEST_USER_ADMIN_PASSWORD")
    return {"Authorization": f"Token {token}"}

@pytest.fixture(scope="session")
def auth_header_zelador(api_base_url) -> dict:
    """Fornece um cabeçalho de autorização para um usuário Zelador."""
    token = TokenManager.get_token(api_base_url, "TEST_USER_ZELADOR_USERNAME", "TEST_USER_ZELADOR_PASSWORD")
    return {"Authorization": f"Token {token}"}

@pytest.fixture(scope="session")
def auth_header_solicitante(api_base_url) -> dict:
    """Fornece um cabeçalho de autorização para um usuário Solicitante."""
    token = TokenManager.get_token(api_base_url, "TEST_USER_SOLICITANTE_USERNAME", "TEST_USER_SOLICITANTE_PASSWORD")
    return {"Authorization": f"Token {token}"}

@pytest.fixture
def test_image_path(tmp_path):
    """Cria uma imagem de teste temporária e retorna seu caminho."""
    image = Image.new('RGB', (10, 10), color='blue')
    file_path = tmp_path / "test_image.png"
    image.save(file_path)
    return file_path

@pytest.fixture
def sala_de_teste(api_base_url, auth_header_admin):
    """
    Fixture que cria uma sala de teste antes de cada teste que a utiliza
    e a remove ao final, garantindo o isolamento dos testes.
    """
    # Define dados base DENTRO da fixture para evitar problemas de escopo
    DADOS_BASE_SALA = {
        "descricao": "Sala fixture para testes automatizados.",
        "capacidade": 15,
        "localizacao": "Corredor Fixture Bloco T",
        # "ativa": True, # Removido - 'ativa' é True por padrão no modelo/serializer
    }

    # Dados únicos para a sala a ser criada
    dados_criacao = DADOS_BASE_SALA.copy()
    # Garante nome único para cada execução de teste que usa a fixture
    dados_criacao["nome_numero"] = f"Sala Fixture {uuid.uuid4()}"

    # Cria a sala
    response = requests.post(
        f"{api_base_url}/salas/",
        headers=auth_header_admin,
        data=dados_criacao # Usar 'data' para multipart/form-data
    )
    # Adiciona verificação detalhada em caso de falha na criação
    assert response.status_code == 201, f"Falha ao CRIAR sala na fixture sala_de_teste. Status: {response.status_code}, Resposta: {response.text}"
    sala_criada = response.json()

    yield sala_criada  # Fornece a sala criada para o teste

    # Limpeza: remove a sala após a execução do teste
    sala_uuid = sala_criada.get("qr_code_id") # Usar .get() para segurança
    if sala_uuid:
        response_delete = requests.delete(f"{api_base_url}/salas/{sala_uuid}/", headers=auth_header_admin)
        # Opcional: Verificar se a exclusão foi bem-sucedida, embora falhas aqui possam mascarar falhas no teste
        # assert response_delete.status_code in [204, 404], f"Falha ao DELETAR sala na fixture sala_de_teste. Status: {response_delete.status_code}"

@pytest.fixture(scope="session")
def auth_header_assistente(api_base_url) -> dict:
    """Fornece um cabeçalho de autorização para um usuário Assistente (Zeladoria)."""
    # Use as variáveis de ambiente corretas para o assistente
    token = TokenManager.get_token(api_base_url, "TEST_USER_ASSISTENTE_USERNAME", "TEST_USER_ASSISTENTE_PASSWORD")
    return {"Authorization": f"Token {token}"}
