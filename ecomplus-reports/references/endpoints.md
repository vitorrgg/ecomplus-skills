# Endpoints E-Com Plus — referência rápida

Só os endpoints relevantes para relatórios. Documentação completa em https://developers.e-com.plus/docs/api/

## Pedidos (`/orders`)

### Listar pedidos
```
GET /orders.json?<filtros>
```

Filtros úteis:
- `status=open|cancelled`
- `financial_status.current=paid|pending|...`
- `created_at>=...&created_at<=...` (UTC, ISO 8601)
- `buyers._id=<customer_id>` (pedidos de um cliente)
- `fields=number,amount,status,...` (economiza payload)
- `sort=-created_at`
- `limit=100&offset=N`

Resposta:
```json
{
  "result": [ { "_id": "...", "number": 12345, "amount": {...}, ... } ],
  "meta": { "limit": 100, "offset": 0, "count": ... }
}
```

### Detalhe de um pedido
```
GET /orders/{order_id}.json
```

Campos relevantes para relatórios:
- `number` — número humano (sequencial)
- `status` — `open`, `cancelled`
- `financial_status.current` — `paid`, `pending`, `refunded`...
- `fulfillment_status.current` — status de envio
- `amount.total` — valor total do pedido
- `amount.subtotal`, `amount.freight`, `amount.discount`, `amount.tax`
- `items[]` — itens, cada um com `quantity`, `final_price`, `product_id`, `sku`, `name`
- `buyers[]` — cliente(s)
- `payment_method_label` — string amigável ("Cartão de Crédito", "Pix"...)
- `created_at`, `updated_at`

## Produtos (`/products`)

### Listar produtos
```
GET /products.json?<filtros>
```

Filtros úteis:
- `available=true` — só publicados
- `quantity<=5` — estoque baixo
- `quantity=0` — zerados
- `categories._id=<id>` — de uma categoria
- `fields=sku,name,quantity,price,...`

### Detalhe de produto
```
GET /products/{product_id}.json
```

Campos relevantes:
- `sku`, `name`, `slug`
- `price`, `base_price`, `cost_price`
- `quantity` — estoque atual
- `min_quantity` — mínimo configurado
- `variations[]` — variações com seu próprio `quantity` e `price`
- `categories[]`, `brands[]`
- `available` — booleano
- `views` — visualizações (útil pra conversão)

## Clientes (`/customers`)

### Listar
```
GET /customers.json?<filtros>
```

Filtros úteis:
- `main_email=...`
- `doc_number=...` (CPF/CNPJ)
- `orders_count>=2` — clientes recorrentes

### Detalhe
```
GET /customers/{customer_id}.json
```

Campos:
- `display_name`, `main_email`
- `orders_count`, `orders_total_value`
- `addresses[]`
- `enabled` — ativo/inativo

## Carrinhos abandonados (`/carts`)

Útil pra relatório de funil:
```
GET /carts.json?available=true&completed=false
```

## Categorias e marcas

```
GET /categories.json
GET /brands.json
```

Geralmente combinados com produtos pra relatórios de "vendas por categoria".
