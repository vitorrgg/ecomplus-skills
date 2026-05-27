#!/usr/bin/env python3
"""
Atualiza preço e/ou preço base (promoção) de um produto ou variação.

Produto simples:
  python update_price.py --sku CAMISETA-P --price 79.90
  python update_price.py --sku CAMISETA-P --price 69.90 --base-price 89.90

Variação específica:
  python update_price.py --sku CAMISETA --variation-sku CAMISETA-G --price 99.90

Desconto % em todas as variações do produto:
  python update_price.py --sku CAMISETA --discount 10

Retirar promoção (iguala base_price ao price):
  python update_price.py --sku CAMISETA-P --price 89.90 --base-price 89.90
"""
import argparse
import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))
from ecomplus_client import EcomplusClient, EcomplusError, format_brl


def apply_discount(price: float, base_price: float, discount_pct: float) -> float:
    """Aplica % de desconto sobre base_price. Arredonda 2 casas."""
    return round(base_price * (1 - discount_pct / 100), 2)


def main():
    parser = argparse.ArgumentParser(description="Atualiza preço de produto E-Com Plus")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--sku", help="SKU do produto")
    group.add_argument("--id", dest="product_id", help="_id do produto")

    parser.add_argument("--price", type=float, help="Novo preço de venda (por)")
    parser.add_argument("--base-price", dest="base_price", type=float,
                        help="Preço original (de) — cria efeito de promoção")
    parser.add_argument("--discount", type=float, metavar="PERCENT",
                        help="Aplicar N%% de desconto sobre o base_price (todas as variações)")
    parser.add_argument("--variation-sku", dest="variation_sku",
                        help="Atualizar apenas esta variação (pelo SKU)")
    parser.add_argument("--sandbox", action="store_true")
    args = parser.parse_args()

    if not any([args.price is not None, args.base_price is not None, args.discount is not None]):
        parser.error("Informe ao menos um: --price, --base-price ou --discount")

    if args.discount is not None and args.variation_sku:
        parser.error("--discount não pode ser combinado com --variation-sku (age em todas as variações)")

    try:
        client = EcomplusClient.from_env()
        if args.sandbox:
            import ecomplus_client
            ecomplus_client.BASE_URL = "https://sandbox.e-com.plus/v1"

        # Resolve produto (GET completo — precisamos das variações e preços atuais)
        if args.product_id:
            product = client.get(f"products/{args.product_id}")
        else:
            product = client.find_product_by_sku(args.sku)

        product_id = product["_id"]
        label = f"'{product.get('sku', product_id)}'"
        variations = product.get("variations") or []
        changes = []

        if args.variation_sku:
            # Atualiza variação específica
            variation = next(
                (v for v in variations if v.get("sku") == args.variation_sku), None
            )
            if variation is None:
                print(
                    f"Erro: variação '{args.variation_sku}' não encontrada em {label}.\n"
                    f"Disponíveis: {[v.get('sku') for v in variations]}",
                    file=sys.stderr,
                )
                sys.exit(1)

            variation_id = variation["_id"]
            patch: dict = {}
            if args.price is not None:
                patch["price"] = args.price
                if not args.base_price and not variation.get("base_price"):
                    patch["base_price"] = variation.get("price", product.get("price", args.price))
                changes.append(f"price → {format_brl(args.price)}")
            if args.base_price is not None:
                patch["base_price"] = args.base_price
                changes.append(f"base_price → {format_brl(args.base_price)}")

            client.patch(f"products/{product_id}/variations/{variation_id}", patch)
            print(f"Variação '{args.variation_sku}' de {label}: {', '.join(changes)}")

        elif args.discount is not None and variations:
            # Aplica desconto em todas as variações
            discount_pct = args.discount
            updated = 0
            for v in variations:
                v_id = v["_id"]
                v_base = v.get("base_price") or product.get("base_price") or v.get("price", 0)
                if v_base <= 0:
                    continue
                new_price = apply_discount(v.get("price", 0), v_base, discount_pct)
                patch = {"price": new_price, "base_price": v_base}
                client.patch(f"products/{product_id}/variations/{v_id}", patch)
                updated += 1
                time.sleep(0.2)

            # Atualiza o produto principal também
            p_base = product.get("base_price") or product.get("price", 0)
            if p_base > 0:
                new_price = apply_discount(product.get("price", 0), p_base, discount_pct)
                client.patch(f"products/{product_id}", {"price": new_price, "base_price": p_base})

            print(f"Desconto de {discount_pct}% aplicado em {label}: {updated} variação(ões) + produto principal")

        else:
            # Produto simples (ou atualiza só o produto pai)
            patch = {}
            current_price = product.get("price", 0)
            current_base = product.get("base_price", current_price)

            if args.price is not None:
                patch["price"] = args.price
                # Garante que base_price seja definido se não existia
                if args.base_price is None and not product.get("base_price"):
                    patch["base_price"] = current_price
                changes.append(f"price → {format_brl(args.price)}")
            if args.base_price is not None:
                patch["base_price"] = args.base_price
                changes.append(f"base_price → {format_brl(args.base_price)}")
            elif args.discount is not None:
                # Produto simples com --discount
                base = product.get("base_price") or current_price
                new_price = apply_discount(current_price, base, args.discount)
                patch["price"] = new_price
                patch["base_price"] = base
                changes.append(f"price → {format_brl(new_price)} (desconto {args.discount}%)")

            client.patch(f"products/{product_id}", patch)
            print(f"Produto {label}: {', '.join(changes)}")

    except EcomplusError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
