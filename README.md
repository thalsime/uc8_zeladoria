# Sistema de Mapeamento da Limpeza de Salas (API RESTful)

Este é o backend do Sistema de Mapeamento da Limpeza de Salas, desenvolvido com Django e Django REST Framework. Ele fornece uma API RESTful para gerenciar salas, registrar suas limpezas e autenticar usuários da equipe de zeladoria. O foco do projeto é otimizar o fluxo de trabalho da equipe de limpeza e fornecer informações atualizadas sobre a disponibilidade de salas limpas, solucionando ineficiências no gerenciamento manual da limpeza de salas no SENAC.

## Ambiente de Desenvolvimento

Siga os passos abaixo para configurar e executar o projeto em seu ambiente local. É altamente recomendado usar um ambiente virtual (`venv`) para isolar as dependências do projeto.

### Pré-requisitos

  * Python 3.12+
  * pip (gerenciador de pacotes do Python)

### 1. Clonar o Repositório

```bash
git clone https://github.com/thalsime/uc8_zeladoria.git
cd uc8_zeladoria # Navegue até a pasta raiz do projeto (onde está manage.py)
```

### 2. Configurar o Ambiente Virtual (venv)

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

### 3. Configurar Variáveis de Ambiente (`.env`)

Este projeto utiliza a biblioteca `python-decouple` para gerenciar variáveis de ambiente, mantendo configurações sensíveis (como `SECRET_KEY`) e variáveis de ambiente (como `DEBUG`, `TIME_ZONE`) fora do código-fonte e do controle de versão.

1.  **Crie um arquivo `.env`:** Na pasta raiz do projeto (a mesma onde está `manage.py` e `.env.sample`), crie um novo arquivo chamado `.env`.
2.  **Copie o conteúdo:** Copie todo o conteúdo do arquivo `.env.sample` para o seu novo arquivo `.env`.
3.  **Ajuste os valores:** Você pode ajustar os valores conforme sua necessidade, por exemplo:
      * `SECRET_KEY`: Uma chave secreta longa e aleatória (essencial para segurança em produção).
      * `DEBUG`: `True` para desenvolvimento, `False` para produção.
      * `TIME_ZONE`: O fuso horário da sua aplicação (ex: `America/Fortaleza` conforme `.env.sample`).

Exemplo do conteúdo do `.env`:

```
SECRET_KEY=uma_grande_string_de_caracteres_aleatorios
DEBUG=True
URI_ADMIN=admin/
LANGUAGE_CODE=pt-br
TIME_ZONE=America/Fortaleza
USE_I18N=True
USE_TZ=True
```

O `settings.py` utiliza a função `config()` da biblioteca `decouple` para ler esses valores, por exemplo: `SECRET_KEY = config("SECRET_KEY")`.

### 4. Instalar as Dependências

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

### 7. Rodar o Servidor de Desenvolvimento

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

### 1. Endpoints da Aplicação `accounts`

Endpoints para autenticação e gerenciamento de usuários.

#### 1.1. Login de Usuário

  * **URI:** `/api/accounts/login/`
  * **Verbos HTTP:** `POST`
  * **Proposta:** Autentica um usuário e retorna um token de autenticação junto com os dados do usuário logado.
  * **Body JSON (Obrigatório):**
    ```json
    {
        "username": "seu_nome_de_usuario",
        "password": "sua_senha"
    }
    ```
  * **Exemplo de Resposta de Sucesso (Status 200 OK):**
    ```json
    {
        "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
        "user_data": {
            "id": 1,
            "username": "seu_nome_de_usuario",
            "email": "email@example.com",
            "is_superuser": false,
            "groups": [
                1
            ],
            "profile": {
                "profile_picture": "[http://127.0.0.1:8000/media/profile_pics/1.jpg](http://127.0.0.1:8000/media/profile_pics/1.jpg)"
            }
        }
    }
    ```

#### 1.2. Obter Dados do Usuário Logado

  * **URI:** `/api/accounts/current_user/`
  * **Verbos HTTP:** `GET`
  * **Proposta:** Permite que um cliente autenticado recupere suas próprias informações.
  * **Headers Necessários:**
      * `Authorization: Token SEU_TOKEN_AQUI`
  * **Exemplo de Resposta de Sucesso (Status 200 OK):**
    ```json
    {
        "id": 1,
        "username": "seu_nome_de_usuario",
        "email": "email@example.com",
        "is_superuser": false,
        "groups": [
            1
        ],
        "profile": {
            "profile_picture": "http://127.0.0.1:8000/media/profile_pics/1.jpg"
        }
    }
    ```

#### 1.3. Listar Usuários

  * **Endpoint:** `GET /api/accounts/list_users/`
  * **Descrição:** Retorna uma lista de todos os usuários cadastrados no sistema.
  * **Permissões:** Apenas administradores (usuários com `is_staff=True`).
  * **Exemplo de Resposta (200 OK):**
    ```json
    [
        {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "is_superuser": true,
            "groups": [],
            "profile": {
                "profile_picture": null
            }
        },
        {
            "id": 2,
            "username": "zelador_a",
            "email": "zelador.a@example.com",
            "is_superuser": false,
            "groups": [
                1
            ],
            "profile": {
                "profile_picture": "http://127.0.0.1:8000/media/profile_pics/2.jpg"
            }
        }
    ]
    ```

#### 1.4. Criar Novo Usuário (Apenas Administradores)

  * **URI:** `/api/accounts/create_user/`
  * **Verbos HTTP:** `POST`
  * **Proposta:** Permite que um usuário com privilégios de administrador (`is_superuser=True`) crie novas contas de usuário no sistema.
  * **Headers Necessários:**
      * `Authorization: Token SEU_TOKEN_DE_ADMIN_AQUI` (Token de um usuário administrador).
      * `Content-Type: application/json`
  * **Body JSON (Obrigatório):**
      * **Estrutura Obrigatória:**
        ```json
        {
            "username": "novo_nome_de_usuario",
            "password": "senha_segura",
            "confirm_password": "senha_segura"
        }
        ```
      * **Estrutura Opcional:**
        ```json
        {
            "email": "email_novo@example.com",
            "is_superuser": false,
            "groups": [1]
        }
        ```
  * **Exemplo de Resposta de Sucesso (Status 201 Created):**
    ```json
    {
        "message": "Usuário criado com sucesso.",
        "user": {
            "id": 3,
            "username": "novo_nome_de_usuario",
            "email": "email_novo@example.com",
            "is_superuser": false,
            "groups": [
                1
            ],
            "profile": {
                "profile_picture": null
            }
        },
        "token": "x9y8z7w6v5u4t3s2r1q0p9o8n7m6l5k4j3i2h1g0"
    }
    ```

#### 1.5. Mudar Senha do Usuário Autenticado

  * **URI:** `/api/accounts/change_password/`
  * **Verbos HTTP:** `POST`
  * **Proposta:** Permite que um usuário autenticado altere sua própria senha, exigindo a senha antiga para validação.
  * **Headers Necessários:**
      * `Authorization: Token SEU_TOKEN_AQUI` (Token do usuário que está mudando a senha).
      * `Content-Type: application/json`
  * **Body JSON (Obrigatório):**
    ```json
    {
        "old_password": "sua_senha_antiga",
        "new_password": "sua_nova_senha",
        "confirm_new_password": "sua_nova_senha"
    }
    ```
  * **Exemplo de Resposta de Sucesso (Status 200 OK):**
    ```json
    {
        "message": "Senha alterada com sucesso."
    }
    ```
  * **Exemplo de Resposta de Erro (Status 400 Bad Request - Ex: senha antiga incorreta):**
    ```json
    {
        "old_password": [
            "A senha antiga está incorreta."
        ]
    }
    ```
  * **Exemplo de Resposta de Erro (Status 400 Bad Request - Ex: novas senhas não coincidem):**
    ```json
    {
        "new_password": [
            "As novas senhas não coincidem."
        ]
    }
    ```
#### 1.6. Listar Grupos Disponíveis

  * **URI:** `/api/accounts/list_groups/`
  * **Verbos HTTP:** `GET`
  * **Proposta:** Retorna uma lista de todos os grupos (papéis) de usuários disponíveis no sistema. Útil para preencher formulários de criação/edição de usuários no front-end.
  * **Permissões:** Qualquer usuário autenticado.
  * **Headers Necessários:**
      * `Authorization: Token SEU_TOKEN_AQUI`
  * **Exemplo de Resposta de Sucesso (Status 200 OK):**
    ```json
    [
        {
            "id": 2,
            "name": "Corpo Docente"
        },
        {
            "id": 1,
            "name": "Zeladoria"
        }
    ]
    ```

#### 1.7. Gerenciar Perfil do Usuário

Permite que um usuário autenticado visualize e atualize seu próprio perfil, incluindo a foto.

  * **URI:** `/api/accounts/profile/`
      * **Verbos HTTP:** `GET`, `PUT`, `PATCH`
      * **Permissões:** Apenas o próprio usuário autenticado.

##### Visualizar Perfil (GET)

  * **Exemplo de Resposta de Sucesso (Status 200 OK):**
    ```json
    {
        "profile_picture": "http://127.0.0.1:8000/media/profile_pics/1.jpg"
    }
    ```

##### Atualizar Perfil (PUT, PATCH)

Para enviar uma foto, a requisição deve ser do tipo `multipart/form-data`.

  * **Corpo da Requisição (Form-data):**
    \* **Chave:** `profile_picture`
    \* **Valor:** O arquivo da imagem (ex: `minha_foto.png`)
      * **Exemplo de Resposta de Sucesso (Status 200 OK):**
        ```json
        {
            "profile_picture": "http://127.0.0.1:8000/media/profile_pics/1.jpg"
        }
        ```

-----

### 2. Endpoints da Aplicação `salas`

Gerencia as informações sobre as salas e seus registros de limpeza.

#### 2.1. Listar Salas / Criar Nova Sala

  * **URI:** `/api/salas/`
  * **Verbos HTTP:** `GET`, `POST`
  * **Proposta:**
      * `GET`: Recupera uma lista de todas as salas cadastradas no sistema.
      * `POST`: Cria um novo registro de sala no banco de dados.
  * **Permissões:**
      * `GET`: Qualquer usuário autenticado.
      * `POST`: Apenas **administradores**.
  * **Headers Necessários:**
      * `Authorization: Token SEU_TOKEN_AQUI` (Para `GET` e `POST`).
      * `Content-Type: application/json` (Apenas para `POST`).
  * **Parâmetros de Query (`GET` - Opcional):**
      * `localizacao` (string): Filtra as salas por uma localização exata (ex: `/api/salas/?localizacao=Bloco A`).
      * `status_limpeza` (string): Filtra as salas pelo status de limpeza. Valores possíveis: `Limpa` ou `Limpeza Pendente` (ex: `/api/salas/?status_limpeza=Limpa`).
  * **Body JSON (`POST` - Obrigatório):**
    ```json
    {
        "nome_numero": "Sala 101",
        "capacidade": 30,
        "validade_limpeza_horas": 4,
        "localizacao": "Bloco A",
        "responsaveis": [1, 5]
    }
    ```
      * `nome_numero` (string, obrigatório): Nome ou número único da sala.
      * `capacidade` (integer, obrigatório): Capacidade máxima de pessoas. Deve ser no mínimo 1.
      * `validade_limpeza_horas` (integer, opcional): Por quantas horas a limpeza é válida. Padrão: 4.
      * `descricao` (string, opcional): Descrição geral sobre a sala.
      * `instrucoes` (string, opcional): Instruções de limpeza para a equipe de zeladoria.
      * `localizacao` (string, obrigatório): Localização física da sala.
      * `responsaveis` (array de integers, opcional): Lista de IDs de usuários do grupo "Zeladoria" responsáveis pela sala.
  * **Exemplo de Resposta de Sucesso (`GET` - Status 200 OK):**
    ```json
    [
        {
            "id": 1,
            "qr_code_id": "c1b3f9a0-3b1a-4b6a-9a0a-0a7d4d3e8c0f",
            "nome_numero": "Sala 101",
            "capacidade": 30,
            "validade_limpeza_horas": 4,
            "descricao": "Sala de aula padrão.",
            "instrucoes": "Limpar o quadro e organizar as carteiras.",
            "localizacao": "Bloco A",
            "ativa": true,
            "responsaveis": [
                {
                    "id": 2,
                    "username": "zelador_a"
                }
            ],
            "status_limpeza": "Limpa",
            "ultima_limpeza_data_hora": "2025-09-10T13:00:00Z",
            "ultima_limpeza_funcionario": "zelador_a"
        }
    ]
    ```

#### 2.2. Obter Detalhes / Atualizar / Excluir Sala Específica

  * **URI:** `/api/salas/{qr_code_id}/`
  * **Verbos HTTP:** `GET`, `PUT`, `PATCH`, `DELETE`
  * **Proposta:**
      * `GET`: Recupera os detalhes de uma sala específica usando seu UUID.
      * `PUT`: Atualiza *todos* os campos de uma sala existente.
      * `PATCH`: Atualiza *parcialmente* os campos de uma sala existente.
      * `DELETE`: Exclui uma sala específica.
  * **Permissões:**
      * `GET`: Qualquer usuário autenticado.
      * `PUT`, `PATCH`, `DELETE`: Apenas administradores.
  * **Headers Necessários:**
      * `Authorization: Token SEU_TOKEN_AQUI`.
      * `Content-Type: application/json` (Apenas para `PUT` e `PATCH`).
  * **Body JSON (`PUT` / `PATCH`):**
      * A estrutura é a mesma do `POST /api/salas/`. `PUT` requer todos os campos, `PATCH` apenas os que serão alterados.
  * **Exemplo (`PATCH` para atualizar os responsáveis):**
    ```json
    {
        "responsaveis": [2, 5]
    }
    ```
  * **Resposta de Sucesso (`DELETE` - Status 204 No Content):**
      * Nenhum conteúdo no corpo da resposta.

#### 2.3. Marcar Sala como Limpa

  * **URI:** `/api/salas/{qr_code_id}/marcar_como_limpa/`
  * **Verbos HTTP:** `POST`
  * **Proposta:** Registra que uma sala específica foi limpa pelo funcionário autenticado, criando um novo `LimpezaRegistro`.
  * **Permissões:** Apenas usuários do grupo ***Zeladoria***.
  * **Headers Necessários:**
      * `Authorization: Token SEU_TOKEN_AQUI`.
      * `Content-Type: application/json`
  * **Body JSON (Opcional):**
    ```json
    {
        "observacoes": "Limpeza realizada com atenção aos detalhes."
    }
    ```
  * **Exemplo de Resposta de Sucesso (Status 201 Created):**
    ```json
    {
        "id": 10,
        "sala": 1,
        "sala_nome": "Sala 101",
        "data_hora_limpeza": "2025-09-10T13:15:30.123456Z",
        "funcionario_responsavel": {
            "id": 2,
            "username": "zelador_a"
        },
        "observacoes": "Limpeza realizada com atenção aos detalhes."
    }
    ```

#### 2.4. Listar Registros de Limpeza

  * **URI:** `/api/limpezas/`
  * **Verbos HTTP:** `GET`
  * **Proposta:** Recupera uma lista de todos os registros históricos de limpeza. Este endpoint é de apenas leitura.
  * **Permissões:** Apenas administradores (`is_superuser=True`).
  * **Headers Necessários:**
      * `Authorization: Token SEU_TOKEN_DE_ADMIN_AQUI`.
  * **Parâmetros de Query (`GET` - Opcional):**
      * `sala_id` (integer): Filtra os registros de limpeza por uma sala específica (ex: `/api/limpezas/?sala_id=1`).
  * **Exemplo de Resposta de Sucesso (`GET` - Status 200 OK):**
    ```json
    [
        {
            "id": 10,
            "sala": 1,
            "sala_nome": "Sala 101",
            "data_hora_limpeza": "2025-09-10T13:15:30.123456Z",
            "funcionario_responsavel": {
                "id": 2,
                "username": "zelador_a"
            },
            "observacoes": "Limpeza realizada com atenção aos detalhes."
        }
    ]
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

-----

## Próximos Passos e Melhorias Futuras

Este projeto é uma base para um Sistema de Mapeamento da Limpeza de Salas. Ele ainda será aprimorado e novos recursos serão adicionados para otimizar ainda mais o gerenciamento da zeladoria e a experiência do usuário.

```