#!/usr/bin/env python3
"""
Lista clientes com filtros.

Uso:
  python list_customers.py --min-orders 2          # recorrentes
  python list_customers.py --birthday-month 6      # aniversariantes de junho
  python list_customers.py --name "Maria"          # por nome (parcial)
  python list_customers.py --enabled false         # inativos
  python list_customers.py --min-orders 1 --sort ltv --limit 20 --format csv
"""
import argparse
import csv
import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from ecomplus_client import EcomplusClient, EcomplusError, format_brl


def full_name(c: dict) -> str:
    n = c.get("name") or {}
    parts = [n.get("given_name", ""), n.get("middle_name", ""), n.get("family_name", "")]
    return c.get("display_name") or " ".join(p for p in parts if p)


def main():
    parser = argparse.ArgumentParser(description="Lista clientes E-Com Plus")
    parser.add_argument("--name", help="Filtrar por nome (parcial, case-insensitive no cliente)")
    parser.add_argument("--email", help="Filtrar por e-mail (parcial)")
    parser.add_argument("--min-orders", type=int, dest="min_orders",
                        help="Mínimo de pedidos (clientes recorrentes)")
    parser.add_argument("--min-ltv", type=float, dest="min_ltv",
                        help="Valor mínimo gasto (R$)")
    parser.add_argument("--birthday-month", type=int, dest="birthday_month",
                        metavar="MES", help="Aniversariantes deste mês (1-12)")
    parser.add_argument("--enabled", choices=["true", "false"],
                        help="Filtrar por conta ativa/inativa")
    parser.add_argument("--sort", choices=["created_at", "ltv", "orders"],
                        default="created_at",
                        help="Ordenar por: created_at (padrão), ltv, orders")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--format", choices=["md", "csv", "json"], default="md")
    parser.add_argument("--sandbox", action="store_true")
    args = parser.parse_args()

    params: dict = {
        "fields": "_id,main_email,display_name,name,doc_number,phones,"
                  "orders_count,orders_total_value,birth_date,enabled,created_at",
    }

    if args.enabled is not None:
        params["enabled"] = args.enabled
    if args.min_orders is not None:
        params["orders_count>="] = args.min_orders
    if args.min_ltv is not None:
        params["orders_total_value>="] = args.min_ltv
    if args.birthday_month is not None:
        params["birth_date.month"] = args.birthday_month
    if args.email:
        params["main_email"] = args.email

    # Ordenação
    sort_map = {"created_at": "-created_at", "ltv": "-orders_total_value",
                "orders": "-orders_count"}
    params["sort"] = sort_map.get(args.sort, "-created_at")

    try:
        client = EcomplusClient.from_env()
        if args.sandbox:
            import ecomplus_client
            ecomplus_client.BASE_URL = "https://sandbox.e-com.plus/v1"

        customers = []
        for c in client.list_all("customers", params=params):
            # Filtro de nome (API não suporta text search em nome, fazemos no cliente)
            if args.name:
                name_str = full_name(c).lower()
                if args.name.lower() not in name_str:
                    continue
            customers.append(c)
            if len(customers) >= args.limit:
                break

        if not customers:
            print("Nenhum cliente encontrado com os filtros informados.")
            return

        if args.format == "json":
            print(json.dumps(customers, ensure_ascii=False, indent=2))
            return

        rows = []
        for c in customers:
            bd = c.get("birth_date") or {}
            bday = f"{bd.get('day', ''):02}/{bd.get('month', ''):02}" if bd.get("day") else ""
            phones = c.get("phones") or []
            phone_str = phones[0].get("number", "") if phones else ""
            rows.append({
                "Nome": full_name(c) or "(sem nome)",
                "E-mail": c.get("main_email", ""),
                "Telefone": phone_str,
                "Pedidos": c.get("orders_count", 0),
                "Total gasto": format_brl(c.get("orders_total_value") or 0),
                "Aniversário": bday,
                "Ativo": "sim" if c.get("enabled", True) else "não",
            })

        if args.format == "csv":
            writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0].keys()),
                                    lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
            return

        print(f"**{len(customers)} cliente(s) encontrado(s)**\n")
        print("| Nome | E-mail | Pedidos | Total gasto | Ativo |")
        print("|---|---|---|---|---|")
        for r in rows:
            print(f"| {r['Nome']} | {r['E-mail']} | {r['Pedidos']} "
                  f"| {r['Total gasto']} | {r['Ativo']} |")

        if len(customers) >= args.limit:
            print(f"\n> Limitado a {args.limit}. Use `--limit N` ou `--format csv`.")

    except EcomplusError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
