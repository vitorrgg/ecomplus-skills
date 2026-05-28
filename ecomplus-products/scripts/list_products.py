#!/usr/bin/env python3
"""
Lista produtos da E-Com Plus com filtros.

Uso:
  python list_products.py --max-stock 5         # estoque baixo (≤ 5)
  python list_products.py --available false     # produtos indisponíveis
  python list_products.py --visible false       # produtos ocultos no vitrine
  python list_products.py --on-sale             # em promoção (base_price > price)
  python list_products.py --category "Camisetas" --format csv
"""
import argparse
import csv
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from ecomplus_client import EcomplusClient, EcomplusError, format_brl


def main():
    parser = argparse.ArgumentParser(description="Lista produtos E-Com Plus")
    parser.add_argument("--available", choices=["true", "false"],
                        help="Filtrar por disponibilidade")
    parser.add_argument("--visible", choices=["true", "false"],
                        help="Filtrar por visibilidade no vitrine")
    parser.add_argument("--max-stock", type=int, dest="max_stock",
                        metavar="N", help="Estoque máximo (≤ N), ex: --max-stock 5")
    parser.add_argument("--min-stock", type=int, dest="min_stock",
                        metavar="N", help="Estoque mínimo (≥ N)")
    parser.add_argument("--on-sale", action="store_true", dest="on_sale",
                        help="Apenas produtos em promoção (base_price definido)")
    parser.add_argument("--category", metavar="NOME_OU_ID",
                        help="Filtrar por nome (parcial) ou _id de categoria")
    parser.add_argument("--brand", metavar="NOME_OU_ID",
                        help="Filtrar por nome (parcial) ou _id de marca")
    parser.add_argument("--sku", help="Filtrar por SKU (prefixo)")
    parser.add_argument("--limit", type=int, default=50,
                        help="Máximo de resultados (default: 50)")
    parser.add_argument("--format", choices=["md", "csv", "json"], default="md")
    parser.add_argument("--sandbox", action="store_true")
    args = parser.parse_args()

    # A API v1 ignora `fields` e `limit` na listagem de produtos —
    # retorna apenas _id, sku, slug. Filtramos IDs aqui e fazemos GET
    # individual para cada produto dentro do limite solicitado.
    list_params = {"sort": "-updated_at"}

    if args.available is not None:
        list_params["available"] = args.available
    if args.visible is not None:
        list_params["visible"] = args.visible
    if args.max_stock is not None:
        list_params["quantity<="] = args.max_stock
    if args.min_stock is not None:
        list_params["quantity>="] = args.min_stock
    if args.category:
        if len(args.category) == 24 and args.category.isalnum():
            list_params["categories._id"] = args.category
        else:
            list_params["categories.name"] = args.category
    if args.brand:
        if len(args.brand) == 24 and args.brand.isalnum():
            list_params["brands._id"] = args.brand
        else:
            list_params["brands.name"] = args.brand
    if args.sku:
        list_params["sku"] = args.sku

    try:
        client = EcomplusClient.from_env()
        if args.sandbox:
            import ecomplus_client
            ecomplus_client.BASE_URL = "https://sandbox.e-com.plus/v1"

        products = []
        for stub in client.list_all("products", params=list_params):
            product_id = stub.get("_id")
            if not product_id:
                continue
            p = client.get(f"products/{product_id}")
            qty = p.get("quantity", 0) or 0
            if args.max_stock is not None and qty > args.max_stock:
                continue
            if args.min_stock is not None and qty < args.min_stock:
                continue
            if args.available is not None and str(p.get("available", "")).lower() != args.available:
                continue
            if args.visible is not None and str(p.get("visible", "")).lower() != args.visible:
                continue
            if args.on_sale:
                bp = p.get("base_price")
                pr = p.get("price", 0)
                if not (bp and bp > pr):
                    continue
            products.append(p)
            if len(products) >= args.limit:
                break

        if not products:
            print("Nenhum produto encontrado com os filtros informados.")
            return

        if args.format == "json":
            print(json.dumps(products, ensure_ascii=False, indent=2))
            return

        rows = []
        for p in products:
            price = p.get("price", 0)
            base_price = p.get("base_price")
            price_str = format_brl(price)
            if base_price and base_price != price:
                price_str += f" (de {format_brl(base_price)})"
            cats = ", ".join(c.get("name", "") for c in (p.get("categories") or []))
            brands = ", ".join(b.get("name", "") for b in (p.get("brands") or []))
            rows.append({
                "SKU": p.get("sku", ""),
                "Nome": p.get("name", ""),
                "Preço": price_str,
                "Estoque": p.get("quantity", 0),
                "Disponível": "sim" if p.get("available") else "não",
                "Visível": "sim" if p.get("visible") else "não",
                "Categorias": cats,
            })

        if args.format == "csv":
            writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0].keys()),
                                    lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
            return

        print(f"**{len(products)} produto(s) encontrado(s)**\n")
        print("| SKU | Nome | Preço | Estoque | Disponível | Visível |")
        print("|---|---|---|---|---|---|")
        for r in rows:
            print(f"| `{r['SKU']}` | {r['Nome']} | {r['Preço']} "
                  f"| {r['Estoque']} | {r['Disponível']} | {r['Visível']} |")

        if len(products) >= args.limit:
            print(f"\n> Resultado limitado a {args.limit}. Use `--limit N` ou `--format csv`.")

    except EcomplusError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
