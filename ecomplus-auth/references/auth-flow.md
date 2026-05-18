# E-Com Plus — Fluxo de Autenticação (referência técnica)

Carregado sob demanda pelo SKILL.md quando for implementar, debugar ou estender o fluxo de auth.

## Visão geral

A autenticação da E-Com Plus funciona em dois passos:

```
1. POST /_login.json          → troca email+senha por {store_id, my_id, api_key}
2. POST /_authenticate.json   → troca {my_id, api_key} por {access_token, expires}
```

O `api_key` é permanente (equivalente a um refresh token). O `access_token` é um JWT que expira em ~1h. Para renovar o token basta repetir o passo 2.

## Passo 1 — Login com email ou username

```
POST https://api.e-com.plus/v1/_login.json
Headers:
  X-Store-ID: 1        ← sempre 1 nesta etapa
  Content-Type: application/json; charset=UTF-8

Body (com email):
  { "email": "user@example.com", "pass_md5_hash": "<md5(senha)>" }

Body (com username — acrescenta ?username=<x> na URL):
  { "username": "meu_usuario", "pass_md5_hash": "<md5(senha)>" }
  URL: /_login.json?username=meu_usuario
```

**Resposta de sucesso (200):**
```json
{
  "store_id": 1011,
  "_id": "5ae...abc",
  "api_key": "eyJ...longkey..."
}
```

**Nota:** a senha é enviada como MD5 hex lowercase. Em Python: `hashlib.md5(senha.encode()).hexdigest()`.

## Passo 2 — Autenticar (obter JWT)

```
POST https://api.e-com.plus/v1/_authenticate.json
Headers:
  X-Store-ID: <store_id>
  Content-Type: application/json; charset=UTF-8

Body:
  { "_id": "<my_id>", "api_key": "<api_key>" }
```

**Resposta de sucesso (200):**
```json
{
  "my_id": "5ae...abc",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires": "2026-05-18T16:00:00.000Z"
}
```

## Shortcut — Login direto com api_key (sem senha)

Quando você já tem `store_id`, `my_id` e `api_key` armazenados, pule o passo 1 e vá direto para o passo 2. Isso é o que o painel admin faz quando detecta que o campo "senha" tem 128+ caracteres e o campo "usuário" está no formato `storeId:myId`.

```python
# Em login.py, --store-id + --my-id + --api-key ativam esse atalho
auth_data = call_authenticate(store_id, my_id, api_key, base_url)
```

## Usando o token nas requests

Todo endpoint autenticado exige os 3 headers:

```
X-Store-ID: <store_id>
X-Access-Token: <access_token>
X-My-ID: <my_id>
```

O `ecomplus_client.py` da `ecomplus-reports` já configura esses headers automaticamente via `EcomplusClient.from_env()`. Para as demais skills, o padrão é o mesmo.

## Refresh — renovar o access_token

Não existe um endpoint específico de refresh. Basta repetir o passo 2 com o mesmo `my_id` e `api_key`:

```python
auth_data = call_authenticate(store_id, my_id, api_key, base_url)
# Salva o novo access_token + expires
```

O `refresh.py` faz exatamente isso, lendo `my_id` e `api_key` do `~/.ecomplus_session.json`.

## Verificar autenticação / dados do usuário

```
GET https://api.e-com.plus/v1/authentications/{my_id}.json
Headers: X-Store-ID, X-My-ID, X-Access-Token
```

Retorna os dados da autenticação: `username`, `name`, `main_email`, `flags`, `panel_preferences`, etc.

Útil para:
- Confirmar que o token ainda é válido (se retornar 200, está OK; 401 = expirado)
- Verificar se o usuário tem 2FA ativo (`panel_preferences.totp_enabled` + flag `totp:...`)

## 2FA (TOTP)

O painel admin verifica 2FA após o passo 2:

1. Chama `GET /authentications/{my_id}.json`
2. Se `panel_preferences.totp_enabled == true` e existe uma flag `totp:<base32secret>`, exige código TOTP
3. Valida o código localmente com a lib TOTP (janela de ±1 período de 30s)
4. Se válido, prossegue; caso contrário, bloqueia

Os scripts desta skill **não implementam 2FA** — fluxo pensado para contas de serviço/automação sem 2FA ativo. Para contas com 2FA, o usuário deve fazer login pelo painel e extrair o `access_token` e `api_key` manualmente (ou via SSO).

## Sandbox

Mesmas rotas, base URL diferente:

```
https://sandbox.e-com.plus/v1/_login.json
https://sandbox.e-com.plus/v1/_authenticate.json
```

Dados do sandbox são resetados a cada 7 dias. Use contas separadas das de produção.

## Erros da API de auth

```json
{
  "status": 401,
  "error_code": 401,
  "message": "Invalid authentication token",
  "user_message": {
    "en_us": "Login or password is incorrect",
    "pt_br": "Login ou senha incorretos"
  }
}
```

Sempre exiba `user_message.pt_br` para o usuário, nunca o campo `message` técnico.

| Status | Significado |
|---|---|
| `401` no login | Senha errada ou usuário não encontrado |
| `401` no authenticate | `api_key` inválida ou revogada |
| `401` em outros endpoints | `access_token` expirado → chamar `refresh.py` |
| `403` em outros endpoints | `store_id` não corresponde ao token |

## Armazenamento local da sessão

Arquivo: `~/.ecomplus_session.json` (permissões 600)

```json
{
  "store_id": "1011",
  "my_id": "5ae...abc",
  "api_key": "longa_api_key_permanente...",
  "access_token": "eyJhbGci...jwt_curto_vivo...",
  "expires": "2026-05-18T16:00:00.000Z",
  "username": "usuario@exemplo.com"
}
```

Este arquivo **nunca deve ser commitado**. Ele fica em `~/` e não entra no repositório.
