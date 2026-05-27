---
name: ecomplus-customers
description: Use esta skill SEMPRE que o usuário quiser consultar, buscar, listar ou editar clientes de uma loja E-Com Plus. Gatilhos: "ver cliente", "buscar cliente", "cliente por e-mail", "cliente por CPF", "histórico de compras do cliente", "listar clientes", "clientes recorrentes", "clientes novos", "aniversariantes", "atualizar cadastro", "nota interna do cliente", "bloquear cliente", "desativar cliente", "loyalty", "pontos do cliente", "LTV", "valor gasto pelo cliente". Funciona com a API REST E-Com Plus.
---

# E-Com Plus — Clientes

Consulta, lista e atualiza cadastros de clientes de uma loja E-Com Plus via API REST.

## Pré-requisitos

Variáveis de ambiente obrigatórias (veja `ecomplus-auth` se estiverem faltando):

- `ECOMPLUS_STORE_ID`
- `ECOMPLUS_ACCESS_TOKEN`
- `ECOMPLUS_MY_ID`

## Scripts disponíveis

| Script | Função |
|---|---|
| `get_customer.py` | Detalhe completo de um cliente + últimos pedidos |
| `list_customers.py` | Listar clientes com filtros (recorrentes, aniversariantes, CPF, e-mail) |
| `update_customer.py` | Atualizar campos do cadastro (notas internas, ativo/inativo, e-mail, nome) |

## Buscar um cliente

```bash
# Por e-mail
python scripts/get_customer.py --email cliente@exemplo.com

# Por CPF/CNPJ (só dígitos)
python scripts/get_customer.py --doc 12345678901

# Por _id
python scripts/get_customer.py --id 5cf...abc

# Incluir últimos pedidos
python scripts/get_customer.py --email cliente@exemplo.com --orders

# Saída JSON
python scripts/get_customer.py --email cliente@exemplo.com --format json
```

Mostra: nome, e-mail, CPF/CNPJ, telefones, endereços, data de nascimento, notas da equipe,
total gasto, número de pedidos, pontos de fidelidade.

## Listar clientes

```bash
# Clientes com mais de 1 pedido (recorrentes)
python scripts/list_customers.py --min-orders 2

# Aniversariantes do mês (mês atual por padrão)
python scripts/list_customers.py --birthday-month 6

# Por nome (parcial)
python scripts/list_customers.py --name "Maria"

# Clientes inativos
python scripts/list_customers.py --enabled false

# Top clientes por valor gasto
python scripts/list_customers.py --min-orders 1 --sort ltv --limit 20

# Exportar CSV
python scripts/list_customers.py --min-orders 2 --format csv
```

## Atualizar cadastro

```bash
# Adicionar nota interna (visible apenas para a equipe)
python scripts/update_customer.py --email cliente@exemplo.com --notes "Cliente VIP, preferência por frete expresso"

# Desativar conta (bloquear acesso)
python scripts/update_customer.py --email cliente@exemplo.com --enabled false

# Reativar conta
python scripts/update_customer.py --email cliente@exemplo.com --enabled true

# Atualizar e-mail
python scripts/update_customer.py --id 5cf...abc --new-email novo@email.com

# Por _id
python scripts/update_customer.py --id 5cf...abc --notes "Atualizado via script"
```

## Campos principais do cadastro

| Campo | Tipo | Descrição |
|---|---|---|
| `main_email` | string | E-mail principal (login) |
| `display_name` | string | Nome de exibição |
| `name.given_name` | string | Primeiro nome |
| `name.family_name` | string | Sobrenome |
| `doc_number` | string | CPF (11 dígitos) ou CNPJ (14 dígitos) |
| `registry_type` | `p` \| `j` | Pessoa física ou jurídica |
| `phones[]` | array | Telefones com `country_code` e `number` |
| `addresses[]` | array | Endereços com campo `default` |
| `birth_date` | object | `{day, month, year}` |
| `staff_notes` | string | Notas internas da equipe |
| `enabled` | boolean | Conta ativa? |
| `orders_count` | int | Total de pedidos |
| `orders_total_value` | float | Valor total gasto (LTV) |

## Quando ESTA skill NÃO é a certa

- Usuário quer **ver/atualizar pedidos** → `ecomplus-orders`
- Usuário quer **relatórios de vendas** → `ecomplus-reports`
- Usuário quer **editar produtos** → `ecomplus-products`

## Referência de campos

Estrutura completa do documento de cliente em `references/customer-fields.md`.
