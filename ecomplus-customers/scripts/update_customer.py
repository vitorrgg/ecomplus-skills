#!/usr/bin/env python3
"""
Atualiza campos do cadastro de um cliente E-Com Plus.

Uso:
  python update_customer.py --email cliente@exemplo.com --notes "Cliente VIP"
  python update_customer.py --email cliente@exemplo.com --enabled false
  python update_customer.py --id 5cf...abc --new-email novo@email.com
  python update_customer.py --doc 12345678901 --notes "Atualizado" --enabled true
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from ecomplus_client import EcomplusClient, EcomplusError


def main():
    parser = argparse.ArgumentParser(description="Atualiza cadastro de cliente E-Com Plus")

    # Como identificar o cliente
    id_group = parser.add_mutually_exclusive_group(required=True)
    id_group.add_argument("--email", help="E-mail do cliente")
    id_group.add_argument("--doc", help="CPF ou CNPJ")
    id_group.add_argument("--id", dest="customer_id", help="_id do cliente")

    # O que atualizar
    parser.add_argument("--notes", dest="staff_notes",
                        help="Notas internas da equipe (staff_notes)")
    parser.add_argument("--enabled", choices=["true", "false"],
                        help="Ativar (true) ou desativar (false) a conta")
    parser.add_argument("--new-email", dest="new_email",
                        help="Novo e-mail principal")
    parser.add_argument("--display-name", dest="display_name",
                        help="Novo nome de exibição")
    parser.add_argument("--referral", help="Código de referral")

    parser.add_argument("--sandbox", action="store_true")
    args = parser.parse_args()

    has_changes = any([
        args.staff_notes is not None,
        args.enabled is not None,
        args.new_email,
        args.display_name,
        args.referral is not None,
    ])
    if not has_changes:
        parser.error(
            "Informe ao menos um campo para atualizar: "
            "--notes, --enabled, --new-email, --display-name ou --referral"
        )

    try:
        client = EcomplusClient.from_env()
        if args.sandbox:
            import ecomplus_client
            ecomplus_client.BASE_URL = "https://sandbox.e-com.plus/v1"

        # Resolve _id do cliente
        if args.customer_id:
            customer_id = args.customer_id
            label = f"(id: {args.customer_id[:8]}...)"
        else:
            customer = client.find_customer(email=args.email, doc=args.doc)
            customer_id = customer["_id"]
            label = f"'{customer.get('main_email', customer_id)}'"

        # Monta o PATCH
        patch: dict = {}
        changes = []

        if args.staff_notes is not None:
            patch["staff_notes"] = args.staff_notes
            changes.append("notas da equipe atualizadas")

        if args.enabled is not None:
            val = args.enabled == "true"
            patch["enabled"] = val
            changes.append(f"conta {'ativada' if val else 'desativada'}")

        if args.new_email:
            patch["main_email"] = args.new_email
            changes.append(f"e-mail → {args.new_email}")

        if args.display_name:
            patch["display_name"] = args.display_name
            changes.append(f"nome → {args.display_name}")

        if args.referral is not None:
            if args.referral == "":
                # Remover referral — a API não suporta deletar campo com PATCH,
                # mas podemos enviar null (depende da versão da API)
                patch["referral"] = None
            else:
                patch["referral"] = args.referral
            changes.append("referral atualizado")

        client.patch(f"customers/{customer_id}", patch)
        print(f"Cliente {label}: {', '.join(changes)}")

    except EcomplusError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
