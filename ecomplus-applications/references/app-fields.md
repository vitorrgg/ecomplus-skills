# E-Com Plus — Campos de Aplicativos e Logs

Carregado sob demanda para implementar scripts ou entender a estrutura de apps instalados.

## Estrutura do documento de aplicativo

```json
{
  "_id": "5cf...abc",
  "app_id": 124890,
  "title": "Loyalty Points",
  "state": "active",
  "version": "1.2.0",
  "installed_at": "2024-03-15T10:00:00.000Z",
  "updated_at": "2026-05-01T12:00:00.000Z",
  "data": {
    "programs_rules": [
      {
        "program_id": "p0_pontos",
        "name": "pontos",
        "ratio": 1
      }
    ],
    "exportation": { ... },
    "importation": { ... }
  },
  "hidden_data": {
    "api_key": "sk_...",
    "webhook_secret": "wh_..."
  }
}
```

- `state` → `active` (funcionando) | `paused` (instalado mas pausado)
- `data` → configuração pública; lida/gravada por `PATCH /applications/{id}/data.json`
- `hidden_data` → credenciais/segredos; lidos/gravados por `PATCH /applications/{id}/hidden_data.json`

## Listagem (GET /applications.json)

| Filtro | Exemplo |
|---|---|
| Por app_id (marketplace) | `app_id=124890` |
| Por estado | `state=active` |
| Campos específicos | `fields=_id,app_id,title,state` |

## PATCH — exemplos

### Atualizar chave em `data`

```
PATCH /applications/{id}/data.json
Body: { "access_token": "tok_xxxx" }
```

Obs: o PATCH em `data.json` faz **merge** no objeto `data` do documento —
não substitui o objeto inteiro, apenas mescla as chaves enviadas.

### Atualizar `hidden_data` (credenciais)

```
PATCH /applications/{id}/hidden_data.json
Body: { "api_key": "sk_novo", "webhook_secret": "wh_novo" }
```

### Enviar dados de exportação para um app

```
PATCH /applications/{id}/data.json
Body: { "exportation": { "orders": ["5cf...abc", "5cf...def"] } }
```

## Logs de auditoria (`@logs`)

### Listar logs de um recurso

```
GET /@logs.json?resource_id={id}&limit=100
```

### Detalhe de uma entrada de log

```
GET /@logs/{log_id}.json
```

### Estrutura de uma entrada de log

```json
{
  "id": "abc123",
  "date_time": "2026-05-27T13:00:00.000Z",
  "method": "PATCH",
  "api_resource": "/v1/orders/5cf...abc.json",
  "ip_addr": "200.100.50.30",
  "authentication_id": "5cf...auth",
  "body": { ... },
  "response": { ... }
}
```

- `ip_addr` prefixado com `127.9` → chamada interna de aplicativo/módulo
- `authentication_id` → quem fez a mudança (admin user ou app)
- `body` → payload enviado na requisição
- `response` → resposta da API (disponível no GET do log individual)

## Erros comuns

| Código | Causa | Solução |
|---|---|---|
| `401` | Token expirado | `eval $(python ecomplus-auth/scripts/refresh.py --export)` |
| `403` | Sem permissão para `hidden_data` | Verificar nível de acesso do token |
| `404` | App não encontrado | Confirmar `_id` ou `app_id` |
