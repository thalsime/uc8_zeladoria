# Sistema de Mapeamento da Limpeza de Salas (API RESTful)

Este é o backend do Sistema de Mapeamento da Limpeza de Salas, desenvolvido com Django e Django REST Framework. Ele fornece uma API RESTful para gerenciar salas, registrar suas limpezas e autenticar usuários da equipe de zeladoria. O foco do projeto é otimizar o fluxo de trabalho da equipe de limpeza e fornecer informações atualizadas sobre a disponibilidade de salas limpas, solucionando ineficiências no gerenciamento manual da limpeza de salas no SENAC.

## Índice

1.  [Ambiente de Desenvolvimento](#ambiente-de-desenvolvimento)
    1.  [Pré-requisitos](#pr%C3%A9-requisitos)
    2.  [Clonar o Repositório](#1-clonar-o-reposit%C3%B3rio)
    3.  [Configurar o Ambiente Virtual (venv)](#2-configurar-o-ambiente-virtual-venv)
    4.  [Configurar Variáveis de Ambiente (.env)](#3-configurar-vari%C3%A1veis-de-ambiente-env)
    5.  [Instalar as Dependências](#4-instalar-as-depend%C3%AAncias)
    6.  [Configurar o Banco de Dados](#5-configurar-o-banco-de-dados)
    7.  [Criar um Superusuário](#6-criar-um-superusu%C3%A1rio-opcional-mas-recomendado)
    8.  [Rodar o Servidor de Desenvolvimento](#7-rodar-o-servidor-de-desenvolvimento)
2.  [Documentação dos Endpoints da API](#documenta%C3%A7%C3%A3o-dos-endpoints-da-api)
    1.  [Endpoints da Aplicação `accounts`](#1-endpoints-da-aplica%C3%A7%C3%A3o-accounts)
        1.  [Login de Usuário](#11-login-de-usu%C3%A1rio)
        2.  [Obter Dados do Usuário Logado](#12-obter-dados-do-usu%C3%A1rio-logado)
        3.  [Listar Usuários](#13-listar-usu%C3%A1rios)
        4.  [Criar Novo Usuário](#14-criar-novo-usu%C3%A1rio-apenas-administradores)
        5.  [Mudar Senha do Usuário Autenticado](#15-mudar-senha-do-usu%C3%A1rio-autenticado)
        6.  [Listar Grupos Disponíveis](#16-listar-grupos-dispon%C3%ADveis)
        7.  [Gerenciar Perfil do Usuário](#17-gerenciar-perfil-do-usu%C3%A1rio)
    2.  [Endpoints da Aplicação `salas`](#2-endpoints-da-aplica%C3%A7%C3%A3o-salas)
        1.  [Listar Salas / Criar Nova Sala](#21-listar-salas--criar-nova-sala)
        2.  [Obter Detalhes / Atualizar / Excluir Sala](#22-obter-detalhes--atualizar--excluir-sala-espec%C3%ADfica)
        3.  [Iniciar Limpeza de Sala](#23-iniciar-limpeza-de-sala)
        4.  [Concluir Limpeza de Sala](#24-concluir-limpeza-de-sala)
        5.  [Marcar Sala como Suja](#25-marcar-sala-como-suja)
    3.  [Endpoints da Aplicação `limpezas`](#3-endpoints-da-aplica%C3%A7%C3%A3o-limpezas)
        1.  [Listar Registros de Limpeza](#31-listar-registros-de-limpeza)
3.  [Entendendo Fusos Horários na API](#entendendo-fusos-hor%C3%A1rios-na-api-ultima_limpeza_data_hora)
    1.  [Por que UTC?](#por-que-utc)
    2.  [O Que é Necessário Ficar Atento no Frontend](#o-que-%C3%A9-necess%C3%A1rio-ficar-atento-no-frontend-react-native--typescript)

## Ambiente de Desenvolvimento

Siga os passos abaixo para configurar e executar o projeto em seu ambiente local. É altamente recomendado usar um ambiente virtual (`venv`) para isolar as dependências do projeto.

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

Este projeto utiliza a biblioteca `python-decouple` para gerenciar variáveis de ambiente, mantendo configurações sensíveis (como `SECRET_KEY`) e variáveis de ambiente (como `DEBUG`, `TIME_ZONE`) fora do código-fonte e do controle de versão.

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

O projeto utiliza SQLite por padrão, o que não requer configurações adicionais de banco de dados no `settings.py` além do padrão do Django.

Aplique as migrações para criar as tabelas no banco de dados:

```bash
python manage.py makemigrations
# Eventaulmente pode ser necessário forcar indicar as aplicações manualmente: 
# python manage.py makemigrations accounts salas

python manage.py migrate
```

### 6\. Criar um Superusuário (Opcional, mas Recomendado)

Um superusuário é necessário para acessar o painel de administração do Django e criar outros usuários administrativos ou funcionários.

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

### **Base URL:** `http://127.0.0.1:8000/api/`

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
      * **`200 OK` (Sucesso):** Retorna o objeto completo do usuário, similar ao `user_data` do login.
      * **`401 Unauthorized` (Erro):** Ocorre se o token não for fornecido ou for inválido.

#### 1.3. Listar Usuários

  * **Proposta:** Retorna uma lista de todos os usuários cadastrados no sistema, com suporte a filtros avançados.
  * **Permissões:** Apenas administradores (`is_superuser=True`).
  * **Requisição:**
      * **Verbo HTTP:** `GET`
      * **URI:** `/api/accounts/list_users/`
      * **Headers:** `Authorization: Token SEU_TOKEN_DE_ADMIN_AQUI`
  * **Filtros (Query Parameters):**
      * **`username`** (string): Busca parcial (case-insensitive) por nome de usuário.
          * **Exemplo:** `/api/accounts/list_users/?username=admin`
      * **`email`** (string): Busca parcial (case-insensitive) por e-mail.
          * **Exemplo:** `/api/accounts/list_users/?email=@example.com`
      * **`is_superuser`** (boolean): Filtra por status de superusuário (`true` ou `false`).
          * **Exemplo:** `/api/accounts/list_users/?is_superuser=true`
      * **`group`** (string): Filtra por nome exato do grupo (case-insensitive).
          * **Exemplo:** `/api/accounts/list_users/?group=Zeladoria`
  * **Respostas:**
      * **`200 OK` (Sucesso):** Retorna um array de objetos de usuário.
      * **`403 Forbidden` (Erro):** Ocorre se o usuário não for um administrador.

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
            "user": { "... objeto do novo usuário ..." },
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
      * **`200 OK` (Sucesso):** `{"message": "Senha alterada com sucesso."}`
      * **`400 Bad Request` (Erro):** Ocorre se a senha antiga está incorreta, as novas não coincidem ou a nova senha é fraca.

#### 1.6. Listar Grupos Disponíveis

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
      * **Ver Perfil:** `GET /api/accounts/profile/`
      * **Atualizar Perfil:** `PUT` ou `PATCH` para `/api/accounts/profile/`
          * **Headers:** `Authorization: Token SEU_TOKEN_AQUI`
          * **Body (Multipart Form-data):** Para enviar uma imagem, a requisição deve ser do tipo `multipart/form-data`.
              * Campo `nome` (texto): `Novo Nome Completo`
              * Campo `profile_picture` (arquivo): Selecionar o arquivo de imagem.
  * **Resposta (`200 OK`):**
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
  * **Verbos HTTP:** `GET`, `POST`
  * **Permissões:** `GET` (Qualquer autenticado), `POST` (Apenas administradores).
  * **Filtros (`GET` - Query Parameters):**
      * **`ativa`** (boolean): Filtra por salas ativas (`true`) ou inativas (`false`).
          * **Exemplo:** `/api/salas/?ativa=true`
      * **`nome_numero`** (string): Busca parcial (case-insensitive) por nome ou número da sala.
          * **Exemplo:** `/api/salas/?nome_numero=Auditório`
      * **`localizacao`** (string): Busca parcial (case-insensitive) por localização.
          * **Exemplo:** `/api/salas/?localizacao=Bloco`
      * **`capacidade_min`** (integer): Filtra por salas com capacidade maior ou igual ao valor informado.
          * **Exemplo:** `/api/salas/?capacidade_min=50`
      * **`capacidade_max`** (integer): Filtra por salas com capacidade menor ou igual ao valor informado.
          * **Exemplo:** `/api/salas/?capacidade_max=100`
      * **`responsavel_username`** (string): Busca parcial (case-insensitive) pelo nome de usuário de um dos responsáveis.
          * **Exemplo:** `/api/salas/?responsavel_username=zelador`
  * **Requisição (`POST`):**
      * **Headers:** `Authorization: Token SEU_TOKEN_DE_ADMIN_AQUI`, `Content-Type: application/json`
      * **Body:**
        ```json
        {
            "nome_numero": "Laboratório de Redes",
            "capacidade": 25,
            "validade_limpeza_horas": 8,
            "localizacao": "Bloco C, Sala 203",
            "descricao": "Laboratório com equipamentos Cisco.",
            "instrucoes": "Limpar bancadas e organizar cabos.",
            "ativa": true,
            "responsaveis": [2]
        }
        ```
  * **Resposta (`200 OK` para `GET`, `201 Created` para `POST`):** Retorna o objeto (ou lista de objetos) da sala.

#### 2.2. Obter Detalhes / Atualizar / Excluir Sala Específica

  * **URI:** `/api/salas/{qr_code_id}/`
  * **Verbos HTTP:** `GET`, `PUT`, `PATCH`, `DELETE`
  * **Permissões:** `GET` (Qualquer autenticado), `PUT/PATCH/DELETE` (Apenas administradores).

#### 2.3. Iniciar Limpeza de Sala

  * **Proposta:** Cria um registro para marcar o **início** de uma sessão de limpeza. O status da sala muda para "Em Limpeza".
  * **Permissões:** Apenas usuários do grupo ***Zeladoria***.
  * **Requisição:**
      * **Verbo HTTP:** `POST`
      * **URI:** `/api/salas/{qr_code_id}/iniciar_limpeza/`
      * **Headers:** `Authorization: Token SEU_TOKEN_DE_ZELADOR_AQUI`
  * **Respostas:**
      * **`201 Created` (Sucesso):** Retorna o objeto `LimpezaRegistro` criado.
      * **`400 Bad Request` (Erro):** Ocorre se a sala está inativa ou se já existe uma limpeza em andamento para ela.
        ```json
        {
            "detail": "Esta sala já está em processo de limpeza."
        }
        ```

#### 2.4. Concluir Limpeza de Sala

  * **Proposta:** Encontra a sessão de limpeza em aberto para a sala e registra o **horário de conclusão**. O status da sala muda para "Limpa".
  * **Permissões:** Apenas usuários do grupo ***Zeladoria***.
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
      * **`200 OK` (Sucesso):** Retorna o objeto `LimpezaRegistro` atualizado.
      * **`400 Bad Request` (Erro):** Ocorre se a sala está inativa ou se nenhuma limpeza foi iniciada.

#### 2.5. Marcar Sala como Suja

  * **Proposta:** Cria um relatório de que uma sala está suja, alterando seu status para "Suja" e sobrepondo o status de "Limpa".
  * **Permissões:** Apenas usuários do grupo ***Solicitante de Serviços***.
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
            "status": "Relatório de sala suja enviado com sucesso.",
            "id_relatorio": 1
        }
        ```
      * **`400 Bad Request` (Erro):** Ocorre se a sala reportada estiver inativa.
      * **`403 Forbidden` (Erro):** Ocorre se o usuário não pertencer ao grupo `Solicitante de Serviços`.

-----

### 3\. Endpoints da Aplicação `limpezas`

Endpoints de apenas leitura para consultar o histórico de limpezas.

#### 3.1. Listar Registros de Limpeza

  * **Proposta:** Recupera uma lista de todos os registros históricos de limpeza, com filtros avançados.
  * **Permissões:** Apenas administradores (`is_superuser=True`).
  * **Requisição:**
      * **Verbo HTTP:** `GET`
      * **URI:** `/api/limpezas/`
      * **Headers:** `Authorization: Token SEU_TOKEN_DE_ADMIN_AQUI`
  * **Filtros (Query Parameters):**
      * **`sala`** (integer): Filtra os registros pelo ID exato da sala.
          * **Exemplo:** `/api/limpezas/?sala=5`
      * **`sala_nome`** (string): Busca textual parcial (case-insensitive) pelo nome da sala.
          * **Exemplo:** `/api/limpezas/?sala_nome=Teórica`
      * **`funcionario_username`** (string): Busca textual parcial (case-insensitive) pelo nome de usuário do funcionário.
          * **Exemplo:** `/api/limpezas/?funcionario_username=zelador`
      * **`data_hora_limpeza_after`** (date): Filtra registros a partir da data informada (formato `YYYY-MM-DD`).
          * **Exemplo:** `/api/limpezas/?data_hora_limpeza_after=2025-09-10`
      * **`data_hora_limpeza_before`** (date): Filtra registros até a data informada (formato `YYYY-MM-DD`).
          * **Exemplo:** `/api/limpezas/?data_hora_limpeza_after=2025-09-01&data_hora_limpeza_before=2025-09-15`
  * **Respostas:**
      * **`200 OK` (Sucesso):** Retorna um array de objetos `LimpezaRegistro`.
      * **`403 Forbidden` (Erro):** Ocorre se o usuário não for um administrador.

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