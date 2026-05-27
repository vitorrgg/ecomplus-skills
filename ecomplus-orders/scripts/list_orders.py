#!/usr/bin/env python3
"""
Lista pedidos da E-Com Plus com filtros.

Uso:
  python list_orders.py --financial-status paid
  python list_orders.py --status open --from 2026-05-01 --to 2026-05-31
  python list_orders.py --buyer cliente@exemplo.com
  python list_orders.py --fulfillment-status shipped --limit 100 --format csv
"""
import argparse
import csv
import io
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from ecomplus_client import EcomplusClient, EcomplusError, format_brl

FINANCIAL_STATUS = [
    "pending", "under_analysis", "authorized", "paid",
    "in_dispute", "refunded", "voided", "unknown",
]
FULFILLMENT_STATUS = [
    "invoice_issued", "in_production", "in_separation", "ready_for_shipping",
    "shipped", "delivered", "partially_delivered", "returned",
]


def fmt_date(iso: str) -> str:
    if not iso:
        return ""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%d/%m/%Y %H:%M")
    except Exception:
        return iso[:10]


def buyer_name(order: dict) -> str:
    buyers = order.get("buyers") or []
    if not buyers:
        return ""
    b = buyers[0]
    n = b.get("name") or {}
    parts = [n.get("given_name", ""), n.get("family_name", "")]
    return b.get("display_name") or " ".join(p for p in parts if p)


def buyer_email(order: dict) -> str:
    buyers = order.get("buyers") or []
    return buyers[0].get("main_email", "") if buyers else ""


def main():
    parser = argparse.ArgumentParser(description="Lista pedidos E-Com Plus")
    parser.add_argument("--status", choices=["open", "cancelled"],
                        help="Status principal do pedido")
    parser.add_argument("--financial-status", dest="financial_status",
                        choices=FINANCIAL_STATUS, help="Status de pagamento")
    parser.add_argument("--fulfillment-status", dest="fulfillment_status",
                        choices=FULFILLMENT_STATUS, help="Status de envio")
    parser.add_argument("--from", dest="date_from", metavar="YYYY-MM-DD",
                        help="Data de início (created_at)")
    parser.add_argument("--to", dest="date_to", metavar="YYYY-MM-DD",
                        help="Data de fim (created_at)")
    parser.add_argument("--buyer", metavar="EMAIL",
                        help="Filtrar por e-mail do comprador")
    parser.add_argument("--limit", type=int, default=50,
                        help="Máximo de resultados (default: 50)")
    parser.add_argument("--format", choices=["md", "csv", "json"], default="md")
    parser.add_argument("--sandbox", action="store_true")
    args = parser.parse_args()

    params = {
        "sort": "-created_at",
        "fields": "_id,number,status,financial_status,fulfillment_status,"
                  "amount.total,buyers.display_name,buyers.name,buyers.main_email,"
                  "payment_method_label,created_at",
    }

    if args.status:
        params["status"] = args.status
    if args.financial_status:
        params["financial_status.current"] = args.financial_status
    if args.fulfillment_status:
        params["fulfillment_status.current"] = args.fulfillment_status
    if args.date_from:
        params["created_at>="] = f"{args.date_from}T00:00:00.000Z"
    if args.date_to:
        params["created_at<="] = f"{args.date_to}T23:59:59.999Z"
    if args.buyer:
        params["buyers.main_email"] = args.buyer

    try:
        client = EcomplusClient.from_env()
        if args.sandbox:
            import ecomplus_client
            ecomplus_client.BASE_URL = "https://sandbox.e-com.plus/v1"

        orders = []
        for order in client.list_all("orders", params=params):
            orders.append(order)
            if len(orders) >= args.limit:
                break

        if not orders:
            print("Nenhum pedido encontrado com os filtros informados.")
            return

        if args.format == "json":
            print(json.dumps(orders, ensure_ascii=False, indent=2))
            return

        rows = []
        for o in orders:
            rows.append({
                "Número": o.get("number", ""),
                "Data": fmt_date(o.get("created_at", "")),
                "Status": o.get("status", ""),
                "Pagamento": (o.get("financial_status") or {}).get("current", ""),
                "Envio": (o.get("fulfillment_status") or {}).get("current", ""),
                "Comprador": buyer_name(o),
                "E-mail": buyer_email(o),
                "Total": format_brl(o.get("amount", {}).get("total", 0)),
            })

        if args.format == "csv":
            writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0].keys()),
                                    lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
            return

        # Markdown
        total_val = sum(o.get("amount", {}).get("total", 0) for o in orders)
        print(f"**{len(orders)} pedido(s) encontrado(s)** — Total: **{format_brl(total_val)}**\n")
        print("| Número | Data | Status | Pagamento | Envio | Comprador | Total |")
        print("|---|---|---|---|---|---|---|")
        for r in rows:
            print(f"| #{r['Número']} | {r['Data']} | {r['Status']} | {r['Pagamento']} "
                  f"| {r['Envio']} | {r['Comprador']} | {r['Total']} |")

        if len(orders) >= args.limit:
            print(f"\n> Resultado limitado a {args.limit} pedidos. "
                  "Use `--limit N` para ampliar ou `--format csv` para exportar.")

    except EcomplusError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
