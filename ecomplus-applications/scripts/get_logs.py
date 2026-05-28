#!/usr/bin/env python3
"""
Consulta logs de auditoria da API E-Com Plus.

Os logs registram PATCH/POST/DELETE em qualquer recurso (pedidos, produtos, etc.).
Útil para rastrear quem/quando alterou um documento.

Uso:
  python get_logs.py --resource-id 5cf...abc          # logs de um recurso
  python get_logs.py --resource-id 5cf...abc --limit 20
  python get_logs.py --log-id abc123                  # detalhe de uma entrada
  python get_logs.py --resource-id 5cf...abc --format json
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
        return dt.astimezone().strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return iso[:19]


def is_internal(ip: str) -> bool:
    """IPs iniciando com 127.9 são chamadas internas de aplicativos."""
    return (ip or "").startswith("127.9")


def main():
    parser = argparse.ArgumentParser(description="Logs de auditoria E-Com Plus")

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--resource-id", dest="resource_id",
                      help="_id do recurso (pedido, produto, cliente, etc.)")
    mode.add_argument("--log-id", dest="log_id",
                      help="ID de uma entrada específica de log")

    parser.add_argument("--limit", type=int, default=50,
                        help="Número máximo de entradas (padrão: 50)")
    parser.add_argument("--format", choices=["md", "json"], default="md")
    parser.add_argument("--sandbox", action="store_true")
    args = parser.parse_args()

    try:
        client = EcomplusClient.from_env()
        if args.sandbox:
            import ecomplus_client
            ecomplus_client.BASE_URL = "https://sandbox.e-com.plus/v1"

        if args.log_id:
            # Detalhe de uma entrada específica
            log = client.get(f"@logs/{args.log_id}")
            if args.format == "json":
                print(json.dumps(log, ensure_ascii=False, indent=2))
                return

            print(f"## Log `{args.log_id}`\n")
            print("| Campo | Valor |")
            print("|---|---|")
            print(f"| Data/hora | {fmt_date(log.get('date_time', ''))} |")
            print(f"| Método | `{log.get('method', '')}` |")
            print(f"| Recurso | `{log.get('api_resource', '')}` |")
            ip = log.get("ip_addr", "")
            src = " *(interno)*" if is_internal(ip) else ""
            print(f"| IP | {ip}{src} |")
            if log.get("authentication_id"):
                print(f"| Auth ID | `{log['authentication_id']}` |")
            if log.get("body"):
                print("\n### Payload enviado\n```json")
                print(json.dumps(log["body"], ensure_ascii=False, indent=2))
                print("```")
            if log.get("response"):
                print("\n### Resposta da API\n```json")
                print(json.dumps(log["response"], ensure_ascii=False, indent=2))
                print("```")
            return

        # Listar logs por resource_id
        body = client.get("@logs", params={
            "resource_id": args.resource_id,
            "limit": min(args.limit, 100),
        })
        logs = body.get("result", [])

        if not logs:
            print(f"Nenhum log encontrado para resource_id={args.resource_id}")
            return

        if args.format == "json":
            print(json.dumps(logs, ensure_ascii=False, indent=2))
            return

        print(f"**{len(logs)} entrada(s) de log** para `{args.resource_id}`\n")
        print("| Data/Hora | Método | Recurso | IP/Origem | Auth ID |")
        print("|---|---|---|---|---|")
        for log in logs:
            ip = log.get("ip_addr", "")
            src = "*(app)*" if is_internal(ip) else ip
            auth = log.get("authentication_id", "")
            auth_short = f"`{auth[:8]}...`" if auth else "-"
            resource = log.get("api_resource", "")
            # shorten long resource path
            if len(resource) > 40:
                resource = "..." + resource[-37:]
            print(f"| {fmt_date(log.get('date_time', ''))} "
                  f"| `{log.get('method', '')}` "
                  f"| `{resource}` "
                  f"| {src} "
                  f"| {auth_short} |")

        print(f"\n> Use `--log-id <id>` para ver o detalhe de uma entrada "
              f"(payload + resposta completa).")
        ids_preview = ", ".join(f"`{l['id']}`" for l in logs[:3])
        print(f"> Log IDs: {ids_preview}{'...' if len(logs) > 3 else ''}")

    except EcomplusError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
