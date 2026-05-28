"""
Ranking de produtos mais abandonados em carrinhos num período.

Identifica itens deixados em carrinhos não finalizados (completed=false)
e os agrupa por produto, ordenando pelos mais abandonados.

Uso:
    python abandoned_carts.py --from 2026-01-01 --to 2026-05-28
    python abandoned_carts.py --from 2026-01-01 --to 2026-05-28 --limit 20 --format csv
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
                "completed": {"$eq": False},
            }
        },
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": {
                    "product_id": "$items.product_id",
                    "name": "$items.name",
                    "variation_id": "$items.variation_id",
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"count": -1}},
    ]


def render_markdown(rows: list, date_from: str, date_to: str, limit: int) -> str:
    shown = min(limit, len(rows))
    lines = [f"## Produtos mais abandonados em carrinho — {date_from} a {date_to}\n"]
    lines.append(f"Top {shown} de {len(rows)} resultados\n")
    lines.append("| # | Produto | Product ID | Variation ID | Abandonamentos |")
    lines.append("|---:|---|---|---|---:|")
    for i, row in enumerate(rows[:limit], 1):
        gid = row.get("_id", {})
        name = gid.get("name", "—")
        pid = gid.get("product_id", "—")
        vid = gid.get("variation_id") or "—"
        count = row.get("count", 0)
        lines.append(f"| {i} | {name} | `{pid}` | {vid} | {count} |")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Produtos mais abandonados em carrinhos")
    parser.add_argument("--from", dest="date_from", required=True, help="Data inicial YYYY-MM-DD")
    parser.add_argument("--to", dest="date_to", required=True, help="Data final YYYY-MM-DD")
    parser.add_argument("--limit", type=int, default=20, help="Número máximo de resultados (default 20)")
    parser.add_argument("--format", choices=["md", "json", "csv"], default="md")
    args = parser.parse_args()

    try:
        client = EcomplusClient.from_env()
        pipeline = build_pipeline(args.date_from, args.date_to)
        rows = client.aggregate("carts", pipeline)
    except EcomplusError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(json.dumps(rows[:args.limit], indent=2, ensure_ascii=False))
    elif args.format == "csv":
        writer = csv.writer(sys.stdout)
        writer.writerow(["rank", "name", "product_id", "variation_id", "abandonment_count"])
        for i, row in enumerate(rows[:args.limit], 1):
            gid = row.get("_id", {})
            writer.writerow([
                i,
                gid.get("name", ""),
                gid.get("product_id", ""),
                gid.get("variation_id", "") or "",
                row.get("count", 0),
            ])
    else:
        print(render_markdown(rows, args.date_from, args.date_to, args.limit))


if __name__ == "__main__":
    main()
