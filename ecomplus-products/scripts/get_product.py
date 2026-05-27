#!/usr/bin/env python3
"""
Exibe os detalhes completos de um produto E-Com Plus.

Uso:
  python get_product.py --sku CAMISETA-P-AZUL
  python get_product.py --id 5cf...abc
  python get_product.py --sku CAMISETA-P-AZUL --format json
"""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from ecomplus_client import EcomplusClient, EcomplusError, format_brl


def render_md(product: dict) -> None:
    name = product.get("name", "?")
    sku = product.get("sku", "?")
    price = product.get("price", 0)
    base_price = product.get("base_price")
    cost_price = product.get("cost_price")
    quantity = product.get("quantity", 0)
    available = product.get("available", False)
    visible = product.get("visible", True)
    manage_stock = product.get("manage_stock", True)
    status = product.get("status", "")

    print(f"## {name}\n")
    print("| Campo | Valor |")
    print("|---|---|")
    print(f"| ID | `{product.get('_id', '')}` |")
    print(f"| SKU | `{sku}` |")
    if product.get("slug"):
        print(f"| Slug | `{product['slug']}` |")
    print(f"| Preço (por) | {format_brl(price)} |")
    if base_price and base_price != price:
        print(f"| Preço base (de) | {format_brl(base_price)} |")
        discount_pct = round((1 - price / base_price) * 100, 1)
        print(f"| Desconto | {discount_pct}% |")
    if cost_price:
        print(f"| Custo | {format_brl(cost_price)} |")
    print(f"| Estoque | {quantity} un |")
    print(f"| Disponível | {'✓ sim' if available else '✗ não'} |")
    print(f"| Visível | {'✓ sim' if visible else '✗ não'} |")
    print(f"| Controla estoque | {'sim' if manage_stock else 'não'} |")
    if status:
        print(f"| Status | {status} |")
    if product.get("sales"):
        print(f"| Vendidos | {product['sales']} un |")

    # Categorias e marcas
    categories = product.get("categories") or []
    brands = product.get("brands") or []
    if categories:
        names = ", ".join(c.get("name", "") for c in categories)
        print(f"| Categorias | {names} |")
    if brands:
        names = ", ".join(b.get("name", "") for b in brands)
        print(f"| Marcas | {names} |")

    # Especificações
    specs = product.get("specifications") or {}
    if specs:
        spec_parts = []
        for grid_id, values in specs.items():
            if isinstance(values, list):
                texts = ", ".join(v.get("text", "") for v in values if isinstance(v, dict))
                spec_parts.append(f"{grid_id}: {texts}")
        if spec_parts:
            print(f"| Especificações | {' / '.join(spec_parts)} |")

    # Variações
    variations = product.get("variations") or []
    if variations:
        print(f"\n### Variações ({len(variations)})\n")
        print("| SKU | Estoque | Preço | Disponível |")
        print("|---|---|---|---|")
        for v in variations:
            v_price = v.get("price") or price
            v_qty = v.get("quantity", 0)
            v_avail = "✓" if v.get("available", True) else "✗"
            specs_str = ""
            v_specs = v.get("specifications") or {}
            for grid_id, vals in v_specs.items():
                if isinstance(vals, list) and vals:
                    text = vals[0].get("text", "") if isinstance(vals[0], dict) else str(vals[0])
                    specs_str += f"{text} "
            label = f"`{v.get('sku', v.get('_id', '')[:8])}`"
            if specs_str:
                label += f" ({specs_str.strip()})"
            print(f"| {label} | {v_qty} un | {format_brl(v_price)} | {v_avail} |")

    # Imagens
    pictures = product.get("pictures") or []
    if pictures:
        print(f"\n### Imagens\n")
        for i, pic in enumerate(pictures[:3], 1):
            url = (pic.get("normal") or pic.get("small") or {}).get("url", "")
            if url:
                print(f"{i}. [{url}]({url})")
        if len(pictures) > 3:
            print(f"\n_... e mais {len(pictures) - 3} imagem(ns)_")


def main():
    parser = argparse.ArgumentParser(description="Detalhe de um produto E-Com Plus")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--sku", help="SKU do produto")
    group.add_argument("--id", dest="product_id", help="_id do produto (ObjectId)")
    parser.add_argument("--format", choices=["md", "json"], default="md")
    parser.add_argument("--sandbox", action="store_true")
    args = parser.parse_args()

    try:
        client = EcomplusClient.from_env()
        if args.sandbox:
            import ecomplus_client
            ecomplus_client.BASE_URL = "https://sandbox.e-com.plus/v1"

        if args.product_id:
            product = client.get(f"products/{args.product_id}")
        else:
            product = client.find_product_by_sku(args.sku)

        if args.format == "json":
            print(json.dumps(product, ensure_ascii=False, indent=2))
        else:
            render_md(product)

    except EcomplusError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
