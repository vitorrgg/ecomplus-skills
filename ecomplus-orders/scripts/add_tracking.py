#!/usr/bin/env python3
"""
Adiciona ou atualiza código de rastreio na linha de envio de um pedido.

Fluxo: GET do pedido → pega o _id da primeira shipping_line → PATCH com tracking_codes.

Uso:
  python add_tracking.py --number 1234 --code BR123456789BR
  python add_tracking.py --number 1234 --code BR123456789BR --link https://rastreamento.correios.com.br
  python add_tracking.py --number 1234 --code BR123456789BR --shipped
  python add_tracking.py --id 5cf...abc --code MX987654321BR
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from ecomplus_client import EcomplusClient, EcomplusError

FULFILLMENT_STATUS = [
    "invoice_issued", "in_production", "in_separation", "ready_for_shipping",
    "shipped", "delivered", "partially_delivered", "returned",
]


def main():
    parser = argparse.ArgumentParser(
        description="Adiciona código de rastreio a um pedido E-Com Plus"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--number", type=int, help="Número do pedido")
    group.add_argument("--id", dest="order_id", help="_id do pedido (ObjectId)")

    parser.add_argument("--code", required=True, help="Código de rastreio (ex: BR123456789BR)")
    parser.add_argument("--link", help="URL de rastreamento (opcional)")
    parser.add_argument("--shipped", action="store_true",
                        help="Também marcar fulfillment_status como 'shipped'")
    parser.add_argument("--fulfillment-status", dest="fulfillment_status",
                        choices=FULFILLMENT_STATUS,
                        help="Definir fulfillment_status explicitamente (substitui --shipped)")
    parser.add_argument("--sandbox", action="store_true")
    args = parser.parse_args()

    try:
        client = EcomplusClient.from_env()
        if args.sandbox:
            import ecomplus_client
            ecomplus_client.BASE_URL = "https://sandbox.e-com.plus/v1"

        # Resolve _id do pedido
        if args.order_id:
            order = client.get(f"orders/{args.order_id}")
            order_id = args.order_id
            label = f"(id: {args.order_id[:8]}...)"
        else:
            order = client.find_order_by_number(args.number)
            order_id = order["_id"]
            label = f"#{args.number}"

        shipping_lines = order.get("shipping_lines") or []
        if not shipping_lines:
            print(
                f"Erro: pedido {label} não tem linhas de envio (shipping_lines vazia).",
                file=sys.stderr,
            )
            sys.exit(1)

        # Pega a primeira shipping_line e acrescenta/substitui o tracking code
        sl = shipping_lines[0]
        sl_id = sl.get("_id")
        existing_codes = sl.get("tracking_codes") or []

        # Substitui se já existir o mesmo código; acrescenta caso contrário
        new_entry = {"code": args.code}
        if args.link:
            new_entry["link"] = args.link

        updated = False
        for tc in existing_codes:
            if tc.get("code") == args.code:
                tc.update(new_entry)
                updated = True
                break
        if not updated:
            existing_codes.append(new_entry)

        # Monta o PATCH
        patch: dict = {
            "shipping_lines": [{
                "_id": sl_id,
                "tracking_codes": existing_codes,
            }]
        }

        # Status de envio
        fulfillment_status = args.fulfillment_status or ("shipped" if args.shipped else None)
        if fulfillment_status:
            patch["fulfillment_status"] = {"current": fulfillment_status}

        client.patch(f"orders/{order_id}", patch)

        action = "atualizado" if updated else "adicionado"
        extra = f" + envio → `{fulfillment_status}`" if fulfillment_status else ""
        print(f"Pedido {label}: rastreio `{args.code}` {action}{extra}")
        if args.link:
            print(f"  Link: {args.link}")

    except EcomplusError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
