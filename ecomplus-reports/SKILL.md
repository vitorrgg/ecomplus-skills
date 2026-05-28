---
name: ecomplus-reports
description: Use esta skill SEMPRE que o usuário pedir relatórios, métricas, análises ou números de uma loja na plataforma E-Com Plus / e-com.plus. Gatilhos linguísticos típicos — "relatório de vendas", "quanto faturei", "vendas do mês", "vendas dessa semana", "top produtos", "produtos mais vendidos", "ticket médio", "estoque baixo", "curva ABC", "comparar períodos", "fechamento financeiro", "quantos pedidos", "faturamento", "performance da loja". Use mesmo se o usuário não disser explicitamente "relatório" — se ele estiver pedindo um número agregado da loja, é esta skill. Funciona com store_id da E-Com Plus e usa a API REST oficial (https://api.e-com.plus/v1/).
---

# E-Com Plus — Relatórios

Gera relatórios e métricas agregadas de uma loja na plataforma E-Com Plus consultando a API REST oficial.

## Pré-requisitos

A skill assume que estas variáveis de ambiente estão preenchidas (a `ecomplus-auth` cuida disso, ou o backend da interface):

- `ECOMPLUS_STORE_ID` — ID numérico da loja (ex: `1011`)
- `ECOMPLUS_ACCESS_TOKEN` — token JWT obtido na autenticação
- `ECOMPLUS_MY_ID` — `authentication_id` retornado no login

Se alguma estiver faltando, pare e avise o usuário antes de tentar chamar a API.

## Decidindo qual relatório rodar

Quando o usuário pedir algo, mapeie a intenção pra um dos scripts em `scripts/`:

| Pedido típico | Script | Saída |
|---|---|---|
| "vendas do mês", "faturei quanto", "fechamento de X" | `sales_summary.py` | total, ticket médio, nº pedidos, por status de pagamento |
| "top produtos", "mais vendidos", "curva ABC" | `top_products.py` | ranking por receita e por qtd |
| "estoque baixo", "produtos zerados", "preciso repor" | `low_stock.py` | lista de SKUs abaixo do mínimo |
| "vendas por dia/semana/mês", "evolução" | `sales_timeline.py` | série temporal agregada |
| "comparar este mês com o anterior" | `sales_compare.py` | dois períodos lado a lado |
| "clientes que mais compraram" | `top_customers.py` | ranking por LTV |

Se o pedido for ambíguo, **pergunte o período antes de rodar**. Padrão razoável: últimos 30 dias.

## Como rodar

Todos os scripts aceitam `--from YYYY-MM-DD --to YYYY-MM-DD` e `--format md|csv|json` (default `md`).

```bash
python scripts/sales_summary.py --from 2026-05-01 --to 2026-05-18
python scripts/top_products.py --from 2026-05-01 --to 2026-05-18 --limit 20
python scripts/low_stock.py --threshold 5
```

## Formatando a resposta pro usuário

- **Sempre apresente em tabela markdown** — a interface renderiza bem e o usuário final não quer ver JSON.
- Coloque os números em BRL (R$) com 2 casas decimais. Use `f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")` para o padrão brasileiro (1.234,56).
- Se o resultado tiver mais de ~20 linhas, mostre as primeiras 10–15 e ofereça exportar CSV.
- Comece pela conclusão (o número principal), depois detalhe. Ex: "Você faturou **R$ 47.231,80** em 142 pedidos no período. Detalhamento abaixo…"

## Pegadinhas conhecidas da E-Com Plus

Vale consultar `references/api-quirks.md` antes de implementar relatórios novos. Os principais pontos:

- Pedido só conta como receita real se `financial_status.current` for `paid`. Pedidos `pending` (PIX aguardando) inflam o número se você não filtrar.
- Pedidos cancelados ainda aparecem na listagem default — filtre por `status != cancelled`.
- A API limita resultados a 100 por página. Sempre pagine usando `offset`.
- Rate limit: 6 req/s autenticadas. Os scripts já têm `time.sleep(0.2)` entre páginas.
- Datas na API são UTC. Converta para America/Sao_Paulo antes de mostrar pro usuário.

## Endpoints usados

- `GET /orders.json` — listagem de pedidos (com filtros via query string)
- `GET /orders/{id}.json` — detalhe de um pedido
- `GET /products.json` — listagem de produtos
- `GET /products/{id}.json` — detalhe de produto (inclui `quantity` para estoque)
- `GET /customers.json` — listagem de clientes

Documentação completa em `references/endpoints.md`.

## Quando ESTA skill NÃO é a certa

- Usuário quer **editar** um produto/pedido/cliente → use `ecomplus-products`, `ecomplus-orders` ou `ecomplus-customers`
- Usuário quer entender um **log de erro** ou problema de integração → use `ecomplus-integrations`
- Usuário quer **configurar** algo da loja (frete, pagamento) → use `ecomplus-stores`
