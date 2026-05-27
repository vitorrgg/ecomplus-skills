#!/usr/bin/env python3
"""
Atualiza campos de um pedido E-Com Plus via PATCH.

Uso:
  python update_order.py --number 1234 --financial-status paid
  python update_order.py --number 1234 --fulfillment-status shipped
  python update_order.py --number 1234 --status cancelled
  python update_order.py --number 1234 --notes "Embalagem frágil"
  python update_order.py --id 5cf...abc --financial-status paid --fulfillment-status shipped
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from ecomplus_client import EcomplusClient, EcomplusError

FINANCIAL_STATUS = [
    "pending", "under_analysis", "authorized", "paid",
    "in_dispute", "refunded", "voided", "unknown",
]
FULFILLMENT_STATUS = [
    "invoice_issued", "in_production", "in_separation", "ready_for_shipping",
    "shipped", "delivered", "partially_delivered", "returned",
]


def main():
    parser = argparse.ArgumentParser(description="Atualiza campos de um pedido E-Com Plus")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--number", type=int, help="Número do pedido")
    group.add_argument("--id", dest="order_id", help="_id do pedido (ObjectId)")

    parser.add_argument("--status", choices=["open", "cancelled"],
                        help="Status principal")
    parser.add_argument("--financial-status", dest="financial_status",
                        choices=FINANCIAL_STATUS, help="Status de pagamento")
    parser.add_argument("--fulfillment-status", dest="fulfillment_status",
                        choices=FULFILLMENT_STATUS, help="Status de envio")
    parser.add_argument("--notes", help="Nota interna do pedido")
    parser.add_argument("--sandbox", action="store_true")
    args = parser.parse_args()

    # Pelo menos um campo de atualização é obrigatório
    if not any([args.status, args.financial_status, args.fulfillment_status, args.notes]):
        parser.error(
            "Informe ao menos um campo para atualizar: "
            "--status, --financial-status, --fulfillment-status ou --notes"
        )

    try:
        client = EcomplusClient.from_env()
        if args.sandbox:
            import ecomplus_client
            ecomplus_client.BASE_URL = "https://sandbox.e-com.plus/v1"

        # Resolve o _id do pedido
        if args.order_id:
            order_id = args.order_id
            number = "(por _id)"
        else:
            order = client.find_order_by_number(args.number)
            order_id = order["_id"]
            number = f"#{args.number}"

        # Monta o payload PATCH
        patch = {}
        if args.status:
            patch["status"] = args.status
        if args.financial_status:
            patch["financial_status"] = {"current": args.financial_status}
        if args.fulfillment_status:
            patch["fulfillment_status"] = {"current": args.fulfillment_status}
        if args.notes is not None:
            patch["notes"] = args.notes

        client.patch(f"orders/{order_id}", patch)

        # Resumo do que foi alterado
        changes = []
        if args.status:
            changes.append(f"status → `{args.status}`")
        if args.financial_status:
            changes.append(f"pagamento → `{args.financial_status}`")
        if args.fulfillment_status:
            changes.append(f"envio → `{args.fulfillment_status}`")
        if args.notes is not None:
            changes.append("nota atualizada")

        print(f"Pedido {number} atualizado: {', '.join(changes)}")

    except EcomplusError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
