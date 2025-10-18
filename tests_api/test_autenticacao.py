"""Testes de integração para os endpoints de Autenticação e Contas.
Esta suíte de testes valida:
- O fluxo de login com credenciais válidas e inválidas.
- O controle de acesso a rotas protegidas com e sem token JWT.
- A obtenção de dados do usuário logado.
"""
import pytest
import requests
import os

# --- Testes de Login (/api/accounts/login/) ---

def test_login_sucesso_admin(api_base_url):
    """Verifica se o login com credenciais de Admin é bem-sucedido."""
    # CORREÇÃO: Busca username e password do .env.test
    admin_username = os.getenv("TEST_USER_ADMIN_USERNAME")
    admin_password = os.getenv("TEST_USER_ADMIN_PASSWORD")
    if not admin_username or not admin_password:
        pytest.fail("Credenciais de Admin não definidas em tests_api/.env.test")

    credentials = {"username": admin_username, "password": admin_password}
    response = requests.post(f"{api_base_url}/accounts/login/", json=credentials)
    # A asserção original permanece, verificando o sucesso do login
    assert response.status_code == 200, f"Falha no login do Admin. Resposta: {response.text}"
    assert "token" in response.json()

def test_login_senha_incorreta(api_base_url):
    """Verifica se o login falha com uma senha incorreta."""
    # Usa o username correto do admin do .env.test para garantir que o teste
    # falhe apenas pela senha.
    admin_username = os.getenv("TEST_USER_ADMIN_USERNAME")
    if not admin_username:
        pytest.fail("Username do Admin não definido em tests_api/.env.test")

    credentials = {"username": admin_username, "password": "senhaerrada"}
    response = requests.post(f"{api_base_url}/accounts/login/", json=credentials)
    assert response.status_code == 400
    assert "non_field_errors" in response.json()

def test_login_usuario_inexistente(api_base_url):
    """Verifica se o login falha com um usuário que não existe."""
    credentials = {
        "username": "usuarioinexistente",
        "password": "qualquersenha"
    }
    response = requests.post(f"{api_base_url}/accounts/login/", json=credentials)
    assert response.status_code == 400

def test_login_sem_credenciais(api_base_url):
    """Verifica se o login falha quando nenhum dado é enviado."""
    response = requests.post(f"{api_base_url}/accounts/login/", json={})
    assert response.status_code == 400


# --- Testes de Acesso a Rotas Protegidas ---

def test_acesso_rota_protegida_sem_token(api_base_url):
    """Verifica se o acesso a uma rota protegida é negado sem um token."""
    response = requests.get(f"{api_base_url}/salas/")
    assert response.status_code == 401

def test_acesso_rota_protegida_com_token_invalido(api_base_url):
    """Verifica se o acesso a uma rota protegida é negado com um token inválido."""
    headers = {"Authorization": "Token tokeninvalido123"}
    response = requests.get(f"{api_base_url}/salas/", headers=headers)
    assert response.status_code == 401

@pytest.mark.skip(reason="O endpoint de logout precisa ser ajustado no backend para invalidar o token.")
def test_logout_sucesso(api_base_url, auth_header_admin):
    """Verifica se o logout é bem-sucedido."""
    response = requests.post(f"{api_base_url}/accounts/logout/", headers=auth_header_admin)
    assert response.status_code == 200

    response_depois_logout = requests.get(f"{api_base_url}/salas/", headers=auth_header_admin)
    assert response_depois_logout.status_code == 401


# --- Testes de Obtenção do Usuário Logado (/api/accounts/current_user/) ---

# CORREÇÃO: Busca os usernames esperados do .env.test
admin_expected_username = os.getenv("TEST_USER_ADMIN_USERNAME", "senac") # Default caso não esteja no .env
zelador_expected_username = os.getenv("TEST_USER_ZELADOR_USERNAME", "zelador")
solicitante_expected_username = os.getenv("TEST_USER_SOLICITANTE_USERNAME", "colaborador")

@pytest.mark.parametrize(
    "auth_fixture, expected_username",
    [
        ("auth_header_admin", admin_expected_username),
        ("auth_header_zelador", zelador_expected_username),
        ("auth_header_solicitante", solicitante_expected_username), # Usa a variável lida do .env
    ],
)
def test_obter_dados_usuario_logado_sucesso(api_base_url, request, auth_fixture, expected_username):
    """
    Verifica se usuários autenticados (Admin, Zelador, Solicitante)
    conseguem obter seus próprios dados com sucesso.
    """
    auth_header = request.getfixturevalue(auth_fixture)

    response = requests.get(
        f"{api_base_url}/accounts/current_user/",
        headers=auth_header
    )

    assert response.status_code == 200, f"Falha ao obter dados do usuário ({expected_username}). Resposta: {response.text}"

    response_data = response.json()
    assert response_data["username"] == expected_username
    assert "id" in response_data
    assert "email" in response_data
    assert "profile" in response_data

def test_obter_dados_usuario_sem_autenticacao_falha(api_base_url):
    """
    Verifica se um usuário não autenticado é proibido (401) de acessar
    o endpoint de usuário atual.
    """
    response = requests.get(f"{api_base_url}/accounts/current_user/")
    assert response.status_code == 401
