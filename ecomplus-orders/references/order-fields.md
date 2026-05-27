# E-Com Plus — Campos do Pedido e PATCH

Carregado sob demanda quando for implementar scripts novos ou entender a estrutura do pedido.

## Estrutura principal do documento de pedido

```json
{
  "_id": "5cf...abc",
  "number": 1234,
  "status": "open",
  "financial_status": { "current": "paid" },
  "fulfillment_status": { "current": "shipped" },
  "amount": {
    "subtotal": 99.00,
    "freight": 15.00,
    "discount": 5.00,
    "tax": 0,
    "extra": 0,
    "balance": 0,
    "total": 109.00
  },
  "buyers": [ { ...customer inline... } ],
  "items": [ { ...item... } ],
  "shipping_lines": [ { ...shipping... } ],
  "transactions": [ { ...payment... } ],
  "payments_history": [ { ...event... } ],
  "fulfillments": [ { ...event... } ],
  "notes": "Observação interna",
  "extra_discount": { "discount_coupon": "PROMO10", "value": 5.00, "app": {...} },
  "affiliate_code": "...",
  "subscription_order": { "_id": "..." },
  "payment_method_label": "Pix",
  "shipping_method_label": "Correios PAC",
  "created_at": "2026-05-18T13:00:00.000Z",
  "updated_at": "2026-05-18T15:00:00.000Z"
}
```

## Items

```json
{
  "_id": "...",
  "product_id": "...",
  "variation_id": "...",
  "sku": "PROD-001-P",
  "name": "Camiseta Básica P",
  "quantity": 2,
  "price": 49.90,
  "final_price": 44.91,
  "picture": { "normal": { "url": "https://..." } },
  "customizations": [{ "label": "Cor", "option": { "text": "Azul" } }]
}
```

- `final_price` é o preço aplicado (com desconto de item); `price` é o preço de tabela.
- Para valor total do item: `final_price * quantity`.

## Shipping lines

```json
{
  "_id": "...",
  "from": { "zip": "...", "street": "...", "city": "...", "province_code": "SP" },
  "to": {
    "name": "João Silva",
    "zip": "01310-100",
    "street": "Av. Paulista",
    "number": "1000",
    "complement": "Apto 42",
    "borough": "Bela Vista",
    "city": "São Paulo",
    "province_code": "SP",
    "phone": { "number": "11999999999" }
  },
  "app": {
    "_id": "...",
    "label": "PAC",
    "carrier": "Correios",
    "carrier_doc_number": "..."
  },
  "tracking_codes": [
    { "code": "BR123456789BR", "link": "https://rastreamento.correios.com.br" }
  ],
  "package": { "weight": { "value": 0.5, "unit": "kg" } }
}
```

## Transactions

```json
{
  "_id": "...",
  "payment_method": { "code": "pix", "name": "Pix" },
  "type": "payment",
  "amount": 109.00,
  "app": { "label": "PagHiper", "intermediator": { "name": "PagHiper" } }
}
```

`type`: `payment` | `recurrence` (assinatura).

## Payments history (timeline de pagamento)

```json
{ "_id": "...", "date_time": "2026-05-18T13:10:00.000Z", "status": "paid", "transaction_id": "..." }
```

## Fulfillments (timeline de envio)

```json
{ "_id": "...", "date_time": "2026-05-18T14:00:00.000Z", "status": "shipped" }
```

## PATCH — como funciona

A API aceita `PATCH /orders/{id}.json` com um body parcial. Só os campos presentes no body são atualizados.

### Atualizar status de pagamento

```
PATCH /orders/{id}.json
Body: { "financial_status": { "current": "paid" } }
```

### Atualizar status de envio

```
PATCH /orders/{id}.json
Body: { "fulfillment_status": { "current": "shipped" } }
```

### Cancelar pedido

```
PATCH /orders/{id}.json
Body: { "status": "cancelled" }
```

### Adicionar código de rastreio

O PATCH em `shipping_lines` é feito por array de objetos com `_id`. A API mescla pelo `_id` existente.

```
PATCH /orders/{id}.json
Body: {
  "shipping_lines": [{
    "_id": "<id_da_shipping_line>",
    "tracking_codes": [{ "code": "BR123456789BR", "link": "https://..." }]
  }]
}
```

**Importante:** sempre inclua o `_id` da shipping_line (obtido no GET do pedido). Sem `_id`, a API pode criar uma nova linha em vez de atualizar a existente.

### Atualizar vários campos juntos

```
PATCH /orders/{id}.json
Body: {
  "fulfillment_status": { "current": "shipped" },
  "shipping_lines": [{ "_id": "...", "tracking_codes": [{ "code": "BR123456789BR" }] }],
  "notes": "Enviado via PAC"
}
```

## Buscar pedidos por filtros

```
GET /orders.json?financial_status.current=paid&created_at>=2026-05-01T00:00:00.000Z
GET /orders.json?buyers.main_email=cliente@exemplo.com
GET /orders.json?number=1234&limit=1
GET /orders.json?_id=5cf...abc&limit=1
```

## Pedidos de assinatura

Pedido mãe: `transactions[0].type === "recurrence"` e tem subcoleção de invoices em `orders.json?subscription_order._id={id}`.

Pedido filho (invoice): tem `subscription_order._id` apontando para o pedido mãe.

## Erros comuns em PATCH

| Código | Causa | Solução |
|---|---|---|
| `401` | Token expirado | `eval $(python ecomplus-auth/scripts/refresh.py --export)` |
| `403` | store_id errado | Verificar se o token é do store_id correto |
| `406` | Valor inválido no enum | Verificar os valores aceitos neste doc |
| `404` | Pedido não encontrado | Confirmar o _id ou número |
