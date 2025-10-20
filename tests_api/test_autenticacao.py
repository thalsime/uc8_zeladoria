"""Testes de integração para os endpoints de Autenticação e Contas."""

import os
import pytest
import requests
import uuid
from io import BytesIO
from pathlib import Path
from PIL import Image
from typing import Dict
from django.core.files.storage import default_storage
from django.contrib.auth.models import User, Group
from rest_framework import status
from rest_framework.test import APIClient
from accounts.models import Profile


# Testes de Login (/api/accounts/login/)


def test_login_sucesso_admin(api_base_url):
    """Verifica se o login com credenciais de Admin é bem-sucedido."""
    admin_username = os.getenv("TEST_USER_ADMIN_USERNAME")
    admin_password = os.getenv("TEST_USER_ADMIN_PASSWORD")
    if not admin_username or not admin_password:
        pytest.fail("Credenciais de Admin não definidas em tests_api/.env.test")

    credentials = {"username": admin_username, "password": admin_password}
    response = requests.post(f"{api_base_url}/accounts/login/", json=credentials)
    assert (
        response.status_code == 200
    ), f"Falha no login do Admin. Resposta: {response.text}"
    assert "token" in response.json()


def test_login_senha_incorreta(api_base_url):
    """Verifica se o login falha com uma senha incorreta."""
    admin_username = os.getenv("TEST_USER_ADMIN_USERNAME")
    if not admin_username:
        pytest.fail("Username do Admin não definido em tests_api/.env.test")

    credentials = {"username": admin_username, "password": "senhaerrada"}
    response = requests.post(f"{api_base_url}/accounts/login/", json=credentials)
    assert response.status_code == 400
    assert "non_field_errors" in response.json()


def test_login_usuario_inexistente(api_base_url):
    """Verifica se o login falha com um usuário que não existe."""
    credentials = {"username": "usuarioinexistente", "password": "qualquersenha"}
    response = requests.post(f"{api_base_url}/accounts/login/", json=credentials)
    assert response.status_code == 400


def test_login_sem_credenciais(api_base_url):
    """Verifica se o login falha quando nenhum dado é enviado."""
    response = requests.post(f"{api_base_url}/accounts/login/", json={})
    assert response.status_code == 400


# Testes de Acesso a Rotas Protegidas


def test_acesso_rota_protegida_sem_token(api_base_url):
    """Verifica se o acesso a uma rota protegida é negado sem um token."""
    response = requests.get(f"{api_base_url}/salas/")
    assert response.status_code == 401


def test_acesso_rota_protegida_com_token_invalido(api_base_url):
    """Verifica se o acesso a uma rota protegida é negado com um token inválido."""
    headers = {"Authorization": "Token tokeninvalido123"}
    response = requests.get(f"{api_base_url}/salas/", headers=headers)
    assert response.status_code == 401


@pytest.mark.skip(
    reason="O endpoint de logout precisa ser ajustado no backend para invalidar o token."
)
def test_logout_sucesso(api_base_url, auth_header_admin):
    """Verifica se o logout é bem-sucedido."""
    response = requests.post(
        f"{api_base_url}/accounts/logout/", headers=auth_header_admin
    )
    assert response.status_code == 200

    response_depois_logout = requests.get(
        f"{api_base_url}/salas/", headers=auth_header_admin
    )
    assert response_depois_logout.status_code == 401


# Testes de Obtenção do Usuário Logado (/api/accounts/current_user/)


admin_expected_username = os.getenv("TEST_USER_ADMIN_USERNAME", "senac")
zelador_expected_username = os.getenv("TEST_USER_ZELADOR_USERNAME", "zelador")
solicitante_expected_username = os.getenv(
    "TEST_USER_SOLICITANTE_USERNAME", "colaborador"
)


@pytest.mark.parametrize(
    "auth_fixture, expected_username",
    [
        ("auth_header_admin", admin_expected_username),
        ("auth_header_zelador", zelador_expected_username),
        (
            "auth_header_solicitante",
            solicitante_expected_username,
        ),
    ],
)
def test_obter_dados_usuario_logado_sucesso(
    api_base_url, request, auth_fixture, expected_username
):
    """
    Verifica se usuários autenticados (Admin, Zelador, Solicitante)
    conseguem obter seus próprios dados com sucesso.
    """
    auth_header = request.getfixturevalue(auth_fixture)

    response = requests.get(
        f"{api_base_url}/accounts/current_user/", headers=auth_header
    )

    assert (
        response.status_code == 200
    ), f"Falha ao obter dados do usuário ({expected_username}). Resposta: {response.text}"

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


# Testes de Gerenciamento de Perfil (/api/accounts/profile/)


@pytest.fixture
def api_client() -> APIClient:
    """Fixture que fornece uma instância do APIClient do DRF."""
    return APIClient()


@pytest.fixture
def user_com_nome(db) -> User:
    """
    Cria ou obtém o usuário 'zelador', garante que ele tenha um first_name
    e DEFINE/RESETA sua senha para o valor esperado do .env.test.
    """
    zelador_username = os.getenv("TEST_USER_ZELADOR_USERNAME", "zelador")
    senha_esperada = os.getenv("TEST_USER_ZELADOR_PASSWORD", "Senac@098")

    user, created = User.objects.get_or_create(username=zelador_username)

    user.set_password(senha_esperada)

    if not user.first_name:
        user.first_name = "Zelador de Teste Nome"

    user.save()

    Profile.objects.get_or_create(user=user)
    return user


def test_get_profile_sucesso(api_client: APIClient, user_com_nome: User):
    """Verifica se GET /api/accounts/profile/ retorna os dados corretos."""
    api_client.force_authenticate(user=user_com_nome)

    url = "/api/accounts/profile/"
    response = api_client.get(url)

    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Esperado status 200, recebido {response.status_code}. Resposta: {response.content}"

    response_data = response.json()
    assert (
        "nome" in response_data
    ), "A chave 'nome' não está presente na resposta do perfil."
    assert (
        "profile_picture" in response_data
    ), "A chave 'profile_picture' não está presente na resposta do perfil."

    assert (
        response_data["nome"] == user_com_nome.first_name
    ), f"Esperado nome '{user_com_nome.first_name}', recebido '{response_data['nome']}'."

    assert response_data["profile_picture"] is None or isinstance(
        response_data["profile_picture"], str
    ), "O campo 'profile_picture' deve ser null ou uma string (URL relativa)."

    api_client.logout()


def test_get_profile_nao_autenticado_falha(
    api_client: APIClient,
):
    """Verifica se GET /api/accounts/profile/ falha sem autenticação (401)."""

    url = "/api/accounts/profile/"
    response = api_client.get(url)

    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), f"Esperado status 401 ao acessar perfil sem autenticação, recebido {response.status_code}. Resposta: {response.content}"


def test_put_profile_nome_e_imagem_sucesso(
    api_client: APIClient,
    user_com_nome: User,
    test_image_path: Path,
):
    """Verifica se PUT /api/accounts/profile/ atualiza nome e imagem com sucesso."""
    api_client.force_authenticate(user=user_com_nome)

    novo_nome = "Nome Atualizado via PUT"
    nome_arquivo_teste = test_image_path.name

    data = {
        "nome": novo_nome,
        "profile_picture": test_image_path.open("rb"),
    }

    url = "/api/accounts/profile/"

    response = api_client.put(url, data=data, format="multipart")

    data["profile_picture"].close()

    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Esperado status 200, recebido {response.status_code}. Resposta: {response.content}"

    response_data = response.json()
    assert (
        response_data.get("nome") == novo_nome
    ), f"Esperado nome '{novo_nome}' na resposta, recebido '{response_data.get('nome')}'."
    assert (
        response_data.get("profile_picture") is not None
    ), "Esperado uma URL para 'profile_picture' na resposta, recebido None."
    assert isinstance(
        response_data.get("profile_picture"), str
    ), "Esperado que 'profile_picture' seja uma string (URL) na resposta."

    assert response_data["profile_picture"].startswith(
        "/media/profile_pics/"
    ), f"URL da imagem '{response_data['profile_picture']}' não parece começar com o caminho esperado."
    assert response_data["profile_picture"].endswith(
        ".jpg"
    ), f"URL da imagem '{response_data['profile_picture']}' não parece terminar com a extensão esperada '.jpg'."

    user_com_nome.refresh_from_db()
    assert (
        user_com_nome.first_name == novo_nome
    ), f"O first_name do usuário no banco deveria ser '{novo_nome}', mas é '{user_com_nome.first_name}'."

    profile = Profile.objects.get(user=user_com_nome)
    assert (
        profile.profile_picture is not None
    ), "O campo profile_picture no Profile não deveria ser None após o PUT."
    assert (
        profile.profile_picture.name != ""
    ), "O nome do arquivo profile_picture no Profile não deveria estar vazio."

    assert (
        nome_arquivo_teste not in profile.profile_picture.name
    ), f"O nome do arquivo salvo '{profile.profile_picture.name}' inesperadamente contém o nome original '{nome_arquivo_teste}'. Esperava-se um UUID."

    image_path_in_storage = profile.profile_picture.name
    assert default_storage.exists(
        image_path_in_storage
    ), f"O arquivo de imagem '{image_path_in_storage}' não foi encontrado no storage padrão."

    if default_storage.exists(image_path_in_storage):
        default_storage.delete(image_path_in_storage)

    api_client.logout()


def test_put_profile_apenas_nome_sucesso(api_client: APIClient, user_com_nome: User):
    """Verifica se PUT /api/accounts/profile/ apenas com 'nome' atualiza o nome."""

    profile_inicial = Profile.objects.get(user=user_com_nome)
    if profile_inicial.profile_picture:

        profile_inicial.profile_picture.delete(save=True)
        profile_inicial.refresh_from_db()
    assert (
        not profile_inicial.profile_picture
    ), "Pré-condição falhou: O perfil inicial não deveria ter foto."

    api_client.force_authenticate(user=user_com_nome)

    novo_nome = "Nome Atualizado Apenas via PUT"

    data = {
        "nome": novo_nome,
    }

    url = "/api/accounts/profile/"
    response = api_client.put(url, data=data, format="multipart")

    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Esperado status 200, recebido {response.status_code}. Resposta: {response.content}"

    response_data = response.json()
    assert (
        response_data.get("nome") == novo_nome
    ), f"Esperado nome '{novo_nome}' na resposta, recebido '{response_data.get('nome')}'."

    assert (
        response_data.get("profile_picture") is None
    ), f"Esperado 'profile_picture' ser None na resposta (pois não foi enviado), recebido '{response_data.get('profile_picture')}'."

    user_com_nome.refresh_from_db()
    assert (
        user_com_nome.first_name == novo_nome
    ), f"O first_name do usuário no banco deveria ser '{novo_nome}', mas é '{user_com_nome.first_name}'."

    profile_final = Profile.objects.get(user=user_com_nome)
    assert (
        not profile_final.profile_picture
    ), f"O campo profile_picture no Profile deveria permanecer vazio/None após o PUT apenas com nome, mas é '{profile_final.profile_picture}'."

    api_client.logout()


def test_put_profile_remover_imagem_sucesso(
    api_client: APIClient, user_com_nome: User, test_image_path: Path
):
    """Verifica se PUT /api/accounts/profile/ sem imagem remove a imagem existente."""
    api_client.force_authenticate(user=user_com_nome)
    url_profile = "/api/accounts/profile/"
    nome_inicial = user_com_nome.first_name
    nome_arquivo_inicial = test_image_path.name

    data_inicial = {
        "nome": nome_inicial,
        "profile_picture": test_image_path.open("rb"),
    }
    response_inicial = api_client.put(url_profile, data_inicial, format="multipart")
    data_inicial["profile_picture"].close()

    assert (
        response_inicial.status_code == status.HTTP_200_OK
    ), "Falha ao configurar imagem inicial para o teste."
    profile_inicial = Profile.objects.get(user=user_com_nome)
    assert (
        profile_inicial.profile_picture
    ), "Pré-condição falhou: O perfil deveria ter uma foto inicial."
    caminho_imagem_inicial = profile_inicial.profile_picture.name
    assert default_storage.exists(
        caminho_imagem_inicial
    ), f"Arquivo inicial {caminho_imagem_inicial} não foi salvo no storage."

    api_client.force_authenticate(user=user_com_nome)

    novo_nome = "Nome Atualizado Sem Imagem via PUT"

    data_remocao = {
        "nome": novo_nome,
    }

    response_remocao = api_client.put(url_profile, data_remocao, format="multipart")

    assert (
        response_remocao.status_code == status.HTTP_200_OK
    ), f"Esperado status 200 ao remover imagem via PUT, recebido {response_remocao.status_code}. Resposta: {response_remocao.content}"

    response_data = response_remocao.json()
    assert (
        response_data.get("nome") == novo_nome
    ), f"Esperado nome '{novo_nome}' na resposta, recebido '{response_data.get('nome')}'."
    assert (
        response_data.get("profile_picture") is None
    ), f"Esperado 'profile_picture' ser None na resposta após remoção via PUT, recebido '{response_data.get('profile_picture')}'."

    user_com_nome.refresh_from_db()
    assert (
        user_com_nome.first_name == novo_nome
    ), f"O first_name do usuário no banco deveria ser '{novo_nome}', mas é '{user_com_nome.first_name}'."

    profile_final = Profile.objects.get(user=user_com_nome)
    assert (
        not profile_final.profile_picture
    ), f"O campo profile_picture no Profile deveria estar vazio/None após remoção via PUT, mas é '{profile_final.profile_picture}'."

    assert not default_storage.exists(
        caminho_imagem_inicial
    ), f"O arquivo de imagem anterior '{caminho_imagem_inicial}' ainda existe no storage, mas deveria ter sido removido."

    api_client.logout()


def test_put_profile_nao_autenticado_falha(
    api_client: APIClient,
):
    """Verifica se PUT /api/accounts/profile/ falha sem autenticação (401)."""

    data = {
        "nome": "Tentativa Nao Autenticada",
    }

    url = "/api/accounts/profile/"

    response = api_client.put(url, data=data, format="multipart")

    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), f"Esperado status 401 ao tentar atualizar perfil sem autenticação, recebido {response.status_code}. Resposta: {response.content}"


def test_patch_profile_apenas_nome_sucesso(
    api_client: APIClient,
    user_com_nome: User,
    test_image_path: Path,
):
    """Verifica se PATCH /api/accounts/profile/ apenas com 'nome' atualiza o nome e NÃO afeta a foto."""
    api_client.force_authenticate(user=user_com_nome)
    url_profile = "/api/accounts/profile/"
    nome_inicial = "Nome Inicial Para PATCH"
    user_com_nome.first_name = nome_inicial
    user_com_nome.save()

    data_inicial = {"profile_picture": test_image_path.open("rb")}
    response_inicial = api_client.patch(url_profile, data_inicial, format="multipart")
    data_inicial["profile_picture"].close()

    assert (
        response_inicial.status_code == status.HTTP_200_OK
    ), "Falha ao configurar imagem inicial para o teste PATCH."
    profile_inicial = Profile.objects.get(user=user_com_nome)
    assert (
        profile_inicial.profile_picture
    ), "Pré-condição falhou: O perfil deveria ter uma foto inicial."
    url_imagem_inicial = profile_inicial.profile_picture.url

    api_client.force_authenticate(user=user_com_nome)

    novo_nome = "Nome Atualizado Apenas via PATCH"

    data_patch = {
        "nome": novo_nome,
    }

    response_patch = api_client.patch(url_profile, data_patch, format="multipart")

    assert (
        response_patch.status_code == status.HTTP_200_OK
    ), f"Esperado status 200, recebido {response_patch.status_code}. Resposta: {response_patch.content}"

    response_data = response_patch.json()
    assert (
        response_data.get("nome") == novo_nome
    ), f"Esperado nome '{novo_nome}' na resposta, recebido '{response_data.get('nome')}'."
    assert (
        response_data.get("profile_picture") == url_imagem_inicial
    ), f"Esperado URL da imagem original '{url_imagem_inicial}' na resposta, recebido '{response_data.get('profile_picture')}'."

    user_com_nome.refresh_from_db()
    assert (
        user_com_nome.first_name == novo_nome
    ), f"O first_name do usuário no banco deveria ser '{novo_nome}', mas é '{user_com_nome.first_name}'."

    profile_final = Profile.objects.get(user=user_com_nome)
    assert (
        profile_final.profile_picture
    ), "O perfil final não deveria ter perdido a imagem."
    assert (
        profile_final.profile_picture.url == url_imagem_inicial
    ), f"A URL da imagem no banco deveria ser '{url_imagem_inicial}', mas é '{profile_final.profile_picture.url}'."

    if profile_final.profile_picture:
        default_storage.delete(profile_final.profile_picture.name)

    api_client.logout()


def test_patch_profile_apenas_imagem_sucesso(
    api_client: APIClient, user_com_nome: User, test_image_path: Path, tmp_path
):
    """Verifica se PATCH /api/accounts/profile/ apenas com 'profile_picture' atualiza a imagem e NÃO afeta o nome."""
    api_client.force_authenticate(user=user_com_nome)
    url_profile = "/api/accounts/profile/"
    nome_inicial = user_com_nome.first_name
    assert nome_inicial, "Pré-condição falhou: user_com_nome deveria ter um first_name."

    data_inicial = {"profile_picture": test_image_path.open("rb")}
    response_inicial = api_client.patch(url_profile, data_inicial, format="multipart")
    data_inicial["profile_picture"].close()

    assert (
        response_inicial.status_code == status.HTTP_200_OK
    ), "Falha ao configurar imagem inicial para o teste PATCH."
    profile_inicial = Profile.objects.get(user=user_com_nome)
    assert (
        profile_inicial.profile_picture
    ), "Pré-condição falhou: O perfil deveria ter uma foto inicial."

    caminho_imagem_inicial = profile_inicial.profile_picture.name
    url_imagem_inicial = profile_inicial.profile_picture.url
    assert default_storage.exists(
        caminho_imagem_inicial
    ), f"Arquivo inicial {caminho_imagem_inicial} não foi salvo no storage."

    api_client.force_authenticate(user=user_com_nome)

    imagem_nova = Image.new("RGB", (20, 20), color="red")
    path_imagem_nova = tmp_path / "nova_imagem.png"
    imagem_nova.save(path_imagem_nova)

    data_patch = {"profile_picture": path_imagem_nova.open("rb")}

    response_patch = api_client.patch(url_profile, data_patch, format="multipart")
    data_patch["profile_picture"].close()

    assert (
        response_patch.status_code == status.HTTP_200_OK
    ), f"Esperado status 200, recebido {response_patch.status_code}. Resposta: {response_patch.content}"

    response_data = response_patch.json()
    assert (
        response_data.get("nome") == nome_inicial
    ), f"Esperado nome original '{nome_inicial}' na resposta, recebido '{response_data.get('nome')}'."
    url_imagem_nova_resposta = response_data.get("profile_picture")
    assert (
        url_imagem_nova_resposta is not None
    ), "Resposta não contém URL da nova imagem."
    assert (
        url_imagem_nova_resposta != url_imagem_inicial
    ), "URL da imagem na resposta é igual à antiga, mas deveria ser nova."
    assert url_imagem_nova_resposta.startswith(
        "/media/profile_pics/"
    ), "URL da nova imagem não começa com o caminho esperado."
    assert url_imagem_nova_resposta.endswith(
        ".jpg"
    ), "URL da nova imagem não termina com a extensão esperada."

    user_com_nome.refresh_from_db()
    assert (
        user_com_nome.first_name == nome_inicial
    ), f"O first_name do usuário no banco deveria ser '{nome_inicial}', mas é '{user_com_nome.first_name}'."

    profile_final = Profile.objects.get(user=user_com_nome)
    assert (
        profile_final.profile_picture
    ), "O perfil final não deveria ter perdido a imagem."
    assert (
        profile_final.profile_picture.url == url_imagem_nova_resposta
    ), f"A URL da imagem no banco ('{profile_final.profile_picture.url}') não corresponde à URL na resposta ('{url_imagem_nova_resposta}')."
    caminho_imagem_nova_salva = profile_final.profile_picture.name

    assert not default_storage.exists(
        caminho_imagem_inicial
    ), f"O arquivo de imagem anterior '{caminho_imagem_inicial}' ainda existe no storage, mas deveria ter sido removido."

    assert default_storage.exists(
        caminho_imagem_nova_salva
    ), f"O novo arquivo de imagem '{caminho_imagem_nova_salva}' não foi encontrado no storage."

    if default_storage.exists(caminho_imagem_nova_salva):
        default_storage.delete(caminho_imagem_nova_salva)

    api_client.logout()


def test_patch_profile_remover_imagem_sucesso(
    api_client: APIClient, user_com_nome: User, test_image_path: Path
):
    """Verifica se PATCH /api/accounts/profile/ com 'profile_picture'=None remove a imagem existente e NÃO afeta o nome."""
    api_client.force_authenticate(user=user_com_nome)
    api_client.force_authenticate(user=user_com_nome)
    url_profile = "/api/accounts/profile/"
    nome_inicial = user_com_nome.first_name
    assert nome_inicial, "Pré-condição falhou: user_com_nome deveria ter um first_name."

    data_inicial = {"profile_picture": test_image_path.open("rb")}
    response_inicial = api_client.patch(url_profile, data_inicial, format="multipart")
    data_inicial["profile_picture"].close()

    assert (
        response_inicial.status_code == status.HTTP_200_OK
    ), "Falha ao configurar imagem inicial para o teste PATCH."
    profile_inicial = Profile.objects.get(user=user_com_nome)
    assert (
        profile_inicial.profile_picture
    ), "Pré-condição falhou: O perfil deveria ter uma foto inicial."

    caminho_imagem_inicial = profile_inicial.profile_picture.name
    assert default_storage.exists(
        caminho_imagem_inicial
    ), f"Arquivo inicial {caminho_imagem_inicial} não foi salvo no storage."

    api_client.force_authenticate(user=user_com_nome)

    data_patch_remocao = {"profile_picture": ""}

    response_patch = api_client.patch(
        url_profile, data_patch_remocao, format="multipart"
    )

    assert (
        response_patch.status_code == status.HTTP_200_OK
    ), f"Esperado status 200 ao remover imagem via PATCH, recebido {response_patch.status_code}. Resposta: {response_patch.content}"

    response_data = response_patch.json()
    assert (
        response_data.get("nome") == nome_inicial
    ), f"Esperado nome original '{nome_inicial}' na resposta, recebido '{response_data.get('nome')}'."
    assert (
        response_data.get("profile_picture") is None
    ), f"Esperado 'profile_picture' ser None na resposta após remoção via PATCH, recebido '{response_data.get('profile_picture')}'."

    user_com_nome.refresh_from_db()
    assert (
        user_com_nome.first_name == nome_inicial
    ), f"O first_name do usuário no banco deveria ser '{nome_inicial}', mas é '{user_com_nome.first_name}'."

    profile_final = Profile.objects.get(user=user_com_nome)
    assert (
        not profile_final.profile_picture
    ), f"O campo profile_picture no Profile deveria estar vazio/None após remoção via PATCH, mas é '{profile_final.profile_picture}'."

    assert not default_storage.exists(
        caminho_imagem_inicial
    ), f"O arquivo de imagem anterior '{caminho_imagem_inicial}' ainda existe no storage, mas deveria ter sido removido."

    api_client.logout()


def test_patch_profile_imagem_invalida_falha(
    api_client: APIClient, user_com_nome: User, tmp_path
):
    """Verifica se PATCH /api/accounts/profile/ com arquivo inválido para 'profile_picture' falha (400)."""
    api_client.force_authenticate(user=user_com_nome)

    arquivo_invalido_conteudo = b"Este nao e um arquivo de imagem valido."
    arquivo_invalido = BytesIO(arquivo_invalido_conteudo)
    nome_arquivo_invalido = "arquivo_texto.txt"

    data_patch = {
        "profile_picture": (nome_arquivo_invalido, arquivo_invalido, "text/plain")
    }

    url = "/api/accounts/profile/"
    response = api_client.patch(url, data=data_patch, format="multipart")

    arquivo_invalido.close()

    assert (
        response.status_code == status.HTTP_400_BAD_REQUEST
    ), f"Esperado status 400 ao enviar imagem inválida, recebido {response.status_code}. Resposta: {response.content}"

    response_data = response.json()
    assert (
        "profile_picture" in response_data
    ), "A resposta de erro não contém a chave 'profile_picture'."

    error_message = response_data["profile_picture"][0]
    assert (
        "imagem válida" in error_message.lower()
        or "não é um arquivo de imagem" in error_message.lower()
    ), f"A mensagem de erro para 'profile_picture' ('{error_message}') não indica um problema de imagem inválida em Português."

    api_client.logout()


def test_patch_profile_nao_autenticado_falha(
    api_client: APIClient,
):
    """Verifica se PATCH /api/accounts/profile/ falha sem autenticação (401)."""

    data = {
        "nome": "Tentativa PATCH Nao Autenticada",
    }

    url = "/api/accounts/profile/"

    response = api_client.patch(url, data=data, format="multipart")

    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), f"Esperado status 401 ao tentar PATCH no perfil sem autenticação, recebido {response.status_code}. Resposta: {response.content}"


def test_change_password_sucesso(api_client: APIClient, user_com_nome: User):
    """Verifica o fluxo completo de troca de senha via POST /api/accounts/change_password/."""

    senha_original = os.getenv("TEST_USER_ZELADOR_PASSWORD", "Senac@098")
    usuario = user_com_nome

    assert usuario.check_password(
        senha_original
    ), f"A senha original '{senha_original}' não corresponde à senha do usuário '{usuario.username}' no início do teste."

    nova_senha = "NovaSenhaSegura@123!"

    api_client.force_authenticate(user=usuario)

    payload = {
        "old_password": senha_original,
        "new_password": nova_senha,
        "confirm_new_password": nova_senha,
    }

    url = "/api/accounts/change_password/"
    response = api_client.post(url, data=payload, format="json")

    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Esperado status 200, recebido {response.status_code}. Resposta: {response.content}"

    response_data = response.json()
    assert "message" in response_data
    assert "Senha alterada com sucesso" in response_data["message"]

    api_client.logout()

    login_url = "/api/accounts/login/"
    response_login_antiga = api_client.post(
        login_url,
        {"username": usuario.username, "password": senha_original},
        format="json",
    )
    assert (
        response_login_antiga.status_code == status.HTTP_400_BAD_REQUEST
    ), "Login com a senha antiga deveria falhar após a mudança, mas retornou status diferente de 400."
    assert (
        "Credenciais inválidas"
        in response_login_antiga.json().get("non_field_errors", [""])[0]
    )

    response_login_nova = api_client.post(
        login_url, {"username": usuario.username, "password": nova_senha}, format="json"
    )
    assert (
        response_login_nova.status_code == status.HTTP_200_OK
    ), f"Login com a nova senha falhou. Status: {response_login_nova.status_code}, Resposta: {response_login_nova.content}"
    assert "token" in response_login_nova.json()

    usuario.set_password(senha_original)
    usuario.save()

    usuario.refresh_from_db()
    assert usuario.check_password(
        senha_original
    ), "Falha ao restaurar a senha original do usuário no final do teste."

    api_client.logout()


def test_change_password_senha_antiga_incorreta_falha(
    api_client: APIClient, user_com_nome: User
):
    """Verifica que a requisição falha (400) quando 'old_password' está incorreta."""

    usuario = user_com_nome
    senha_original_correta = os.getenv("TEST_USER_ZELADOR_PASSWORD", "Senac@098")

    senha_antiga_incorreta = "senha_errada_123"
    nova_senha = "NovaSenhaSegura@123!"

    api_client.force_authenticate(user=usuario)

    payload = {
        "old_password": senha_antiga_incorreta,
        "new_password": nova_senha,
        "confirm_new_password": nova_senha,
    }

    url = "/api/accounts/change_password/"
    response = api_client.post(url, data=payload, format="json")

    assert (
        response.status_code == status.HTTP_400_BAD_REQUEST
    ), f"Esperado status 400 ao fornecer senha antiga incorreta, recebido {response.status_code}. Resposta: {response.content}"

    response_data = response.json()
    assert (
        "old_password" in response_data
    ), "A resposta de erro não contém a chave 'old_password'."
    assert (
        "A senha antiga está incorreta." in response_data["old_password"]
    ), f"Mensagem de erro inesperada para 'old_password': {response_data['old_password']}"

    usuario.refresh_from_db()
    assert usuario.check_password(
        senha_original_correta
    ), "A senha do usuário foi alterada indevidamente, mesmo com a senha antiga incorreta."
    assert not usuario.check_password(
        nova_senha
    ), "A senha do usuário foi alterada para a nova senha, o que não deveria ocorrer."

    api_client.logout()


def test_change_password_senha_antiga_incorreta_falha(
    api_client: APIClient, user_com_nome: User
):
    """Verifica que a requisição retorna 400 quando 'old_password' está incorreta."""

    usuario = user_com_nome
    senha_original_correta = os.getenv("TEST_USER_ZELADOR_PASSWORD", "Senac@098")

    senha_antiga_incorreta = "senha_que_nao_e_a_certa_XYZ"
    nova_senha = "OutraNovaSenha@456!"

    api_client.force_authenticate(user=usuario)

    payload = {
        "old_password": senha_antiga_incorreta,
        "new_password": nova_senha,
        "confirm_new_password": nova_senha,
    }

    url = "/api/accounts/change_password/"
    response = api_client.post(url, data=payload, format="json")

    assert (
        response.status_code == status.HTTP_400_BAD_REQUEST
    ), f"Esperado status 400 ao fornecer senha antiga incorreta, recebido {response.status_code}. Resposta: {response.content}"

    response_data = response.json()
    assert (
        "old_password" in response_data
    ), "A resposta de erro não contém a chave 'old_password'."  #

    assert (
        "A senha antiga está incorreta." in response_data["old_password"]
    ), f"Mensagem de erro inesperada para 'old_password': {response_data['old_password']}"  #

    usuario.refresh_from_db()
    assert usuario.check_password(
        senha_original_correta
    ), "A senha do usuário foi alterada indevidamente, mesmo com a senha antiga incorreta."  #
    assert not usuario.check_password(
        nova_senha
    ), "A senha do usuário foi alterada para a nova senha, o que não deveria ocorrer."  #

    api_client.logout()


def test_change_password_senha_antiga_incorreta_falha(
    api_client: APIClient, user_com_nome: User
):
    """Verifica que mudar senha com 'old_password' incorreta retorna 400."""

    usuario = user_com_nome
    senha_original_correta = os.getenv("TEST_USER_ZELADOR_PASSWORD", "Senac@098")

    senha_antiga_incorreta = "senha_que_nao_e_a_certa_XYZ"
    nova_senha = "OutraNovaSenha@456!"

    api_client.force_authenticate(user=usuario)

    payload = {
        "old_password": senha_antiga_incorreta,
        "new_password": nova_senha,
        "confirm_new_password": nova_senha,
    }

    url = "/api/accounts/change_password/"
    response = api_client.post(url, data=payload, format="json")

    assert (
        response.status_code == status.HTTP_400_BAD_REQUEST
    ), f"Esperado status 400 ao fornecer senha antiga incorreta, recebido {response.status_code}. Resposta: {response.content}"

    response_data = response.json()
    assert (
        "old_password" in response_data
    ), "A resposta de erro não contém a chave 'old_password'."  #

    assert (
        "A senha antiga está incorreta." in response_data["old_password"]
    ), f"Mensagem de erro inesperada para 'old_password': {response_data['old_password']}"  #

    usuario.refresh_from_db()
    assert usuario.check_password(
        senha_original_correta
    ), "A senha do usuário foi alterada indevidamente, mesmo com a senha antiga incorreta."  #
    assert not usuario.check_password(
        nova_senha
    ), "A senha do usuário foi alterada para a nova senha, o que não deveria ocorrer."  #

    api_client.logout()


def test_change_password_confirmacao_nova_senha_falha(
    api_client: APIClient, user_com_nome: User
):
    """Verifica que a requisição falha (400) quando a confirmação da nova senha não coincide."""

    usuario = user_com_nome
    senha_original_correta = os.getenv("TEST_USER_ZELADOR_PASSWORD", "Senac@098")

    nova_senha = "SenhaValida@123"
    confirmacao_incorreta = "SenhaDiferente@456"

    api_client.force_authenticate(user=usuario)

    payload = {
        "old_password": senha_original_correta,
        "new_password": nova_senha,
        "confirm_new_password": confirmacao_incorreta,
    }

    url = "/api/accounts/change_password/"
    response = api_client.post(url, data=payload, format="json")

    assert (
        response.status_code == status.HTTP_400_BAD_REQUEST
    ), f"Esperado status 400 quando confirmação de senha falha, recebido {response.status_code}. Resposta: {response.content}"

    response_data = response.json()
    assert (
        "new_password" in response_data
    ), "A resposta de erro não contém a chave 'new_password'."

    assert (
        "As novas senhas não coincidem." in response_data["new_password"]
    ), f"Mensagem de erro inesperada para 'new_password': {response_data['new_password']}"

    usuario.refresh_from_db()
    assert usuario.check_password(
        senha_original_correta
    ), "A senha do usuário foi alterada indevidamente, mesmo com a confirmação incorreta."
    assert not usuario.check_password(
        nova_senha
    ), "A senha do usuário foi alterada para a nova senha, o que não deveria ocorrer."

    api_client.logout()


def test_change_password_confirmacao_nova_senha_falha(
    api_client: APIClient, user_com_nome: User
):
    """Verifica que a requisição falha (400) quando a confirmação da nova senha não coincide."""

    usuario = user_com_nome
    senha_original_correta = os.getenv("TEST_USER_ZELADOR_PASSWORD", "Senac@098")

    nova_senha = "SenhaValida@123"
    confirmacao_incorreta = "SenhaDiferente@456"

    api_client.force_authenticate(user=usuario)

    payload = {
        "old_password": senha_original_correta,
        "new_password": nova_senha,
        "confirm_new_password": confirmacao_incorreta,
    }

    url = "/api/accounts/change_password/"
    response = api_client.post(url, data=payload, format="json")

    assert (
        response.status_code == status.HTTP_400_BAD_REQUEST
    ), f"Esperado status 400 quando confirmação de senha falha, recebido {response.status_code}. Resposta: {response.content}"

    response_data = response.json()
    assert (
        "new_password" in response_data
    ), "A resposta de erro não contém a chave 'new_password'."

    assert (
        "As novas senhas não coincidem." in response_data["new_password"]
    ), f"Mensagem de erro inesperada para 'new_password': {response_data['new_password']}"  #

    usuario.refresh_from_db()
    assert usuario


@pytest.mark.parametrize(
    "senha_fraca",
    [
        "123",
        "password",
        "USERNAME_PLACEHOLDER",
    ],
)
def test_change_password_nova_senha_fraca_falha(
    api_client: APIClient,
    user_com_nome: User,
    senha_fraca: str,
):
    """
    Verifica se POST /api/accounts/change_password/ falha (400)
    quando a nova senha ('new_password') é considerada fraca pelos validadores.

    """

    usuario = user_com_nome
    senha_original_correta = os.getenv("TEST_USER_ZELADOR_PASSWORD", "Senac@098")

    if senha_fraca == "USERNAME_PLACEHOLDER":
        senha_fraca_atual = usuario.username
    else:
        senha_fraca_atual = senha_fraca

    api_client.force_authenticate(user=usuario)

    payload = {
        "old_password": senha_original_correta,
        "new_password": senha_fraca_atual,
        "confirm_new_password": senha_fraca_atual,
    }

    url = "/api/accounts/change_password/"
    response = api_client.post(url, data=payload, format="json")

    assert (
        response.status_code == status.HTTP_400_BAD_REQUEST
    ), f"Esperado status 400 ao usar senha fraca '{senha_fraca_atual}', recebido {response.status_code}. Resposta: {response.content}"

    response_data = response.json()
    assert (
        "new_password" in response_data
    ), f"A resposta de erro para senha fraca '{senha_fraca_atual}' não contém a chave 'new_password'."
    assert (
        len(response_data["new_password"]) > 0
    ), f"Esperado pelo menos uma mensagem de erro de validação para 'new_password' com senha fraca '{senha_fraca_atual}', mas a lista está vazia."

    usuario.refresh_from_db()
    assert usuario.check_password(
        senha_original_correta
    ), f"A senha do usuário foi alterada indevidamente ao tentar usar a senha fraca '{senha_fraca_atual}'."
    assert not usuario.check_password(
        senha_fraca_atual
    ), f"A senha fraca '{senha_fraca_atual}' foi definida, o que não deveria ocorrer."

    api_client.logout()


def test_change_password_nao_autenticado_falha(
    api_client: APIClient,
):
    """Verifica que change_password exige autenticação (401)."""

    payload = {
        "old_password": "alguma_senha_antiga",
        "new_password": "NovaSenha@123!",
        "confirm_new_password": "NovaSenha@123!",
    }

    url = "/api/accounts/change_password/"
    response = api_client.post(url, data=payload, format="json")

    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    ), f"Esperado status 401 ao tentar mudar senha sem autenticação, recebido {response.status_code}. Resposta: {response.content}"


@pytest.fixture
def admin_user(db) -> User:
    """Garante que o usuário admin exista, tenha a senha correta e seja superuser."""
    admin_username = os.getenv("TEST_USER_ADMIN_USERNAME", "administrador")
    admin_password = os.getenv("TEST_USER_ADMIN_PASSWORD", "Senac@123")

    user, created = User.objects.get_or_create(username=admin_username)

    user.set_password(admin_password)
    user.is_staff = True
    user.is_superuser = True
    user.save()

    return user


@pytest.fixture
def grupo_zeladoria(db) -> Group:
    """Garante que o grupo Zeladoria exista e o retorna."""
    grupo, _ = Group.objects.get_or_create(name="Zeladoria")
    return grupo


@pytest.fixture
def solicitante_user(db) -> User:
    """Garante que o usuário solicitante exista com a senha correta."""
    username = os.getenv("TEST_USER_SOLICITANTE_USERNAME", "colaborador")
    password = os.getenv("TEST_USER_SOLICITANTE_PASSWORD", "Senac@432")

    grupo_nome = "Solicitante de Serviços"
    grupo, _ = Group.objects.get_or_create(name=grupo_nome)

    user, created = User.objects.get_or_create(username=username)

    user.set_password(password)
    user.is_staff = False
    user.is_superuser = False
    user.save()

    user.groups.set([grupo])

    return user


def test_create_user_admin_sucesso(
    api_client: APIClient,
    admin_user: User,
    grupo_zeladoria: Group,
):
    """
    Verifica se POST /api/accounts/create_user/ funciona para admin.
    ... (docstring) ...
    """

    novo_username = f"novo_usuario_{uuid.uuid4().hex[:8]}"
    novo_nome = "Nome Completo Novo Usuario"
    novo_email = f"{novo_username}@teste.com"
    nova_senha_valida = "SenhaF0rte@123"

    payload = {
        "username": novo_username,
        "password": nova_senha_valida,
        "confirm_password": nova_senha_valida,
        "nome": novo_nome,
        "email": novo_email,
        "groups": [grupo_zeladoria.id],
    }

    url = "/api/accounts/create_user/"

    api_client.force_authenticate(user=admin_user)

    response = api_client.post(url, data=payload, format="json")

    assert (
        response.status_code == status.HTTP_201_CREATED
    ), f"Esperado status 201, recebido {response.status_code}. Resposta: {response.content}"

    response_data = response.json()
    assert "message" in response_data
    assert "Usuário criado com sucesso" in response_data["message"]

    try:
        usuario_criado = User.objects.get(username=novo_username)

    except User.DoesNotExist:
        pytest.fail(
            f"Usuário '{novo_username}' não foi encontrado no banco de dados após criação bem-sucedida."
        )

    usuario_criado.delete()

    api_client.logout()


@pytest.mark.parametrize(
    "non_admin_user_fixture",
    [
        "user_com_nome",
        "solicitante_user",
    ],
)
def test_create_user_nao_admin_falha(
    api_client: APIClient,
    non_admin_user_fixture: str,
    request: pytest.FixtureRequest,
):
    """
    Verifica se POST /api/accounts/create_user/ falha (403) para não-admins.
    ... (docstring) ...
    """

    usuario_nao_admin = request.getfixturevalue(non_admin_user_fixture)
    assert (
        not usuario_nao_admin.is_staff
    ), f"Fixture {non_admin_user_fixture} deveria ser não-staff."

    novo_username = f"teste_falha_{uuid.uuid4().hex[:8]}"
    payload = {
        "username": novo_username,
        "password": "SenhaQualquer@123",
        "confirm_password": "SenhaQualquer@123",
        "nome": "Teste Falha",
    }

    api_client.force_authenticate(user=usuario_nao_admin)

    url = "/api/accounts/create_user/"
    response = api_client.post(url, data=payload, format="json")

    assert (
        response.status_code == status.HTTP_403_FORBIDDEN
    ), f"Esperado status 403 para o usuário '{usuario_nao_admin.username}', recebido {response.status_code}. Resposta: {response.content}"

    response_data = response.json()
    assert "detail" in response_data

    assert "Você não tem permissão para executar essa ação." in response_data["detail"]

    assert not User.objects.filter(
        username=novo_username
    ).exists(), f"O usuário '{novo_username}' foi criado indevidamente pelo usuário não-admin '{usuario_nao_admin.username}'."

    api_client.logout()


def test_create_user_username_duplicado_falha(
    api_client: APIClient,
    admin_user: User,
    user_com_nome: User,
):
    """Verifica que criar usuário com username duplicado retorna 400."""

    usuario_existente = user_com_nome
    username_duplicado = usuario_existente.username

    payload = {
        "username": username_duplicado,
        "password": "SenhaQualquer@123",
        "confirm_password": "SenhaQualquer@123",
        "nome": "Tentativa Duplicada",
    }

    api_client.force_authenticate(user=admin_user)

    url = "/api/accounts/create_user/"
    response = api_client.post(url, data=payload, format="json")

    assert (
        response.status_code == status.HTTP_400_BAD_REQUEST
    ), f"Esperado status 400 ao tentar criar usuário com username duplicado '{username_duplicado}', recebido {response.status_code}. Resposta: {response.content}"

    response_data = response.json()
    assert (
        "username" in response_data
    ), "A resposta de erro não contém a chave 'username'."

    assert (
        "Um usuário com este nome de usuário já existe." in response_data["username"]
    ), f"Mensagem de erro inesperada para 'username': {response_data['username']}"

    api_client.logout()


@pytest.mark.parametrize(
    "senha_fraca",
    [
        "123",
        "password",
        "USERNAME_PLACEHOLDER",
    ],
)
def test_create_user_senha_fraca_falha(
    api_client: APIClient,
    admin_user: User,
    senha_fraca: str,
):
    """Verifica que criar usuário com senha fraca falha (400)."""

    novo_username = f"user_fraco_{uuid.uuid4().hex[:8]}"

    if senha_fraca == "USERNAME_PLACEHOLDER":

        senha_fraca_atual = novo_username
    else:
        senha_fraca_atual = senha_fraca

    payload = {
        "username": novo_username,
        "password": senha_fraca_atual,
        "confirm_password": senha_fraca_atual,
        "nome": "Usuario Senha Fraca",
        "email": f"{novo_username}@teste.com",
    }

    api_client.force_authenticate(user=admin_user)

    url = "/api/accounts/create_user/"
    response = api_client.post(url, data=payload, format="json")

    assert (
        response.status_code == status.HTTP_400_BAD_REQUEST
    ), f"Esperado status 400 ao tentar criar usuário com senha fraca '{senha_fraca_atual}', recebido {response.status_code}. Resposta: {response.content}"

    response_data = response.json()
    assert (
        "password" in response_data
    ), f"A resposta de erro para senha fraca '{senha_fraca_atual}' não contém a chave 'password'."

    assert (
        len(response_data["password"]) > 0
    ), f"Esperado pelo menos uma mensagem de erro de validação para 'password' com senha fraca '{senha_fraca_atual}', mas a lista está vazia."

    assert not User.objects.filter(
        username=novo_username
    ).exists(), (
        f"O usuário '{novo_username}' foi criado indevidamente com uma senha fraca."
    )

    api_client.logout()


@pytest.mark.parametrize(
    "payload_invalido, campo_faltante",
    [
        (
            {
                "password": "SenhaValida@123",
                "confirm_password": "SenhaValida@123",
                "nome": "Teste Sem User",
            },
            "username",
        ),
        (
            {
                "username": f"user_sem_senha_{uuid.uuid4().hex[:8]}",
                "confirm_password": "SenhaValida@123",
                "nome": "Teste Sem Senha",
            },
            "password",
        ),
        (
            {
                "username": f"user_sem_conf_{uuid.uuid4().hex[:8]}",
                "password": "SenhaValida@123",
                "nome": "Teste Sem Confirmacao",
            },
            "confirm_password",
        ),
    ],
)
def test_create_user_campos_obrigatorios_faltando_falha(
    api_client: APIClient,
    admin_user: User,
    payload_invalido: Dict[str, str],
    campo_faltante: str,
):
    """Verifica que criar usuário sem campos obrigatórios retorna 400."""

    api_client.force_authenticate(user=admin_user)

    url = "/api/accounts/create_user/"
    response = api_client.post(url, data=payload_invalido, format="json")

    assert (
        response.status_code == status.HTTP_400_BAD_REQUEST
    ), f"Esperado status 400 ao tentar criar usuário sem o campo '{campo_faltante}', recebido {response.status_code}. Resposta: {response.content}"

    response_data = response.json()
    assert (
        campo_faltante in response_data
    ), f"A resposta de erro não contém a chave esperada '{campo_faltante}'."
    assert (
        "Este campo é obrigatório." in response_data[campo_faltante]
    ), f"Mensagem de erro inesperada para o campo '{campo_faltante}': {response_data[campo_faltante]}"

    api_client.logout()
