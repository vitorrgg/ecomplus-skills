---
name: ecomplus-aggregations
description: Use esta skill SEMPRE que o usuário pedir agrupamentos, agregações, rankings ou análises de dados calculados no servidor para uma loja E-Com Plus. Gatilhos típicos — "produtos mais abandonados", "carrinhos abandonados", "quais produtos foram mais pedidos", "produtos mais vendidos por quantidade", "aniversariantes do mês", "lista de aniversariantes", "clientes por estado", "clientes por UF", "campanhas mais eficazes", "quantos pedidos por campanha", "UTM campanha", "quero agrupar por", "aggregation", "agregar dados", "ranking de estados", "quais estados têm mais clientes". Diferente de ecomplus-reports (que pagina a API e calcula localmente), esta skill usa POST /$aggregate.json para deixar o servidor fazer o agrupamento — muito mais eficiente para grandes volumes.
---

# E-Com Plus — Aggregations

Executa pipelines de agregação MongoDB via `POST /$aggregate.json` para produzir rankings, agrupamentos e análises calculadas no servidor.

## Pré-requisitos

Variáveis de ambiente obrigatórias (veja `ecomplus-auth` se estiverem faltando):

- `ECOMPLUS_STORE_ID`
- `ECOMPLUS_ACCESS_TOKEN`
- `ECOMPLUS_MY_ID`

## Como funciona o endpoint `$aggregate.json`

```
POST https://api.e-com.plus/v1/$aggregate.json
Headers: X-Store-ID, X-Access-Token, X-My-ID
Body: { "resource": "<coleção>", "pipeline": [ <estágios MongoDB> ] }
```

O pipeline segue a sintaxe do MongoDB Aggregation Framework. Os recursos disponíveis são os mesmos da API REST: `orders`, `carts`, `customers`, `products`, `items`, `categories`, `brands`.

Resposta:
```json
{ "result": [ ... ] }
```

## Scripts disponíveis

| Script | Função | Recursos |
|---|---|---|
| `abandoned_carts.py` | Produtos mais abandonados em carrinhos | `carts` |
| `campaigns.py` | Pedidos por campanha UTM (ranking de campanhas) | `orders` |
| `top_products_agg.py` | Produtos mais pedidos por quantidade (server-side) | `orders` |
| `birthdays.py` | Aniversariantes agrupados por mês | `customers` |
| `customers_by_state.py` | Clientes agrupados por estado (UF) | `customers` |

## Como rodar

Todos os scripts aceitam `--format md|csv|json` (default `md`). Scripts com recorte temporal aceitam `--from YYYY-MM-DD --to YYYY-MM-DD`.

```bash
# Produtos mais abandonados em carrinho (último semestre)
python scripts/abandoned_carts.py --from 2026-01-01 --to 2026-05-28 --limit 20

# Ranking de campanhas UTM
python scripts/campaigns.py --from 2026-01-01 --to 2026-05-28

# Produtos mais pedidos (só pagos, exceto cancelados)
python scripts/top_products_agg.py --from 2026-01-01 --to 2026-05-28 --limit 30

# Aniversariantes de junho
python scripts/birthdays.py --month 6

# Todos os aniversariantes organizados por mês
python scripts/birthdays.py --format csv

# Clientes por estado (resumo)
python scripts/customers_by_state.py

# Clientes por estado com lista detalhada
python scripts/customers_by_state.py --detail

# Apenas clientes de SP
python scripts/customers_by_state.py --state SP --detail --format csv
```

## Quando usar aggregation vs. relatórios tradicionais

| Situação | Use |
|---|---|
| Precisa agrupar por campo (produto, campanha, estado, mês) | **ecomplus-aggregations** |
| Volume alto e quer cálculo no servidor | **ecomplus-aggregations** |
| Relatório simples de receita/pedidos paginando | `ecomplus-reports` |
| Editar ou atualizar registros | `ecomplus-orders`, `ecomplus-products`, `ecomplus-customers` |

## Formatando a resposta pro usuário

- Apresente em tabela markdown — a interface renderiza bem.
- Rankings: mostre no máximo 20–30 linhas e ofereça exportar CSV para mais.
- Para aniversariantes: mostre o mês atual em destaque se o usuário não especificou.
- Para campanhas: inclua % do total para dar proporção.

## Pegadinhas

- O campo `addresses.province_code` em clientes pode ser um array se o cliente tiver múltiplos endereços. O aggregation agrupa pelo primeiro valor indexado.
- Carrinhos: `completed: false` identifica abandonados. Carrinhos com `completed: true` já viraram pedido.
- Nos pedidos, `items.quantity` pode ser `float` (produto vendido por peso). Use `$sum: "$items.quantity"` para somar corretamente.
- O endpoint `$aggregate.json` não tem paginação — retorna todos os resultados. Limite o `pipeline` com `$limit` se o resultado for muito grande.

## Referência

Exemplos completos de pipelines em `references/aggregation-guide.md`.
