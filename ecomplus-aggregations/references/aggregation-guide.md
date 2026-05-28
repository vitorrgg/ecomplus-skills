# Guia de Aggregations — E-Com Plus API v1

## Endpoint

```
POST https://api.e-com.plus/v1/$aggregate.json
```

Headers obrigatórios:
```
X-Store-ID: <store_id>
X-Access-Token: <token>
X-My-ID: <my_id>
```

Body:
```json
{
  "resource": "<coleção>",
  "pipeline": [ <estágios MongoDB> ]
}
```

Resposta:
```json
{ "result": [ ... ] }
```

## Recursos disponíveis

| Resource | Coleção |
|---|---|
| `orders` | Pedidos |
| `carts` | Carrinhos |
| `customers` | Clientes |
| `products` | Produtos |
| `items` | Itens/SKUs de produtos |
| `categories` | Categorias |
| `brands` | Marcas |

## Estágios do pipeline (MongoDB Aggregation Framework)

### `$match` — filtrar documentos

```json
{ "$match": { "campo": { "$operador": "valor" } } }
```

Operadores comuns:
- `$eq` — igual
- `$ne` — diferente
- `$gt`, `$gte` — maior, maior ou igual
- `$lt`, `$lte` — menor, menor ou igual
- `$exists` — campo existe (true/false)
- `$in` — valor está na lista

Exemplo — pedidos pagos em janeiro/2026:
```json
{
  "$match": {
    "created_at": {
      "$gte": "2026-01-01T00:00:00.000Z",
      "$lte": "2026-01-31T23:59:59.999Z"
    },
    "financial_status.current": { "$eq": "paid" },
    "status": { "$ne": "cancelled" }
  }
}
```

### `$unwind` — desagregar arrays

Transforma cada elemento de um array em um documento separado.
Necessário para agregar campos dentro de arrays como `items[]`.

```json
{ "$unwind": "$items" }
```

### `$group` — agrupar e calcular

```json
{
  "$group": {
    "_id": "<campo de agrupamento>",
    "alias": { "$operadorAcumulador": "$campo" }
  }
}
```

Acumuladores comuns:
- `$sum` — soma (use `1` para contar, `"$campo"` para somar valores)
- `$avg` — média
- `$first` — primeiro valor do grupo
- `$last` — último valor do grupo
- `$addToSet` — conjunto de valores únicos (array sem repetição)
- `$push` — todos os valores (array com repetição)
- `$max`, `$min` — máximo, mínimo

Exemplo — agrupar pedidos por campanha:
```json
{
  "$group": {
    "_id": "$utm.campaign",
    "count": { "$sum": 1 }
  }
}
```

Exemplo — agrupar itens por produto somando quantidade:
```json
{
  "$group": {
    "_id": "$items.product_id",
    "name": { "$first": "$items.name" },
    "quantity": { "$sum": "$items.quantity" },
    "orders": { "$sum": 1 }
  }
}
```

### `$sort` — ordenar

```json
{ "$sort": { "campo": 1 } }   // ascendente
{ "$sort": { "campo": -1 } }  // descendente
```

### `$limit` — limitar resultados

```json
{ "$limit": 10 }
```

### `$project` — selecionar/renomear campos

```json
{
  "$project": {
    "nome_campo_saida": "$campo_original",
    "campo_excluido": 0
  }
}
```

### `$concat` — concatenar strings (dentro de `$group` ou `$project`)

```json
{
  "$concat": ["$name.given_name", " ", "$name.family_name"]
}
```

## Pipelines completos de referência

### Carrinhos abandonados por produto

```json
{
  "resource": "carts",
  "pipeline": [
    {
      "$match": {
        "created_at": {
          "$gte": "2026-01-01T00:00:00.000Z",
          "$lte": "2026-05-31T23:59:59.999Z"
        },
        "completed": { "$eq": false }
      }
    },
    { "$unwind": "$items" },
    {
      "$group": {
        "_id": {
          "product_id": "$items.product_id",
          "name": "$items.name",
          "variation_id": "$items.variation_id"
        },
        "count": { "$sum": 1 }
      }
    },
    { "$sort": { "count": -1 } }
  ]
}
```

### Pedidos por campanha UTM

```json
{
  "resource": "orders",
  "pipeline": [
    {
      "$match": {
        "created_at": {
          "$gte": "2026-01-01T00:00:00.000Z",
          "$lte": "2026-05-31T00:00:00.000Z"
        },
        "utm.campaign": { "$exists": true }
      }
    },
    {
      "$group": {
        "_id": "$utm.campaign",
        "count": { "$sum": 1 }
      }
    },
    { "$sort": { "count": -1 } }
  ]
}
```

### Produtos mais pedidos (só pagos)

```json
{
  "resource": "orders",
  "pipeline": [
    {
      "$match": {
        "created_at": { "$gte": "2026-01-01T00:00:00.000Z" },
        "status": { "$ne": "cancelled" },
        "financial_status.current": { "$eq": "paid" }
      }
    },
    { "$unwind": "$items" },
    {
      "$group": {
        "_id": "$items.product_id",
        "name": { "$first": "$items.name" },
        "sku": { "$first": "$items.sku" },
        "quantity": { "$sum": "$items.quantity" },
        "orders": { "$sum": 1 }
      }
    },
    { "$sort": { "quantity": -1 } }
  ]
}
```

### Aniversariantes por mês

```json
{
  "resource": "customers",
  "pipeline": [
    { "$match": { "birth_date.month": { "$exists": true } } },
    {
      "$group": {
        "_id": "$birth_date.month",
        "total": { "$sum": 1 },
        "birthdays": {
          "$addToSet": {
            "id": "$_id",
            "name": { "$concat": ["$name.given_name", " ", "$name.family_name"] },
            "day": "$birth_date.day",
            "email": "$main_email"
          }
        }
      }
    },
    { "$sort": { "_id": 1 } }
  ]
}
```

### Clientes por estado

```json
{
  "resource": "customers",
  "pipeline": [
    { "$match": { "addresses.province_code": { "$exists": true } } },
    {
      "$group": {
        "_id": "$addresses.province_code",
        "total": { "$sum": 1 },
        "customers": {
          "$addToSet": {
            "id": "$_id",
            "name": { "$concat": ["$name.given_name", " ", "$name.family_name"] },
            "email": "$main_email"
          }
        }
      }
    },
    { "$sort": { "total": -1 } }
  ]
}
```

## Dicas

- **Datas**: sempre em UTC, formato ISO 8601 com `Z` (`2026-01-01T00:00:00.000Z`).
- **`$aggregate.json` não pagina**: retorna todos os resultados de uma vez. Use `$limit` no pipeline para grandes coleções.
- **Arrays aninhados**: campos como `items[]`, `addresses[]`, `buyers[]` precisam de `$unwind` antes do `$group`.
- **`$addToSet` vs `$push`**: prefira `$addToSet` para evitar duplicatas quando agrupar dados de clientes.
- **Timeout**: a requisição tem timeout de 60s. Pipelines em coleções muito grandes podem precisar de `$match` restritivo no início para reduzir o volume processado.

## Referências externas

- Exemplos da comunidade: https://community.e-com.plus/t/como-criar-agrupamentos-de-dados-aggregation/3517
- MongoDB Aggregation: https://www.mongodb.com/docs/manual/aggregation/
