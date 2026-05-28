# E-Com Plus — Diferenças entre API v1 e v2

Este documento serve como guia para adaptar as skills do repo `ecomplus-skills` (v1)
para o repo `ecomplus-v2-skills` (v2).

## Lojas por versão

| Versão | Exemplos de lojas |
|---|---|
| **v1** (maioria) | conexaohome, coelhandia, festcakes, foisonbrasil, ministerioler |
| **v2** | tiasonia, barradoce, efacini, ladofit, ladorosa |

Como identificar: lojas v2 têm um monorepo com pasta `storefront/` + `functions/many/`
e usam pacotes `@cloudcommerce/*`. Lojas v1 têm apps separados por integração.

---

## Diferenças de API

### Base URL

| | v1 | v2 |
|---|---|---|
| Produção | `https://api.e-com.plus/v1` | `https://ecomplus.io/v2` |
| Sandbox | `https://sandbox.e-com.plus/v1` | não confirmado |
| Padrão de URL | `/RECURSO.json` | `/:STORE_ID/RECURSO` |
| Store ID na URL | não (vai no header) | sim (`/:1024/customers`) — o `:` antes do ID é **literal**, não notação de parâmetro |
| Sufixo `.json` | sim (obrigatório) | não |

### Autenticação

| | v1 | v2 |
|---|---|---|
| Mecanismo | 3 headers customizados | `Authorization` header padrão |
| Header auth | `X-Store-ID` + `X-Access-Token` + `X-My-ID` | `Authorization: Bearer {token}` |
| Auth alternativa | — | `Authorization: Basic base64(authId:apiKey)` |
| Env vars | `ECOMPLUS_STORE_ID` `ECOMPLUS_ACCESS_TOKEN` `ECOMPLUS_MY_ID` | `ECOM_STORE_ID` `ECOM_ACCESS_TOKEN` |
| Auth com api_key | `ECOM_AUTHENTICATION_ID` + `ECOM_API_KEY` (no v1 são `my_id` + `api_key`) | `ECOM_AUTHENTICATION_ID` + `ECOM_API_KEY` |

### Fluxo de login

**v1 (dois passos):**
```
POST /_login.json          → { _id, api_key, ... }
POST /_authenticate.json   → { access_token, expires }
```

**v2 (dois passos, endpoints sem prefixo `_` e sem `.json`):**
```
POST /login                → { _id, api_key, ... }
POST /authenticate         → { access_token, expires }
```

### Exemplos de requisição

**v1:**
```python
headers = {
    "X-Store-ID": "1024",
    "X-Access-Token": "token...",
    "X-My-ID": "5cf...abc",
}
GET https://api.e-com.plus/v1/customers.json?limit=10
PATCH https://api.e-com.plus/v1/orders/5cf...abc.json
```

**v2:**
```python
headers = {
    "Authorization": "Bearer token...",
}
GET https://ecomplus.io/v2/:1024/customers?limit=10
PATCH https://ecomplus.io/v2/:1024/orders/5cf...abc
```

---

## Infraestrutura

| | v1 | v2 |
|---|---|---|
| Apps/integrações | Firebase apps separados por integração (app-bling-erp-v2, app-loyalty-points, etc.) | Tudo no monorepo da loja em `functions/many/` |
| Pacotes | `@ecomplus/application-sdk`, `@ecomplus/client` | `@cloudcommerce/api`, `@cloudcommerce/firebase` |
| Deploy | CI/CD por app separado | CI/CD do monorepo da loja |
| GCP project | Um projeto GCP por integração (`ecom-{app}`, ex: `ecom-bling-erp-v2`) | Um projeto GCP por loja (`ecom2{slug}`, ex: `ecom2tiasonia`) |

---

## O que mudar em cada skill para v2

### `ecomplus_client.py` (presente em todas as skills)

```python
# v1
BASE_URL = "https://api.e-com.plus/v1"

# v2
BASE_URL = "https://ecomplus.io/v2"
```

**`_url()`** — remover sufixo `.json` e incluir store_id no path (nota: `ecomplus-reports` não tem `_url()` — o sufixo `.json` está inline em `get()`; ajustar diretamente lá):
```python
# v1
def _url(self, path):
    url = f"{BASE_URL}/{path.lstrip('/')}"
    if not url.split("?")[0].endswith(".json"):
        url = url.replace("?", ".json?", 1) if "?" in url else f"{url}.json"
    return url

# v2
def _url(self, path):
    url = f"{BASE_URL}/:{self.store_id}/{path.lstrip('/')}"
    return url
```

**Headers** — trocar os 3 headers customizados por `Authorization`:
```python
# v1
self.session.headers.update({
    "X-Store-ID": self.store_id,
    "X-Access-Token": access_token,
    "X-My-ID": my_id,
    ...
})

# v2
self.session.headers.update({
    "Authorization": f"Bearer {access_token}",
    ...
})
# my_id não é necessário no v2
```

**`from_env()`** — trocar nomes das env vars:
```python
# v1
store_id = os.environ.get("ECOMPLUS_STORE_ID")
access_token = os.environ.get("ECOMPLUS_ACCESS_TOKEN")
my_id = os.environ.get("ECOMPLUS_MY_ID")

# v2
store_id = os.environ.get("ECOM_STORE_ID")
access_token = os.environ.get("ECOM_ACCESS_TOKEN")
# my_id: não necessário; auth alternativa com api_key:
# authentication_id = os.environ.get("ECOM_AUTHENTICATION_ID")
# api_key = os.environ.get("ECOM_API_KEY")
```

**`--sandbox`** — ajustar URL do sandbox quando confirmado para v2.

---

### `ecomplus-auth` (scripts de login/refresh)

| Ponto | v1 | v2 |
|---|---|---|
| Login endpoint | `POST /_login.json` com `X-Store-ID: 1` (**`1` é intencional** — o login sempre usa store_id `1` nesta etapa, independente da loja) | `POST /login` (sem store_id na URL) |
| Authenticate endpoint | `POST /_authenticate.json` | `POST /authenticate` |
| Campos no body | `{ email, pass_md5_hash }` | confirmar (possivelmente `{ email, password }` sem MD5) |
| Session file keys | `store_id`, `my_id`, `api_key`, `access_token`, `expires` | `store_id`, `authentication_id`, `api_key`, `access_token`, `expires` |
| Env vars exportadas | `ECOMPLUS_STORE_ID` `ECOMPLUS_ACCESS_TOKEN` `ECOMPLUS_MY_ID` | `ECOM_STORE_ID` `ECOM_ACCESS_TOKEN` |

---

### `ecomplus-applications` — GCP logs

Os projetos GCP das lojas v2 seguem o padrão `ecom2{slug}` (ex: `ecom2tiasonia`).
Tudo roda dentro do projeto da loja, não em projetos separados por app.

```bash
# Logs do app bling-erp na loja tiasonia (v2 monorepo)
~/google-cloud-sdk/bin/gcloud functions logs read app \
  --project=ecom2tiasonia \
  --account=servidor@e-com.club \
  --region=us-central1 \
  --limit=50
```

---

## Campos e schema dos recursos

Os schemas dos recursos (pedidos, produtos, clientes) são **muito similares** entre
v1 e v2. As principais diferenças são operacionais (URL, auth, infra), não de dados.
Verificar campos específicos consultando a documentação de cada versão quando houver dúvida.
