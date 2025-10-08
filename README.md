# **Sistema de Mapeamento da Limpeza de Salas (API RESTful)**

Este é o backend do Sistema de Mapeamento da Limpeza de Salas, desenvolvido com Django e Django REST Framework. Ele fornece uma API RESTful para gerenciar salas, registrar suas limpezas e autenticar usuários da equipe de zeladoria. O foco do projeto é otimizar o fluxo de trabalho da equipe de limpeza e fornecer informações atualizadas sobre a disponibilidade de salas limpas, solucionando ineficiências no gerenciamento manual da limpeza de salas no SENAC.

## **Índice**

1.  [Ambiente de Desenvolvimento](#ambiente-de-desenvolvimento)
    1.  [Pré-requisitos](#pré-requisitos)
    2.  [Clonar o Repositório](#1-clonar-o-repositório)
    3.  [Configurar o Ambiente Virtual (venv)](#2-configurar-o-ambiente-virtual-venv)
    4.  [Configurar Variáveis de Ambiente (.env)](#3-configurar-variáeis-de-ambiente-env)
    5.  [Instalar as Dependências](#4-instalar-as-dependências)
    6.  [Configurar o Banco de Dados](#5-configurar-o-banco-de-dados)
    7.  [Criar um Superusuário](#6-criar-um-superusuário-opcional-mas-recomendado)
    8.  [Rodar o Servidor de Desenvolvimento](#7-rodar-o-servidor-de-desenvolvimento)
2.  [Documentação dos Endpoints da API](#documentação-dos-endpoints-da-api)
    1.  [Endpoints da Aplicação accounts](#1-endpoints-da-aplicação-accounts)
        1.  [Login de Usuário](#11-login-de-usuário)
        2.  [Obter Dados do Usuário Logado](#12-obter-dados-do-usuário-logado)
        3.  [Listar Usuários](#13-listar-usuários)
        4.  [Criar Novo Usuário](#14-criar-novo-usuário-apenas-administradores)
        5.  [Mudar Senha do Usuário Autenticado](#15-mudar-senha-do-usuário-autenticado)
        6.  [Listar Grupos Disponíveis](#16-listar-grupos-disponíveis)
        7.  [Gerenciar Perfil do Usuário](#17-gerenciar-perfil-do-usuário)
    2.  [Endpoints da Aplicação salas](#2-endpoints-da-aplicação-salas)
        1.  [Listar Salas / Criar Nova Sala](#21-listar-salas--criar-nova-sala)
        2.  [Obter Detalhes / Atualizar / Excluir Sala](#22-obter-detalhes--atualizar--excluir-sala-específica)
        3.  [Iniciar Limpeza de Sala](#23-iniciar-limpeza-de-sala)
        4.  [Concluir Limpeza de Sala](#24-concluir-limpeza-de-sala)
        5.  [Marcar Sala como Suja](#25-marcar-sala-como-suja)
    3.  [Endpoints da Aplicação limpezas](#3-endpoints-da-aplicação-limpezas)
        1.  [Listar Registros de Limpeza](#31-listar-registros-de-limpeza)
    4.  [Endpoints da Aplicação notificacoes](#4-endpoints-da-aplicação-notificacoes)
        1.  [Listar Notificações](#41-listar-notificaões)
        2.  [Marcar Notificação Específica como Lida](#42-marcar-notificação-específica-como-lida)
        3.  [Marcar Todas as Notificações como Lidas](#43-marcar-todas-as-notificaões-como-lidas)
    5.  [Endpoints de Fotos de Limpeza](#5-endpoints-de-fotos-de-limpeza)
        1.  [Adicionar Foto a uma Limpeza](#51-adicionar-foto-a-uma-limpeza)
        2.  [Listar Fotos de Limpeza](#52-listar-fotos-de-limpeza)
        3.  [Obter / Excluir Foto de Limpeza](#53-obter--excluir-foto-de-limpeza-específica)
3.  [Tarefas Agendadas (Cron Job)](#tarefas-agendadas-cron-job)
    1.  [Notificações de Limpeza Pendente](#notificaões-de-limpeza-pendente)
4.  [Recursos Adicionais](#recursos-adicionais)
    1.  [PDF de QR Codes das Salas](#pdf-de-qr-codes-das-salas)
    2.  [Coleção para Insomnia](#coleção-para-insomnia)
    3.  [Guia para Requisições multipart/form-data](#guia-para-requisiões-multipartform-data-frontend)
5.  [Entendendo Fusos Horários na API](#entendendo-fusos-horários-na-api-ultima_limpeza_data_hora)
    1.  [Por que UTC?](#por-que-utc)
    2.  [O Que é Necessário Ficar Atento no Frontend](#o-que-é-necessário-ficar-atento-no-frontend-react-native--typescript)

## Ambiente de Desenvolvimento

Siga os passos abaixo para configurar e executar o projeto em seu ambiente local. É altamente recomendado usar um ambiente virtual (venv) para isolar as dependências do projeto.

### Pré-requisitos

  * Python 3.12+
  * pip (gerenciador de pacotes do Python)

### 1\. Clonar o Repositório

```bash
git clone https://github.com/thalsime/uc8_zeladoria.git
cd uc8_zeladoria # Navegue até a pasta raiz do projeto (onde está manage.py)
```

### 2\. Configurar o Ambiente Virtual (venv)

É uma boa prática usar `venv` para gerenciar as dependências do seu projeto, evitando conflitos com outras instalações Python. Acesse a pasta do projeto clonado e siga as instruções:

```bash
# Criar o ambiente virtual
python -m venv venv

# Ativar o ambiente virtual

# No Linux/Mac:
source venv/bin/activate

# No Windows (Command Prompt):
venv\Scripts\activate.bat

# No Windows (PowerShell):
venv\Scripts\Activate.ps1
```

### 3\. Configurar Variáveis de Ambiente (`.env`)

Este projeto utiliza a biblioteca `python-decouple` para gerenciar variáveis de ambiente, mantendo configurações sensíveis e específicas de ambiente fora do código-fonte.

1.  **Crie um arquivo `.env`:** Na pasta raiz do projeto (a mesma onde está `manage.py` e `.env.sample`), crie um novo arquivo chamado `.env`.
2.  **Copie o conteúdo:** Copie todo o conteúdo do arquivo `.env.sample` para o seu novo arquivo `.env`.
3.  **Ajuste os valores:** Você deve ajustar os valores para o seu ambiente.
      * `SECRET_KEY`: Uma chave secreta longa e aleatória (essencial para segurança em produção).
      * `DEBUG`: `True` para desenvolvimento, `False` para produção.
      * `ALLOWED_HOSTS`: Lista de domínios permitidos, separados por vírgula. Para desenvolvimento local, `127.0.0.1,localhost` é suficiente.
      * `CSRF_TRUSTED_ORIGINS`: Lista de domínios confiáveis para requisições CSRF. Para desenvolvimento, `http://127.0.0.1:8000,http://localhost:8000` é o ideal.

Exemplo do conteúdo do `.env`:

```
SECRET_KEY=uma_grande_string_de_caracteres_aleatorios
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
URI_ADMIN=admin/
LANGUAGE_CODE=pt-br
TIME_ZONE=America/Fortaleza
USE_I18N=True
USE_TZ=True
```

### 4\. Instalar as Dependências

Com o ambiente virtual ativado, instale todas as bibliotecas necessárias listadas no arquivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 5\. Configurar o Banco de Dados

O projeto utiliza SQLite por padrão, o que não requer configurações adicionais de banco de dados.

Aplique as migrações para criar as tabelas no banco de dados:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6\. Criar um Superusuário (Opcional, mas Recomendado)

Um superusuário é necessário para acessar o painel de administração do Django e criar outros usuários.

```bash
python manage.py createsuperuser
```

Siga as instruções no terminal para criar seu superusuário.

### 7\. Rodar o Servidor de Desenvolvimento

Com todas as configurações prontas, você pode iniciar o servidor de desenvolvimento do Django:

```bash
# 0.0.0.0:8000 permite que todos os IPs da máquina
# escutem a porta 8000 e não somente 127.0.0.1
python manage.py runserver 0.0.0.0:8000
```

O servidor estará rodando em `http://127.0.0.1:8000/`. Você pode acessar o painel de administração em `http://127.0.0.1:8000/admin/`.

## Documentação dos Endpoints da API

A API é composta por endpoints para gerenciamento de contas de usuário e gerenciamento de salas/registros de limpeza.

**Base URL:** `http://127.0.0.1:8000/api/`

-----

### 1\. Endpoints da Aplicação `accounts`

Endpoints para autenticação e gerenciamento de usuários.

#### 1.1. Login de Usuário

  * **Proposta:** Autenticar um usuário e retorna um token de autenticação junto com os dados do usuário logado.

  * **Requisição:**

      * **Verbo HTTP:** `POST`
      * **URI:** `/api/accounts/login/`
      * **Headers:** `Content-Type: application/json`
      * **Body:**
        ```json
        {
            "username": "seu_usuario",
            "password": "sua_senha"
        }
        ```

  * **Respostas:**

      * **`200 OK` (Sucesso):**
        ```json
        {
            "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
            "user_data": {
                "id": 1,
                "username": "seu_usuario",
                "email": "email@example.com",
                "is_superuser": false,
                "groups": [1],
                "nome": "Nome Completo do Usuário",
                "profile": {
                    "profile_picture": "http://127.0.0.1:8000/media/profile_pics/imagem.jpg"
                }
            }
        }
        ```
      * **`400 Bad Request` (Erro de Validação):**
        ```json
        {
            "non_field_errors": [
                "Credenciais inválidas."
            ]
        }
        ```

#### 1.2. Obter Dados do Usuário Logado

  * **Proposta:** Permite que um cliente autenticado recupere suas próprias informações.
  * **Requisição:**
      * **Verbo HTTP:** `GET`
      * **URI:** `/api/accounts/current_user/`
      * **Headers:** `Authorization: Token SEU_TOKEN_AQUI`
  * **Respostas:**
      * **`200 OK` (Sucesso):**
        ```json
        {
            "id": 1,
            "username": "seu_usuario",
            "email": "email@example.com",
            "is_superuser": false,
            "groups": [1],
            "nome": "Nome Completo do Usuário",
            "profile": {
                "profile_picture": "http://127.0.0.1:8000/media/profile_pics/imagem.jpg"
            }
        }
        ```
      * **`401 Unauthorized` (Erro):** Ocorre se o token não for fornecido ou for inválido.
        ```json
        {
            "detail": "As credenciais de autenticação não foram fornecidas."
        }
        ```

#### 1.3. Listar Usuários

  * **Proposta:** Retorna uma lista de todos os usuários cadastrados no sistema, com suporte a filtros avançados.
  * **Permissões:** Apenas administradores (`is_superuser=True`).
  * **Requisição:**
      * **Verbo HTTP:** `GET`
      * **URI:** `/api/accounts/list_users/`
      * **Headers:** `Authorization: Token SEU_TOKEN_DE_ADMIN_AQUI`
  * **Filtros (Query Parameters):**
      * `username` (string): Busca parcial (case-insensitive) por nome de usuário.
          * **Exemplo:** `/api/accounts/list_users/?username=admin`
      * `email` (string): Busca parcial (case-insensitive) por e-mail.
          * **Exemplo:** `/api/accounts/list_users/?email=@example.com`
      * `is_superuser` (boolean): Filtra por status de superusuário (`true` ou `false`).
          * **Exemplo:** `/api/accounts/list_users/?is_superuser=true`
      * `group` (string): Filtra por nome exato do grupo (case-insensitive).
          * **Exemplo:** `/api/accounts/list_users/?group=Zeladoria`
  * **Respostas:**
      * **`200 OK` (Sucesso):** Retorna um array de objetos de usuário.
        ```json
        [
            {
                "id": 1,
                "username": "admin",
                "email": "admin@example.com",
                "is_superuser": true,
                "groups": [],
                "nome": "Admin User",
                "profile": { "profile_picture": null }
            },
            {
                "id": 2,
                "username": "zelador1",
                "email": "zelador1@example.com",
                "is_superuser": false,
                "groups": [1],
                "nome": "Zelador Um",
                "profile": { "profile_picture": null }
            }
        ]
        ```
      * **`403 Forbidden` (Erro):** Ocorre se o usuário não for um administrador.
        ```json
        {
            "detail": "Você não tem permissão para executar essa ação."
        }
        ```

#### 1.4. Criar Novo Usuário (Apenas Administradores)

  * **Proposta:** Cria uma nova conta de usuário. A senha informada será validada contra as regras de força de senha do Django.

  * **Permissões:** Apenas administradores.

  * **Requisição:**

      * **Verbo HTTP:** `POST`
      * **URI:** `/api/accounts/create_user/`
      * **Headers:** `Authorization: Token SEU_TOKEN_DE_ADMIN_AQUI`, `Content-Type: application/json`
      * **Body:**
        ```json
        {
            "username": "novo_usuario",
            "password": "Senha@Forte123",
            "confirm_password": "Senha@Forte123",
            "nome": "Nome Completo",
            "email": "novo@email.com",
            "groups": [1]
        }
        ```

  * **Respostas:**

      * **`201 Created` (Sucesso):**

        ```json
        {
            "message": "Usuário criado com sucesso.",
            "user": {
                "id": 3,
                "username": "novo_usuario",
                "email": "novo@email.com",
                "is_superuser": false,
                "groups": [1],
                "nome": "Nome Completo",
                "profile": { "profile_picture": null }
            },
            "token": "x9y8z7w6v5u4t3s2r1q0p9o8n7m6l5k4j3i2h1g0"
        }
        ```

      * **`400 Bad Request` (Erro de Validação):** Ocorre se as senhas não coincidem, a senha é fraca, ou o `username` já existe.

        ```json
        {
            "password": [
                "As senhas não coincidem."
            ]
        }
        ```

        ```json
        {
            "username": [
                "Um usuário com este nome de usuário já existe."
            ]
        }
        ```

#### 1.5. Mudar Senha do Usuário Autenticado

  * **Proposta:** Permite que o usuário autenticado altere sua própria senha. A nova senha será validada contra as regras de força do Django.

  * **Permissões:** Qualquer usuário autenticado.

  * **Requisição:**

      * **Verbo HTTP:** `POST`
      * **URI:** `/api/accounts/change_password/`
      * **Headers:** `Authorization: Token SEU_TOKEN_AQUI`, `Content-Type: application/json`
      * **Body:**
        ```json
        {
            "old_password": "sua_senha_antiga",
            "new_password": "Nova@Senha123",
            "confirm_new_password": "Nova@Senha123"
        }
        ```

  * **Respostas:**

      * **`200 OK` (Sucesso):**

        ```json
        {
            "message": "Senha alterada com sucesso."
        }
        ```

      * **`400 Bad Request` (Erro):** Ocorre se a senha antiga está incorreta, as novas não coincidem ou a nova senha é fraca.

        ```json
        {
            "old_password": "A senha antiga está incorreta."
        }
        ```

        ```json
        {
            "new_password": "As novas senhas não coincidem."
        }
        ```

#### **1.6. Listar Grupos Disponíveis**

  * **Proposta:** Retorna uma lista de todos os grupos (papéis) de usuários disponíveis no sistema.
  * **Permissões:** Qualquer usuário autenticado.
  * **Requisição:**
      * **Verbo HTTP:** `GET`
      * **URI:** `/api/accounts/list_groups/`
      * **Headers:** `Authorization: Token SEU_TOKEN_AQUI`
  * **Resposta (`200 OK`):**
    ```json
    [
        {"id": 2, "name": "Solicitante de Serviços"},
        {"id": 1, "name": "Zeladoria"}
    ]
    ```

#### 1.7. Gerenciar Perfil do Usuário

  * **Proposta:** Permite visualizar e atualizar o próprio perfil, incluindo nome e foto.
  * **Permissões:** Apenas o próprio usuário autenticado.
  * **Requisições:**
      * **Ver Perfil (`GET`):**
          * **URI:** `/api/accounts/profile/`
          * **Headers:** `Authorization: Token SEU_TOKEN_AQUI`
      * **Atualizar Perfil (`PUT` ou `PATCH`):**
          * **URI:** `/api/accounts/profile/`
          * **Headers:** `Authorization: Token SEU_TOKEN_AQUI`, `Content-Type: multipart/form-data`
          * **Body (Multipart Form-data):** Para enviar uma imagem, a requisição deve ser do tipo `multipart/form-data`.
              * Campo `nome` (texto): `Novo Nome Completo`
              * Campo `profile_picture` (arquivo): Selecionar o arquivo de imagem.
  * **Respostas (`200 OK`):**
      * **Resposta para `GET` e `PUT`/`PATCH`:**
        ```json
        {
            "nome": "Nome Atualizado",
            "profile_picture": "http://127.0.0.1:8000/media/profile_pics/uuid_aleatorio.jpg"
        }
        ```

-----

### 2\. Endpoints da Aplicação `salas`

Gerencia as informações sobre as salas e o processo de limpeza.

#### 2.1. Listar Salas / Criar Nova Sala

  * **URI:** `/api/salas/`

  * **Verbo `GET` (Listar):**

      * **Proposta:** Lista todas as salas com filtros.

      * **Permissões:** Qualquer usuário autenticado.

      * **Filtros (Query Parameters):**

          * `ativa` (boolean): Filtra por salas ativas (`true`) ou inativas (`false`).
              * **Exemplo:** `/api/salas/?ativa=true`
          * `nome_numero` (string): Busca parcial (case-insensitive) por nome ou número da sala.
              * **Exemplo:** `/api/salas/?nome_numero=Auditório`
          * `localizacao` (string): Busca parcial (case-insensitive) por localização.
              * **Exemplo:** `/api/salas/?localizacao=Bloco`
          * `capacidade_min` (integer): Filtra por salas com capacidade maior ou igual ao valor informado.
              * **Exemplo:** `/api/salas/?capacidade_min=50`
          * `capacidade_max` (integer): Filtra por salas com capacidade menor ou igual ao valor informado.
              * **Exemplo:** `/api/salas/?capacidade_max=100`
          * `responsavel_username` (string): Busca parcial (case-insensitive) pelo nome de usuário de um dos responsáveis.
              * **Exemplo:** `/api/salas/?responsavel_username=zelador`

      * **Resposta (`200 OK`):**

        ```json
        [
            {
                "id": 1,
                "qr_code_id": "uuid-da-sala-1",
                "nome_numero": "Laboratório de Redes",
                "imagem": "http://127.0.0.1:8000/media/sala_pics/uuid_aleatorio.jpg",
                "capacidade": 25,
                "validade_limpeza_horas": 8,
                "descricao": null,
                "instrucoes": null,
                "localizacao": "Bloco C, Sala 203",
                "ativa": true,
                "responsaveis": ["zelador1"],
                "status_limpeza": "Limpeza Pendente",
                "ultima_limpeza_data_hora": null,
                "ultima_limpeza_funcionario": null,
                "detalhes_suja": null
            },
            {
                "id": 2,
                "qr_code_id": "uuid-da-sala-2",
                "nome_numero": "Auditório Principal",
                "imagem": null,
                "capacidade": 150,
                "validade_limpeza_horas": 24,
                "descricao": "Auditório para eventos.",
                "instrucoes": "Verificar microfones.",
                "localizacao": "Bloco A",
                "ativa": true,
                "responsaveis": ["zelador1", "zelador2"],
                "status_limpeza": "Suja",
                "ultima_limpeza_data_hora": "2025-10-01T10:00:00Z",
                "ultima_limpeza_funcionario": "zelador1",
                "detalhes_suja": {
                    "data_hora": "2025-10-02T15:30:00Z",
                    "reportado_por": "funcionario_solicitante",
                    "observacoes": "Derramaram café no chão da primeira fileira."
                }
            }
        ]
        ```

      * **Observação sobre o campo `detalhes_suja`:** Este campo é um objeto que contém os detalhes do último relatório de sujeira. Ele será null para todas as salas que não estiverem com o status "Suja". Quando o status for "Suja", ele será preenchido com a data, o usuário que reportou e as observações do relatório.

  * **Verbo POST (Criar):**

      * **Proposta:** Cria uma nova sala.
      * **Permissões:** Apenas administradores.
      * **Headers:** `Authorization: Token SEU_TOKEN_DE_ADMIN_AQUI`, `Content-Type: multipart/form-data`
      * **Body (Multipart Form-data):**
          * Campo `nome_numero` (texto): `Laboratório de Redes`
          * Campo `capacidade` (texto): `25`
          * Campo `validade_limpeza_horas` (texto): `8`
          * Campo `localizacao` (texto): `Bloco C, Sala 203`
          * Campo `imagem` (arquivo, opcional): Selecionar o arquivo de imagem.
          * Campo `responsaveis` (texto, opcional): `zelador1` (para múltiplos, envie o campo repetido: `responsaveis=zelador1&responsaveis=zelador2`)
      * **Respostas:**
          * **`201 Created`:** A resposta contém o objeto da sala recém-criada, que sempre iniciará com `status\limpeza`: "Limpeza Pendente" e `detalhes\suja`: null.

            ```json
            {
                "id": 1,
                "qr_code_id": "uuid-da-sala-1",
                "nome_numero": "Laboratório de Redes",
                "imagem": "http://127.0.0.1:8000/media/sala_pics/uuid_aleatorio.jpg",
                "capacidade": 25,
                "validade_limpeza_horas": 8,
                "descricao": null,
                "instrucoes": null,
                "localizacao": "Bloco C, Sala 203",
                "ativa": true,
                "responsaveis": ["zelador1"],
                "status_limpeza": "Limpeza Pendente",
                "ultima_limpeza_data_hora": null,
                "ultima_limpeza_funcionario": null,
                "detalhes_suja": null
            }
            ```

          * **`400 Bad Request` (Erro de Validação):**

            ```json
            {
                "nome_numero": [ "sala com este Nome/Número já existe." ]
            }
            ```

          * **`403 Forbidden`:**

            ```json
            { "detail": "Você não tem permissão para executar essa ação." }
            ```

#### 2.2. Obter Detalhes / Atualizar / Excluir Sala Específica

  * **URI:** `/api/salas/{qr_code_id}/`

  * **Verbo `GET` (Detalhes):**

      * **Permissões:** Qualquer usuário autenticado.
      * **Respostas:**
          * **`200 OK` (Exemplo de sala Suja):** Retorna o objeto completo da sala. O campo `detalhes\suja` será preenchido se o status for `"Suja"`.

            ```json
            {
                "id": 2,
                "qr_code_id": "uuid-da-sala-2",
                "nome_numero": "Auditório Principal",
                "imagem": null,
                "capacidade": 150,
                "validade_limpeza_horas": 24,
                "descricao": "Auditório para eventos.",
                "instrucoes": "Verificar microfones.",
                "localizacao": "Bloco A",
                "ativa": true,
                "responsaveis": ["zelador1", "zelador2"],
                "status_limpeza": "Suja",
                "ultima_limpeza_data_hora": "2025-10-01T10:00:00Z",
                "ultima_limpeza_funcionario": "zelador1",
                "detalhes_suja": {
                    "data_hora": "2025-10-02T15:30:00Z",
                    "reportado_por": "funcionario_solicitante",
                    "observacoes": "Derramaram café no chão da primeira fileira."
                }
            }
            ```

          * **`200 OK` (Exemplo de sala Limpa):** Se o status não for "Suja", `detalhes\suja` será `null`.

            ```json
            {
                "id": 3,
                "qr_code_id": "uuid-da-sala-3",
                "nome_numero": "Sala de Reuniões",
                "imagem": null,
                "capacidade": 10,
                "validade_limpeza_horas": 48,
                "descricao": null,
                "instrucoes": null,
                "localizacao": "Administração",
                "ativa": true,
                "responsaveis": [],
                "status_limpeza": "Limpa",
                "ultima_limpeza_data_hora": "2025-10-03T09:00:00Z",
                "ultima_limpeza_funcionario": "zelador2",
                "detalhes_suja": null
            }
            ```

          * **`404 Not Found`:**

            ```json
            { "detail": "Não encontrado." }
            ```

  * **Verbos `PUT` / `PATCH` (Atualizar):**

      * **Permissões:** Apenas administradores.
      * **Headers:** `Authorization: Token SEU_TOKEN_DE_ADMIN_AQUI`, `Content-Type: multipart/form-data`
      * **Body (Multipart Form-data):** Envie apenas os campos que deseja alterar. `PATCH` para atualização parcial, `PUT` para completa.
          * Campo `localizacao` (texto): `Bloco D, Auditório Principal`
      * **Respostas:**
          * **`200 OK`:** Retorna o objeto da sala atualizado.
          * **`400 Bad Request` / `403 Forbidden` / `404 Not Found`.**

  * **Verbo `DELETE` (Excluir):**

      * **Permissões:** Apenas administradores.
      * **Respostas:**
          * **`204 No Content` (Sucesso):** A sala foi excluída.

          * **`400 Bad Request` (Erro de Negócio):**

            ```json
            { "detail": "Salas inativas não podem ser excluídas. Ative a sala primeiro." }
            ```

          * **`403 Forbidden` / `404 Not Found`.**

#### **2.3. Iniciar Limpeza de Sala**

  * **Proposta:** Cria um registro para marcar o **início** de uma sessão de limpeza. O status da sala muda para "Em Limpeza".
  * **Permissões:** Apenas usuários do grupo **Zeladoria**.
  * **Requisição:**
      * **Verbo HTTP:** `POST`
      * **URI:** `/api/salas/{qr_code_id}/iniciar_limpeza/`
      * **Headers:** `Authorization: Token SEU_TOKEN_DE_ZELADOR_AQUI`
  * **Respostas:**
      * **`201 Created` (Sucesso):**

        ```json
        {
            "id": 10,
            "sala": "uuid-da-sala-1",
            "sala_nome": "Laboratório de Redes",
            "data_hora_inicio": "2025-09-15T14:30:00Z",
            "data_hora_fim": null,
            "funcionario_responsavel": "zelador1",
            "observacoes": null,
            "fotos": []
        }
        ```

      * **`400 Bad Request` (Erro):**

          * Se a sala já está em limpeza:

            ```json
            { "detail": "Esta sala já está em processo de limpeza." }
            ```

          * Se a sala está inativa:

            ```json
            { "detail": "Salas inativas não podem ter a limpeza iniciada." }
            ```

      * **`403 Forbidden` / `404 Not Found`.**

#### 2.4. Concluir Limpeza de Sala

  * **Proposta:** Encontra a sessão de limpeza em aberto para a sala e registra o **horário de conclusão**. O status da sala muda para "Limpa". Requer que pelo menos uma foto de comprovação tenha sido enviada.

  * **Permissões:** Apenas usuários do grupo **Zeladoria**.

  * **Requisição:**

      * **Verbo HTTP:** `POST`
      * **URI:** `/api/salas/{qr_code_id}/concluir_limpeza/`
      * **Headers:** `Authorization: Token SEU_TOKEN_DE_ZELADOR_AQUI`, `Content-Type: application/json`
      * **Body (Opcional):**
        ```json
        {
            "observacoes": "Limpeza finalizada, tudo em ordem."
        }
        ```

  * **Respostas:**

      * **`200 OK` (Sucesso):**

        ```json
        {
            "id": 10,
            "sala": "uuid-da-sala-1",
            "sala_nome": "Laboratório de Redes",
            "data_hora_inicio": "2025-09-15T14:30:00Z",
            "data_hora_fim": "2025-09-15T14:45:00Z",
            "funcionario_responsavel": "zelador1",
            "observacoes": "Limpeza finalizada, tudo em ordem.",
            "fotos": [
                {
                    "id": 1,
                    "imagem": "http://127.0.0.1:8000/media/fotos_limpeza/foto1.jpg",
                    "timestamp": "2025-09-15T14:40:00Z"
                }
            ]
        }
        ```

      * **`400 Bad Request` (Erro):**

          * Se nenhuma limpeza foi iniciada:

            ```json
            { "detail": "Nenhuma limpeza foi iniciada para esta sala." }
            ```

          * Se nenhuma foto de comprovação foi enviada:

            ```json
            { "detail": "É necessário enviar pelo menos uma foto antes de concluir a limpeza." }
            ```

      * **`403 Forbidden` / `404 Not Found`.**

#### 2.5. Marcar Sala como Suja

  * **Proposta:** Cria um relatório de que uma sala está suja, alterando seu status para "Suja" e sobrepondo o status de "Limpa".

  * **Permissões:** Apenas usuários do grupo **Solicitante de Serviços**.

  * **Requisição:**

      * **Verbo HTTP:** `POST`
      * **URI:** `/api/salas/{qr_code_id}/marcar_como_suja/`
      * **Headers:** `Authorization: Token SEU_TOKEN_DE_SOLICITANTE_AQUI`, `Content-Type: application/json`
      * **Body (Opcional):**
        ```json
        {
            "observacoes": "Material derramado no chão."
        }
        ```

  * **Respostas:**

      * **`201 Created` (Sucesso):**

        ```json
        {
            "status": "Relatório de sala suja enviado com sucesso."
        }
        ```

      * **`400 Bad Request` (Erro):** Ocorre se a sala reportada estiver inativa.

        ```json
        { "detail": "Não é possível reportar uma sala inativa." }
        ```

      * **403 Forbidden (Erro):** Ocorre se o usuário não pertencer ao grupo Solicitante de Serviços.

### 3\. Endpoints da Aplicação `limpezas`

Endpoints de apenas leitura para consultar o histórico de limpezas.

#### 3.1. Listar Registros de Limpeza

  * **Proposta:** Recupera o histórico de registros de limpeza. Administradores visualizam todos os registros, enquanto usuários da Zeladoria visualizam apenas os registros que eles próprios criaram.
  * **Permissões:** Acesso permitido para **Administradores** e membros do grupo **Zeladoria**.
  * **Requisição:**
      * **Verbo HTTP:** `GET`
      * **URI:** `/api/limpezas/`
      * **Headers:** `Authorization: Token SEU_TOKEN_DE_ADMIN_OU_ZELADOR_AQUI`
  * **Filtros (Query Parameters):**
      * `sala_uuid` (string): Filtra os registros pelo UUID (`qr_code_id`) exato da sala.
          * **Exemplo:** `/api/limpezas/?sala_uuid=e0b3cdba-3489-4954-b988-763ceb72b7c1`
      * `sala_nome` (string): Busca textual parcial (case-insensitive) pelo nome da sala.
          * **Exemplo:** `/api/limpezas/?sala_nome=Teórica`
      * `funcionario_username` (string): Busca textual parcial (case-insensitive) pelo nome de usuário do funcionário.
          * **Exemplo:** `/api/limpezas/?funcionario_username=zelador`
      * `data_hora_limpeza_after` (date): Filtra registros a partir da data informada (formato `YYYY-MM-DD`).
          * **Exemplo:** `/api/limpezas/?data_hora_limpeza_after=2025-09-10`
      * `data_hora_limpeza_before` (date): Filtra registros até a data informada (formato `YYYY-MM-DD`).
          * **Exemplo:** `/api/limpezas/?data_hora_limpeza_after=2025-09-01&data_hora_limpeza_before=2025-09-15`
      * **Observação:** Para usuários do grupo 'Zeladoria', estes filtros são aplicados apenas sobre o subconjunto de seus próprios registros.
  * **Respostas:**
      * **`200 OK` (Sucesso):**
        ```json
        [
            {
                "id": 10,
                "sala": "uuid-da-sala-1",
                "sala_nome": "Laboratório de Redes",
                "data_hora_inicio": "2025-09-15T14:30:00Z",
                "data_hora_fim": "2025-09-15T14:45:00Z",
                "funcionario_responsavel": "zelador1",
                "observacoes": "Limpeza finalizada.",
                "fotos": [
                    { "id": 1, "imagem": "...", "timestamp": "..." }
                ]
            }
        ]
        ```
      * **`403 Forbidden` (Erro):** Ocorre se o usuário autenticado não for um administrador nem pertencer ao grupo 'Zeladoria'.

-----

### 4\. Endpoints da Aplicação `notificacoes`

Endpoints para o usuário logado consultar e gerenciar suas notificações.

#### 4.1. Listar Notificações

  * **Proposta:** Retorna a lista de todas as notificações do usuário autenticado.
  * **Permissões:** Qualquer usuário autenticado.
  * **Requisição:**
      * **Verbo HTTP:** `GET`
      * **URI:** `/api/notificacoes/`
      * **Headers:** `Authorization: Token SEU_TOKEN_AQUI`
  * **Resposta (`200 OK`):**
    ```json
    [
        {
            "id": 1,
            "mensagem": "A sala 'Laboratório de Redes' foi reportada como suja.",
            "link": "/salas/uuid-da-sala/",
            "data_criacao": "2025-09-14T18:00:00Z",
            "lida": false
        }
    ]
    ```

#### 4.2. Marcar Notificação Específica como Lida

  * **Proposta:** Marca uma única notificação como lida.
  * **Permissões:** Apenas o destinatário da notificação.
  * **Requisição:**
      * **Verbo HTTP:** `POST`
      * **URI:** `/api/notificacoes/{id}/marcar_como_lida/`
      * **Headers:** `Authorization: Token SEU_TOKEN_AQUI`
  * **Respostas:**
      * **`204 No Content` (Sucesso):** A notificação foi marcada como lida com sucesso.
      * **`404 Not Found` (Erro):** Ocorre se a notificação não existir ou não pertencer ao usuário.
        ```json
        { "detail": "Não encontrado." }
        ```

#### 4.3. Marcar Todas as Notificações como Lidas

  * **Proposta:** Marca todas as notificações não lidas do usuário como lidas.
  * **Permissões:** Qualquer usuário autenticado.
  * **Requisição:**
      * **Verbo HTTP:** `POST`
      * **URI:** `/api/notificacoes/marcar_todas_como_lidas/`
      * **Headers:** `Authorization: Token SEU_TOKEN_AQUI`
  * **Resposta (`204 No Content`):** Todas as notificações foram marcadas como lidas com sucesso.

-----

### 5\. Endpoints de Fotos de Limpeza

Endpoints para adicionar e gerenciar fotos de comprovação de uma sessão de limpeza.

#### 5.1. Adicionar Foto a uma Limpeza

  * **Proposta:** Faz o upload de uma foto e a associa a um registro de limpeza em andamento. Limite de 3 fotos por limpeza.
  * **Permissões:** Apenas usuários do grupo **Zeladoria**.
  * **Requisição:**
      * **Verbo HTTP:** `POST`
      * **URI:** `/api/fotos_limpeza/`
      * **Headers:** `Authorization: Token SEU_TOKEN_DE_ZELADOR_AQUI`, `Content-Type: multipart/form-data`
      * **Body (Multipart Form-data):**
          * Campo `registro_limpeza` (texto): `ID do registro retornado por 'iniciar_limpeza'`
          * Campo `imagem` (arquivo): Selecionar o arquivo de imagem.
  * **Respostas:**
      * **`201 Created` (Sucesso):**
        ```json
        {
            "id": 1,
            "imagem": "http://127.0.0.1:8000/media/fotos_limpeza/uuid_aleatorio.jpg",
            "timestamp": "2025-09-14T21:40:00Z"
        }
        ```
      * **`400 Bad Request` (Erro):**
          * Se o limite de fotos foi atingido:

            ```json
            { "detail": "Limite de 3 fotos por registro de limpeza atingido." }
            ```

          * Se a limpeza já foi concluída:

            ```json
            { "detail": "Esta limpeza já foi concluída e não aceita mais fotos." }
            ```

          * Se campos obrigatórios faltaram:

            ```json
            { "detail": "Os campos \"registro_limpeza\" (ID) e \"imagem\" são obrigatórios." }
            ```
      * **`404 Not Found` (Erro):** Ocorre se o `registro_limpeza` não existe ou não pertence ao usuário.
        ```json
        { "detail": "Registro de limpeza não encontrado ou não pertence a você." }
        ```

#### 5.2. Listar Fotos de Limpeza

  * **Proposta:** Lista as fotos de limpeza. Administradores veem todas; zeladores veem apenas as suas.
  * **Permissões:** Qualquer usuário autenticado.
  * **Requisição:**
      * **Verbo HTTP:** `GET`
      * **URI:** `/api/fotos_limpeza/`
      * **Headers:** `Authorization: Token SEU_TOKEN_AQUI`
  * **Resposta (`200 OK`):**
    ```json
    [
        {
            "id": 1,
            "imagem": "http://127.0.0.1:8000/media/fotos_limpeza/uuid_aleatorio.jpg",
            "timestamp": "2025-09-14T21:40:00Z"
        }
    ]
    ```

#### 5.3. Obter / Excluir Foto de Limpeza Específica

  * **URI:** `/api/fotos_limpeza/{id}/`

  * **Permissões:** O próprio zelador que enviou a foto ou um administrador.

  * **Verbo `GET` (Obter):**

      * **Proposta:** Obtém os detalhes de uma foto específica.
      * **Respostas:**
          * **`200 OK`:** Retorna o objeto da foto (mesmo formato da criação).
          * **`404 Not Found`**.

  * **Verbo `DELETE` (Excluir):**

      * **Proposta:** Exclui uma foto.
      * **Respostas:**
          * **`204 No Content` (Sucesso):** A foto foi excluída.
          * **`404 Not Found`**.

-----

## Tarefas Agendadas (Cron Job)

Para garantir que a equipe de Zeladoria seja notificada sobre salas cuja limpeza expirou por tempo, o sistema utiliza uma tarefa agendada.

### Notificações de Limpeza Pendente

O projeto inclui um comando de gerenciamento (`verificar_limpezas_pendentes`) que deve ser executado periodicamente no servidor. Este comando verifica todas as salas ativas e, para aquelas cujo prazo de validade da limpeza expirou, cria notificações para os zeladores responsáveis.

  * **Configuração no Servidor:**
    Para executar esta verificação a cada 15 minutos, adicione a seguinte linha ao `crontab` do seu servidor. Certifique-se de substituir os caminhos para os do seu ambiente.

    ```bash
    */15 * * * * /caminho/para/seu/projeto/venv/bin/python /caminho/para/seu/projeto/manage.py verificar_limpezas_pendentes >> /caminho/para/seu/projeto/logs/cron.log 2>&1
    ```

      * `*/15 * * * *`: Define a execução a cada 15 minutos.
      * `/caminho/para/seu/projeto/venv/bin/python`: Caminho absoluto para o interpretador Python do seu ambiente virtual.
      * `>> /caminho/para/seu/projeto/logs/cron.log 2>&1`: (Recomendado) Redireciona a saída do comando para um arquivo de log para facilitar a depuração.

-----

## Recursos Adicionais

### PDF de QR Codes das Salas

O sistema gera automaticamente um arquivo PDF contendo uma página para cada sala ativa, com seus detalhes e um QR Code para identificação. Este arquivo é atualizado sempre que uma sala é criada ou deletada.

  * **URL de Acesso:** O arquivo está publicamente acessível através do diretório de mídias.
  * **Exemplo:** `http://127.0.0.1:8000/media/salas_qr_codes.pdf`

### Coleção para Insomnia

O projeto inclui um arquivo `extra/insomnia.json` que pode ser importado no cliente de API [Insomnia](https://insomnia.rest/). Ele contém uma coleção pré-configurada de todas as requisições da API, facilitando os testes e o desenvolvimento.

### Guia para Requisições `multipart/form-data` (Frontend)

Endpoints que envolvem upload de arquivos (como fotos de salas ou de perfil) exigem que a requisição seja enviada com o `Content-Type` `multipart/form-data`. Em clientes JavaScript/TypeScript, isso é feito com a classe `FormData`.

**Principais Pontos:**

1.  **Não defina o `Content-Type` manualmente:** Ao usar `FormData` com `fetch` ou `axios`, o navegador define automaticamente o `Content-Type` correto, incluindo o `boundary` necessário. Se você definir manualmente como `'multipart/form-data'`, a requisição falhará.
2.  **Use `append`:** Use o método `.append()` do objeto `FormData` para adicionar campos de texto e arquivos.
3.  **Para arquivos (React Native):** O objeto do arquivo deve ter as propriedades `uri`, `name`, e `type`.

#### Exemplo 1: Criando uma Nova Sala (POST `/api/salas/`)

```typescript
// Exemplo para criar uma nova sala com uma imagem

interface File {
  uri: string;
  name: string;
  type: string; // Ex: 'image/jpeg'
}

const criarNovaSala = async (token: string, nome: string, capacidade: number, imagem: File) => {
  const formData = new FormData();

  formData.append('nome_numero', nome);
  formData.append('capacidade', capacidade.toString());
  formData.append('validade_limpeza_horas', '8');
  formData.append('localizacao', 'Bloco Teste, Sala 101');

  // Anexa o arquivo
  // O terceiro argumento (nome do arquivo) é crucial
  formData.append('imagem', {
    uri: imagem.uri,
    name: imagem.name,
    type: imagem.type,
  } as any);

  // Adicionando um responsável (pode ser repetido para múltiplos)
  formData.append('responsaveis', 'zelador1');

  try {
    const response = await fetch('http://127.0.0.1:8000/api/salas/', {
      method: 'POST',
      headers: {
        'Authorization': `Token ${token}`,
        // Não defina 'Content-Type' aqui!
      },
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      console.error('Erro ao criar sala:', data);
    } else {
      console.log('Sala criada com sucesso:', data);
    }
  } catch (error) {
    console.error('Erro de rede:', error);
  }
};
```

#### Exemplo 2: Adicionando Foto a uma Limpeza (POST `/api/fotos_limpeza/`)

```typescript
// Exemplo para fazer upload de uma foto de comprovação

const adicionarFotoLimpeza = async (token: string, registroLimpezaId: number, foto: File) => {
  const formData = new FormData();

  formData.append('registro_limpeza', registroLimpezaId.toString());
  formData.append('imagem', {
    uri: foto.uri,
    name: foto.name,
    type: foto.type,
  } as any);

  try {
    const response = await fetch('http://127.0.0.1:8000/api/fotos_limpeza/', {
      method: 'POST',
      headers: {
        'Authorization': `Token ${token}`,
      },
      body: formData,
    });

    // ... tratar resposta ...
  } catch (error) {
    console.error('Erro de rede:', error);
  }
};
```

-----

## Entendendo Fusos Horários na API (`ultima_limpeza_data_hora`)

Um ponto crucial para o consumo desta API, especialmente em aplicações front-end como React Native, é a propriedade `ultima_limpeza_data_hora`.

### Por que UTC?

A API retorna todos os timestamps no formato **UTC (Coordinated Universal Time)** e como strings **ISO 8601** (ex: `"2025-07-09T12:00:00Z"`).

  * **Universalidade:** UTC é um padrão global de tempo, independente de qualquer fuso horário local.
  * **Precisão:** Evita ambiguidades e erros comuns de fuso horário.

### O Que é Necessário Ficar Atento no Frontend (React Native + TypeScript)

A responsabilidade de converter e exibir os horários no fuso horário *local do usuário* é do aplicativo cliente.

```typescript
// Exemplo de como consumir e exibir 'ultima_limpeza_data_hora' no React Native

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { parseISO, format } from 'date-fns';
import { ptBR } from 'date-fns/locale'; // Para formatar em português

// Supondo que você tenha um tipo para os dados da Sala
interface Sala {
  id: number;
  nome_numero: string;
  // ... outros campos
  ultima_limpeza_data_hora: string | null; // A API retorna string ISO 8601 em UTC
  ultima_limpeza_funcionario: string | null;
}

interface SalaCardProps {
  sala: Sala;
}

const SalaCard: React.FC<SalaCardProps> = ({ sala }) => {
  const displayLastCleanedTime = (utcDateTimeString: string | null): string => {
    if (!utcDateTimeString) {
      return "N/A";
    }

    try {
      // 1. Parsing: Converte a string ISO 8601 (UTC) para um objeto Date
      const dateObjectUTC = parseISO(utcDateTimeString);

      // 2. Formatação: `format` de date-fns, por padrão, formata para o fuso horário local do dispositivo
      return format(dateObjectUTC, "dd/MM/yyyy 'às' HH:mm:ss", { locale: ptBR });

    } catch (error) {
      console.error("Erro ao processar data/hora:", error);
      return "Data Inválida";
    }
  };

  return (
    <View style={styles.card}>
      <Text style={styles.title}>{sala.nome_numero}</Text>
      <Text>
        Última Limpeza: {displayLastCleanedTime(sala.ultima_limpeza_data_hora)}
      </Text>
      {sala.ultima_limpeza_funcionario && (
        <Text>Por: {sala.ultima_limpeza_funcionario}</Text>
      )}
    </View>
  );
};
// ... (styles) ...
export default SalaCard;
```