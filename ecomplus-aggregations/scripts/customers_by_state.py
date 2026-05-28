"""
Agrupa clientes por estado (UF) para campanhas regionais.

Usa o campo addresses.province_code dos cadastros de clientes.
Produz um resumo de volume por estado e, com --detail, a lista de clientes.

Uso:
    python customers_by_state.py                     # resumo por estado
    python customers_by_state.py --detail            # com lista de clientes
    python customers_by_state.py --state SP          # apenas São Paulo
    python customers_by_state.py --state SP --detail --format csv
"""
import argparse
import csv
import json
import sys

from ecomplus_client import EcomplusClient, EcomplusError


def build_pipeline(state: str = None) -> list:
    if state:
        match_stage = {"addresses.province_code": state.upper()}
    else:
        match_stage = {"addresses.0": {"$exists": True}}

    return [
        {"$match": match_stage},
        {
            "$group": {
                # arrayElemAt pega o primeiro endereço — evita agrupar pelo array inteiro
                "_id": {"$arrayElemAt": ["$addresses.province_code", 0]},
                "total": {"$sum": 1},
                "customers": {
                    "$addToSet": {
                        "id": "$_id",
                        "name": {
                            "$concat": [
                                "$name.given_name",
                                " ",
                                "$name.family_name",
                            ]
                        },
                        "email": "$main_email",
                    }
                },
            }
        },
        {"$sort": {"total": -1}},
    ]


def render_markdown(rows: list, state: str = None, detail: bool = False) -> str:
    title = f"Clientes no estado {state.upper()}" if state else "Clientes por estado"
    total_all = sum(r.get("total", 0) for r in rows)
    lines = [f"## {title}\n"]
    lines.append(f"**Total geral:** {total_all} cliente{'s' if total_all != 1 else ''} em {len(rows)} estado(s)\n")
    lines.append("| Estado | Clientes | % |")
    lines.append("|---|---:|---:|")
    for row in rows:
        pct = (row.get("total", 0) / total_all * 100) if total_all else 0
        lines.append(f"| **{row['_id']}** | {row.get('total', 0)} | {pct:.1f}% |")

    if detail:
        lines.append("")
        for row in rows:
            s = row.get("_id", "?")
            total = row.get("total", 0)
            lines.append(f"\n### {s} ({total} cliente{'s' if total != 1 else ''})\n")
            lines.append("| Nome | E-mail | Customer ID |")
            lines.append("|---|---|---|")
            for c in sorted(row.get("customers", []), key=lambda x: x.get("name", "")):
                lines.append(f"| {c.get('name', '—')} | {c.get('email', '—')} | `{c.get('id', '—')}` |")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Clientes agrupados por estado (UF)")
    parser.add_argument("--state", help="Filtrar por estado (ex: SP, RJ, MG)")
    parser.add_argument("--detail", action="store_true",
                        help="Incluir lista de clientes por estado no output")
    parser.add_argument("--format", choices=["md", "json", "csv"], default="md")
    args = parser.parse_args()

    try:
        client = EcomplusClient.from_env()
        pipeline = build_pipeline(args.state)
        rows = client.aggregate("customers", pipeline)
    except EcomplusError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    elif args.format == "csv":
        writer = csv.writer(sys.stdout)
        if args.detail:
            writer.writerow(["state", "name", "email", "customer_id"])
            for row in rows:
                state_code = row.get("_id", "")
                for c in sorted(row.get("customers", []), key=lambda x: x.get("name", "")):
                    writer.writerow([
                        state_code,
                        c.get("name", ""),
                        c.get("email", ""),
                        c.get("id", ""),
                    ])
        else:
            writer.writerow(["state", "total"])
            for row in rows:
                writer.writerow([row["_id"], row.get("total", 0)])
    else:
        print(render_markdown(rows, args.state, args.detail))


if __name__ == "__main__":
    main()
