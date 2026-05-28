"""
Lista aniversariantes de clientes agrupados por mês de nascimento.

Usa birth_date.month e birth_date.day dos cadastros de clientes.
Clientes sem data de nascimento não aparecem no resultado.

Uso:
    python birthdays.py                  # todos os meses
    python birthdays.py --month 6        # apenas junho
    python birthdays.py --format csv     # exportar todos
"""
import argparse
import csv
import json
import sys

from ecomplus_client import EcomplusClient, EcomplusError

MONTHS_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}


def build_pipeline(month: int = None) -> list:
    if month:
        match_stage = {"birth_date.month": {"$eq": month}}
    else:
        match_stage = {"birth_date.month": {"$exists": True}}

    return [
        {"$match": match_stage},
        {
            "$group": {
                "_id": "$birth_date.month",
                "total": {"$sum": 1},
                "birthdays": {
                    "$addToSet": {
                        "id": "$_id",
                        "name": {
                            "$concat": [
                                "$name.given_name",
                                " ",
                                "$name.family_name",
                            ]
                        },
                        "day": "$birth_date.day",
                        "email": "$main_email",
                    }
                },
            }
        },
        {"$sort": {"_id": 1}},
    ]


def render_markdown(rows: list, month: int = None) -> str:
    if month:
        title = f"Aniversariantes de {MONTHS_PT.get(month, str(month))}"
    else:
        title = "Aniversariantes por mês"
    lines = [f"## {title}\n"]

    for row in rows:
        m = row.get("_id")
        month_name = MONTHS_PT.get(m, f"Mês {m}")
        total = row.get("total", 0)
        lines.append(f"### {month_name} ({total} cliente{'s' if total != 1 else ''})\n")
        lines.append("| Dia | Nome | E-mail |")
        lines.append("|---:|---|---|")
        bdays = sorted(row.get("birthdays", []), key=lambda x: x.get("day") or 0)
        for b in bdays:
            day = b.get("day", "—")
            lines.append(f"| {day} | {b.get('name', '—')} | {b.get('email', '—')} |")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Aniversariantes de clientes por mês")
    parser.add_argument("--month", type=int, choices=range(1, 13), metavar="1-12",
                        help="Filtrar por mês (1=Jan … 12=Dez). Sem este argumento lista todos.")
    parser.add_argument("--format", choices=["md", "json", "csv"], default="md")
    args = parser.parse_args()

    try:
        client = EcomplusClient.from_env()
        pipeline = build_pipeline(args.month)
        rows = client.aggregate("customers", pipeline)
    except EcomplusError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    elif args.format == "csv":
        writer = csv.writer(sys.stdout)
        writer.writerow(["month_num", "month_name", "day", "name", "email", "customer_id"])
        for row in rows:
            m = row.get("_id", "")
            month_name = MONTHS_PT.get(m, "")
            for b in sorted(row.get("birthdays", []), key=lambda x: x.get("day") or 0):
                writer.writerow([
                    m,
                    month_name,
                    b.get("day", ""),
                    b.get("name", ""),
                    b.get("email", ""),
                    b.get("id", ""),
                ])
    else:
        print(render_markdown(rows, args.month))


if __name__ == "__main__":
    main()
