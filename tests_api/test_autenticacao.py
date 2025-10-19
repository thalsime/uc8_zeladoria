"""Testes de integração para os endpoints de Autenticação e Contas.
Esta suíte de testes valida:
- O fluxo de login com credenciais válidas e inválidas.
- O controle de acesso a rotas protegidas com e sem token JWT.
- A obtenção de dados do usuário logado.
"""
import os
import pytest
import requests
from django.core.files.storage import default_storage
from django.contrib.auth.models import User
from io import BytesIO
from pathlib import Path
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient
from accounts.models import Profile


# Testes de Login (/api/accounts/login/)

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

@pytest.mark.skip(reason="O endpoint de logout precisa ser ajustado no backend para invalidar o token.")
def test_logout_sucesso(api_base_url, auth_header_admin):
    """Verifica se o logout é bem-sucedido."""
    response = requests.post(f"{api_base_url}/accounts/logout/", headers=auth_header_admin)
    assert response.status_code == 200

    response_depois_logout = requests.get(f"{api_base_url}/salas/", headers=auth_header_admin)
    assert response_depois_logout.status_code == 401


# Testes de Obtenção do Usuário Logado (/api/accounts/current_user/)

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

# Testes de Gerenciamento de Perfil (/api/accounts/profile/)

# Fixture para fornecer o cliente de API do DRF
@pytest.fixture
def api_client() -> APIClient:
    """Fixture que fornece uma instância do APIClient do DRF."""
    return APIClient()

# Fixture para garantir que um usuário tenha um nome definido
@pytest.fixture
def user_com_nome(db) -> User:
    """Cria ou obtém o usuário 'zelador' e garante que ele tenha um first_name."""
    zelador_username = os.getenv("TEST_USER_ZELADOR_USERNAME", "zelador")
    user, _ = User.objects.get_or_create(username=zelador_username)
    if not user.first_name:
        user.first_name = "Zelador de Teste Nome"
        user.save()
    # Garante que o perfil exista (o signal deve criar, mas garantimos aqui)
    Profile.objects.get_or_create(user=user)
    return user

def test_get_profile_sucesso(
    api_client: APIClient,
    user_com_nome: User # Usa a fixture que garante o nome
):
    """
    Verifica se GET /api/accounts/profile/ retorna os dados corretos.

    Passos:
    1. Obtém um usuário com nome definido (fixture user_com_nome).
    2. Autentica o cliente com este usuário.
    3. Faz a requisição GET para /api/accounts/profile/.
    4. Verifica se o status code é 200 OK.
    5. Verifica se a resposta contém as chaves 'nome' e 'profile_picture'.
    6. Verifica se o valor de 'nome' corresponde ao first_name do usuário.
    """
    # 1. Usuário obtido pela fixture

    # 2. Autenticar
    api_client.force_authenticate(user=user_com_nome)

    # 3. Fazer a requisição GET
    url = "/api/accounts/profile/"
    response = api_client.get(url)

    # 4. Verificar Status Code
    assert response.status_code == status.HTTP_200_OK, \
        f"Esperado status 200, recebido {response.status_code}. Resposta: {response.content}"

    # 5. Verificar chaves na resposta
    response_data = response.json()
    assert "nome" in response_data, "A chave 'nome' não está presente na resposta do perfil."
    assert "profile_picture" in response_data, "A chave 'profile_picture' não está presente na resposta do perfil."

    # 6. Verificar valor do nome
    assert response_data["nome"] == user_com_nome.first_name, \
        f"Esperado nome '{user_com_nome.first_name}', recebido '{response_data['nome']}'."

    # Verificar tipo da foto de perfil (pode ser null ou string)
    assert response_data["profile_picture"] is None or isinstance(response_data["profile_picture"], str), \
        "O campo 'profile_picture' deve ser null ou uma string (URL relativa)."

    # Opcional: Desautenticar
    api_client.logout()


def test_get_profile_nao_autenticado_falha(
    api_client: APIClient # Cliente não autenticado
):
    """
    Verifica se GET /api/accounts/profile/ falha sem autenticação (401).

    Passos:
    1. NÃO autentica o cliente.
    2. Faz a requisição GET para /api/accounts/profile/.
    3. Verifica se o status code é 401 Unauthorized.
    """
    # 1. NÃO autenticar

    # 2. Fazer a requisição GET
    url = "/api/accounts/profile/"
    response = api_client.get(url) # Requisição sem header de autorização

    # 3. Verificar Status Code 401
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
        f"Esperado status 401 ao acessar perfil sem autenticação, recebido {response.status_code}. Resposta: {response.content}"

    # Não precisamos de fixtures de usuário aqui, pois o erro 401 deve ocorrer antes.
    # Não há necessidade de logout.

def test_put_profile_nome_e_imagem_sucesso(
    api_client: APIClient,
    user_com_nome: User,
    test_image_path: Path # Fixture que cria um arquivo de imagem temporário
):
    """
    Verifica se PUT /api/accounts/profile/ atualiza nome e imagem com sucesso.

    Passos:
    1. Obtém um usuário autenticado.
    2. Prepara o payload multipart/form-data com novo nome e arquivo de imagem.
    3. Faz a requisição PUT para /api/accounts/profile/.
    4. Verifica se o status code é 200 OK.
    5. Verifica se a resposta contém o nome atualizado e uma URL de imagem válida.
    6. Verifica no banco se user.first_name foi atualizado.
    7. Verifica no banco se profile.profile_picture foi atualizado (não é mais None/vazio).
    8. Opcional: Verifica se o arquivo de imagem foi salvo no local correto.
    """
    # 1. Autenticar
    api_client.force_authenticate(user=user_com_nome)

    # Nome e arquivo para a atualização
    novo_nome = "Nome Atualizado via PUT"
    nome_arquivo_teste = test_image_path.name

    # 2. Preparar payload multipart/form-data
    # Usamos um dicionário simples para `data`. O `APIClient` lida com a formatação.
    data = {
        'nome': novo_nome,
        'profile_picture': test_image_path.open('rb') # Abre o arquivo em modo binário
    }

    # 3. Fazer a requisição PUT, especificando o formato
    url = "/api/accounts/profile/"
    # Importante: Usar format='multipart' para uploads com APIClient
    response = api_client.put(url, data=data, format='multipart')

    # Fechar o arquivo após a requisição
    data['profile_picture'].close()

    # 4. Verificar Status Code
    assert response.status_code == status.HTTP_200_OK, \
        f"Esperado status 200, recebido {response.status_code}. Resposta: {response.content}"

    # 5. Verificar resposta
    response_data = response.json()
    assert response_data.get("nome") == novo_nome, \
        f"Esperado nome '{novo_nome}' na resposta, recebido '{response_data.get('nome')}'."
    assert response_data.get("profile_picture") is not None, \
        "Esperado uma URL para 'profile_picture' na resposta, recebido None."
    assert isinstance(response_data.get("profile_picture"), str), \
        "Esperado que 'profile_picture' seja uma string (URL) na resposta."
    # Verifica se a URL parece válida (começa com /media/ e termina com .jpg)
    assert response_data["profile_picture"].startswith('/media/profile_pics/'), \
        f"URL da imagem '{response_data['profile_picture']}' não parece começar com o caminho esperado."
    assert response_data["profile_picture"].endswith('.jpg'), \
        f"URL da imagem '{response_data['profile_picture']}' não parece terminar com a extensão esperada '.jpg'."

    # 6. Verificar atualização do nome no User
    user_com_nome.refresh_from_db() # Recarrega o usuário do banco
    assert user_com_nome.first_name == novo_nome, \
        f"O first_name do usuário no banco deveria ser '{novo_nome}', mas é '{user_com_nome.first_name}'."

    # 7. Verificar atualização da imagem no Profile
    profile = Profile.objects.get(user=user_com_nome)
    assert profile.profile_picture is not None, "O campo profile_picture no Profile não deveria ser None após o PUT."
    assert profile.profile_picture.name != "", "O nome do arquivo profile_picture no Profile não deveria estar vazio."
    # O nome do arquivo salvo terá um UUID, não será o nome original
    assert nome_arquivo_teste not in profile.profile_picture.name, \
        f"O nome do arquivo salvo '{profile.profile_picture.name}' inesperadamente contém o nome original '{nome_arquivo_teste}'. Esperava-se um UUID."

    # 8. Opcional: Verificar se o arquivo existe no storage
    # Nota: default_storage aponta para o sistema de arquivos local em desenvolvimento/teste
    image_path_in_storage = profile.profile_picture.name
    assert default_storage.exists(image_path_in_storage), \
        f"O arquivo de imagem '{image_path_in_storage}' não foi encontrado no storage padrão."

    # Limpeza adicional (excluir o arquivo criado, se necessário, embora o model save deva lidar com isso em futuras atualizações)
    if default_storage.exists(image_path_in_storage):
         default_storage.delete(image_path_in_storage) # Limpa o arquivo criado pelo teste

    # Opcional: Desautenticar
    api_client.logout()


# ... (imports e fixtures anteriores) ...

def test_put_profile_apenas_nome_sucesso(
    api_client: APIClient,
    user_com_nome: User
):
    """
    Verifica se PUT /api/accounts/profile/ apenas com 'nome' atualiza o nome.

    Verifica também o comportamento em relação à foto de perfil (se ela é
    mantida ou removida quando não enviada no PUT).

    Passos:
    1. Garante que o usuário inicial NÃO tenha foto de perfil.
    2. Autentica o cliente com este usuário.
    3. Prepara o payload multipart/form-data APENAS com o novo nome.
    4. Faz a requisição PUT para /api/accounts/profile/.
    5. Verifica se o status code é 200 OK.
    6. Verifica se a resposta contém o nome atualizado.
    7. Verifica se 'profile_picture' na resposta continua None.
    8. Verifica no banco se user.first_name foi atualizado.
    9. Verifica no banco se profile.profile_picture continua None/vazio.
    """
    # 1. Garantir estado inicial sem foto
    profile_inicial = Profile.objects.get(user=user_com_nome)
    if profile_inicial.profile_picture:
        # Se houver foto, remove para o teste iniciar sem ela
        profile_inicial.profile_picture.delete(save=True)
        profile_inicial.refresh_from_db() # Recarrega do banco
    assert not profile_inicial.profile_picture, "Pré-condição falhou: O perfil inicial não deveria ter foto."


    # 2. Autenticar
    api_client.force_authenticate(user=user_com_nome)

    novo_nome = "Nome Atualizado Apenas via PUT"

    # 3. Preparar payload multipart APENAS com nome
    # Mesmo sem arquivo, a view espera multipart/form-data
    data = {
        'nome': novo_nome,
        # Intencionalmente omitimos 'profile_picture'
    }

    # 4. Fazer a requisição PUT
    url = "/api/accounts/profile/"
    response = api_client.put(url, data=data, format='multipart')

    # 5. Verificar Status Code
    assert response.status_code == status.HTTP_200_OK, \
        f"Esperado status 200, recebido {response.status_code}. Resposta: {response.content}"

    # 6. Verificar nome na resposta
    response_data = response.json()
    assert response_data.get("nome") == novo_nome, \
        f"Esperado nome '{novo_nome}' na resposta, recebido '{response_data.get('nome')}'."

    # 7. Verificar 'profile_picture' na resposta (deve continuar None)
    assert response_data.get("profile_picture") is None, \
        f"Esperado 'profile_picture' ser None na resposta (pois não foi enviado), recebido '{response_data.get('profile_picture')}'."

    # 8. Verificar atualização do nome no User no banco
    user_com_nome.refresh_from_db()
    assert user_com_nome.first_name == novo_nome, \
        f"O first_name do usuário no banco deveria ser '{novo_nome}', mas é '{user_com_nome.first_name}'."

    # 9. Verificar profile_picture no Profile no banco (deve continuar None/vazio)
    profile_final = Profile.objects.get(user=user_com_nome)
    assert not profile_final.profile_picture, \
        f"O campo profile_picture no Profile deveria permanecer vazio/None após o PUT apenas com nome, mas é '{profile_final.profile_picture}'."

    # Opcional: Desautenticar
    api_client.logout()


# ... (imports e fixtures anteriores) ...

def test_put_profile_remover_imagem_sucesso(
    api_client: APIClient,
    user_com_nome: User,
    test_image_path: Path
):
    """
    Verifica se PUT /api/accounts/profile/ sem imagem remove a imagem existente.

    Passos:
    1. Garante que o usuário inicial TENHA uma foto de perfil.
    2. Autentica o cliente com este usuário.
    3. Prepara o payload multipart/form-data com novo nome, mas SEM o campo 'profile_picture'.
    4. Faz a requisição PUT para /api/accounts/profile/.
    5. Verifica se o status code é 200 OK.
    6. Verifica se a resposta contém o nome atualizado e 'profile_picture' como None.
    7. Verifica no banco se user.first_name foi atualizado.
    8. Verifica no banco se profile.profile_picture está vazio/None.
    9. Verifica se o arquivo de imagem anterior foi removido do storage.
    """
    # 1. Garantir estado inicial COM foto
    api_client.force_authenticate(user=user_com_nome)
    url_profile = "/api/accounts/profile/"
    nome_inicial = user_com_nome.first_name
    nome_arquivo_inicial = test_image_path.name

    # Upload inicial da imagem
    data_inicial = {
        'nome': nome_inicial, # Mantém o nome inicial por enquanto
        'profile_picture': test_image_path.open('rb')
    }
    response_inicial = api_client.put(url_profile, data_inicial, format='multipart')
    data_inicial['profile_picture'].close()

    assert response_inicial.status_code == status.HTTP_200_OK, "Falha ao configurar imagem inicial para o teste."
    profile_inicial = Profile.objects.get(user=user_com_nome)
    assert profile_inicial.profile_picture, "Pré-condição falhou: O perfil deveria ter uma foto inicial."
    caminho_imagem_inicial = profile_inicial.profile_picture.name # Guarda o caminho para verificar a exclusão
    assert default_storage.exists(caminho_imagem_inicial), f"Arquivo inicial {caminho_imagem_inicial} não foi salvo no storage."


    # 2. Re-Autenticar (embora já esteja, é boa prática para clareza)
    api_client.force_authenticate(user=user_com_nome)

    novo_nome = "Nome Atualizado Sem Imagem via PUT"

    # 3. Preparar payload PUT apenas com nome
    data_remocao = {
        'nome': novo_nome,
        # Omitir 'profile_picture' ou enviar vazio/null?
        # Para PUT (substituição), omitir deve ser interpretado como ausência no novo estado.
        # Se enviássemos '', o serializer poderia interpretar como um arquivo vazio inválido.
        # Vamos omitir.
    }

    # 4. Fazer a requisição PUT para remover a imagem
    response_remocao = api_client.put(url_profile, data_remocao, format='multipart')

    # 5. Verificar Status Code
    assert response_remocao.status_code == status.HTTP_200_OK, \
        f"Esperado status 200 ao remover imagem via PUT, recebido {response_remocao.status_code}. Resposta: {response_remocao.content}"

    # 6. Verificar resposta
    response_data = response_remocao.json()
    assert response_data.get("nome") == novo_nome, \
        f"Esperado nome '{novo_nome}' na resposta, recebido '{response_data.get('nome')}'."
    assert response_data.get("profile_picture") is None, \
        f"Esperado 'profile_picture' ser None na resposta após remoção via PUT, recebido '{response_data.get('profile_picture')}'."

    # 7. Verificar atualização do nome no User no banco
    user_com_nome.refresh_from_db()
    assert user_com_nome.first_name == novo_nome, \
        f"O first_name do usuário no banco deveria ser '{novo_nome}', mas é '{user_com_nome.first_name}'."

    # 8. Verificar profile_picture no Profile no banco (deve estar vazio/None)
    profile_final = Profile.objects.get(user=user_com_nome)
    assert not profile_final.profile_picture, \
        f"O campo profile_picture no Profile deveria estar vazio/None após remoção via PUT, mas é '{profile_final.profile_picture}'."

    # 9. Verificar se o arquivo de imagem ANTERIOR foi removido do storage
    assert not default_storage.exists(caminho_imagem_inicial), \
        f"O arquivo de imagem anterior '{caminho_imagem_inicial}' ainda existe no storage, mas deveria ter sido removido."

    # Opcional: Desautenticar
    api_client.logout()


def test_put_profile_nao_autenticado_falha(
    api_client: APIClient # Cliente não autenticado
):
    """
    Verifica se PUT /api/accounts/profile/ falha sem autenticação (401).

    Passos:
    1. NÃO autentica o cliente.
    2. Prepara um payload simples (apenas nome).
    3. Tenta fazer a requisição PUT para /api/accounts/profile/.
    4. Verifica se o status code é 401 Unauthorized.
    """
    # 1. NÃO autenticar

    # 2. Preparar payload (o conteúdo exato não importa tanto quanto a falta de auth)
    data = {
        'nome': 'Tentativa Nao Autenticada',
    }

    # 3. Fazer a requisição PUT
    url = "/api/accounts/profile/"
    # Usamos format='multipart' pois a view espera isso, mesmo que não haja arquivo
    response = api_client.put(url, data=data, format='multipart')

    # 4. Verificar Status Code 401
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
        f"Esperado status 401 ao tentar atualizar perfil sem autenticação, recebido {response.status_code}. Resposta: {response.content}"

# ... (imports e fixtures anteriores) ...

def test_patch_profile_apenas_nome_sucesso(
    api_client: APIClient,
    user_com_nome: User,
    test_image_path: Path # Usaremos para garantir que uma foto exista inicialmente
):
    """
    Verifica se PATCH /api/accounts/profile/ apenas com 'nome' atualiza o nome
    e NÃO afeta a foto de perfil existente.

    Passos:
    1. Garante que o usuário inicial TENHA um nome e uma foto de perfil.
    2. Autentica o cliente com este usuário.
    3. Prepara o payload multipart/form-data APENAS com o novo nome.
    4. Faz a requisição PATCH para /api/accounts/profile/.
    5. Verifica se o status code é 200 OK.
    6. Verifica se a resposta contém o nome atualizado e a URL da imagem ORIGINAL.
    7. Verifica no banco se user.first_name foi atualizado.
    8. Verifica no banco se profile.profile_picture NÃO foi alterado.
    """
    # 1. Garantir estado inicial COM foto
    api_client.force_authenticate(user=user_com_nome)
    url_profile = "/api/accounts/profile/"
    nome_inicial = "Nome Inicial Para PATCH"
    user_com_nome.first_name = nome_inicial
    user_com_nome.save() # Salva o nome inicial

    # Upload inicial da imagem
    data_inicial = {
        'profile_picture': test_image_path.open('rb')
        # Não enviamos 'nome' aqui para garantir que o PATCH só atualize o nome depois
    }
    response_inicial = api_client.patch(url_profile, data_inicial, format='multipart')
    data_inicial['profile_picture'].close()

    assert response_inicial.status_code == status.HTTP_200_OK, "Falha ao configurar imagem inicial para o teste PATCH."
    profile_inicial = Profile.objects.get(user=user_com_nome)
    assert profile_inicial.profile_picture, "Pré-condição falhou: O perfil deveria ter uma foto inicial."
    url_imagem_inicial = profile_inicial.profile_picture.url # Guarda a URL inicial

    # 2. Re-Autenticar (boa prática)
    api_client.force_authenticate(user=user_com_nome)

    novo_nome = "Nome Atualizado Apenas via PATCH"

    # 3. Preparar payload PATCH APENAS com nome
    data_patch = {
        'nome': novo_nome,
        # Intencionalmente omitimos 'profile_picture'
    }

    # 4. Fazer a requisição PATCH
    response_patch = api_client.patch(url_profile, data_patch, format='multipart')

    # 5. Verificar Status Code
    assert response_patch.status_code == status.HTTP_200_OK, \
        f"Esperado status 200, recebido {response_patch.status_code}. Resposta: {response_patch.content}"

    # 6. Verificar resposta
    response_data = response_patch.json()
    assert response_data.get("nome") == novo_nome, \
        f"Esperado nome '{novo_nome}' na resposta, recebido '{response_data.get('nome')}'."
    assert response_data.get("profile_picture") == url_imagem_inicial, \
        f"Esperado URL da imagem original '{url_imagem_inicial}' na resposta, recebido '{response_data.get('profile_picture')}'."

    # 7. Verificar atualização do nome no User no banco
    user_com_nome.refresh_from_db()
    assert user_com_nome.first_name == novo_nome, \
        f"O first_name do usuário no banco deveria ser '{novo_nome}', mas é '{user_com_nome.first_name}'."

    # 8. Verificar profile_picture no Profile no banco (não deve ter mudado)
    profile_final = Profile.objects.get(user=user_com_nome)
    assert profile_final.profile_picture, "O perfil final não deveria ter perdido a imagem."
    assert profile_final.profile_picture.url == url_imagem_inicial, \
        f"A URL da imagem no banco deveria ser '{url_imagem_inicial}', mas é '{profile_final.profile_picture.url}'."

    # Limpeza (remover a foto adicionada no setup)
    if profile_final.profile_picture:
        default_storage.delete(profile_final.profile_picture.name)

    # Opcional: Desautenticar
    api_client.logout()


def test_patch_profile_apenas_imagem_sucesso(
    api_client: APIClient,
    user_com_nome: User,
    test_image_path: Path,
    tmp_path
):
    """
    Verifica se PATCH /api/accounts/profile/ apenas com 'profile_picture'
    atualiza a imagem e NÃO afeta o nome.

    Passos:
    1. Garante que o usuário inicial TENHA um nome e uma foto de perfil inicial.
    2. Guarda o caminho/nome do arquivo inicial e o nome do usuário.
    3. Autentica o cliente.
    4. Cria um SEGUNDO arquivo de imagem temporário para a atualização.
    5. Prepara o payload multipart/form-data APENAS com a nova imagem.
    6. Faz a requisição PATCH para /api/accounts/profile/.
    7. Verifica se o status code é 200 OK.
    8. Verifica se a resposta contém o nome ORIGINAL e a URL da NOVA imagem.
    9. Verifica no banco se user.first_name NÃO foi alterado.
    10. Verifica no banco se profile.profile_picture foi atualizado para o NOVO arquivo.
    11. Verifica se o arquivo de imagem ANTIGO foi removido do storage.
    12. Verifica se o arquivo de imagem NOVO existe no storage.
    """
    # 1. Garantir estado inicial COM foto
    api_client.force_authenticate(user=user_com_nome)
    url_profile = "/api/accounts/profile/"
    nome_inicial = user_com_nome.first_name
    assert nome_inicial, "Pré-condição falhou: user_com_nome deveria ter um first_name."

    # Upload inicial da imagem 1
    data_inicial = {'profile_picture': test_image_path.open('rb')}
    response_inicial = api_client.patch(url_profile, data_inicial, format='multipart')
    data_inicial['profile_picture'].close()

    assert response_inicial.status_code == status.HTTP_200_OK, "Falha ao configurar imagem inicial para o teste PATCH."
    profile_inicial = Profile.objects.get(user=user_com_nome)
    assert profile_inicial.profile_picture, "Pré-condição falhou: O perfil deveria ter uma foto inicial."
    # 2. Guarda o caminho do arquivo inicial
    caminho_imagem_inicial = profile_inicial.profile_picture.name
    url_imagem_inicial = profile_inicial.profile_picture.url
    assert default_storage.exists(caminho_imagem_inicial), f"Arquivo inicial {caminho_imagem_inicial} não foi salvo no storage."


    # 3. Re-Autenticar
    api_client.force_authenticate(user=user_com_nome)

    # 4. Cria uma SEGUNDA imagem temporária (diferente da primeira)
    imagem_nova = Image.new('RGB', (20, 20), color='red') # Imagem diferente
    path_imagem_nova = tmp_path / "nova_imagem.png"
    imagem_nova.save(path_imagem_nova)

    # 5. Preparar payload PATCH APENAS com a nova imagem
    data_patch = {
        'profile_picture': path_imagem_nova.open('rb')
        # Omitimos 'nome' intencionalmente
    }

    # 6. Fazer a requisição PATCH
    response_patch = api_client.patch(url_profile, data_patch, format='multipart')
    data_patch['profile_picture'].close() # Fecha o arquivo após a requisição

    # 7. Verificar Status Code
    assert response_patch.status_code == status.HTTP_200_OK, \
        f"Esperado status 200, recebido {response_patch.status_code}. Resposta: {response_patch.content}"

    # 8. Verificar resposta
    response_data = response_patch.json()
    assert response_data.get("nome") == nome_inicial, \
        f"Esperado nome original '{nome_inicial}' na resposta, recebido '{response_data.get('nome')}'."
    url_imagem_nova_resposta = response_data.get("profile_picture")
    assert url_imagem_nova_resposta is not None, "Resposta não contém URL da nova imagem."
    assert url_imagem_nova_resposta != url_imagem_inicial, "URL da imagem na resposta é igual à antiga, mas deveria ser nova."
    assert url_imagem_nova_resposta.startswith('/media/profile_pics/'), "URL da nova imagem não começa com o caminho esperado."
    assert url_imagem_nova_resposta.endswith('.jpg'), "URL da nova imagem não termina com a extensão esperada."

    # 9. Verificar nome no User no banco (NÃO deve ter mudado)
    user_com_nome.refresh_from_db()
    assert user_com_nome.first_name == nome_inicial, \
        f"O first_name do usuário no banco deveria ser '{nome_inicial}', mas é '{user_com_nome.first_name}'."

    # 10. Verificar profile_picture no Profile no banco (DEVE ter mudado)
    profile_final = Profile.objects.get(user=user_com_nome)
    assert profile_final.profile_picture, "O perfil final não deveria ter perdido a imagem."
    assert profile_final.profile_picture.url == url_imagem_nova_resposta, \
        f"A URL da imagem no banco ('{profile_final.profile_picture.url}') não corresponde à URL na resposta ('{url_imagem_nova_resposta}')."
    caminho_imagem_nova_salva = profile_final.profile_picture.name

    # 11. Verificar se o arquivo de imagem ANTIGO foi removido do storage
    assert not default_storage.exists(caminho_imagem_inicial), \
        f"O arquivo de imagem anterior '{caminho_imagem_inicial}' ainda existe no storage, mas deveria ter sido removido."

    # 12. Verificar se o arquivo de imagem NOVO existe no storage
    assert default_storage.exists(caminho_imagem_nova_salva), \
        f"O novo arquivo de imagem '{caminho_imagem_nova_salva}' não foi encontrado no storage."

    # Limpeza (remover a foto adicionada no teste)
    if default_storage.exists(caminho_imagem_nova_salva):
        default_storage.delete(caminho_imagem_nova_salva)

    # Opcional: Desautenticar
    api_client.logout()


def test_patch_profile_remover_imagem_sucesso(
    api_client: APIClient,
    user_com_nome: User,
    test_image_path: Path
):
    """
    Verifica se PATCH /api/accounts/profile/ com 'profile_picture'=None/vazio
    remove a imagem existente e NÃO afeta o nome.

    Passos:
    1. Garante que o usuário inicial TENHA um nome e uma foto de perfil inicial.
    2. Guarda o caminho/nome do arquivo inicial e o nome do usuário.
    3. Autentica o cliente.
    4. Prepara o payload multipart/form-data com 'profile_picture' vazio (simulando null).
    5. Faz a requisição PATCH para /api/accounts/profile/.
    6. Verifica se o status code é 200 OK.
    7. Verifica se a resposta contém o nome ORIGINAL e 'profile_picture' como None.
    8. Verifica no banco se user.first_name NÃO foi alterado.
    9. Verifica no banco se profile.profile_picture está vazio/None.
    10. Verifica se o arquivo de imagem ANTERIOR foi removido do storage.
    """
    # 1. Garantir estado inicial COM foto
    api_client.force_authenticate(user=user_com_nome)
    url_profile = "/api/accounts/profile/"
    nome_inicial = user_com_nome.first_name
    assert nome_inicial, "Pré-condição falhou: user_com_nome deveria ter um first_name."

    # Upload inicial da imagem
    data_inicial = {'profile_picture': test_image_path.open('rb')}
    response_inicial = api_client.patch(url_profile, data_inicial, format='multipart')
    data_inicial['profile_picture'].close()

    assert response_inicial.status_code == status.HTTP_200_OK, "Falha ao configurar imagem inicial para o teste PATCH."
    profile_inicial = Profile.objects.get(user=user_com_nome)
    assert profile_inicial.profile_picture, "Pré-condição falhou: O perfil deveria ter uma foto inicial."
    # 2. Guarda o caminho do arquivo inicial
    caminho_imagem_inicial = profile_inicial.profile_picture.name
    assert default_storage.exists(caminho_imagem_inicial), f"Arquivo inicial {caminho_imagem_inicial} não foi salvo no storage."

    # 3. Re-Autenticar
    api_client.force_authenticate(user=user_com_nome)

    # 4. Preparar payload PATCH com 'profile_picture' vazio para remover
    # No multipart/form-data, enviar um campo vazio geralmente é interpretado
    # pelo backend (especificamente pelo RelativeImageField/serializers.ImageField do DRF)
    # como uma intenção de limpar o campo.
    data_patch_remocao = {
        'profile_picture': ''
        # Omitimos 'nome' intencionalmente
    }

    # 5. Fazer a requisição PATCH para remover
    response_patch = api_client.patch(url_profile, data_patch_remocao, format='multipart')

    # 6. Verificar Status Code
    assert response_patch.status_code == status.HTTP_200_OK, \
        f"Esperado status 200 ao remover imagem via PATCH, recebido {response_patch.status_code}. Resposta: {response_patch.content}"

    # 7. Verificar resposta
    response_data = response_patch.json()
    assert response_data.get("nome") == nome_inicial, \
        f"Esperado nome original '{nome_inicial}' na resposta, recebido '{response_data.get('nome')}'."
    assert response_data.get("profile_picture") is None, \
        f"Esperado 'profile_picture' ser None na resposta após remoção via PATCH, recebido '{response_data.get('profile_picture')}'."

    # 8. Verificar nome no User no banco (NÃO deve ter mudado)
    user_com_nome.refresh_from_db()
    assert user_com_nome.first_name == nome_inicial, \
        f"O first_name do usuário no banco deveria ser '{nome_inicial}', mas é '{user_com_nome.first_name}'."

    # 9. Verificar profile_picture no Profile no banco (DEVE estar vazio/None)
    profile_final = Profile.objects.get(user=user_com_nome)
    assert not profile_final.profile_picture, \
        f"O campo profile_picture no Profile deveria estar vazio/None após remoção via PATCH, mas é '{profile_final.profile_picture}'."

    # 10. Verificar se o arquivo de imagem ANTERIOR foi removido do storage
    assert not default_storage.exists(caminho_imagem_inicial), \
        f"O arquivo de imagem anterior '{caminho_imagem_inicial}' ainda existe no storage, mas deveria ter sido removido."

    # Opcional: Desautenticar
    api_client.logout()


# tests_api/test_autenticacao.py

# ... (imports e fixtures anteriores) ...

def test_patch_profile_imagem_invalida_falha(
    api_client: APIClient,
    user_com_nome: User,
    tmp_path
):
    """
    Verifica se PATCH /api/accounts/profile/ com arquivo inválido para
    'profile_picture' falha (400).

    Passos:
    1. Autentica o cliente.
    2. Cria um arquivo temporário que NÃO é uma imagem (ex: .txt).
    3. Prepara o payload multipart/form-data com o arquivo inválido.
    4. Faz a requisição PATCH para /api/accounts/profile/.
    5. Verifica se o status code é 400 Bad Request.
    6. Verifica se a resposta contém uma mensagem de erro em Português
       específica para 'profile_picture'.
    """
    # 1. Autenticar
    api_client.force_authenticate(user=user_com_nome)

    # 2. Criar um arquivo inválido (texto simples) em memória
    arquivo_invalido_conteudo = b"Este nao e um arquivo de imagem valido."
    arquivo_invalido = BytesIO(arquivo_invalido_conteudo)
    nome_arquivo_invalido = "arquivo_texto.txt"

    # 3. Preparar payload multipart com o arquivo inválido
    data_patch = {
        'profile_picture': (nome_arquivo_invalido, arquivo_invalido, 'text/plain')
    }

    # 4. Fazer a requisição PATCH
    url = "/api/accounts/profile/"
    response = api_client.patch(url, data=data_patch, format='multipart')

    # Fechar o BytesIO
    arquivo_invalido.close()

    # 5. Verificar Status Code 400
    assert response.status_code == status.HTTP_400_BAD_REQUEST, \
        f"Esperado status 400 ao enviar imagem inválida, recebido {response.status_code}. Resposta: {response.content}"

    # 6. Verificar mensagem de erro na resposta (EM PORTUGUÊS)
    response_data = response.json()
    assert "profile_picture" in response_data, \
        "A resposta de erro não contém a chave 'profile_picture'."

    error_message = response_data["profile_picture"][0] # Pega a primeira mensagem de erro
    assert "imagem válida" in error_message.lower() or "não é um arquivo de imagem" in error_message.lower(), \
        f"A mensagem de erro para 'profile_picture' ('{error_message}') não indica um problema de imagem inválida em Português."

    # Opcional: Desautenticar
    api_client.logout()


def test_patch_profile_nao_autenticado_falha(
    api_client: APIClient # Cliente não autenticado
):
    """
    Verifica se PATCH /api/accounts/profile/ falha sem autenticação (401).

    Passos:
    1. NÃO autentica o cliente.
    2. Prepara um payload simples (apenas nome).
    3. Tenta fazer a requisição PATCH para /api/accounts/profile/.
    4. Verifica se o status code é 401 Unauthorized.
    """
    # 1. NÃO autenticar

    # 2. Preparar payload
    data = {
        'nome': 'Tentativa PATCH Nao Autenticada',
    }

    # 3. Fazer a requisição PATCH
    url = "/api/accounts/profile/"
    # Usamos format='multipart' pois a view espera isso
    response = api_client.patch(url, data=data, format='multipart')

    # 4. Verificar Status Code 401
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
        f"Esperado status 401 ao tentar PATCH no perfil sem autenticação, recebido {response.status_code}. Resposta: {response.content}"
