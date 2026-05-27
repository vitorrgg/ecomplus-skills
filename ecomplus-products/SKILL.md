---
name: ecomplus-products
description: Use esta skill SEMPRE que o usuário quiser consultar, buscar, listar, editar ou gerenciar produtos de uma loja E-Com Plus. Gatilhos: "ver produto", "buscar produto", "produto SKU", "listar produtos", "estoque baixo", "atualizar estoque", "quantidade em estoque", "produtos zerados", "precisa repor", "alterar preço", "atualizar preço", "colocar em promoção", "preço das variações", "desativar produto", "ativar produto", "produto disponível", "produto visível", "detalhes do produto", "variações do produto", "foto do produto". Funciona com a API REST E-Com Plus.
---

# E-Com Plus — Produtos

Consulta, lista e atualiza produtos (preço, estoque, disponibilidade) de uma loja E-Com Plus via API REST.

## Pré-requisitos

Variáveis de ambiente obrigatórias (veja `ecomplus-auth` se estiverem faltando):

- `ECOMPLUS_STORE_ID`
- `ECOMPLUS_ACCESS_TOKEN`
- `ECOMPLUS_MY_ID`

## Scripts disponíveis

| Script | Função |
|---|---|
| `get_product.py` | Detalhe completo de um produto (por SKU ou _id) |
| `list_products.py` | Listar com filtros: estoque baixo, disponibilidade, categoria, marca |
| `update_stock.py` | Atualizar estoque (produto simples ou variações individuais) |
| `update_price.py` | Atualizar preço e/ou preço base (produto simples ou variações) |

## Buscar um produto

```bash
# Por SKU
python scripts/get_product.py --sku CAMISETA-P-AZUL

# Por _id
python scripts/get_product.py --id 5cf...abc

# Saída JSON
python scripts/get_product.py --sku CAMISETA-P-AZUL --format json
```

Mostra: nome, SKU, preço, base_price, estoque, disponibilidade, categorias, marcas, variações.

## Listar produtos

```bash
# Estoque zerado ou crítico (≤ 5 unidades)
python scripts/list_products.py --max-stock 5

# Produtos indisponíveis
python scripts/list_products.py --available false

# Produtos invisíveis no vitrine
python scripts/list_products.py --visible false

# Por categoria (nome parcial)
python scripts/list_products.py --category "Camisetas"

# Todos os produtos, exportar CSV
python scripts/list_products.py --limit 500 --format csv

# Em promoção (base_price > price)
python scripts/list_products.py --on-sale
```

Filtros: `--available`, `--visible`, `--max-stock`, `--min-stock`, `--category`, `--brand`, `--on-sale`, `--limit`.

## Atualizar estoque

```bash
# Produto simples
python scripts/update_stock.py --sku CAMISETA-P-AZUL --quantity 50

# Variação específica (por SKU da variação)
python scripts/update_stock.py --sku CAMISETA --variation-sku CAMISETA-P-AZUL --quantity 50

# Por _id do produto
python scripts/update_stock.py --id 5cf...abc --quantity 50
```

Se o produto tiver variações, o estoque total é a soma das variações — não é possível editar
o total diretamente. Use `--variation-sku` para atualizar uma variação específica.

## Atualizar preço

```bash
# Preço simples (produto sem variações)
python scripts/update_price.py --sku CAMISETA-P-AZUL --price 79.90

# Colocar em promoção: define base_price (de) e price (por)
python scripts/update_price.py --sku CAMISETA-P --price 69.90 --base-price 89.90

# Retirar promoção (iguala base_price ao price)
python scripts/update_price.py --sku CAMISETA-P --price 89.90 --base-price 89.90

# Alterar preço de variação específica
python scripts/update_price.py --sku CAMISETA --variation-sku CAMISETA-G --price 99.90

# Aplicar desconto % em todas as variações de um produto
python scripts/update_price.py --sku CAMISETA --discount 10
```

## Campos de disponibilidade

Para ativar/desativar ou mostrar/ocultar um produto, use `update_stock.py --available` ou `--visible`:

```bash
# Desativar produto (sai de venda)
python scripts/update_stock.py --sku CAMISETA-P-AZUL --available false

# Ativar produto
python scripts/update_stock.py --sku CAMISETA-P-AZUL --available true

# Ocultar do vitrine
python scripts/update_stock.py --sku CAMISETA-P-AZUL --visible false
```

## Quando ESTA skill NÃO é a certa

- Usuário quer **relatórios de vendas** ou top produtos → `ecomplus-reports`
- Usuário quer **ver/atualizar pedidos** → `ecomplus-orders`
- Usuário quer **ver/editar clientes** → `ecomplus-customers`
- Usuário quer **configurar categorias, frete, pagamento** → `ecomplus-stores`

## Referência de campos

Estrutura completa do documento de produto em `references/product-fields.md`.
