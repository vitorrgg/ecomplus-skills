# Econpost — Skills E-Com Plus

Este repo contém skills para o Claude Code interagir com a API REST
da E-Com Plus (https://api.e-com.plus/v1/), focadas em relatórios,
edição de loja e diagnóstico de integrações.

## Convenções

- Cada skill é uma pasta com SKILL.md + scripts/ + references/
- Scripts Python 3, sempre com argparse e --format md|csv|json (default md)
- Output default em markdown para renderizar bem na interface chat futura
- Autenticação via env vars: ECOMPLUS_STORE_ID, ECOMPLUS_ACCESS_TOKEN, ECOMPLUS_MY_ID
- Valores monetários em BRL formato brasileiro (R$ 1.234,56)
- Datas: API em UTC, exibição em America/Sao_Paulo
- Receita = financial_status.current == "paid" AND status != "cancelled"

## Stack alvo da interface final
Chat embedado tipo Claude Code, usando a API Anthropic + estas skills.

## Roadmap das skills
- [x] ecomplus-reports
- [x] ecomplus-auth
- [x] ecomplus-orders
- [x] ecomplus-products
- [x] ecomplus-customers
- [x] ecomplus-applications

## Testes
Sempre rodar contra sandbox (https://sandbox.e-com.plus/v1/) antes de mexer em produção.
