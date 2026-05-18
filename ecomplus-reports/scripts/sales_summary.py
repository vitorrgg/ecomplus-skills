"""
Relatório de resumo de vendas para uma loja E-Com Plus.

Calcula, em um período:
- faturamento total (apenas pedidos pagos)
- número de pedidos
- ticket médio
- breakdown por status de pagamento
- breakdown por status do pedido

Uso:
    python sales_summary.py --from 2026-05-01 --to 2026-05-18
    python sales_summary.py --from 2026-05-01 --to 2026-05-18 --format json
"""
import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone

from ecomplus_client import EcomplusClient, EcomplusError, format_brl


def fetch_orders(client: EcomplusClient, date_from: str, date_to: str):
    """
    Busca pedidos no período. A API E-Com Plus aceita filtros de data
    no campo created_at via query string com operadores >= e <=.
    """
    params = {
        # ISO 8601 com Z (UTC). A API trata datas em UTC.
        "created_at>=": f"{date_from}T00:00:00.000Z",
        "created_at<=": f"{date_to}T23:59:59.999Z",
        "fields": "number,status,amount,financial_status,payment_method_label,created_at",
        "sort": "-created_at",
    }
    return list(client.list_all("orders", params=params))


def summarize(orders: list) -> dict:
    paid_revenue = 0.0
    paid_count = 0
    by_financial = defaultdict(lambda: {"count": 0, "total": 0.0})
    by_status = defaultdict(int)

    for o in orders:
        status = o.get("status", "unknown")
        fin = (o.get("financial_status") or {}).get("current", "unknown")
        amount = (o.get("amount") or {}).get("total", 0.0) or 0.0

        by_status[status] += 1
        by_financial[fin]["count"] += 1
        by_financial[fin]["total"] += amount

        # Receita "de verdade": só pedidos pagos e não cancelados
        if fin == "paid" and status != "cancelled":
            paid_revenue += amount
            paid_count += 1

    avg_ticket = paid_revenue / paid_count if paid_count else 0.0

    return {
        "total_orders": len(orders),
        "paid_orders": paid_count,
        "paid_revenue": paid_revenue,
        "average_ticket": avg_ticket,
        "by_financial_status": dict(by_financial),
        "by_order_status": dict(by_status),
    }


def render_markdown(summary: dict, date_from: str, date_to: str) -> str:
    lines = []
    lines.append(f"## Resumo de vendas — {date_from} a {date_to}\n")
    lines.append(f"**Faturamento (pagos):** {format_brl(summary['paid_revenue'])}")
    lines.append(f"**Pedidos pagos:** {summary['paid_orders']}")
    lines.append(f"**Ticket médio:** {format_brl(summary['average_ticket'])}")
    lines.append(f"**Total de pedidos no período:** {summary['total_orders']} (inclui pendentes e cancelados)\n")

    lines.append("### Por status de pagamento\n")
    lines.append("| Status | Pedidos | Valor |")
    lines.append("|---|---:|---:|")
    for status, data in sorted(summary["by_financial_status"].items(), key=lambda x: -x[1]["total"]):
        lines.append(f"| {status} | {data['count']} | {format_brl(data['total'])} |")

    lines.append("\n### Por status do pedido\n")
    lines.append("| Status | Pedidos |")
    lines.append("|---|---:|")
    for status, count in sorted(summary["by_order_status"].items(), key=lambda x: -x[1]):
        lines.append(f"| {status} | {count} |")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="date_from", required=True, help="Data inicial YYYY-MM-DD")
    parser.add_argument("--to", dest="date_to", required=True, help="Data final YYYY-MM-DD")
    parser.add_argument("--format", choices=["md", "json", "csv"], default="md")
    args = parser.parse_args()

    try:
        client = EcomplusClient.from_env()
        orders = fetch_orders(client, args.date_from, args.date_to)
        summary = summarize(orders)
    except EcomplusError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    elif args.format == "csv":
        print("metric,value")
        print(f"paid_revenue,{summary['paid_revenue']:.2f}")
        print(f"paid_orders,{summary['paid_orders']}")
        print(f"average_ticket,{summary['average_ticket']:.2f}")
        print(f"total_orders,{summary['total_orders']}")
    else:
        print(render_markdown(summary, args.date_from, args.date_to))


if __name__ == "__main__":
    main()
