"""
Ranking de clientes por valor total gasto no período (LTV parcial).

Agrega pedidos pagos por comprador e rankeia por receita.

Uso:
    python top_customers.py --from 2026-05-01 --to 2026-05-28
    python top_customers.py --from 2026-05-01 --to 2026-05-28 --limit 30
    python top_customers.py --from 2026-05-01 --to 2026-05-28 --format csv
"""
import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone

from ecomplus_client import EcomplusClient, EcomplusError, format_brl


def fetch_and_aggregate(client: EcomplusClient, date_from: str, date_to: str) -> list[dict]:
    params = {
        "created_at>=": f"{date_from}T00:00:00.000Z",
        "created_at<=": f"{date_to}T23:59:59.999Z",
        "financial_status.current": "paid",
        "fields": "status,financial_status,amount,buyers",
    }

    customers: dict[str, dict] = defaultdict(lambda: {
        "name": "",
        "email": "",
        "orders": 0,
        "revenue": 0.0,
    })

    for order in client.list_all("orders", params=params):
        if order.get("status") == "cancelled":
            continue
        total = (order.get("amount") or {}).get("total", 0.0) or 0.0
        buyers = order.get("buyers") or []
        buyer = buyers[0] if buyers else {}
        email = buyer.get("main_email", "") or buyer.get("_id", "desconhecido")
        name = buyer.get("display_name", "") or buyer.get("name", {}).get("full", email)

        c = customers[email]
        c["email"] = email
        c["name"] = name
        c["orders"] += 1
        c["revenue"] += total

    rows = list(customers.values())
    rows.sort(key=lambda x: -x["revenue"])
    return rows


def render_markdown(rows: list[dict], date_from: str, date_to: str, limit: int) -> str:
    d0 = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    d1 = datetime.strptime(date_to, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    days = (d1 - d0).days + 1

    lines = [
        f"## Top {limit} clientes — {date_from} a {date_to} ({days} dias)\n",
        "| # | Cliente | E-mail | Pedidos | Total gasto |",
        "|---:|---|---|---:|---:|",
    ]
    for i, c in enumerate(rows[:limit], 1):
        lines.append(
            f"| {i} | {str(c['name'])[:40]} | {c['email']} "
            f"| {c['orders']} | {format_brl(c['revenue'])} |"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="date_from", required=True)
    parser.add_argument("--to", dest="date_to", required=True)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--format", choices=["md", "json", "csv"], default="md")
    args = parser.parse_args()

    try:
        client = EcomplusClient.from_env()
        rows = fetch_and_aggregate(client, args.date_from, args.date_to)
    except EcomplusError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(json.dumps(rows[:args.limit], indent=2, ensure_ascii=False))
    elif args.format == "csv":
        writer = csv.DictWriter(sys.stdout, fieldnames=["name", "email", "orders", "revenue"])
        writer.writeheader()
        writer.writerows(rows[:args.limit])
    else:
        print(render_markdown(rows, args.date_from, args.date_to, args.limit))


if __name__ == "__main__":
    main()
