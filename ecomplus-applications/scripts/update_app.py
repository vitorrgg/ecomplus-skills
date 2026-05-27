#!/usr/bin/env python3
"""
Atualiza data ou hidden_data de um aplicativo instalado na E-Com Plus.

O PATCH em data.json / hidden_data.json faz MERGE — só as chaves enviadas
são alteradas; as demais permanecem intactas.

Uso:
  # Setar uma chave simples em data
  python update_app.py --id 5cf...abc --key access_token --value "tok_xxx"

  # Setar uma chave em hidden_data (credenciais)
  python update_app.py --id 5cf...abc --hidden --key api_key --value "sk_xxx"

  # Enviar JSON completo (arquivo ou string)
  python update_app.py --id 5cf...abc --json-file new_data.json
  python update_app.py --app-id 124890 --json '{"programs_rules": []}'

  # Identificar pelo app_id em vez do _id
  python update_app.py --app-id 124890 --key debug_mode --value true
"""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from ecomplus_client import EcomplusClient, EcomplusError


def parse_value(raw: str):
    """Tenta interpretar o valor como JSON; cai back para string."""
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw


def main():
    parser = argparse.ArgumentParser(
        description="Atualiza data/hidden_data de um app E-Com Plus"
    )

    id_group = parser.add_mutually_exclusive_group(required=True)
    id_group.add_argument("--id", dest="app_doc_id",
                          help="_id do documento do app instalado")
    id_group.add_argument("--app-id", type=int, dest="app_id",
                          help="app_id numérico do marketplace")

    payload_group = parser.add_mutually_exclusive_group(required=True)
    payload_group.add_argument("--key", help="Chave a atualizar (use com --value)")
    payload_group.add_argument("--json", dest="json_str",
                               help="JSON completo a mergear (string)")
    payload_group.add_argument("--json-file", dest="json_file",
                               help="Arquivo JSON a mergear")

    parser.add_argument("--value",
                        help="Valor da chave (usado com --key). Aceita JSON ou string.")
    parser.add_argument("--hidden", action="store_true",
                        help="Atualizar hidden_data em vez de data")
    parser.add_argument("--sandbox", action="store_true")
    args = parser.parse_args()

    if args.key and args.value is None:
        parser.error("--key requer --value")

    # Monta payload
    if args.key:
        patch_data = {args.key: parse_value(args.value)}
    elif args.json_str:
        try:
            patch_data = json.loads(args.json_str)
        except json.JSONDecodeError as exc:
            parser.error(f"JSON inválido em --json: {exc}")
    else:  # json_file
        try:
            with open(args.json_file, encoding="utf-8") as f:
                patch_data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            parser.error(f"Erro ao ler --json-file: {exc}")

    if not isinstance(patch_data, dict):
        parser.error("O payload deve ser um objeto JSON (dict).")

    endpoint_suffix = "hidden_data" if args.hidden else "data"
    target_label = "hidden_data" if args.hidden else "data"

    try:
        client = EcomplusClient.from_env()
        if args.sandbox:
            import ecomplus_client
            ecomplus_client.BASE_URL = "https://sandbox.e-com.plus/v1"

        # Resolve _id
        if args.app_doc_id:
            app_doc_id = args.app_doc_id
            label = f"(id: {app_doc_id[:8]}...)"
        else:
            ref = client.find_application(args.app_id)
            app_doc_id = ref["_id"]
            label = f"'{ref.get('title', '')}' (app_id={args.app_id})"

        client.patch(f"applications/{app_doc_id}/{endpoint_suffix}", patch_data)
        keys_changed = ", ".join(patch_data.keys())
        print(f"App {label}: {target_label} atualizado — chave(s): {keys_changed}")

    except EcomplusError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
