#!/usr/bin/env python3
"""
Lista aplicativos instalados na loja E-Com Plus.

Uso:
  python list_apps.py                          # todos os apps
  python list_apps.py --state active           # só os ativos
  python list_apps.py --app-id 124890          # filtrar por app_id do marketplace
  python list_apps.py --format json
  python list_apps.py --format csv
"""
import argparse
import csv
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
        return dt.astimezone().strftime("%d/%m/%Y")
    except Exception:
        return iso[:10]


def main():
    parser = argparse.ArgumentParser(description="Lista apps instalados na E-Com Plus")
    parser.add_argument("--app-id", type=int, dest="app_id",
                        help="Filtrar pelo app_id numérico do marketplace")
    parser.add_argument("--state", choices=["active", "paused"],
                        help="Filtrar por estado: active ou paused")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--format", choices=["md", "csv", "json"], default="md")
    parser.add_argument("--sandbox", action="store_true")
    args = parser.parse_args()

    params: dict = {
        "fields": "_id,app_id,title,state,version,installed_at,updated_at",
    }
    if args.app_id is not None:
        params["app_id"] = args.app_id
    if args.state:
        params["state"] = args.state

    try:
        client = EcomplusClient.from_env()
        if args.sandbox:
            import ecomplus_client
            ecomplus_client.BASE_URL = "https://sandbox.e-com.plus/v1"

        apps = []
        for app in client.list_all("applications", params=params):
            apps.append(app)
            if len(apps) >= args.limit:
                break

        if not apps:
            print("Nenhum aplicativo encontrado com os filtros informados.")
            return

        if args.format == "json":
            print(json.dumps(apps, ensure_ascii=False, indent=2))
            return

        rows = []
        for app in apps:
            rows.append({
                "ID": app.get("_id", ""),
                "App ID": app.get("app_id", ""),
                "Título": app.get("title", "(sem título)"),
                "Estado": app.get("state", ""),
                "Versão": app.get("version", ""),
                "Instalado em": fmt_date(app.get("installed_at", "")),
                "Atualizado em": fmt_date(app.get("updated_at", "")),
            })

        if args.format == "csv":
            writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0].keys()),
                                    lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
            return

        # Markdown
        print(f"**{len(apps)} aplicativo(s) encontrado(s)**\n")
        print("| Título | App ID | Estado | Versão | Instalado em | ID |")
        print("|---|---|---|---|---|---|")
        for r in rows:
            state_icon = "✓" if r["Estado"] == "active" else "⏸"
            print(f"| {r['Título']} | {r['App ID']} | {state_icon} {r['Estado']} "
                  f"| {r['Versão']} | {r['Instalado em']} | `{r['ID'][:8]}...` |")

        if len(apps) >= args.limit:
            print(f"\n> Limitado a {args.limit}. Use `--limit N` para ver mais.")

    except EcomplusError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
