---
name: ecomplus-auth
description: Use esta skill SEMPRE que o usuário precisar se autenticar na E-Com Plus, fazer login, obter ou renovar token de acesso, configurar credenciais, ou quando outra skill retornar erro 401/403 por token expirado. Gatilhos: "fazer login", "me autenticar", "token expirado", "erro 401", "erro 403", "meu token", "renovar token", "refresh token", "credenciais", "configurar acesso", "store_id", "api_key", "ECOMPLUS_ACCESS_TOKEN", "ECOMPLUS_STORE_ID", "ECOMPLUS_MY_ID", "sessão expirada", "não consigo acessar a API". Também use antes de qualquer outra skill se as env vars estiverem ausentes ou inválidas.
---

# E-Com Plus — Autenticação

Gerencia o ciclo de vida de autenticação na API REST da E-Com Plus: login, obtenção de token JWT, refresh e exposição das 3 variáveis de ambiente que todas as outras skills precisam.

## Variáveis de ambiente necessárias

Todas as skills deste repositório dependem de:

| Variável | Descrição | Exemplo |
|---|---|---|
| `ECOMPLUS_STORE_ID` | ID numérico da loja | `1011` |
| `ECOMPLUS_ACCESS_TOKEN` | Token JWT de sessão (expira em ~1h) | `eyJhbGci...` |
| `ECOMPLUS_MY_ID` | ID da autenticação (`authentication_id`) | `5ae...abc` |

Se qualquer uma estiver ausente, execute o fluxo de login abaixo **antes** de usar qualquer outra skill.

## Scripts disponíveis

| Script | Função |
|---|---|
| `login.py` | Login com email+senha ou api_key direta. Salva sessão. |
| `refresh.py` | Renova o `access_token` usando a `api_key` salva. |
| `whoami.py` | Mostra informações da sessão atual (loja, usuário, validade do token). |

## Fluxo de login padrão (email + senha)

```bash
# Interativo (pede senha no terminal)
python scripts/login.py --username usuario@exemplo.com

# Não-interativo (para scripts/automação)
eval $(python scripts/login.py --username usuario@exemplo.com --password minhasenha --export)
```

O `--export` imprime apenas `export VAR=val` — ideal para usar com `eval` e definir as env vars na sessão atual.

### Login com API Key (sem senha — automação / service account)

Se você já tem `store_id`, `my_id` e `api_key` armazenados (obtidos em login anterior ou gerados no painel):

```bash
eval $(python scripts/login.py --store-id 1011 --my-id <my_id> --api-key <api_key> --export)
```

## Renovar token expirado (refresh)

O `access_token` expira em ~1 hora. A `api_key` é permanente e fica salva em `~/.ecomplus_session.json`. Para renovar sem redigitar senha:

```bash
# Renovar e já exportar as vars atualizadas
eval $(python scripts/refresh.py --export)
```

**Quando renovar:**
- Outra skill retornou `HTTP 401` com mensagem de token expirado
- `whoami.py` mostrou status "EXPIRADO"
- Proativamente, se `expires` estiver próximo

## Verificar sessão atual

```bash
python scripts/whoami.py
# Mostra: loja, usuário, My ID, validade do token, status
```

Flags: `--format md|json` (default `md`), `--export` (imprime export VAR=val da sessão salva sem chamar a API).

## Onde a sessão é armazenada

Login e refresh salvam em `~/.ecomplus_session.json` (permissões 600). Contém:

- `store_id`, `my_id`, `api_key` — credenciais permanentes (usadas para refresh)
- `access_token`, `expires` — atualizados a cada autenticação
- `username` — para referência humana

**Nunca commitar esse arquivo.** Ele fica em `~/.` e não aparece no repositório.

## Sandbox

Todos os scripts aceitam `--sandbox` para usar `https://sandbox.e-com.plus/v1/` (dados resetados a cada 7 dias):

```bash
python scripts/login.py --username usuario@exemplo.com --sandbox
eval $(python scripts/refresh.py --export --sandbox)
```

## Erros comuns e o que fazer

| Código | Causa | Ação |
|---|---|---|
| `401` | Token expirado ou inválido | Execute `refresh.py` |
| `403` | `store_id` não bate com o token | Refaça o login com o `store_id` correto |
| Login `401` | Senha errada ou usuário inexistente | Verificar credenciais no painel E-Com Plus |
| `api_key` inválida | Credencial revogada | Refaça o login com email+senha |

## Quando ESTA skill NÃO é a certa

- Usuário quer ver **relatórios** → `ecomplus-reports`
- Usuário quer **editar pedidos** → `ecomplus-orders`
- Usuário quer **editar produtos** → `ecomplus-products`
- Usuário quer **configurar a loja** → `ecomplus-stores`

## Referência técnica dos endpoints

Documentação detalhada do fluxo OAuth e dos endpoints em `references/auth-flow.md`.
