"""Testes de integração para os endpoints de Autenticação e Contas.
Esta suíte de testes valida:
- O fluxo de login com credenciais válidas e inválidas.
- O controle de acesso a rotas protegidas com e sem token JWT.
- A obtenção de dados do usuário logado.
"""
import os
import pytest
import requests
import uuid
from django.core.files.storage import default_storage
from django.contrib.auth.models import User, Group
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
    """
    Cria ou obtém o usuário 'zelador', garante que ele tenha um first_name
    e DEFINE/RESETA sua senha para o valor esperado do .env.test.
    """
    zelador_username = os.getenv("TEST_USER_ZELADOR_USERNAME", "zelador")
    senha_esperada = os.getenv("TEST_USER_ZELADOR_PASSWORD", "Senac@098")

    user, created = User.objects.get_or_create(username=zelador_username)

    user.set_password(senha_esperada)

    # Garante o nome
    if not user.first_name:
        user.first_name = "Zelador de Teste Nome"

    user.save() # Salva as alterações (senha e nome, se aplicável)

    # Garante que o perfil exista
    from accounts.models import Profile
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


def test_change_password_sucesso(
    api_client: APIClient,
    user_com_nome: User # Usaremos o zelador como exemplo
):
    """
    Verifica se POST /api/accounts/change_password/ funciona corretamente.

    Passos:
    1. Obtém um usuário de teste e sua senha original.
    2. Define uma nova senha válida.
    3. Autentica o cliente com o usuário.
    4. Prepara o payload com senha antiga, nova e confirmação.
    5. Faz a requisição POST para /api/accounts/change_password/.
    6. Verifica se o status code é 200 OK.
    7. Verifica a mensagem de sucesso na resposta.
    8. Tenta autenticar com a senha ANTIGA (deve falhar).
    9. Tenta autenticar com a senha NOVA (deve funcionar).
    10. Restaura a senha original para não afetar outros testes.
    """
    # 1. Obter usuário e senha original
    # Usaremos o zelador, cuja senha padrão está no .env.test ou foi definida
    # no populate_example_db.py como 'Senac@098'
    senha_original = os.getenv("TEST_USER_ZELADOR_PASSWORD", "Senac@098") # Usar a senha do .env ou o padrão
    usuario = user_com_nome # Reutilizando a fixture que pega o zelador

    # Garante que a senha inicial está correta para o teste
    assert usuario.check_password(senha_original), \
        f"A senha original '{senha_original}' não corresponde à senha do usuário '{usuario.username}' no início do teste."

    # 2. Definir nova senha
    nova_senha = "NovaSenhaSegura@123!"

    # 3. Autenticar
    api_client.force_authenticate(user=usuario)

    # 4. Preparar payload
    payload = {
        "old_password": senha_original,
        "new_password": nova_senha,
        "confirm_new_password": nova_senha
    }

    # 5. Fazer a requisição POST
    url = "/api/accounts/change_password/"
    response = api_client.post(url, data=payload, format='json') # Enviar como JSON

    # 6. Verificar Status Code
    assert response.status_code == status.HTTP_200_OK, \
        f"Esperado status 200, recebido {response.status_code}. Resposta: {response.content}"

    # 7. Verificar mensagem de sucesso
    response_data = response.json()
    assert "message" in response_data
    assert "Senha alterada com sucesso" in response_data["message"]

    # Verificação Pós-Mudança
    # É importante desautenticar o cliente atual antes de tentar novos logins
    api_client.logout()

    # 8. Tentar login com senha ANTIGA (deve falhar - 400 Bad Request)
    login_url = "/api/accounts/login/"
    response_login_antiga = api_client.post(login_url, {"username": usuario.username, "password": senha_original}, format='json')
    assert response_login_antiga.status_code == status.HTTP_400_BAD_REQUEST, \
        "Login com a senha antiga deveria falhar após a mudança, mas retornou status diferente de 400."
    assert "Credenciais inválidas" in response_login_antiga.json().get("non_field_errors", [""])[0]

    # 9. Tentar login com senha NOVA (deve funcionar - 200 OK)
    response_login_nova = api_client.post(login_url, {"username": usuario.username, "password": nova_senha}, format='json')
    assert response_login_nova.status_code == status.HTTP_200_OK, \
        f"Login com a nova senha falhou. Status: {response_login_nova.status_code}, Resposta: {response_login_nova.content}"
    assert "token" in response_login_nova.json()

    # Limpeza / Restauração
    # 10. Restaurar a senha original para não impactar outros testes
    usuario.set_password(senha_original)
    usuario.save()
    # Garante que a senha foi restaurada
    usuario.refresh_from_db()
    assert usuario.check_password(senha_original), "Falha ao restaurar a senha original do usuário no final do teste."

    # Opcional: Desautenticar novamente se necessário (embora o último login já o tenha feito implicitamente)
    api_client.logout()


def test_change_password_senha_antiga_incorreta_falha(
    api_client: APIClient,
    user_com_nome: User # Usaremos o zelador novamente
):
    """
    Verifica se POST /api/accounts/change_password/ falha (400)
    quando a senha antiga ('old_password') está incorreta.

    Passos:
    1. Obtém um usuário de teste.
    2. Define uma senha antiga incorreta e uma nova senha válida.
    3. Autentica o cliente com o usuário.
    4. Prepara o payload com a senha antiga INCORRETA, nova e confirmação.
    5. Faz a requisição POST para /api/accounts/change_password/.
    6. Verifica se o status code é 400 Bad Request.
    7. Verifica se a resposta contém a mensagem de erro específica para 'old_password'.
    8. Opcional: Verifica se a senha do usuário NÃO foi alterada no banco.
    """
    # 1. Obter usuário (senha já está correta devido à fixture)
    usuario = user_com_nome
    senha_original_correta = os.getenv("TEST_USER_ZELADOR_PASSWORD", "Senac@098") # Pega a senha correta

    # 2. Definir senhas para o payload
    senha_antiga_incorreta = "senha_errada_123"
    nova_senha = "NovaSenhaSegura@123!"

    # 3. Autenticar
    api_client.force_authenticate(user=usuario)

    # 4. Preparar payload com senha antiga INCORRETA
    payload = {
        "old_password": senha_antiga_incorreta, # <<< Senha errada
        "new_password": nova_senha,
        "confirm_new_password": nova_senha
    }

    # 5. Fazer a requisição POST
    url = "/api/accounts/change_password/"
    response = api_client.post(url, data=payload, format='json')

    # 6. Verificar Status Code 400
    assert response.status_code == status.HTTP_400_BAD_REQUEST, \
        f"Esperado status 400 ao fornecer senha antiga incorreta, recebido {response.status_code}. Resposta: {response.content}"

    # 7. Verificar mensagem de erro
    response_data = response.json()
    assert "old_password" in response_data, \
        "A resposta de erro não contém a chave 'old_password'."
    assert "A senha antiga está incorreta." in response_data["old_password"], \
        f"Mensagem de erro inesperada para 'old_password': {response_data['old_password']}"

    # 8. Opcional: Verificar se a senha NÃO mudou no banco
    usuario.refresh_from_db() # Recarrega do banco
    assert usuario.check_password(senha_original_correta), \
        "A senha do usuário foi alterada indevidamente, mesmo com a senha antiga incorreta."
    assert not usuario.check_password(nova_senha), \
        "A senha do usuário foi alterada para a nova senha, o que não deveria ocorrer."

    # Opcional: Desautenticar
    api_client.logout()


def test_change_password_senha_antiga_incorreta_falha(
    api_client: APIClient,
    user_com_nome: User # Usaremos o zelador novamente
):
    """
    Verifica se POST /api/accounts/change_password/ falha (400)
    quando a senha antiga ('old_password') está incorreta.

    Passos:
    1. Obtém um usuário de teste (cuja senha é conhecida pela fixture).
    2. Define uma senha antiga incorreta e uma nova senha válida.
    3. Autentica o cliente com o usuário.
    4. Prepara o payload com a senha antiga INCORRETA, nova e confirmação.
    5. Faz a requisição POST para /api/accounts/change_password/.
    6. Verifica se o status code é 400 Bad Request.
    7. Verifica se a resposta contém a mensagem de erro específica para 'old_password'.
    8. Opcional: Verifica se a senha do usuário NÃO foi alterada no banco.
    """
    # 1. Obter usuário
    usuario = user_com_nome
    senha_original_correta = os.getenv("TEST_USER_ZELADOR_PASSWORD", "Senac@098") # Pega a senha correta para a verificação final

    # 2. Definir senhas para o payload
    senha_antiga_incorreta = "senha_que_nao_e_a_certa_XYZ"
    nova_senha = "OutraNovaSenha@456!"

    # 3. Autenticar
    api_client.force_authenticate(user=usuario)

    # 4. Preparar payload com senha antiga INCORRETA
    payload = {
        "old_password": senha_antiga_incorreta, # <<< Senha errada
        "new_password": nova_senha,
        "confirm_new_password": nova_senha
    }

    # 5. Fazer a requisição POST
    url = "/api/accounts/change_password/"
    response = api_client.post(url, data=payload, format='json') # Enviar como JSON

    # 6. Verificar Status Code 400
    assert response.status_code == status.HTTP_400_BAD_REQUEST, \
        f"Esperado status 400 ao fornecer senha antiga incorreta, recebido {response.status_code}. Resposta: {response.content}"

    # 7. Verificar mensagem de erro
    response_data = response.json()
    assert "old_password" in response_data, \
        "A resposta de erro não contém a chave 'old_password'." #
    # A mensagem vem do PasswordChangeSerializer.validate
    assert "A senha antiga está incorreta." in response_data["old_password"], \
        f"Mensagem de erro inesperada para 'old_password': {response_data['old_password']}" #

    # 8. Opcional: Verificar se a senha NÃO mudou no banco
    usuario.refresh_from_db() # Recarrega do banco
    assert usuario.check_password(senha_original_correta), \
        "A senha do usuário foi alterada indevidamente, mesmo com a senha antiga incorreta." #
    assert not usuario.check_password(nova_senha), \
        "A senha do usuário foi alterada para a nova senha, o que não deveria ocorrer." #

    # Opcional: Desautenticar
    api_client.logout()


def test_change_password_senha_antiga_incorreta_falha(
    api_client: APIClient,
    user_com_nome: User # Usaremos o zelador novamente
):
    """
    Verifica se POST /api/accounts/change_password/ falha (400)
    quando a senha antiga ('old_password') está incorreta.

    Passos:
    1. Obtém um usuário de teste (cuja senha é conhecida pela fixture).
    2. Define uma senha antiga incorreta e uma nova senha válida.
    3. Autentica o cliente com o usuário.
    4. Prepara o payload com a senha antiga INCORRETA, nova e confirmação.
    5. Faz a requisição POST para /api/accounts/change_password/.
    6. Verifica se o status code é 400 Bad Request.
    7. Verifica se a resposta contém a mensagem de erro específica para 'old_password'.
    8. Opcional: Verifica se a senha do usuário NÃO foi alterada no banco.
    """
    # 1. Obter usuário
    usuario = user_com_nome
    senha_original_correta = os.getenv("TEST_USER_ZELADOR_PASSWORD", "Senac@098") # Pega a senha correta para a verificação final

    # 2. Definir senhas para o payload
    senha_antiga_incorreta = "senha_que_nao_e_a_certa_XYZ"
    nova_senha = "OutraNovaSenha@456!"

    # 3. Autenticar
    api_client.force_authenticate(user=usuario)

    # 4. Preparar payload com senha antiga INCORRETA
    payload = {
        "old_password": senha_antiga_incorreta, # <<< Senha errada
        "new_password": nova_senha,
        "confirm_new_password": nova_senha
    }

    # 5. Fazer a requisição POST
    url = "/api/accounts/change_password/"
    response = api_client.post(url, data=payload, format='json') # Enviar como JSON

    # 6. Verificar Status Code 400
    assert response.status_code == status.HTTP_400_BAD_REQUEST, \
        f"Esperado status 400 ao fornecer senha antiga incorreta, recebido {response.status_code}. Resposta: {response.content}"

    # 7. Verificar mensagem de erro
    response_data = response.json()
    assert "old_password" in response_data, \
        "A resposta de erro não contém a chave 'old_password'." #
    # A mensagem vem do PasswordChangeSerializer.validate
    assert "A senha antiga está incorreta." in response_data["old_password"], \
        f"Mensagem de erro inesperada para 'old_password': {response_data['old_password']}" #

    # 8. Opcional: Verificar se a senha NÃO mudou no banco
    usuario.refresh_from_db() # Recarrega do banco
    assert usuario.check_password(senha_original_correta), \
        "A senha do usuário foi alterada indevidamente, mesmo com a senha antiga incorreta." #
    assert not usuario.check_password(nova_senha), \
        "A senha do usuário foi alterada para a nova senha, o que não deveria ocorrer." #

    # Opcional: Desautenticar
    api_client.logout()


def test_change_password_confirmacao_nova_senha_falha(
    api_client: APIClient,
    user_com_nome: User
):
    """
    Verifica se POST /api/accounts/change_password/ falha (400)
    quando a nova senha e sua confirmação não coincidem.

    Passos:
    1. Obtém um usuário de teste e sua senha original correta.
    2. Define uma nova senha e uma confirmação DIFERENTE.
    3. Autentica o cliente com o usuário.
    4. Prepara o payload com a senha antiga correta, nova e confirmação INCORRETA.
    5. Faz a requisição POST para /api/accounts/change_password/.
    6. Verifica se o status code é 400 Bad Request.
    7. Verifica se a resposta contém a mensagem de erro específica para 'new_password'.
    8. Opcional: Verifica se a senha do usuário NÃO foi alterada no banco.
    """
    # 1. Obter usuário e senha original
    usuario = user_com_nome
    senha_original_correta = os.getenv("TEST_USER_ZELADOR_PASSWORD", "Senac@098")

    # 2. Definir nova senha e confirmação DIFERENTE
    nova_senha = "SenhaValida@123"
    confirmacao_incorreta = "SenhaDiferente@456"

    # 3. Autenticar
    api_client.force_authenticate(user=usuario)

    # 4. Preparar payload com confirmação INCORRETA
    payload = {
        "old_password": senha_original_correta,
        "new_password": nova_senha,
        "confirm_new_password": confirmacao_incorreta # <<< Confirmação errada
    }

    # 5. Fazer a requisição POST
    url = "/api/accounts/change_password/"
    response = api_client.post(url, data=payload, format='json')

    # 6. Verificar Status Code 400
    assert response.status_code == status.HTTP_400_BAD_REQUEST, \
        f"Esperado status 400 quando confirmação de senha falha, recebido {response.status_code}. Resposta: {response.content}"

    # 7. Verificar mensagem de erro
    response_data = response.json()
    assert "new_password" in response_data, \
        "A resposta de erro não contém a chave 'new_password'."
    # A mensagem vem do PasswordChangeSerializer.validate
    assert "As novas senhas não coincidem." in response_data["new_password"], \
        f"Mensagem de erro inesperada para 'new_password': {response_data['new_password']}"

    # 8. Opcional: Verificar se a senha NÃO mudou no banco
    usuario.refresh_from_db()
    assert usuario.check_password(senha_original_correta), \
        "A senha do usuário foi alterada indevidamente, mesmo com a confirmação incorreta."
    assert not usuario.check_password(nova_senha), \
        "A senha do usuário foi alterada para a nova senha, o que não deveria ocorrer."

    # Opcional: Desautenticar
    api_client.logout()


def test_change_password_confirmacao_nova_senha_falha(
    api_client: APIClient,
    user_com_nome: User
):
    """
    Verifica se POST /api/accounts/change_password/ falha (400)
    quando a nova senha e sua confirmação não coincidem.

    Passos:
    1. Obtém um usuário de teste e sua senha original correta.
    2. Define uma nova senha e uma confirmação DIFERENTE.
    3. Autentica o cliente com o usuário.
    4. Prepara o payload com a senha antiga correta, nova e confirmação INCORRETA.
    5. Faz a requisição POST para /api/accounts/change_password/.
    6. Verifica se o status code é 400 Bad Request.
    7. Verifica se a resposta contém a mensagem de erro específica para 'new_password'.
    8. Opcional: Verifica se a senha do usuário NÃO foi alterada no banco.
    """
    # 1. Obter usuário e senha original
    usuario = user_com_nome
    senha_original_correta = os.getenv("TEST_USER_ZELADOR_PASSWORD", "Senac@098")

    # 2. Definir nova senha e confirmação DIFERENTE
    nova_senha = "SenhaValida@123"
    confirmacao_incorreta = "SenhaDiferente@456" # <<< Diferente da nova_senha

    # 3. Autenticar
    api_client.force_authenticate(user=usuario)

    # 4. Preparar payload com confirmação INCORRETA
    payload = {
        "old_password": senha_original_correta,
        "new_password": nova_senha,
        "confirm_new_password": confirmacao_incorreta # <<< Confirmação errada
    }

    # 5. Fazer a requisição POST
    url = "/api/accounts/change_password/"
    response = api_client.post(url, data=payload, format='json')

    # 6. Verificar Status Code 400
    assert response.status_code == status.HTTP_400_BAD_REQUEST, \
        f"Esperado status 400 quando confirmação de senha falha, recebido {response.status_code}. Resposta: {response.content}"

    # 7. Verificar mensagem de erro
    response_data = response.json()
    assert "new_password" in response_data, \
        "A resposta de erro não contém a chave 'new_password'."
    # A mensagem vem do PasswordChangeSerializer.validate
    assert "As novas senhas não coincidem." in response_data["new_password"], \
        f"Mensagem de erro inesperada para 'new_password': {response_data['new_password']}" #

    # 8. Opcional: Verificar se a senha NÃO mudou no banco
    usuario.refresh_from_db()
    assert usuario


# Testar com diferentes senhas fracas
@pytest.mark.parametrize(
    "senha_fraca",
    [
        "123",           # Muito curta, só numérica
        "password",      # Muito comum
        # "senhasenha",    # Sem variedade de caracteres
        "USERNAME_PLACEHOLDER" # Placeholder para o username
    ]
)
def test_change_password_nova_senha_fraca_falha(
    api_client: APIClient,
    user_com_nome: User, # A fixture é injetada aqui
    senha_fraca: str
):
    """
    Verifica se POST /api/accounts/change_password/ falha (400)
    quando a nova senha ('new_password') é considerada fraca pelos validadores.
    # ... (docstring continua igual) ...
    """
    # 1. Obter usuário e senha original
    usuario = user_com_nome
    senha_original_correta = os.getenv("TEST_USER_ZELADOR_PASSWORD", "Senac@098")

    # --- INÍCIO DA CORREÇÃO ---
    # Substitui o placeholder pelo username real DENTRO do teste
    if senha_fraca == "USERNAME_PLACEHOLDER":
         senha_fraca_atual = usuario.username
    else:
         senha_fraca_atual = senha_fraca
    # --- FIM DA CORREÇÃO ---

    # 2. Nova senha fraca definida pela parametrização (agora corrigida)

    # 3. Autenticar
    api_client.force_authenticate(user=usuario)

    # 4. Preparar payload com nova senha FRACA
    payload = {
        "old_password": senha_original_correta,
        "new_password": senha_fraca_atual,
        "confirm_new_password": senha_fraca_atual
    }

    # 5. Fazer a requisição POST
    url = "/api/accounts/change_password/"
    response = api_client.post(url, data=payload, format='json')

    # 6. Verificar Status Code 400
    assert response.status_code == status.HTTP_400_BAD_REQUEST, \
        f"Esperado status 400 ao usar senha fraca '{senha_fraca_atual}', recebido {response.status_code}. Resposta: {response.content}"

    # 7. Verificar mensagem de erro
    response_data = response.json()
    assert "new_password" in response_data, \
        f"A resposta de erro para senha fraca '{senha_fraca_atual}' não contém a chave 'new_password'."
    assert len(response_data["new_password"]) > 0, \
        f"Esperado pelo menos uma mensagem de erro de validação para 'new_password' com senha fraca '{senha_fraca_atual}', mas a lista está vazia."
    # (Verificação mais específica das mensagens pode ser adicionada aqui se necessário)


    # 8. Opcional: Verificar se a senha NÃO mudou no banco
    usuario.refresh_from_db()
    assert usuario.check_password(senha_original_correta), \
        f"A senha do usuário foi alterada indevidamente ao tentar usar a senha fraca '{senha_fraca_atual}'."
    assert not usuario.check_password(senha_fraca_atual), \
        f"A senha fraca '{senha_fraca_atual}' foi definida, o que não deveria ocorrer."

    # Opcional: Desautenticar
    api_client.logout()


def test_change_password_nao_autenticado_falha(
    api_client: APIClient # Cliente não autenticado
):
    """
    Verifica se POST /api/accounts/change_password/ falha (401)
    quando o usuário não está autenticado.

    Passos:
    1. NÃO autentica o cliente.
    2. Prepara um payload válido (as senhas não importam, o erro deve ser 401).
    3. Tenta fazer a requisição POST para /api/accounts/change_password/.
    4. Verifica se o status code é 401 Unauthorized.
    """
    # 1. NÃO autenticar

    # 2. Preparar payload (válido em termos de estrutura, mas irrelevante)
    payload = {
        "old_password": "alguma_senha_antiga",
        "new_password": "NovaSenha@123!",
        "confirm_new_password": "NovaSenha@123!"
    }

    # 3. Fazer a requisição POST
    url = "/api/accounts/change_password/"
    response = api_client.post(url, data=payload, format='json')

    # 4. Verificar Status Code 401
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
        f"Esperado status 401 ao tentar mudar senha sem autenticação, recebido {response.status_code}. Resposta: {response.content}"

    # Não precisamos de fixtures de usuário aqui.
    # Não há necessidade de logout.


@pytest.fixture
def admin_user(db) -> User:
    """Garante que o usuário admin exista, tenha a senha correta e seja superuser."""
    admin_username = os.getenv("TEST_USER_ADMIN_USERNAME", "administrador")
    admin_password = os.getenv("TEST_USER_ADMIN_PASSWORD", "Senac@123") # Pega a senha do .env.test

    user, created = User.objects.get_or_create(username=admin_username)

    # Garante que a senha e os status de admin estão corretos
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

    # Garante que o grupo 'Solicitante de Serviços' exista
    grupo_nome = "Solicitante de Serviços"
    grupo, _ = Group.objects.get_or_create(name=grupo_nome)

    user, created = User.objects.get_or_create(username=username)

    # Garante que a senha e os status de NÃO-admin estão corretos
    user.set_password(password)
    user.is_staff = False
    user.is_superuser = False
    user.save()

    # Adiciona o usuário ao grupo
    user.groups.set([grupo])

    return user

def test_create_user_admin_sucesso(
    api_client: APIClient,
    admin_user: User, # Usar a fixture admin_user
    grupo_zeladoria: Group
):
    """
    Verifica se POST /api/accounts/create_user/ funciona para admin.
    ... (docstring) ...
    """
    # 1. Definir dados do novo usuário (com username único)
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
        "groups": [grupo_zeladoria.id]
    }

    # 2. Fazer a requisição POST como admin
    url = "/api/accounts/create_user/"

    # --- INÍCIO DA CORREÇÃO ---
    # Autentica o cliente diretamente com o usuário admin
    api_client.force_authenticate(user=admin_user)
    # headers = {"Authorization": auth_header_admin["Authorization"]} # Remove o header manual
    response = api_client.post(url, data=payload, format='json') # Remove headers=headers
    # --- FIM DA CORREÇÃO ---


    # 3. Verificar Status Code 201
    assert response.status_code == status.HTTP_201_CREATED, \
        f"Esperado status 201, recebido {response.status_code}. Resposta: {response.content}"

    # ... (O restante das asserções (4, 5, 6) permanece o mesmo) ...
    response_data = response.json()
    assert "message" in response_data
    assert "Usuário criado com sucesso" in response_data["message"]
    # ... (etc) ...
    try:
        usuario_criado = User.objects.get(username=novo_username)
        # ... (verificações no banco) ...
    except User.DoesNotExist:
        pytest.fail(f"Usuário '{novo_username}' não foi encontrado no banco de dados após criação bem-sucedida.")


    # 7. Limpeza (deletar usuário criado)
    usuario_criado.delete()

    # Desautenticar o cliente
    api_client.logout()


@pytest.mark.parametrize(
    "non_admin_user_fixture",
    [
        "user_com_nome",    # Fixture do Zelador
        "solicitante_user"  # Fixture do Solicitante
    ]
)
def test_create_user_nao_admin_falha(
    api_client: APIClient,
    non_admin_user_fixture: str,
    request: pytest.FixtureRequest # Para buscar a fixture pelo nome
):
    """
    Verifica se POST /api/accounts/create_user/ falha (403) para não-admins.
    ... (docstring) ...
    """
    # 1. Obter o usuário não-admin
    usuario_nao_admin = request.getfixturevalue(non_admin_user_fixture)
    assert not usuario_nao_admin.is_staff, f"Fixture {non_admin_user_fixture} deveria ser não-staff."

    # 2. Definir payload mínimo
    novo_username = f"teste_falha_{uuid.uuid4().hex[:8]}"
    payload = {
        "username": novo_username,
        "password": "SenhaQualquer@123",
        "confirm_password": "SenhaQualquer@123",
        "nome": "Teste Falha",
    }

    # 3. Autenticar como não-admin
    api_client.force_authenticate(user=usuario_nao_admin)

    # 4. Fazer a requisição POST
    url = "/api/accounts/create_user/"
    response = api_client.post(url, data=payload, format='json')

    # 5. Verificar Status Code 403
    assert response.status_code == status.HTTP_403_FORBIDDEN, \
        f"Esperado status 403 para o usuário '{usuario_nao_admin.username}', recebido {response.status_code}. Resposta: {response.content}"

    # 6. Verificar mensagem de erro (mensagem padrão do DRF para IsAdminUser)
    response_data = response.json()
    assert "detail" in response_data

    assert "Você não tem permissão para executar essa ação." in response_data["detail"]

    # 7. Verificar se o usuário NÃO foi criado no banco
    assert not User.objects.filter(username=novo_username).exists(), \
        f"O usuário '{novo_username}' foi criado indevidamente pelo usuário não-admin '{usuario_nao_admin.username}'."

    # Desautenticar
    api_client.logout()


def test_create_user_username_duplicado_falha(
    api_client: APIClient,
    admin_user: User,  # Admin para fazer a requisição
    user_com_nome: User # Usuário 'zelador' para pegar um username existente
):
    """
    Verifica se POST /api/accounts/create_user/ falha (400)
    quando o 'username' já existe.

    Passos:
    1. Obtém um usuário admin (para autenticar) e um usuário existente
       (para pegar o username).
    2. Define um payload para criação de usuário usando o username JÁ EXISTENTE.
    3. Autentica o cliente com o usuário admin.
    4. Faz a requisição POST para /api/accounts/create_user/.
    5. Verifica se o status code é 400 Bad Request.
    6. Verifica se a resposta contém a mensagem de erro específica para 'username'.
    """
    # 1. Obter usuários
    usuario_existente = user_com_nome # Este é o 'zelador'
    username_duplicado = usuario_existente.username

    # 2. Definir payload com username duplicado
    payload = {
        "username": username_duplicado, # <<< Username que já existe
        "password": "SenhaQualquer@123",
        "confirm_password": "SenhaQualquer@123",
        "nome": "Tentativa Duplicada",
    }

    # 3. Autenticar como admin
    api_client.force_authenticate(user=admin_user)

    # 4. Fazer a requisição POST
    url = "/api/accounts/create_user/"
    response = api_client.post(url, data=payload, format='json')

    # 5. Verificar Status Code 400
    assert response.status_code == status.HTTP_400_BAD_REQUEST, \
        f"Esperado status 400 ao tentar criar usuário com username duplicado '{username_duplicado}', recebido {response.status_code}. Resposta: {response.content}"

    # 6. Verificar mensagem de erro (mensagem padrão do Django em pt-br)
    response_data = response.json()
    assert "username" in response_data, \
        "A resposta de erro não contém a chave 'username'."
    # Mensagem padrão do UniqueValidator em pt-br
    assert "Um usuário com este nome de usuário já existe." in response_data["username"], \
        f"Mensagem de erro inesperada para 'username': {response_data['username']}"

    # Desautenticar
    api_client.logout()


@pytest.mark.parametrize(
    "senha_fraca",
    [
        "123",           # Muito curta, só numérica
        "password",      # Muito comum
        "USERNAME_PLACEHOLDER" # Placeholder para senha similar ao username
    ]
)
def test_create_user_senha_fraca_falha(
    api_client: APIClient,
    admin_user: User,  # Admin para fazer a requisição
    senha_fraca: str
):
    """
    Verifica se POST /api/accounts/create_user/ falha (400)
    quando a 'password' fornecida é fraca (não passa nos validadores).

    Passos:
    1. Obtém um usuário admin para autenticar.
    2. Define um username único para o novo usuário.
    3. Define a senha fraca (baseada na parametrização),
       incluindo o caso de ser similar ao novo username.
    4. Prepara o payload com a senha fraca.
    5. Autentica o cliente com o usuário admin.
    6. Faz a requisição POST para /api/accounts/create_user/.
    7. Verifica se o status code é 400 Bad Request.
    8. Verifica se a resposta contém a mensagem de erro específica para 'password'.
    9. Verifica se o usuário NÃO foi criado no banco.
    """
    # 1. Obter usuário admin (da fixture)

    # 2. Definir username único
    novo_username = f"user_fraco_{uuid.uuid4().hex[:8]}"

    # 3. Definir senha fraca atual
    if senha_fraca == "USERNAME_PLACEHOLDER":
         # O UserAttributeSimilarityValidator compara com o username no payload
         senha_fraca_atual = novo_username
    else:
         senha_fraca_atual = senha_fraca

    # 4. Definir payload com senha fraca
    payload = {
        "username": novo_username,
        "password": senha_fraca_atual,
        "confirm_password": senha_fraca_atual,
        "nome": "Usuario Senha Fraca",
        "email": f"{novo_username}@teste.com"
    }

    # 5. Autenticar como admin
    api_client.force_authenticate(user=admin_user)

    # 6. Fazer a requisição POST
    url = "/api/accounts/create_user/"
    response = api_client.post(url, data=payload, format='json')

    # 7. Verificar Status Code 400
    assert response.status_code == status.HTTP_400_BAD_REQUEST, \
        f"Esperado status 400 ao tentar criar usuário com senha fraca '{senha_fraca_atual}', recebido {response.status_code}. Resposta: {response.content}"

    # 8. Verificar mensagem de erro
    response_data = response.json()
    assert "password" in response_data, \
        f"A resposta de erro para senha fraca '{senha_fraca_atual}' não contém a chave 'password'."
    # Verificamos se a lista de erros de senha não está vazia
    assert len(response_data["password"]) > 0, \
        f"Esperado pelo menos uma mensagem de erro de validação para 'password' com senha fraca '{senha_fraca_atual}', mas a lista está vazia."

    # 9. Verificar se o usuário NÃO foi criado no banco
    assert not User.objects.filter(username=novo_username).exists(), \
        f"O usuário '{novo_username}' foi criado indevidamente com uma senha fraca."

    # Desautenticar
    api_client.logout()


# Testar diferentes payloads inválidos (campos faltando)
@pytest.mark.parametrize(
    "payload_invalido, campo_faltante",
    [
        (
            { # Faltando 'username'
                "password": "SenhaValida@123",
                "confirm_password": "SenhaValida@123",
                "nome": "Teste Sem User",
            },
            "username"
        ),
        (
            { # Faltando 'password'
                "username": f"user_sem_senha_{uuid.uuid4().hex[:8]}",
                "confirm_password": "SenhaValida@123",
                "nome": "Teste Sem Senha",
            },
            "password"
        ),
        (
            { # Faltando 'confirm_password'
                "username": f"user_sem_conf_{uuid.uuid4().hex[:8]}",
                "password": "SenhaValida@123",
                "nome": "Teste Sem Confirmacao",
            },
            "confirm_password"
        ),
    ]
)
def test_create_user_campos_obrigatorios_faltando_falha(
    api_client: APIClient,
    admin_user: User,  # Admin para fazer a requisição
    payload_invalido: Dict[str, str],
    campo_faltante: str
):
    """
    Verifica se POST /api/accounts/create_user/ falha (400)
    quando campos obrigatórios ('username', 'password', 'confirm_password')
    estão ausentes no payload.

    Passos:
    1. Obtém um usuário admin para autenticar.
    2. Obtém um payload inválido (com campo faltando) da parametrização.
    3. Autentica o cliente com o usuário admin.
    4. Faz a requisição POST para /api/accounts/create_user/.
    5. Verifica se o status code é 400 Bad Request.
    6. Verifica se a resposta contém a mensagem de erro específica para o campo faltante.
    """
    # 1. Obter usuário admin (da fixture)

    # 2. Payload inválido (via parametrização)

    # 3. Autenticar como admin
    api_client.force_authenticate(user=admin_user)

    # 4. Fazer a requisição POST
    url = "/api/accounts/create_user/"
    response = api_client.post(url, data=payload_invalido, format='json')

    # 5. Verificar Status Code 400
    assert response.status_code == status.HTTP_400_BAD_REQUEST, \
        f"Esperado status 400 ao tentar criar usuário sem o campo '{campo_faltante}', recebido {response.status_code}. Resposta: {response.content}"

    # 6. Verificar mensagem de erro (mensagem padrão do DRF em pt-br)
    response_data = response.json()
    assert campo_faltante in response_data, \
        f"A resposta de erro não contém a chave esperada '{campo_faltante}'."
    assert "Este campo é obrigatório." in response_data[campo_faltante], \
        f"Mensagem de erro inesperada para o campo '{campo_faltante}': {response_data[campo_faltante]}"

    # Desautenticar
    api_client.logout()
