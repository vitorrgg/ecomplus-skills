#!/usr/bin/env python3
"""
Consulta logs de auditoria da API E-Com Plus.

Os logs registram PATCH/POST/DELETE em qualquer recurso (pedidos, produtos, etc.).
Útil para rastrear quem/quando alterou um documento.

Modos de uso:
  Por recurso específico:
    python get_logs.py --resource-id 5cf...abc
    python get_logs.py --resource-id 5cf...abc --limit 20

  Por período (obrigatório --from, --to opcional):
    python get_logs.py --from 2026-05-01
    python get_logs.py --from 2026-05-01 --to 2026-05-28

  Combinando filtros:
    python get_logs.py --from 2026-05-01 --to 2026-05-28 --resource-type orders
    python get_logs.py --from 2026-05-01 --method PATCH
    python get_logs.py --from 2026-05-01 --resource-type products --method DELETE

  Detalhe de uma entrada:
    python get_logs.py --log-id abc123
"""
import argparse
import csv
import json
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
from ecomplus_client import EcomplusClient, EcomplusError

RESOURCE_TYPES = [
    "orders", "products", "customers", "carts", "applications",
    "categories", "brands", "collections", "grids", "stores",
]


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


def origin_label(ip: str) -> str:
    return "*(app)*" if is_internal(ip) else (ip or "—")


def fetch_logs_by_resource(client, resource_id: str, limit: int) -> list:
    body = client.get("@logs", params={
        "resource_id": resource_id,
        "limit": min(limit, 100),
    })
    return body.get("result", [])


def fetch_logs_by_period(client, date_from: str, date_to: str, limit: int) -> list:
    """
    Busca logs por período usando filtros date_time>= / date_time<=.
    A API pode retornar no máximo 100 por página; paginamos até o limite pedido.
    """
    params = {
        "date_time>=": f"{date_from}T00:00:00.000Z",
        "sort": "-date_time",
        "limit": min(limit, 100),
    }
    if date_to:
        params["date_time<="] = f"{date_to}T23:59:59.999Z"

    collected = []
    offset = 0
    while len(collected) < limit:
        params["offset"] = offset
        body = client.get("@logs", params=params)
        page = body.get("result", [])
        if not page:
            break
        collected.extend(page)
        if len(page) < params["limit"]:
            break
        offset += params["limit"]

    return collected[:limit]


def apply_filters(logs: list, resource_type: str = None, method: str = None) -> list:
    if resource_type:
        needle = f"/{resource_type}/"
        logs = [l for l in logs if needle in (l.get("api_resource") or "")]
    if method:
        logs = [l for l in logs if l.get("method", "").upper() == method.upper()]
    return logs


def render_log_detail(log: dict) -> str:
    lines = [f"## Log `{log.get('id', '?')}`\n"]
    lines.append("| Campo | Valor |")
    lines.append("|---|---|")
    lines.append(f"| Data/hora | {fmt_date(log.get('date_time', ''))} |")
    lines.append(f"| Método | `{log.get('method', '')}` |")
    lines.append(f"| Recurso | `{log.get('api_resource', '')}` |")
    ip = log.get("ip_addr", "")
    src = " *(interno)*" if is_internal(ip) else ""
    lines.append(f"| IP | {ip}{src} |")
    if log.get("authentication_id"):
        lines.append(f"| Auth ID | `{log['authentication_id']}` |")
    if log.get("body"):
        lines.append("\n### Payload enviado\n```json")
        lines.append(json.dumps(log["body"], ensure_ascii=False, indent=2))
        lines.append("```")
    if log.get("response"):
        lines.append("\n### Resposta da API\n```json")
        lines.append(json.dumps(log["response"], ensure_ascii=False, indent=2))
        lines.append("```")
    return "\n".join(lines)


def render_log_list_md(logs: list, title: str) -> str:
    lines = [f"## {title}\n"]
    lines.append(f"**{len(logs)} entrada(s) encontrada(s)**\n")
    lines.append("| Data/Hora | Método | Recurso | Origem | Auth ID |")
    lines.append("|---|---|---|---|---|")
    for log in logs:
        resource = log.get("api_resource", "")
        if len(resource) > 45:
            resource = "…" + resource[-42:]
        auth = log.get("authentication_id", "")
        auth_short = f"`{auth[:8]}…`" if auth else "—"
        lines.append(
            f"| {fmt_date(log.get('date_time', ''))} "
            f"| `{log.get('method', '')}` "
            f"| `{resource}` "
            f"| {origin_label(log.get('ip_addr', ''))} "
            f"| {auth_short} |"
        )
    if logs:
        sample_ids = ", ".join(f"`{l['id']}`" for l in logs[:3])
        suffix = "…" if len(logs) > 3 else ""
        lines.append(f"\n> Use `--log-id <id>` para ver payload + resposta completa. IDs: {sample_ids}{suffix}")
    return "\n".join(lines)


def render_log_list_csv(logs: list, writer) -> None:
    writer.writerow(["date_time", "method", "api_resource", "ip_addr", "origin", "authentication_id", "log_id"])
    for log in logs:
        writer.writerow([
            log.get("date_time", ""),
            log.get("method", ""),
            log.get("api_resource", ""),
            log.get("ip_addr", ""),
            "app" if is_internal(log.get("ip_addr", "")) else "external",
            log.get("authentication_id", ""),
            log.get("id", ""),
        ])


def main():
    parser = argparse.ArgumentParser(description="Logs de auditoria E-Com Plus")

    parser.add_argument("--resource-id", dest="resource_id",
                        help="_id do documento (pedido, produto, cliente…) para ver seus logs")
    parser.add_argument("--log-id", dest="log_id",
                        help="ID de uma entrada específica de log (mostra payload + resposta)")
    parser.add_argument("--from", dest="date_from",
                        help="Data inicial YYYY-MM-DD (busca por período)")
    parser.add_argument("--to", dest="date_to",
                        help="Data final YYYY-MM-DD (opcional com --from; default: hoje)")
    parser.add_argument("--resource-type", dest="resource_type",
                        choices=RESOURCE_TYPES, metavar="|".join(RESOURCE_TYPES),
                        help="Filtrar por tipo de recurso (ex: orders, products, customers)")
    parser.add_argument("--method", choices=["GET", "POST", "PATCH", "DELETE", "PUT"],
                        help="Filtrar por método HTTP")
    parser.add_argument("--limit", type=int, default=50,
                        help="Máximo de entradas a retornar (padrão: 50)")
    parser.add_argument("--format", choices=["md", "json", "csv"], default="md")
    parser.add_argument("--sandbox", action="store_true",
                        help="Usar sandbox.e-com.plus em vez de produção")
    args = parser.parse_args()

    if not args.resource_id and not args.log_id and not args.date_from:
        parser.error("Informe ao menos um de: --resource-id, --log-id ou --from")

    try:
        client = EcomplusClient.from_env()
        if args.sandbox:
            import ecomplus_client as _m
            _m.BASE_URL = "https://sandbox.e-com.plus/v1"

        # --- Modo detalhe de log individual ---
        if args.log_id:
            log = client.get(f"@logs/{args.log_id}")
            if args.format == "json":
                print(json.dumps(log, ensure_ascii=False, indent=2))
            else:
                print(render_log_detail(log))
            return

        # --- Modo por recurso específico ---
        if args.resource_id:
            logs = fetch_logs_by_resource(client, args.resource_id, args.limit)
            logs = apply_filters(logs, args.resource_type, args.method)
            title = f"Logs de auditoria — recurso `{args.resource_id}`"

        # --- Modo por período ---
        else:
            logs = fetch_logs_by_period(client, args.date_from, args.date_to, args.limit)
            logs = apply_filters(logs, args.resource_type, args.method)
            date_range = args.date_from
            if args.date_to:
                date_range += f" a {args.date_to}"
            filters = []
            if args.resource_type:
                filters.append(f"recurso={args.resource_type}")
            if args.method:
                filters.append(f"método={args.method}")
            suffix = f" ({', '.join(filters)})" if filters else ""
            title = f"Logs de auditoria — {date_range}{suffix}"

        if not logs:
            print("Nenhum log encontrado para os filtros informados.")
            return

        if args.format == "json":
            print(json.dumps(logs, ensure_ascii=False, indent=2))
        elif args.format == "csv":
            writer = csv.writer(sys.stdout)
            render_log_list_csv(logs, writer)
        else:
            print(render_log_list_md(logs, title))

    except EcomplusError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
