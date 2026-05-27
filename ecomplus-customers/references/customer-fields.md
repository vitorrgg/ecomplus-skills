# E-Com Plus — Campos do Cliente e PATCH

Carregado sob demanda para implementar scripts novos ou entender a estrutura do cliente.

## Estrutura principal do documento de cliente

```json
{
  "_id": "5cf...abc",
  "enabled": true,
  "main_email": "joao@exemplo.com",
  "display_name": "João Silva",
  "name": {
    "given_name": "João",
    "middle_name": "",
    "family_name": "Silva"
  },
  "registry_type": "p",
  "doc_number": "12345678901",
  "phones": [
    { "country_code": 55, "number": "31999998888" }
  ],
  "birth_date": { "day": 15, "month": 6, "year": 1985 },
  "staff_notes": "Nota interna visível só para a equipe",
  "referral": "AMIGO123",
  "addresses": [ { ...ver abaixo... } ],
  "orders_count": 7,
  "orders_total_value": 1234.56,
  "loyalty_points_entries": [ { ...ver abaixo... } ],
  "created_at": "2024-01-10T10:00:00.000Z",
  "updated_at": "2026-05-18T15:00:00.000Z"
}
```

## Endereços

```json
{
  "_id": "...",
  "zip": "35700092",
  "name": "João Silva",
  "street": "Rua Piauí",
  "number": "416",
  "complement": "Apto 2",
  "borough": "Boa Vista",
  "city": "Sete Lagoas",
  "province_code": "MG",
  "default": true
}
```

- `default: true` → endereço principal (usado no checkout por padrão)
- `province_code` → sigla do estado (UF), 2 letras maiúsculas

## Pontos de fidelidade (`loyalty_points_entries`)

```json
{
  "_id": "...",
  "name": "pontos",
  "program_id": "p0_pontos",
  "ratio": 1,
  "earned_points": 150.00,
  "active_points": 100.00,
  "valid_thru": "2027-12-31T23:59:59.000Z",
  "order_id": "5cf...xyz"
}
```

- `earned_points` → total ganho na entrada
- `active_points` → saldo disponível para uso
- `valid_thru` → expiração; se no passado, entrada está expirada
- Para calcular saldo atual: somar `active_points` de entradas não expiradas

## PATCH — exemplos

### Notas internas da equipe
```
PATCH /customers/{id}.json
Body: { "staff_notes": "Cliente VIP, preferência por frete expresso" }
```

### Desativar conta (bloquear acesso)
```
PATCH /customers/{id}.json
Body: { "enabled": false }
```

### Atualizar e-mail
```
PATCH /customers/{id}.json
Body: { "main_email": "novo@email.com" }
```

### Atualizar nome
```
PATCH /customers/{id}.json
Body: {
  "display_name": "João P. Silva",
  "name": { "given_name": "João", "middle_name": "P.", "family_name": "Silva" }
}
```

## Filtros em listagem (GET /customers.json)

| Filtro | Exemplo |
|---|---|
| Por e-mail exato | `main_email=joao@exemplo.com` |
| Por CPF/CNPJ | `doc_number=12345678901` |
| Clientes recorrentes | `orders_count>=2` |
| Por LTV mínimo | `orders_total_value>=500` |
| Aniversariantes de junho | `birth_date.month=6` |
| Inativos | `enabled=false` |
| Ordenar por LTV | `sort=-orders_total_value` |
| Ordenar por pedidos | `sort=-orders_count` |

## Buscar pedidos de um cliente

```
GET /orders.json?buyers._id={customer_id}&sort=-created_at&limit=10
  &fields=_id,number,amount,created_at,financial_status,fulfillment_status
```

## Erros comuns

| Código | Causa | Solução |
|---|---|---|
| `401` | Token expirado | `eval $(python ecomplus-auth/scripts/refresh.py --export)` |
| `404` | Cliente não encontrado | Confirmar _id ou e-mail |
| `406` | Valor inválido no schema | Verificar tipo do campo |
