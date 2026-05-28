"""
Ranking de campanhas UTM por número de pedidos num período.

Agrupa pedidos pelo campo utm.campaign e ordena pela quantidade,
permitindo identificar quais campanhas geraram mais conversões.

Uso:
    python campaigns.py --from 2026-01-01 --to 2026-05-28
    python campaigns.py --from 2026-01-01 --to 2026-05-28 --format csv
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
                "utm.campaign": {"$exists": True},
            }
        },
        {
            "$group": {
                "_id": "$utm.campaign",
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"count": -1}},
    ]


def render_markdown(rows: list, date_from: str, date_to: str) -> str:
    total = sum(r.get("count", 0) for r in rows)
    lines = [f"## Pedidos por campanha UTM — {date_from} a {date_to}\n"]
    lines.append(f"**Total de pedidos com campanha registrada:** {total} em {len(rows)} campanhas\n")
    lines.append("| # | Campanha | Pedidos | % do total |")
    lines.append("|---:|---|---:|---:|")
    for i, row in enumerate(rows, 1):
        count = row.get("count", 0)
        pct = (count / total * 100) if total else 0
        lines.append(f"| {i} | {row['_id']} | {count} | {pct:.1f}% |")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Pedidos por campanha UTM")
    parser.add_argument("--from", dest="date_from", required=True, help="Data inicial YYYY-MM-DD")
    parser.add_argument("--to", dest="date_to", required=True, help="Data final YYYY-MM-DD")
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
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    elif args.format == "csv":
        writer = csv.writer(sys.stdout)
        writer.writerow(["rank", "campaign", "orders"])
        for i, row in enumerate(rows, 1):
            writer.writerow([i, row["_id"], row.get("count", 0)])
    else:
        print(render_markdown(rows, args.date_from, args.date_to))


if __name__ == "__main__":
    main()
