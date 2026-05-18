#!/usr/bin/env python3
"""
Mostra informações da sessão E-Com Plus atual.

Lê credenciais em ordem: env vars > ~/.ecomplus_session.json.
Consulta GET /authentications/{my_id}.json para confirmar que o token é válido.

Uso:
  python whoami.py
  python whoami.py --format json
  python whoami.py --export     # imprime export VAR=val a partir da sessão salva (sem chamar a API)
"""
import argparse
import json
import sys
import os
from datetime import datetime, timezone

import requests

sys.path.insert(0, os.path.dirname(__file__))
from auth_session import (
    AuthError, SESSION_FILE, get_base_url, get_credentials, load_session, print_export
)


def parse_expires(expires: str):
    """Retorna (is_valid, expires_local_str). Nunca levanta exceção."""
    if not expires:
        return True, "desconhecida"
    try:
        if expires.lstrip("-").isdigit():
            dt = datetime.fromtimestamp(int(expires) / 1000, tz=timezone.utc)
        else:
            dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        is_valid = dt > datetime.now(tz=timezone.utc)
        local = dt.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        return is_valid, local
    except Exception:
        return True, expires


def fetch_auth_info(base_url: str, store_id: str, my_id: str, access_token: str) -> dict:
    try:
        r = requests.get(
            f"{base_url}/authentications/{my_id}.json",
            headers={
                "X-Store-ID": store_id,
                "X-My-ID": my_id,
                "X-Access-Token": access_token,
            },
            timeout=15,
        )
        if r.ok:
            return r.json()
    except Exception:
        pass
    return {}


def main():
    parser = argparse.ArgumentParser(description="Mostra sessão E-Com Plus atual")
    parser.add_argument("--format", choices=["md", "json"], default="md")
    parser.add_argument("--sandbox", action="store_true", help="Usar sandbox")
    parser.add_argument("--export", action="store_true",
                        help="Imprimir export VAR=val da sessão salva (não chama a API)")
    args = parser.parse_args()

    if args.export:
        try:
            session = load_session()
            print_export(session)
        except AuthError as e:
            print(f"Erro: {e}", file=sys.stderr)
            sys.exit(1)
        return

    base_url = get_base_url(args.sandbox)

    try:
        store_id, access_token, my_id = get_credentials()
    except AuthError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)

    # Carrega metadados extras da sessão salva (username, expires)
    session_data = {}
    if SESSION_FILE.exists():
        try:
            session_data = json.loads(SESSION_FILE.read_text())
        except Exception:
            pass

    expires = session_data.get("expires", "")
    username = session_data.get("username", "")
    is_valid, expires_local = parse_expires(expires)

    # Busca info adicional na API (melhor esforço, não bloqueia se falhar)
    auth_info = fetch_auth_info(base_url, store_id, my_id, access_token)
    if auth_info:
        username = username or auth_info.get("username", "")

    status_label = "válido" if is_valid else "EXPIRADO"

    data = {
        "store_id": store_id,
        "my_id": my_id,
        "username": username or "(desconhecido)",
        "token_status": status_label,
        "expires": expires_local,
    }

    if args.format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    print("## Sessão E-Com Plus\n")
    print("| Campo | Valor |")
    print("|---|---|")
    print(f"| Store ID | `{data['store_id']}` |")
    print(f"| My ID | `{data['my_id']}` |")
    print(f"| Usuário | {data['username']} |")
    print(f"| Token expira em | {data['expires']} |")
    status_display = "✓ válido" if is_valid else "✗ EXPIRADO"
    print(f"| Status | {status_display} |")

    if not is_valid:
        print()
        print("> Token expirado. Execute: `python scripts/refresh.py`")


if __name__ == "__main__":
    main()
