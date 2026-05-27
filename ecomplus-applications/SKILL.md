---
name: ecomplus-applications
description: >
  Use esta skill para listar, inspecionar e configurar aplicativos instalados
  na loja E-Com Plus. Cobre: listar apps, ver configuração (data/hidden_data),
  atualizar configuração de um app, e consultar logs de auditoria (changelog de
  recursos). Palavras-chave: aplicativo, app, integração, configuração, data,
  hidden_data, logs, auditoria, changelog, marketplace, módulo instalado.
prerequisites:
  - name: ecomplus-auth
    reason: Credenciais (ECOMPLUS_STORE_ID, ECOMPLUS_ACCESS_TOKEN, ECOMPLUS_MY_ID)
---

# ecomplus-applications

Gerencia aplicativos instalados na loja e logs de auditoria da API.

## Pré-requisitos

| Item | Como obter |
|---|---|
| `ECOMPLUS_STORE_ID` | `ecomplus-auth/scripts/login.py` ou `--export` |
| `ECOMPLUS_ACCESS_TOKEN` | idem |
| `ECOMPLUS_MY_ID` | idem |

Se as env vars não estiverem setadas, os scripts leem `~/.ecomplus_session.json`
automaticamente.

## Scripts disponíveis

| Script | O que faz | Exemplo rápido |
|---|---|---|
| `list_apps.py` | Lista todos os apps instalados | `python list_apps.py` |
| `get_app.py` | Detalhe completo de um app (data + hidden_data) | `python get_app.py --id <id>` |
| `update_app.py` | Atualiza `data` ou `hidden_data` de um app | `python update_app.py --id <id> --key foo --value bar` |
| `get_logs.py` | Logs de auditoria de um recurso | `python get_logs.py --resource-id <id>` |

## Casos de uso comuns

### Listar todos os apps instalados

```bash
python list_apps.py
python list_apps.py --state active
python list_apps.py --app-id 124890          # filtrar por app_id do marketplace
python list_apps.py --format json
```

### Inspecionar configuração de um app

```bash
python get_app.py --id 5cf...abc             # por _id do documento
python get_app.py --app-id 124890            # pelo app_id do marketplace
python get_app.py --app-id 124890 --show-hidden   # inclui hidden_data
```

### Atualizar configuração (data)

```bash
# Setar uma chave simples
python update_app.py --id 5cf...abc --key access_token --value "tok_xxx"

# Enviar JSON completo (substitui toda a chave)
python update_app.py --id 5cf...abc --json-file new_data.json

# Atualizar hidden_data (credenciais)
python update_app.py --id 5cf...abc --hidden --key api_secret --value "s3cr3t"
```

### Consultar logs de auditoria

```bash
python get_logs.py --resource-id 5cf...abc           # logs de um pedido/produto/etc.
python get_logs.py --resource-id 5cf...abc --limit 20
python get_logs.py --log-id abc123                   # detalhe de uma entrada
```

## Campos principais do documento de aplicativo

Ver `references/app-fields.md` para schema completo.

- `_id` → ID do documento da aplicação instalada
- `app_id` → ID numérico do app no marketplace
- `title` → nome do app
- `state` → `active` | `paused`
- `data` → configuração pública (pode ser lida por módulos externos)
- `hidden_data` → credenciais/segredos (somente leitura autenticada)

## Campos de log (`@logs`)

- `id` → ID da entrada de log
- `date_time` → data/hora UTC
- `method` → `GET` | `POST` | `PATCH` | `DELETE` | `PUT`
- `api_resource` → endpoint acessado
- `ip_addr` → IP de origem (prefixo `127.9` = chamada interna de app)
- `authentication_id` → ID de quem fez a chamada

## Referências carregadas sob demanda

- `references/app-fields.md` — schema completo, exemplos de PATCH

## Erros comuns

| Código | Causa | Solução |
|---|---|---|
| `401` | Token expirado | `eval $(python ecomplus-auth/scripts/refresh.py --export)` |
| `403` | Sem permissão para `hidden_data` | Verificar credenciais; `hidden_data` requer admin |
| `404` | App não encontrado | Confirmar `_id` ou `app_id` correto |

## Formato de saída

Todos os scripts aceitam `--format md` (padrão), `--format csv` e `--format json`.
Use `--sandbox` para rodar contra `https://sandbox.e-com.plus/v1/`.
