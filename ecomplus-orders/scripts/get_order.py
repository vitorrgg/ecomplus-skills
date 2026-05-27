#!/usr/bin/env python3
"""
Exibe os detalhes completos de um pedido E-Com Plus.

Uso:
  python get_order.py --number 1234
  python get_order.py --id 5cf...abc
  python get_order.py --number 1234 --format json
"""
import argparse
import json
import sys
import os
from datetime import timezone

sys.path.insert(0, os.path.dirname(__file__))
from ecomplus_client import EcomplusClient, EcomplusError, format_brl


def fmt_date(iso: str) -> str:
    if not iso:
        return ""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%d/%m/%Y %H:%M")
    except Exception:
        return iso


def render_md(order: dict) -> None:
    number = order.get("number", "?")
    status = order.get("status", "")
    fin = (order.get("financial_status") or {}).get("current", "")
    ful = (order.get("fulfillment_status") or {}).get("current", "")
    amount = order.get("amount", {})
    created = fmt_date(order.get("created_at", ""))
    updated = fmt_date(order.get("updated_at", ""))

    print(f"## Pedido #{number}\n")

    # Cabeçalho de status
    print("| Campo | Valor |")
    print("|---|---|")
    print(f"| ID | `{order.get('_id', '')}` |")
    print(f"| Criado em | {created} |")
    print(f"| Atualizado em | {updated} |")
    print(f"| Status | {status} |")
    print(f"| Pagamento | {fin} |")
    print(f"| Envio | {ful} |")
    if order.get("payment_method_label"):
        print(f"| Forma de pagamento | {order['payment_method_label']} |")
    if order.get("shipping_method_label"):
        print(f"| Transportadora | {order['shipping_method_label']} |")
    if order.get("affiliate_code"):
        print(f"| Código afiliado | {order['affiliate_code']} |")

    # Comprador
    buyers = order.get("buyers") or []
    if buyers:
        b = buyers[0]
        name_parts = [
            (b.get("name") or {}).get("given_name", ""),
            (b.get("name") or {}).get("family_name", ""),
        ]
        full_name = b.get("display_name") or " ".join(p for p in name_parts if p)
        print(f"\n### Comprador\n")
        print(f"| Campo | Valor |")
        print("|---|---|")
        print(f"| Nome | {full_name} |")
        if b.get("main_email"):
            print(f"| E-mail | {b['main_email']} |")
        if b.get("doc_number"):
            print(f"| CPF/CNPJ | {b['doc_number']} |")
        phones = b.get("phones") or []
        if phones:
            print(f"| Telefone | {phones[0].get('number', '')} |")

    # Endereço de entrega
    shipping_lines = order.get("shipping_lines") or []
    if shipping_lines:
        to = shipping_lines[0].get("to") or {}
        if to:
            print(f"\n### Endereço de entrega\n")
            parts = [
                to.get("name", ""),
                f"{to.get('street', '')} {to.get('number', '')}".strip(),
                to.get("complement", ""),
                to.get("borough", ""),
                f"{to.get('city', '')} - {to.get('province_code', '')}".strip(" -"),
                to.get("zip", ""),
            ]
            print(" / ".join(p for p in parts if p))
        # Rastreio
        tracking = shipping_lines[0].get("tracking_codes") or []
        if tracking:
            print(f"\n### Rastreio\n")
            for t in tracking:
                code = t.get("code", "")
                link = t.get("link", "")
                print(f"- `{code}`" + (f" → [{link}]({link})" if link else ""))

    # Itens
    items = order.get("items") or []
    if items:
        print(f"\n### Itens\n")
        print("| # | SKU | Nome | Qtd | Preço | Total |")
        print("|---|---|---|---|---|---|")
        for i, item in enumerate(items, 1):
            qty = item.get("quantity", 0)
            price = item.get("final_price") or item.get("price", 0)
            total = qty * price
            print(f"| {i} | {item.get('sku', '')} | {item.get('name', '')} "
                  f"| {qty} | {format_brl(price)} | {format_brl(total)} |")

    # Valores
    print(f"\n### Valores\n")
    print("| Campo | Valor |")
    print("|---|---|")
    if amount.get("subtotal") is not None:
        print(f"| Subtotal | {format_brl(amount['subtotal'])} |")
    if amount.get("freight"):
        print(f"| Frete | {format_brl(amount['freight'])} |")
    if amount.get("discount"):
        print(f"| Desconto | {format_brl(amount['discount'])} |")
    if amount.get("tax"):
        print(f"| Imposto | {format_brl(amount['tax'])} |")
    if amount.get("extra"):
        print(f"| Juros | {format_brl(amount['extra'])} |")
    print(f"| **Total** | **{format_brl(amount.get('total', 0))}** |")

    if order.get("notes"):
        print(f"\n> **Notas:** {order['notes']}")

    if order.get("extra_discount", {}).get("discount_coupon"):
        print(f"\n> **Cupom:** `{order['extra_discount']['discount_coupon']}`")


def main():
    parser = argparse.ArgumentParser(description="Detalhe de um pedido E-Com Plus")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--number", type=int, help="Número do pedido (ex: 1234)")
    group.add_argument("--id", dest="order_id", help="_id do pedido (ObjectId)")
    parser.add_argument("--format", choices=["md", "json"], default="md")
    parser.add_argument("--sandbox", action="store_true")
    args = parser.parse_args()

    try:
        client = EcomplusClient.from_env()
        if args.sandbox:
            from ecomplus_client import BASE_URL
            import ecomplus_client
            ecomplus_client.BASE_URL = "https://sandbox.e-com.plus/v1"

        if args.order_id:
            order = client.get(f"orders/{args.order_id}")
        else:
            order = client.find_order_by_number(args.number)

        if args.format == "json":
            print(json.dumps(order, ensure_ascii=False, indent=2))
        else:
            render_md(order)

    except EcomplusError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
