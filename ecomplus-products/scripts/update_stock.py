#!/usr/bin/env python3
"""
Atualiza estoque (quantity), disponibilidade ou visibilidade de um produto.

Produto simples:
  python update_stock.py --sku CAMISETA-P --quantity 50
  python update_stock.py --sku CAMISETA-P --available false
  python update_stock.py --sku CAMISETA-P --visible false

Produto com variações (--variation-sku atualiza só aquela variação):
  python update_stock.py --sku CAMISETA --variation-sku CAMISETA-P-AZUL --quantity 30

Por _id:
  python update_stock.py --id 5cf...abc --quantity 50
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from ecomplus_client import EcomplusClient, EcomplusError


def bool_arg(value: str) -> bool:
    return value.lower() in ("true", "1", "sim", "yes")


def main():
    parser = argparse.ArgumentParser(description="Atualiza estoque/disponibilidade de produto")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--sku", help="SKU do produto")
    group.add_argument("--id", dest="product_id", help="_id do produto")

    parser.add_argument("--quantity", type=int, help="Nova quantidade em estoque")
    parser.add_argument("--available", choices=["true", "false"],
                        help="Disponível para compra")
    parser.add_argument("--visible", choices=["true", "false"],
                        help="Visível no vitrine")
    parser.add_argument("--manage-stock", dest="manage_stock", choices=["true", "false"],
                        help="Controlar estoque")
    parser.add_argument("--variation-sku", dest="variation_sku",
                        help="SKU da variação específica (para produtos com variações)")
    parser.add_argument("--sandbox", action="store_true")
    args = parser.parse_args()

    if not any([
        args.quantity is not None,
        args.available is not None,
        args.visible is not None,
        args.manage_stock is not None,
    ]):
        parser.error("Informe ao menos um campo: --quantity, --available, --visible ou --manage-stock")

    try:
        client = EcomplusClient.from_env()
        if args.sandbox:
            import ecomplus_client
            ecomplus_client.BASE_URL = "https://sandbox.e-com.plus/v1"

        # Resolve produto
        if args.product_id:
            product = client.get(f"products/{args.product_id}")
        else:
            product = client.find_product_by_sku(args.sku)

        product_id = product["_id"]
        label = f"'{product.get('sku', product_id)}'"
        changes = []

        if args.variation_sku:
            # Atualiza variação específica
            variations = product.get("variations") or []
            variation = next(
                (v for v in variations if v.get("sku") == args.variation_sku), None
            )
            if variation is None:
                print(
                    f"Erro: variação com SKU '{args.variation_sku}' não encontrada no produto {label}.\n"
                    f"Variações disponíveis: {[v.get('sku') for v in variations]}",
                    file=sys.stderr,
                )
                sys.exit(1)

            variation_id = variation["_id"]
            patch: dict = {}
            if args.quantity is not None:
                patch["quantity"] = args.quantity
                changes.append(f"estoque → {args.quantity} un")
            if args.available is not None:
                patch["available"] = bool_arg(args.available)
                changes.append(f"disponível → {args.available}")

            client.patch(f"products/{product_id}/variations/{variation_id}", patch)
            print(f"Variação '{args.variation_sku}' do produto {label}: {', '.join(changes)}")

            # Se atualizou estoque, recalcula total do produto
            if args.quantity is not None:
                updated_product = client.get(f"products/{product_id}",
                                             params={"fields": "variations"})
                total_qty = sum(
                    v.get("quantity", 0)
                    for v in (updated_product.get("variations") or [])
                )
                client.patch(f"products/{product_id}", {"quantity": total_qty})
                print(f"  Estoque total do produto atualizado: {total_qty} un")

        else:
            # Atualiza produto principal
            variations = product.get("variations") or []
            patch = {}
            if args.quantity is not None:
                if variations:
                    print(
                        f"Aviso: produto {label} tem variações. "
                        "O estoque total é a soma das variações.\n"
                        "Use --variation-sku <sku> para atualizar uma variação específica.",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                patch["quantity"] = args.quantity
                changes.append(f"estoque → {args.quantity} un")
            if args.available is not None:
                patch["available"] = bool_arg(args.available)
                changes.append(f"disponível → {args.available}")
            if args.visible is not None:
                patch["visible"] = bool_arg(args.visible)
                changes.append(f"visível → {args.visible}")
            if args.manage_stock is not None:
                patch["manage_stock"] = bool_arg(args.manage_stock)
                changes.append(f"controla estoque → {args.manage_stock}")

            client.patch(f"products/{product_id}", patch)
            print(f"Produto {label}: {', '.join(changes)}")

    except EcomplusError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
