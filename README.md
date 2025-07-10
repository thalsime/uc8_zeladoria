# Sistema de Mapeamento da Limpeza de Salas (API RESTful)

Este é o backend do Sistema de Mapeamento da Limpeza de Salas, desenvolvido com Django e Django REST Framework. Ele fornece uma API RESTful para gerenciar salas, registrar suas limpezas e autenticar usuários da equipe de zeladoria. O foco do projeto é otimizar o fluxo de trabalho da equipe de limpeza e fornecer informações atualizadas sobre a disponibilidade de salas limpas, solucionando ineficiências no gerenciamento manual da limpeza de salas no SENAC.

## Ambiente de Desenvolvimento

Siga os passos abaixo para configurar e executar o projeto em seu ambiente local. É altamente recomendado usar um ambiente virtual (`venv`) para isolar as dependências do projeto.

### Pré-requisitos

  * Python 3.8+
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
python manage.py runserver
```

O servidor estará rodando em `http://127.0.0.1:8000/`. Você pode acessar o painel de administração em `http://127.0.0.1:8000/admin/`.

## Documentação dos Endpoints da API

A API é composta por endpoints para gerenciamento de contas de usuário e gerenciamento de salas/registros de limpeza.

### **Base URL:** `http://127.0.0.1:8000/api/`

-----

### 1. Endpoints da Aplicação `accounts`

Gerencia a autenticação de usuários e a criação de novas contas.

#### 1.1. Login de Usuário

  * **URI:** `/api/accounts/login/`
  * **Verbos HTTP:** `POST`
  * **Proposta:** Autentica um usuário no sistema e retorna um token de autenticação (Token Auth do DRF) para ser usado em requisições subsequentes, além dos dados básicos do usuário logado.
  * **Headers Necessários:**
      * `Content-Type: application/json`
  * **Body JSON (Obrigatório):**
    ```json
    {
        "username": "seu_nome_de_usuario", // string: Nome de usuário válido.
        "password": "sua_senha"            // string: Senha do usuário.
    }
    ```
  * **Exemplo de Resposta de Sucesso (Status 200 OK):**
    ```json
    {
        "username": "seu_nome_de_usuario",
        "password": "sua_senha",
        "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
        "user_data": {
            "id": 1,
            "username": "seu_nome_de_usuario",
            "email": "email@example.com",
            "is_staff": false,
            "is_superuser": false
        }
    }
    ```

#### 1.2. Obter Dados do Usuário Logado

  * **URI:** `/api/accounts/current_user/`
  * **Verbos HTTP:** `GET`
  * **Proposta:** Permite que um cliente autenticado recupere as informações do usuário associado ao token de autenticação.
  * **Headers Necessários:**
      * `Authorization: Token SEU_TOKEN_AQUI` (substitua `SEU_TOKEN_AQUI` pelo token obtido no login).
  * **Body JSON:** Não necessário.
  * **Exemplo de Resposta de Sucesso (Status 200 OK):**
    ```json
    {
        "id": 1,
        "username": "seu_nome_de_usuario",
        "email": "email@example.com",
        "is_staff": true,
        "is_superuser": false
    }
    ```

#### 1.3. Criar Novo Usuário (Apenas Administradores)

  * **URI:** `/api/accounts/create_user/`
  * **Verbos HTTP:** `POST`
  * **Proposta:** Permite que um usuário com privilégios de administrador (`is_staff=True` ou `is_superuser=True`) crie novas contas de usuário no sistema.
  * **Headers Necessários:**
      * `Authorization: Token SEU_TOKEN_DE_ADMIN_AQUI` (Token de um usuário administrador).
      * `Content-Type: application/json`
  * **Body JSON (Obrigatório):**
      * **Estrutura Obrigatória:**
        ```json
        {
            "username": "novo_nome_de_usuario",   // string: Nome de usuário único.
            "password": "senha_segura",            // string: Senha para o novo usuário.
            "confirm_password": "senha_segura"     // string: Confirmação da senha (deve ser idêntica a 'password').
        }
        ```
      * **Estrutura Opcional:**
        ```json
        {
            "email": "email_novo@example.com",     // string: E-mail do usuário (opcional, pode ser vazio).
            "is_staff": false,                     // boolean: Define se o usuário terá acesso ao admin (padrão: false).
            "is_superuser": false                  // boolean: Define se o usuário será um superusuário (padrão: false).
        }
        ```
  * **Exemplo de Resposta de Sucesso (Status 201 Created):**
    ```json
    {
        "message": "Usuário criado com sucesso.",
        "user": {
            "id": 2,
            "username": "novo_nome_de_usuario",
            "email": "email_novo@example.com",
            "is_staff": false,
            "is_superuser": false
        },
        "token": "x9y8z7w6v5u4t3s2r1q0p9o8n7m6l5k4j3i2h1g0"
    }
    ```

#### 1.4. Mudar Senha do Usuário Autenticado

  * **URI:** `/api/accounts/change_password/`
  * **Verbos HTTP:** `POST`
  * **Proposta:** Permite que um usuário autenticado altere sua própria senha, exigindo a senha antiga para validação.
  * **Headers Necessários:**
      * `Authorization: Token SEU_TOKEN_AQUI` (Token do usuário que está mudando a senha).
      * `Content-Type: application/json`
  * **Body JSON (Obrigatório):**
    ```json
    {
        "old_password": "sua_senha_antiga",      // string: A senha atual do usuário.
        "new_password": "sua_nova_senha",         // string: A nova senha desejada.
        "confirm_new_password": "sua_nova_senha"  // string: Confirmação da nova senha (deve ser idêntica a 'new_password').
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

-----

### 2. Endpoints da Aplicação `salas`

Gerencia as informações sobre as salas e seus registros de limpeza.

#### 2.1. Listar Salas / Criar Nova Sala

  * **URI:** `/api/salas/`
  * **Verbos HTTP:** `GET`, `POST`
  * **Proposta:**
      * `GET`: Recupera uma lista de todas as salas cadastradas no sistema.
      * `POST`: Cria um novo registro de sala no banco de dados.
  * **Headers Necessários (`GET`):**
      * `Authorization: Token SEU_TOKEN_AQUI` (Para qualquer usuário autenticado).
  * **Headers Necessários (`POST`):**
      * `Authorization: Token SEU_TOKEN_DE_ADMIN_AQUI` (Apenas token de usuário administrador).
      * `Content-Type: application/json`
  * **Body JSON (`GET`):** Não necessário.
  * **Body JSON (`POST` - Obrigatório):**
    ```json
    {
        "nome_numero": "Sala 101",             // string: Nome ou número único da sala.
        "capacidade": 30,                      // integer: Capacidade máxima de pessoas da sala.
        "descricao": "Uma descrição rápiada das principais atviidades realizadas na sala.", // string: Descrição detalhada da sala.
        "localizacao": "Bloco A"               // string: Localização física da sala.
    }
    ```
  * **Exemplo de Resposta de Sucesso (`GET` - Status 200 OK):**
    ```json
    [
        {
            "id": 1,
            "nome_numero": "Sala 101",
            "capacidade": 30,
            "descricao": "Uma descrição rápiada das principais atviidades realizadas na sala.",
            "localizacao": "Bloco A",
            "status_limpeza": "Limpa",
            "ultima_limpeza_data_hora": "2025-07-09T12:00:00Z",
            "ultima_limpeza_funcionario": "funcionariocz"
        },
        {
            "id": 2,
            "nome_numero": "Laboratório de Informática",
            "capacidade": 20,
            "descricao": "Sala equipada com computadores para aulas práticas.",
            "localizacao": "Bloco B",
            "status_limpeza": "Limpeza Pendente",
            "ultima_limpeza_data_hora": null,
            "ultima_limpeza_funcionario": null
        }
    ]
    ```
  * **Exemplo de Resposta de Sucesso (`POST` - Status 201 Created):**
    ```json
    {
        "id": 3,
        "nome_numero": "Sala de Reuniões",
        "capacidade": 10,
        "descricao": "Sala pequena para reuniões rápidas.",
        "localizacao": "Prédio Principal",
        "status_limpeza": "Limpeza Pendente",
        "ultima_limpeza_data_hora": null,
        "ultima_limpeza_funcionario": null
    }
    ```

#### 2.2. Obter Detalhes / Atualizar / Excluir Sala Específica

  * **URI:** `/api/salas/{id}/` (onde `{id}` é o ID numérico da sala)
  * **Verbos HTTP:** `GET`, `PUT`, `PATCH`, `DELETE`
  * **Proposta:**
      * `GET`: Recupera os detalhes de uma sala específica.
      * `PUT`: Atualiza *todos* os campos de uma sala existente.
      * `PATCH`: Atualiza *parcialmente* os campos de uma sala existente.
      * `DELETE`: Exclui uma sala específica.
  * **Headers Necessários (`GET`, `PUT`, `PATCH`, `DELETE`):**
      * `Authorization: Token SEU_TOKEN_AQUI` (Para qualquer usuário autenticado com `GET`).
      * `Authorization: Token SEU_TOKEN_AQUI` (Apenas token de usuário administrador com `PUT`, `PATCH`, `DELETE`).
      * `Content-Type: application/json` (Apenas para `PUT` e `PATCH`).
  * **Body JSON (`GET`, `DELETE`):** Não necessário.
  * **Body JSON (`PUT` - Obrigatório):**
      * A estrutura é a mesma do `POST /api/salas/`, mas *todos* os campos são obrigatórios.
  * **Body JSON (`PATCH` - Opcional):**
      * Pode conter *qualquer subconjunto* dos campos de `POST /api/salas/`.
      * **Exemplo (`PATCH` para atualizar apenas a capacidade):**
        ```json
        {
            "capacidade": 35
        }
        ```
  * **Exemplo de Resposta de Sucesso (`GET` - Status 200 OK):**
      * Mesma estrutura da resposta de `POST /api/salas/`.
  * **Exemplo de Resposta de Sucesso (`PUT`/`PATCH` - Status 200 OK):**
      * Mesma estrutura da resposta de `POST /api/salas/`, mas com os dados atualizados.
  * **Exemplo de Resposta de Sucesso (`DELETE` - Status 204 No Content):**
      * Nenhum conteúdo no corpo da resposta.

#### 2.3. Marcar Sala como Limpa

  * **URI:** `/api/salas/{id}/marcar_como_limpa/` (onde `{id}` é o ID numérico da sala)
  * **Verbos HTTP:** `POST`
  * **Proposta:** Registra que uma sala específica foi limpa pelo funcionário autenticado, criando um novo `LimpezaRegistro`.
  * **Headers Necessários:**
      * `Authorization: Token SEU_TOKEN_AQUI` (Para qualquer usuário autenticado).
      * `Content-Type: application/json`
  * **Body JSON (Opcional):**
      * Pode ser um objeto JSON vazio `{}` ou conter o campo `observacoes`.
      * **Estrutura Opcional:**
        ```json
        {
            "observacoes": "Limpeza realizada com atenção aos detalhes, janelas abertas." // string: Observações adicionais.
        }
        ```
  * **Exemplo de Resposta de Sucesso (Status 201 Created):**
    ```json
    {
        "id": 10,
        "sala": 1,
        "sala_nome": "Sala 101",
        "data_hora_limpeza": "2025-07-09T13:15:30.123456Z",
        "funcionario_responsavel": {
            "id": 1,
            "username": "funcionariocz"
        },
        "observacoes": "Limpeza realizada com atenção aos detalhes, janelas abertas."
    }
    ```

-----

## Entendendo Fusos Horários na API (`ultima_limpeza_data_hora`)

Um ponto crucial para o consumo desta API, especialmente em aplicações front-end como React Native, é a propriedade `ultima_limpeza_data_hora`.

### Por que UTC?

A API retorna todos os timestamps (especificamente `ultima_limpeza_data_hora` e `data_hora_limpeza` nos registros) no formato **UTC (Coordinated Universal Time)** e como strings **ISO 8601** (ex: `"2025-07-09T12:00:00Z"`).

  * **Universalidade:** UTC é um padrão global de tempo, independente de qualquer fuso horário local. Isso garante que o ponto no tempo transmitido pela API é sempre o mesmo, não importa onde o servidor esteja rodando ou de onde a requisição foi feita.
  * **Precisão:** Evita ambiguidades e erros comuns de fuso horário que podem surgir ao converter entre diferentes fusos ou ao lidar com horários de verão.

### O Que é Necessário Ficar Atento no Frontend (React Native + TypeScript)

Como o backend está enviando os horários em UTC, a responsabilidade de convertê-los e exibi-los no fuso horário *local do usuário* (ou em qualquer outro fuso desejado) é do aplicativo cliente.

Aqui está um exemplo de como você faria isso no seu aplicativo React Native com TypeScript, utilizando bibliotecas como `date-fns` ou a API nativa `Date` do JavaScript, que são excelentes para essa tarefa:

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
  capacidade: number;
  descricao: string;
  localizacao: string;
  status_limpeza: string;
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
      // `parseISO` de date-fns é ótimo para isso, pois entende o formato 'Z'.
      const dateObjectUTC = parseISO(utcDateTimeString);

      // 2. Conversão de Fuso Horário e 3. Formatação:
      // `format` de date-fns, por padrão, formata para o fuso horário local do dispositivo
      // onde o código está sendo executado.
      return format(dateObjectUTC, "dd/MM/yyyy 'às' HH:mm:ss", { locale: ptBR });

    } catch (error) {
      console.error("Erro ao processar data/hora:", error);
      return "Data Inválida";
    }
  };

  return (
    <View style={styles.card}>
      <Text style={styles.title}>{sala.nome_numero}</Text>
      <Text>Capacidade: {sala.capacidade}</Text>
      <Text>Localização: {sala.localizacao}</Text>
      <Text>Status: {sala.status_limpeza}</Text>
      <Text>
        Última Limpeza: {displayLastCleanedTime(sala.ultima_limpeza_data_hora)}
      </Text>
      {sala.ultima_limpeza_funcionario && (
        <Text>Por: {sala.ultima_limpeza_funcionario}</Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    padding: 15,
    marginVertical: 8,
    marginHorizontal: 16,
    borderRadius: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 5,
  },
});

export default SalaCard;
```

### Pontos Chave para o Frontend:

  * **`parseISO` (ou `new Date()`):** A função que irá converter a string ISO 8601 em um objeto `Date` manipulável. Ela já entende o sufixo `Z` para UTC.
  * **Fuso Horário Local:** Por padrão, quando você usa métodos como `format` de `date-fns` (ou `toLocaleString` do `Date` nativo), eles exibirão a data/hora no fuso horário configurado no **dispositivo do usuário**. Isso é geralmente o que se deseja para a maioria das aplicações móveis.
  * **Fusos Horários Específicos:** Se você precisar exibir o horário em um fuso horário *diferente* do local do dispositivo (ex: sempre no fuso horário de Brasília, independentemente de onde o usuário esteja), você precisará de bibliotecas como `date-fns-tz` ou `moment-timezone`.
  * **Tratamento de `null`:** Lembre-se que `ultima_limpeza_data_hora` pode vir como `null` se a sala nunca foi limpa. Seu código frontend deve lidar com essa possibilidade.

-----

## Próximos Passos e Melhorias Futuras

Este projeto é uma base para um Sistema de Mapeamento da Limpeza de Salas. Ele ainda será aprimorado e novos recursos serão adicionados para otimizar ainda mais o gerenciamento da zeladoria e a experiência do usuário.
