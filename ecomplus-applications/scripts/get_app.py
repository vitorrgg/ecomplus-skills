#!/usr/bin/env python3
"""
Exibe detalhes de um aplicativo instalado na E-Com Plus.

Uso:
  python get_app.py --id 5cf...abc              # pelo _id do documento
  python get_app.py --app-id 124890             # pelo app_id do marketplace
  python get_app.py --app-id 124890 --show-hidden   # inclui hidden_data
  python get_app.py --id 5cf...abc --format json
"""
import argparse
import json
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
from ecomplus_client import EcomplusClient, EcomplusError


def fmt_date(iso: str) -> str:
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%d/%m/%Y %H:%M")
    except Exception:
        return iso[:10]


def render_md(app: dict, show_hidden: bool) -> None:
    title = app.get("title") or f"App {app.get('app_id', '?')}"
    print(f"## {title}\n")

    print("| Campo | Valor |")
    print("|---|---|")
    print(f"| ID | `{app.get('_id', '')}` |")
    print(f"| App ID (marketplace) | {app.get('app_id', '')} |")
    if app.get("version"):
        print(f"| Versão | {app['version']} |")
    state = app.get("state", "")
    state_icon = "✓ ativo" if state == "active" else "⏸ pausado"
    print(f"| Estado | {state_icon} |")
    if app.get("installed_at"):
        print(f"| Instalado em | {fmt_date(app['installed_at'])} |")
    if app.get("updated_at"):
        print(f"| Atualizado em | {fmt_date(app['updated_at'])} |")

    # data pública
    data = app.get("data")
    if data:
        print(f"\n### Configuração pública (`data`)\n")
        print("```json")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        print("```")
    else:
        print("\n> `data`: (vazio)")

    # hidden_data
    if show_hidden:
        hidden = app.get("hidden_data")
        if hidden:
            print(f"\n### Dados ocultos (`hidden_data`)\n")
            print("```json")
            print(json.dumps(hidden, ensure_ascii=False, indent=2))
            print("```")
        else:
            print("\n> `hidden_data`: (vazio ou sem permissão)")


def main():
    parser = argparse.ArgumentParser(description="Detalhe de um app E-Com Plus")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--id", dest="app_doc_id", help="_id do documento do app instalado")
    group.add_argument("--app-id", type=int, dest="app_id",
                       help="app_id numérico do marketplace")
    parser.add_argument("--show-hidden", action="store_true",
                        help="Exibir hidden_data (credenciais/segredos)")
    parser.add_argument("--format", choices=["md", "json"], default="md")
    parser.add_argument("--sandbox", action="store_true")
    args = parser.parse_args()

    try:
        client = EcomplusClient.from_env()
        if args.sandbox:
            import ecomplus_client
            ecomplus_client.BASE_URL = "https://sandbox.e-com.plus/v1"

        if args.app_doc_id:
            app = client.get(f"applications/{args.app_doc_id}")
        else:
            # resolve _id via app_id
            ref = client.find_application(args.app_id)
            app = client.get(f"applications/{ref['_id']}")

        if args.format == "json":
            print(json.dumps(app, ensure_ascii=False, indent=2))
        else:
            render_md(app, show_hidden=args.show_hidden)

    except EcomplusError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
