# GCP Logs — Apps E-Com Plus (Firebase Cloud Functions)

Os aplicativos E-Com Plus rodam como Firebase Cloud Functions. Os logs são
consultados pelo `gcloud` CLI ou pelo `firebase` CLI.

## Localização do gcloud

```bash
~/google-cloud-sdk/bin/gcloud
```

## Contas autenticadas

| Conta | Status |
|---|---|
| `servidor@e-com.club` | padrão/ativo (`gcloud config`) |
| `vitorrggm@gmail.com` | disponível (`gcloud auth list`) |

Para trocar: `~/google-cloud-sdk/bin/gcloud config set account servidor@e-com.club`

## Padrão dos projetos GCP

- Apps da plataforma (bling, loyalty, tiny, etc.):
  `FIREBASE_PROJECT_ID` está no GitHub Secrets do repo — não fica local
- Lojas com deploy customizado: `ecom2{slug-da-loja}` (ex: `ecom2tiasonia`)
- Apps com `.firebaserc` local:

| Diretório | Projeto GCP |
|---|---|
| `~/app-freteclick` | `ecom-freteclick` |
| `~/pagseguro-v2` | `ecom-pagseguro-v2` |
| `~/barradoce` | `ecom2barradoce` |
| `~/ladorosa` | `ecom2ladorosa` |
| `~/tiasonia` | `ecom2tiasonia` |
| `~/efacini` | `ecom2efacini` |
| `~/ladofit` | `ecom2ladofit` |

Para descobrir o projeto GCP de um app sem `.firebaserc`: consultar o campo
`auth_callback_uri` ou `base_uri` no documento do app via
`GET /applications/{id}.json` — o URL segue o padrão
`https://us-central1-{FIREBASE_PROJECT_ID}.cloudfunctions.net/app/`.

## Nome da função

Todos os apps E-Com Plus usam **`app`** como nome da Cloud Function por padrão
(`functionName = 'app'`). Funções customizadas de loja podem ter outros nomes
(ex: `custom-cronUxtmsTracking`).

Para listar todas as funções de um projeto:
```bash
~/google-cloud-sdk/bin/gcloud functions list \
  --project=FIREBASE_PROJECT_ID \
  --account=servidor@e-com.club
```

## Consultar logs de uma função

```bash
~/google-cloud-sdk/bin/gcloud functions logs read app \
  --project=FIREBASE_PROJECT_ID \
  --account=servidor@e-com.club \
  --region=us-central1 \
  --limit=50
```

### Parâmetros úteis

| Flag | Descrição |
|---|---|
| `--limit=N` | Número de entradas (padrão 20, máx 1000) |
| `--region=us-central1` | Região (padrão dos apps E-Com Plus) |
| `--min-log-level=ERROR` | Filtrar por nível: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `--start-time="2026-05-27T00:00:00Z"` | Logs a partir de uma data |
| `--end-time="2026-05-27T23:59:59Z"` | Logs até uma data |

### Exemplos práticos

```bash
# Últimos 100 logs do app bling-erp (project ID no secrets do repo)
~/google-cloud-sdk/bin/gcloud functions logs read app \
  --project=ecom-bling-erp-v2 \
  --account=servidor@e-com.club \
  --region=us-central1 \
  --limit=100

# Só erros da última hora — loja tiasonia
~/google-cloud-sdk/bin/gcloud functions logs read app \
  --project=ecom2tiasonia \
  --account=servidor@e-com.club \
  --region=us-central1 \
  --min-log-level=ERROR \
  --limit=50

# Função customizada de cron
~/google-cloud-sdk/bin/gcloud functions logs read custom-cronUxtmsTracking \
  --project=ecom2tiasonia \
  --account=vitorrggm@gmail.com \
  --region=us-east4 \
  --limit=50
```

## Alternativa: Firebase CLI

```bash
# Firebase CLI está em /mnt/c/Users/vitor/AppData/Roaming/npm/firebase (v15.15.0)
firebase functions:log --project=FIREBASE_PROJECT_ID

# Com --only para função específica
firebase functions:log --only app --project=FIREBASE_PROJECT_ID
```

## Login / reautenticação

```bash
# Login interativo
~/google-cloud-sdk/bin/gcloud auth login

# Ver contas disponíveis
~/google-cloud-sdk/bin/gcloud auth list

# Trocar conta ativa
~/google-cloud-sdk/bin/gcloud config set account vitorrggm@gmail.com
```
