"""
Comparação de dois períodos de vendas lado a lado.

Se --prev-from/--prev-to não forem informados, calcula automaticamente
o período anterior de igual duração.

Uso:
    python sales_compare.py --from 2026-05-01 --to 2026-05-28
    python sales_compare.py --from 2026-05-01 --to 2026-05-28 --prev-from 2025-05-01 --prev-to 2025-05-31
"""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone

from ecomplus_client import EcomplusClient, EcomplusError, format_brl
from sales_summary import fetch_orders, summarize


def auto_prev_period(date_from: str, date_to: str) -> tuple[str, str]:
    d0 = datetime.strptime(date_from, "%Y-%m-%d")
    d1 = datetime.strptime(date_to, "%Y-%m-%d")
    span = (d1 - d0).days + 1
    prev_to = d0 - timedelta(days=1)
    prev_from = prev_to - timedelta(days=span - 1)
    return prev_from.strftime("%Y-%m-%d"), prev_to.strftime("%Y-%m-%d")


def pct_change(new: float, old: float) -> str:
    if old == 0:
        return "—"
    change = (new - old) / old * 100
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.1f}%"


def render_markdown(curr: dict, prev: dict,
                    curr_from: str, curr_to: str,
                    prev_from: str, prev_to: str) -> str:
    curr_days = (datetime.strptime(curr_to, "%Y-%m-%d") - datetime.strptime(curr_from, "%Y-%m-%d")).days + 1
    prev_days = (datetime.strptime(prev_to, "%Y-%m-%d") - datetime.strptime(prev_from, "%Y-%m-%d")).days + 1

    curr_rpd = curr["paid_revenue"] / curr_days if curr_days else 0
    prev_rpd = prev["paid_revenue"] / prev_days if prev_days else 0

    curr_opd = curr["paid_orders"] / curr_days if curr_days else 0
    prev_opd = prev["paid_orders"] / prev_days if prev_days else 0

    lines = [
        "## Comparativo de vendas\n",
        f"| Métrica | {prev_from} → {prev_to} ({prev_days}d) "
        f"| {curr_from} → {curr_to} ({curr_days}d) | Variação |",
        "|---|---:|---:|---:|",
        f"| Faturamento (pagos) | {format_brl(prev['paid_revenue'])} "
        f"| {format_brl(curr['paid_revenue'])} | {pct_change(curr['paid_revenue'], prev['paid_revenue'])} |",
        f"| Faturamento/dia | {format_brl(prev_rpd)} "
        f"| {format_brl(curr_rpd)} | {pct_change(curr_rpd, prev_rpd)} |",
        f"| Pedidos pagos | {prev['paid_orders']} ({prev_opd:.1f}/dia) "
        f"| {curr['paid_orders']} ({curr_opd:.1f}/dia) | {pct_change(curr['paid_orders'], prev['paid_orders'])} |",
        f"| Ticket médio | {format_brl(prev['average_ticket'])} "
        f"| {format_brl(curr['average_ticket'])} | {pct_change(curr['average_ticket'], prev['average_ticket'])} |",
        f"| Total pedidos | {prev['total_orders']} | {curr['total_orders']} "
        f"| {pct_change(curr['total_orders'], prev['total_orders'])} |",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="date_from", required=True)
    parser.add_argument("--to", dest="date_to", required=True)
    parser.add_argument("--prev-from", dest="prev_from")
    parser.add_argument("--prev-to", dest="prev_to")
    parser.add_argument("--format", choices=["md", "json"], default="md")
    args = parser.parse_args()

    if not args.prev_from or not args.prev_to:
        args.prev_from, args.prev_to = auto_prev_period(args.date_from, args.date_to)

    try:
        client = EcomplusClient.from_env()
        curr_orders = fetch_orders(client, args.date_from, args.date_to)
        prev_orders = fetch_orders(client, args.prev_from, args.prev_to)
        curr = summarize(curr_orders)
        prev = summarize(prev_orders)
    except EcomplusError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(json.dumps({"current": curr, "previous": prev}, indent=2, ensure_ascii=False))
    else:
        print(render_markdown(curr, prev, args.date_from, args.date_to, args.prev_from, args.prev_to))


if __name__ == "__main__":
    main()
