"""
Ranking de produtos mais vendidos no período.

Agrega os items de pedidos pagos (não cancelados) e rankeia por
receita ou por quantidade vendida.

Uso:
    python top_products.py --from 2026-05-01 --to 2026-05-28
    python top_products.py --from 2026-05-01 --to 2026-05-28 --limit 30 --sort-by units
    python top_products.py --from 2026-05-01 --to 2026-05-28 --format csv
"""
import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone

from ecomplus_client import EcomplusClient, EcomplusError, format_brl


def fetch_paid_orders(client: EcomplusClient, date_from: str, date_to: str):
    params = {
        "created_at>=": f"{date_from}T00:00:00.000Z",
        "created_at<=": f"{date_to}T23:59:59.999Z",
        "financial_status.current": "paid",
        "fields": "status,financial_status,items",
    }
    for order in client.list_all("orders", params=params):
        if order.get("status") != "cancelled":
            yield order


def aggregate_products(orders) -> list[dict]:
    products: dict[str, dict] = defaultdict(lambda: {
        "sku": "",
        "name": "",
        "units": 0,
        "revenue": 0.0,
        "orders": 0,
    })

    for order in orders:
        seen_skus = set()
        for item in order.get("items") or []:
            sku = item.get("sku") or item.get("product_id") or "?"
            name = item.get("name", "")
            qty = item.get("quantity", 0) or 0
            price = item.get("final_price", 0.0) or 0.0

            p = products[sku]
            p["sku"] = sku
            p["name"] = name
            p["units"] += qty
            p["revenue"] += qty * price
            if sku not in seen_skus:
                p["orders"] += 1
                seen_skus.add(sku)

    return list(products.values())


def render_markdown(rows: list[dict], date_from: str, date_to: str,
                    sort_by: str, limit: int) -> str:
    d0 = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    d1 = datetime.strptime(date_to, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    days = (d1 - d0).days + 1

    sort_label = "receita" if sort_by == "revenue" else "unidades"
    lines = [
        f"## Top {limit} produtos — {date_from} a {date_to} ({days} dias)",
        f"_Ordenado por {sort_label}. Apenas pedidos pagos e não cancelados._\n",
        "| # | SKU | Produto | Unidades | Receita | Pedidos |",
        "|---:|---|---|---:|---:|---:|",
    ]
    for i, p in enumerate(rows, 1):
        lines.append(
            f"| {i} | {p['sku']} | {p['name'][:50]} "
            f"| {p['units']} | {format_brl(p['revenue'])} | {p['orders']} |"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="date_from", required=True)
    parser.add_argument("--to", dest="date_to", required=True)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--sort-by", choices=["revenue", "units"], default="revenue")
    parser.add_argument("--format", choices=["md", "json", "csv"], default="md")
    args = parser.parse_args()

    try:
        client = EcomplusClient.from_env()
        orders = list(fetch_paid_orders(client, args.date_from, args.date_to))
        rows = aggregate_products(orders)
    except EcomplusError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        sys.exit(1)

    rows.sort(key=lambda x: -x[args.sort_by])
    rows = rows[: args.limit]

    if args.format == "json":
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    elif args.format == "csv":
        writer = csv.DictWriter(sys.stdout, fieldnames=["sku", "name", "units", "revenue", "orders"])
        writer.writeheader()
        writer.writerows(rows)
    else:
        print(render_markdown(rows, args.date_from, args.date_to, args.sort_by, args.limit))


if __name__ == "__main__":
    main()
