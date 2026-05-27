#!/usr/bin/env python3
"""
Exibe o cadastro completo de um cliente E-Com Plus.

Uso:
  python get_customer.py --email cliente@exemplo.com
  python get_customer.py --doc 12345678901
  python get_customer.py --id 5cf...abc
  python get_customer.py --email cliente@exemplo.com --orders
  python get_customer.py --email cliente@exemplo.com --format json
"""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from ecomplus_client import EcomplusClient, EcomplusError, format_brl


def full_name(customer: dict) -> str:
    n = customer.get("name") or {}
    parts = [n.get("given_name", ""), n.get("middle_name", ""), n.get("family_name", "")]
    return customer.get("display_name") or " ".join(p for p in parts if p)


def fmt_date(iso: str) -> str:
    if not iso:
        return ""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%d/%m/%Y %H:%M")
    except Exception:
        return iso[:10]


def render_md(customer: dict, orders: list) -> None:
    name = full_name(customer)
    print(f"## {name or customer.get('main_email', '?')}\n")

    print("| Campo | Valor |")
    print("|---|---|")
    print(f"| ID | `{customer.get('_id', '')}` |")
    if customer.get("main_email"):
        print(f"| E-mail | {customer['main_email']} |")
    if customer.get("display_name"):
        print(f"| Nome exibição | {customer['display_name']} |")
    if customer.get("doc_number"):
        doc = customer["doc_number"]
        tipo = "CPF" if customer.get("registry_type") == "p" else "CNPJ"
        print(f"| {tipo} | {doc} |")
    phones = customer.get("phones") or []
    if phones:
        nums = " / ".join(f"+{p.get('country_code', '')}{p.get('number', '')}" for p in phones)
        print(f"| Telefones | {nums} |")
    bd = customer.get("birth_date") or {}
    if bd.get("day"):
        print(f"| Nascimento | {bd['day']:02d}/{bd['month']:02d}/{bd['year']} |")
    print(f"| Ativo | {'✓ sim' if customer.get('enabled', True) else '✗ não'} |")
    if customer.get("orders_count"):
        print(f"| Total de pedidos | {customer['orders_count']} |")
    if customer.get("orders_total_value"):
        print(f"| Total gasto (LTV) | {format_brl(customer['orders_total_value'])} |")
    created = fmt_date(customer.get("created_at", ""))
    if created:
        print(f"| Cadastrado em | {created} |")
    if customer.get("referral"):
        print(f"| Referral | {customer['referral']} |")

    # Notas internas
    if customer.get("staff_notes"):
        print(f"\n> **Notas da equipe:** {customer['staff_notes']}")

    # Endereços
    addresses = customer.get("addresses") or []
    if addresses:
        print(f"\n### Endereços ({len(addresses)})\n")
        for addr in addresses:
            default_mark = " ★ (padrão)" if addr.get("default") else ""
            parts = [
                addr.get("name", ""),
                f"{addr.get('street', '')} {addr.get('number', '')}".strip(),
                addr.get("complement", ""),
                addr.get("borough", ""),
                f"{addr.get('city', '')} - {addr.get('province_code', '')}".strip(" -"),
                addr.get("zip", ""),
            ]
            print(f"- {' / '.join(p for p in parts if p)}{default_mark}")

    # Pontos de fidelidade
    points_entries = customer.get("loyalty_points_entries") or []
    if points_entries:
        from datetime import datetime, timezone
        now = datetime.now(tz=timezone.utc)
        total_active = 0.0
        total_earned = 0.0
        for e in points_entries:
            ep = e.get("earned_points", 0)
            ap = e.get("active_points", 0)
            total_earned += ep
            vt = e.get("valid_thru")
            if vt:
                try:
                    exp = datetime.fromisoformat(vt.replace("Z", "+00:00"))
                    if exp > now:
                        total_active += ap
                except Exception:
                    total_active += ap
            else:
                total_active += ap
        print(f"\n### Pontos de fidelidade\n")
        print(f"- Ganhos: **{round(total_earned, 2)}**")
        print(f"- Ativos (válidos): **{round(total_active, 2)}**")

    # Pedidos recentes
    if orders:
        print(f"\n### Últimos pedidos\n")
        print("| Número | Data | Pagamento | Total |")
        print("|---|---|---|---|")
        for o in orders[:8]:
            fin = (o.get("financial_status") or {}).get("current", "")
            total = (o.get("amount") or {}).get("total", 0)
            print(f"| #{o.get('number', '')} | {fmt_date(o.get('created_at', ''))} "
                  f"| {fin} | {format_brl(total)} |")


def main():
    parser = argparse.ArgumentParser(description="Detalhe de um cliente E-Com Plus")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--email", help="E-mail do cliente")
    group.add_argument("--doc", help="CPF ou CNPJ (só dígitos ou formatado)")
    group.add_argument("--id", dest="customer_id", help="_id do cliente")
    parser.add_argument("--orders", action="store_true",
                        help="Buscar e exibir últimos pedidos do cliente")
    parser.add_argument("--format", choices=["md", "json"], default="md")
    parser.add_argument("--sandbox", action="store_true")
    args = parser.parse_args()

    try:
        client = EcomplusClient.from_env()
        if args.sandbox:
            import ecomplus_client
            ecomplus_client.BASE_URL = "https://sandbox.e-com.plus/v1"

        if args.customer_id:
            customer = client.get(f"customers/{args.customer_id}")
        else:
            customer = client.find_customer(email=args.email, doc=args.doc)

        orders = []
        if args.orders or args.format == "md":
            customer_id = customer["_id"]
            body = client.get("orders", params={
                "buyers._id": customer_id,
                "sort": "-created_at",
                "limit": 8,
                "fields": "_id,number,amount,created_at,financial_status,fulfillment_status",
            })
            orders = body.get("result", [])

        if args.format == "json":
            out = dict(customer)
            if orders:
                out["_recent_orders"] = orders
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            render_md(customer, orders)

    except EcomplusError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
