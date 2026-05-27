# E-Com Plus — Campos do Produto e PATCH

Carregado sob demanda quando for implementar scripts novos ou entender a estrutura do produto.

## Estrutura principal do documento de produto

```json
{
  "_id": "5cf...abc",
  "sku": "CAMISETA-P-AZUL",
  "name": "Camiseta Básica P Azul",
  "slug": "camiseta-basica-p-azul",
  "status": "active",
  "available": true,
  "visible": true,
  "manage_stock": true,

  "price": 69.90,
  "base_price": 89.90,
  "cost_price": 30.00,
  "price_effective_date": {
    "start": "2026-05-01T00:00:00.000Z",
    "end": "2026-05-31T23:59:59.000Z"
  },

  "quantity": 50,
  "min_quantity": 1,
  "sales": 120,
  "views": 540,

  "categories": [{ "_id": "...", "name": "Camisetas" }],
  "brands": [{ "_id": "...", "name": "Minha Marca" }],
  "keywords": ["camiseta", "azul", "básica"],

  "pictures": [
    {
      "_id": "...",
      "small": { "url": "https://...", "width": 300, "height": 300 },
      "normal": { "url": "https://...", "width": 800, "height": 800 }
    }
  ],

  "specifications": {
    "colors": [{ "text": "Azul", "value": "#0000FF" }],
    "size": [{ "text": "P" }]
  },

  "variations": [ { ...ver abaixo... } ],

  "short_description": "Camiseta confortável 100% algodão",
  "body_html": "<p>Descrição completa em HTML</p>",

  "created_at": "2026-01-15T10:00:00.000Z",
  "updated_at": "2026-05-18T15:00:00.000Z"
}
```

## Variações

```json
{
  "_id": "5ae...var",
  "sku": "CAMISETA-P-AZUL",
  "quantity": 20,
  "price": 69.90,
  "base_price": 89.90,
  "available": true,
  "specifications": {
    "colors": [{ "text": "Azul" }],
    "size": [{ "text": "P" }]
  },
  "picture": { "normal": { "url": "https://..." } }
}
```

**Regra de estoque com variações:**
- O campo `quantity` no produto pai é a **soma** das variações.
- Nunca edite `quantity` do produto pai diretamente se ele tiver variações.
- Sempre edite `PATCH /products/{id}/variations/{variation_id}.json` e depois recalcule o total no produto pai.

## Preço e promoção

| Campo | Significado |
|---|---|
| `price` | Preço de venda atual (o "por") |
| `base_price` | Preço original antes da promoção (o "de") |
| `cost_price` | Custo do produto (não é exibido ao cliente) |

- Se `base_price > price` → o produto está em promoção.
- Se `base_price == price` ou `base_price` ausente → sem promoção.
- `price_effective_date.start/end` delimita a validade do preço promocional.

## Disponibilidade e visibilidade

| Campo | Tipo | Significado |
|---|---|---|
| `available` | boolean | Produto pode ser adicionado ao carrinho |
| `visible` | boolean | Aparece no vitrine / buscas |
| `manage_stock` | boolean | Se `false`, ignora `quantity` e não bloqueia venda por falta de estoque |

## PATCH — exemplos

### Atualizar preço do produto
```
PATCH /products/{id}.json
Body: { "price": 79.90, "base_price": 99.90 }
```

### Atualizar estoque do produto simples
```
PATCH /products/{id}.json
Body: { "quantity": 50 }
```

### Atualizar estoque de uma variação
```
PATCH /products/{id}/variations/{variation_id}.json
Body: { "quantity": 20 }
```

Depois recalcule o total:
```
PATCH /products/{id}.json
Body: { "quantity": <soma_das_variações> }
```

### Desativar produto
```
PATCH /products/{id}.json
Body: { "available": false }
```

### Ocultar do vitrine
```
PATCH /products/{id}.json
Body: { "visible": false }
```

### Atualizar preço de variação
```
PATCH /products/{id}/variations/{variation_id}.json
Body: { "price": 79.90, "base_price": 99.90 }
```

## Filtros em listagem (GET /products.json)

| Filtro | Exemplo |
|---|---|
| Disponíveis | `available=true` |
| Visíveis | `visible=true` |
| Estoque zerado | `quantity=0` |
| Estoque baixo | `quantity<=5` |
| Estoque acima | `quantity>=10` |
| Por categoria | `categories._id=<id>` ou `categories.name=Camisetas` |
| Por marca | `brands.name=Minha Marca` |
| Por SKU | `sku=CAMISETA-P` |
| Variação com SKU | `variations.sku=CAMISETA-P-AZUL` |

Paginação: `limit=100&offset=N` (máximo 100 por página).

## Endpoints de variações e categorias

```
# Detalhe do produto
GET /products/{id}.json

# PATCH no produto
PATCH /products/{id}.json

# PATCH em variação específica
PATCH /products/{id}/variations/{variation_id}.json

# Adicionar categoria ao produto
POST /products/{id}/categories.json
Body: { "_id": "<category_id>" }

# Remover categoria
DELETE /products/{id}/categories/{category_id}.json
```

## Erros comuns

| Código | Causa | Solução |
|---|---|---|
| `401` | Token expirado | `eval $(python ecomplus-auth/scripts/refresh.py --export)` |
| `403` | store_id errado | Verificar token |
| `404` | Produto não encontrado | Confirmar SKU ou _id |
| `406` | Valor fora do schema | Verificar tipo do campo (number, boolean, string) |
