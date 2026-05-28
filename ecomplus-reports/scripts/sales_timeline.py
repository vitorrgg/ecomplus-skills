"""
Evolução de vendas ao longo do tempo (série temporal).

Agrega pedidos pagos por dia, semana ou mês e mostra faturamento,
pedidos e ticket médio em cada bucket.

Uso:
    python sales_timeline.py --from 2026-04-01 --to 2026-05-28
    python sales_timeline.py --from 2026-01-01 --to 2026-05-28 --group-by month
    python sales_timeline.py --from 2026-05-01 --to 2026-05-28 --group-by day --format csv
"""
import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone

from ecomplus_client import EcomplusClient, EcomplusError, format_brl


def bucket_key(created_at: str, group_by: str) -> str:
    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    if group_by == "month":
        return dt.strftime("%Y-%m")
    if group_by == "week":
        iso = dt.isocalendar()
        return f"{iso[0]}-W{iso[1]:02d}"
    return dt.strftime("%Y-%m-%d")


def fetch_and_group(client: EcomplusClient, date_from: str, date_to: str, group_by: str) -> list[dict]:
    params = {
        "created_at>=": f"{date_from}T00:00:00.000Z",
        "created_at<=": f"{date_to}T23:59:59.999Z",
        "fields": "status,financial_status,amount,created_at",
    }

    buckets: dict[str, dict] = defaultdict(lambda: {"revenue": 0.0, "orders": 0})

    for order in client.list_all("orders", params=params):
        fin = (order.get("financial_status") or {}).get("current", "")
        if fin != "paid" or order.get("status") == "cancelled":
            continue
        key = bucket_key(order["created_at"], group_by)
        total = (order.get("amount") or {}).get("total", 0.0) or 0.0
        buckets[key]["revenue"] += total
        buckets[key]["orders"] += 1

    rows = []
    for key in sorted(buckets):
        b = buckets[key]
        avg = b["revenue"] / b["orders"] if b["orders"] else 0.0
        rows.append({"period": key, "revenue": b["revenue"], "orders": b["orders"], "avg_ticket": avg})
    return rows


def render_markdown(rows: list[dict], date_from: str, date_to: str, group_by: str) -> str:
    label = {"day": "dia", "week": "semana", "month": "mês"}[group_by]
    total_rev = sum(r["revenue"] for r in rows)
    total_orders = sum(r["orders"] for r in rows)

    lines = [
        f"## Evolução de vendas por {label} — {date_from} a {date_to}\n",
        f"**Total no período:** {format_brl(total_rev)} em {total_orders} pedidos pagos\n",
        f"| Período | Pedidos | Faturamento | Ticket médio |",
        "|---|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['period']} | {r['orders']} "
            f"| {format_brl(r['revenue'])} | {format_brl(r['avg_ticket'])} |"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="date_from", required=True)
    parser.add_argument("--to", dest="date_to", required=True)
    parser.add_argument("--group-by", choices=["day", "week", "month"], default="day")
    parser.add_argument("--format", choices=["md", "json", "csv"], default="md")
    args = parser.parse_args()

    try:
        client = EcomplusClient.from_env()
        rows = fetch_and_group(client, args.date_from, args.date_to, args.group_by)
    except EcomplusError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    elif args.format == "csv":
        writer = csv.DictWriter(sys.stdout, fieldnames=["period", "orders", "revenue", "avg_ticket"])
        writer.writeheader()
        writer.writerows(rows)
    else:
        print(render_markdown(rows, args.date_from, args.date_to, args.group_by))


if __name__ == "__main__":
    main()
