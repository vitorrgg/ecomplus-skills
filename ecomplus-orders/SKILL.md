---
name: ecomplus-orders
description: Use esta skill SEMPRE que o usuário quiser consultar, buscar, listar, atualizar ou gerenciar pedidos de uma loja E-Com Plus. Gatilhos: "ver pedido", "buscar pedido", "pedido número", "pedido #", "listar pedidos", "pedidos em aberto", "pedidos pagos", "pedidos enviados", "atualizar status", "marcar como pago", "marcar como enviado", "marcar como entregue", "cancelar pedido", "código de rastreio", "adicionar rastreio", "rastreamento", "tracking", "nota do pedido", "detalhe do pedido", "histórico do pedido", "customer made an order", "pedidos do cliente". Funciona com a API REST E-Com Plus.
---

# E-Com Plus — Pedidos

Consulta, lista e atualiza pedidos de uma loja E-Com Plus via API REST.

## Pré-requisitos

Variáveis de ambiente obrigatórias (veja `ecomplus-auth` se estiverem faltando):

- `ECOMPLUS_STORE_ID`
- `ECOMPLUS_ACCESS_TOKEN`
- `ECOMPLUS_MY_ID`

## Scripts disponíveis

| Script | Função |
|---|---|
| `get_order.py` | Detalhe completo de um pedido (por número ou _id) |
| `list_orders.py` | Listar/buscar pedidos com filtros de status, data, cliente |
| `update_order.py` | Atualizar status (financeiro, envio ou principal) e notas |
| `add_tracking.py` | Adicionar ou atualizar código de rastreio numa linha de envio |

## Buscar um pedido específico

```bash
# Por número humano (ex: 1234)
python scripts/get_order.py --number 1234

# Por _id (ObjectId MongoDB)
python scripts/get_order.py --id 5cf...abc

# Saída em JSON
python scripts/get_order.py --number 1234 --format json
```

Mostra: número, status, comprador, itens, valores (subtotal, frete, desconto, total),
forma de pagamento, status do pagamento, status do envio, rastreio, data.

## Listar pedidos

```bash
# Todos os pedidos pagos do mês atual
python scripts/list_orders.py --financial-status paid

# Pedidos enviados nos últimos 7 dias
python scripts/list_orders.py --fulfillment-status shipped --from 2026-05-20

# Pedidos de um cliente pelo e-mail
python scripts/list_orders.py --buyer cliente@exemplo.com

# Pedidos em aberto num período
python scripts/list_orders.py --status open --from 2026-05-01 --to 2026-05-31

# Mais resultados e exportar CSV
python scripts/list_orders.py --financial-status paid --limit 200 --format csv
```

Filtros disponíveis: `--status`, `--financial-status`, `--fulfillment-status`, `--from`, `--to`, `--buyer`, `--limit` (default 50).

## Atualizar status de um pedido

```bash
# Marcar como pago
python scripts/update_order.py --number 1234 --financial-status paid

# Marcar como enviado
python scripts/update_order.py --number 1234 --fulfillment-status shipped

# Marcar como entregue
python scripts/update_order.py --number 1234 --fulfillment-status delivered

# Cancelar pedido
python scripts/update_order.py --number 1234 --status cancelled

# Adicionar/atualizar nota interna
python scripts/update_order.py --number 1234 --notes "Embalagem frágil, reforçar"
```

Campos atualizáveis: `--status`, `--financial-status`, `--fulfillment-status`, `--notes`.
Mais de um campo pode ser passado ao mesmo tempo.

## Adicionar código de rastreio

```bash
# Adicionar rastreio (usa a primeira linha de envio do pedido)
python scripts/add_tracking.py --number 1234 --code BR123456789BR

# Com link de rastreamento
python scripts/add_tracking.py --number 1234 --code BR123456789BR \
  --link https://rastreamento.correios.com.br/app/index.php

# Marcar como enviado junto com o rastreio
python scripts/add_tracking.py --number 1234 --code BR123456789BR --shipped
```

## Enums de status

### `status` (status principal)
| Valor | Significado |
|---|---|
| `open` | Em aberto |
| `cancelled` | Cancelado |

### `financial_status.current` (pagamento)
| Valor | Significado |
|---|---|
| `pending` | Aguardando pagamento (PIX gerado, boleto emitido) |
| `under_analysis` | Em análise antifraude |
| `authorized` | Autorizado (não capturado) |
| `paid` | **Pago** ← principal |
| `in_dispute` | Em disputa (chargeback) |
| `refunded` | Estornado |
| `voided` | Cancelado antes da captura |

### `fulfillment_status.current` (envio)
| Valor | Significado |
|---|---|
| `invoice_issued` | Nota fiscal emitida |
| `in_production` | Em produção |
| `in_separation` | Em separação |
| `ready_for_shipping` | Pronto para envio |
| `shipped` | Enviado (com rastreio) |
| `delivered` | Entregue |
| `partially_delivered` | Parcialmente entregue |
| `returned` | Devolvido |

## Quando ESTA skill NÃO é a certa

- Usuário quer **métricas/relatórios** de vendas → `ecomplus-reports`
- Usuário quer **editar produtos** → `ecomplus-products`
- Usuário quer **ver/editar cadastro do cliente** → `ecomplus-customers`
- Usuário quer **configurar a loja** → `ecomplus-stores`

## Referência de campos

Documentação detalhada dos campos do pedido e exemplos de PATCH em `references/order-fields.md`.
