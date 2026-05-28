# API E-Com Plus — armadilhas e padrões

Documento carregado pelo SKILL.md quando for implementar relatórios novos ou debugar um existente.

## Autenticação

- 3 headers obrigatórios em rotas autenticadas: `X-Store-ID`, `X-Access-Token`, `X-My-ID`
- `X-Access-Token` é JWT, expira. A refresh é responsabilidade da skill `ecomplus-auth`
- Algumas rotas GET funcionam sem autenticação, mas retornam payload reduzido. Para relatórios sempre autentique.

## URL e formato

- Base: `https://api.e-com.plus/v1/`
- Sandbox: `https://sandbox.e-com.plus/{version}/` (dados são apagados a cada 7 dias)
- **Todo endpoint termina em `.json`**. Ex.: `/orders.json`, `/products/{id}.json`
- Content-Type sempre `application/json; charset=utf-8`

## Rate limit

- 30 req/s por IP em GETs cacheáveis (sem query string)
- 6 req/s por IP em GETs com query string
- 6 req/s autenticadas por usuário (mesmo `X-Access-Token`)
- Acima do limite: respostas são *atrasadas*, raramente retornam erro. Mesmo assim, trate 503.

Estratégia adotada nos scripts: `time.sleep(0.2)` entre páginas (5 req/s, com folga).

## Paginação

- `limit` máximo: 100
- `offset` é numérico (zero-based)
- Continue paginando enquanto `len(result) == limit`

## Filtros em listagens

Query string usa operadores anexados ao nome do campo:

| Operador | Significado |
|---|---|
| `campo=valor` | igualdade exata |
| `campo>=valor` | maior ou igual |
| `campo<=valor` | menor ou igual |
| `campo!=valor` | diferente |
| `fields=a,b,c` | retornar só esses campos (economiza banda) |
| `sort=-created_at` | ordenação descendente; sem `-` é ascendente |

Exemplo: pedidos pagos do último mês:
```
GET /orders.json?financial_status.current=paid&created_at>=2026-04-18T00:00:00.000Z&sort=-created_at
```

## Status que importam pra relatórios

### `status` (status do pedido)
- `open` — em aberto
- `cancelled` — cancelado (ignorar em receita)

### `financial_status.current` (status de pagamento)
- `pending` — aguardando (PIX gerado mas não pago)
- `under_analysis` — em análise antifraude
- `authorized` — autorizado mas não capturado
- `paid` — **pago de fato** (este é o que conta como receita)
- `in_dispute` — em disputa (chargeback em curso)
- `refunded` — estornado
- `voided` — cancelado antes da captura
- `unknown`

### `fulfillment_status.current` (status de envio)
- `invoice_issued`, `in_production`, `in_separation`, `ready_for_shipping`, `shipped`, `delivered`, `partially_delivered`, `returned`

**Regra prática:** receita = `status != cancelled` AND `financial_status.current == paid`

## Datas

- API armazena tudo em **UTC**.
- Formato: ISO 8601 com milissegundos e Z. Ex.: `2026-05-18T13:45:00.000Z`
- Antes de mostrar pro usuário, converta para `America/Sao_Paulo` (UTC-3).

## Endpoint `/products.json` — comportamento especial

O endpoint de listagem de produtos **não suporta filtros, `fields`, `limit` nem `sort`**. Sempre retorna todos os produtos da loja com apenas três campos: `_id`, `sku`, `slug`. A `query` no `meta` sempre aparece como `{}`.

- Não use `GET /products.json?quantity<=5&fields=sku,name` — os parâmetros são ignorados.
- Para relatórios de estoque, a estratégia correta é: listar todos os IDs com `/products.json`, depois buscar cada produto individualmente via `/products/{_id}.json` e filtrar no cliente.
- O endpoint individual `/products/{_id}.json` retorna o documento completo com `name` (string), `price`, `quantity`, `available`, `visible`, variações, etc.
- O campo `name` no produto individual é **string plana** (ex: `"Plotter FOISON S48"`), não um objeto multilíngue.

## Caso especial: integração com Bling

Coisa que o Rafael já tropeçou (conversas anteriores):

- Movimentação de estoque vinda do Bling pode sobrescrever campos da E-Com Plus (preço, descrição). Não é problema desta skill, mas se um relatório mostrar valores "estranhos" depois de uma sincronização, vale checar.
- "Descrição curta" no Bling corresponde a "descrição complementar" na E-Com Plus — mapeamento confuso, fica registrado aqui.

## Erros comuns

| Código | Significado | O que fazer |
|---|---|---|
| 401 | Token expirado ou inválido | Avise o usuário pra refazer login |
| 403 | Sem permissão pra esse recurso/loja | Verifique se store_id bate com o token |
| 406 | Erro de validação | A resposta tem `user_message.pt_br` explicando |
| 429 | (raro) Rate limit estourado | Backoff exponencial |
| 503 | API indisponível | Retry com backoff |

Toda resposta de erro segue:
```json
{
  "status": 406,
  "error_code": 123,
  "message": "Invalid value on resource ID",
  "user_message": {
    "en_us": "...",
    "pt_br": "O ID informado é inválido"
  },
  "more_info": null
}
```

Mostre `user_message.pt_br` pro usuário, nunca o `message` técnico.
