"""
Ranking de produtos mais pedidos num período (server-side via aggregation).

Filtra apenas pedidos pagos e não cancelados, desagrupa os itens,
agrupa por produto_id somando quantidades e ordena pelo total vendido.

Diferença em relação a ecomplus-reports/top_products.py: este script
usa o endpoint $aggregate.json, então o servidor faz o agrupamento —
mais eficiente para lojas com grande volume de pedidos.

Uso:
    python top_products_agg.py --from 2026-01-01 --to 2026-05-28
    python top_products_agg.py --from 2026-01-01 --to 2026-05-28 --limit 30 --format csv
"""
import argparse
import csv
import json
import sys

from ecomplus_client import EcomplusClient, EcomplusError


def build_pipeline(date_from: str, date_to: str) -> list:
    return [
        {
            "$match": {
                "created_at": {
                    "$gte": f"{date_from}T00:00:00.000Z",
                    "$lte": f"{date_to}T23:59:59.999Z",
                },
                "status": {"$ne": "cancelled"},
                "financial_status.current": {"$eq": "paid"},
            }
        },
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": "$items.product_id",
                "name": {"$first": "$items.name"},
                "sku": {"$first": "$items.sku"},
                "quantity": {"$sum": "$items.quantity"},
                "orders": {"$sum": 1},
            }
        },
        {"$sort": {"quantity": -1}},
    ]


def render_markdown(rows: list, date_from: str, date_to: str, limit: int) -> str:
    shown = min(limit, len(rows))
    lines = [f"## Produtos mais pedidos — {date_from} a {date_to}\n"]
    lines.append(f"Top {shown} (pedidos pagos, exceto cancelados)\n")
    lines.append("| # | Produto | SKU | Qtd vendida | Nº pedidos | Product ID |")
    lines.append("|---:|---|---|---:|---:|---|")
    for i, row in enumerate(rows[:limit], 1):
        qty = row.get("quantity", 0)
        qty_str = f"{int(qty)}" if qty == int(qty) else f"{qty:.2f}"
        lines.append(
            f"| {i} | {row.get('name', '—')} | {row.get('sku', '—')} "
            f"| {qty_str} | {row.get('orders', 0)} | `{row['_id']}` |"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Produtos mais pedidos por quantidade (aggregation)")
    parser.add_argument("--from", dest="date_from", required=True, help="Data inicial YYYY-MM-DD")
    parser.add_argument("--to", dest="date_to", required=True, help="Data final YYYY-MM-DD")
    parser.add_argument("--limit", type=int, default=20, help="Número máximo de resultados (default 20)")
    parser.add_argument("--format", choices=["md", "json", "csv"], default="md")
    args = parser.parse_args()

    try:
        client = EcomplusClient.from_env()
        pipeline = build_pipeline(args.date_from, args.date_to)
        rows = client.aggregate("orders", pipeline)
    except EcomplusError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(json.dumps(rows[:args.limit], indent=2, ensure_ascii=False))
    elif args.format == "csv":
        writer = csv.writer(sys.stdout)
        writer.writerow(["rank", "name", "sku", "product_id", "quantity", "orders"])
        for i, row in enumerate(rows[:args.limit], 1):
            writer.writerow([
                i,
                row.get("name", ""),
                row.get("sku", ""),
                row["_id"],
                row.get("quantity", 0),
                row.get("orders", 0),
            ])
    else:
        print(render_markdown(rows, args.date_from, args.date_to, args.limit))


if __name__ == "__main__":
    main()
