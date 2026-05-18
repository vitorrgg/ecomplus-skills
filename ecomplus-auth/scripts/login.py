#!/usr/bin/env python3
"""
Login na E-Com Plus. Salva sessão em ~/.ecomplus_session.json.

Uso:
  python login.py --username user@example.com
  python login.py --username user@example.com --password minhasenha
  eval $(python login.py --username user@example.com --password s3cr3t --export)

Login direto com api_key (sem senha):
  eval $(python login.py --store-id 1011 --my-id <my_id> --api-key <api_key> --export)
"""
import argparse
import getpass
import hashlib
import sys
import os

import requests

sys.path.insert(0, os.path.dirname(__file__))
from auth_session import (
    AuthError, get_base_url, save_session, print_export, call_authenticate, SESSION_FILE
)


def md5_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def call_login(base_url: str, username: str, password_md5: str) -> dict:
    """POST /_login.json → {store_id, _id, api_key}."""
    is_email = "@" in username
    data = {"pass_md5_hash": password_md5}
    url = f"{base_url}/_login.json"
    if is_email:
        data["email"] = username
    else:
        data["username"] = username
        url += f"?username={username}"

    r = requests.post(
        url,
        json=data,
        headers={
            "X-Store-ID": "1",
            "Content-Type": "application/json; charset=UTF-8",
        },
        timeout=30,
    )
    if not r.ok:
        try:
            body = r.json()
            msg = (body.get("user_message") or {}).get("pt_br") or body.get("message", r.text)
        except Exception:
            msg = r.text[:300]
        raise AuthError(f"Login falhou ({r.status_code}): {msg}")
    return r.json()


def main():
    parser = argparse.ArgumentParser(description="Login na E-Com Plus")
    parser.add_argument("--username", help="E-mail ou username da conta")
    parser.add_argument("--password", help="Senha (pedida interativamente se omitida)")
    parser.add_argument("--store-id", type=int, dest="store_id",
                        help="Store ID (requerido com --api-key)")
    parser.add_argument("--my-id", dest="my_id",
                        help="My ID (requerido com --api-key)")
    parser.add_argument("--api-key", dest="api_key",
                        help="API Key permanente (dispensa --username e --password)")
    parser.add_argument("--sandbox", action="store_true", help="Usar sandbox")
    parser.add_argument("--export", action="store_true",
                        help="Imprimir apenas 'export VAR=val' (para uso com eval)")
    args = parser.parse_args()

    base_url = get_base_url(args.sandbox)

    try:
        if args.api_key:
            # Login direto: pula /_login.json, vai direto para /_authenticate.json
            if not args.store_id or not args.my_id:
                print("Erro: --store-id e --my-id são obrigatórios com --api-key", file=sys.stderr)
                sys.exit(1)
            store_id = args.store_id
            my_id = args.my_id
            api_key = args.api_key
            display_name = f"{store_id}:{my_id}"
        else:
            username = args.username
            if not username:
                if args.export:
                    print("Erro: --username obrigatório com --export", file=sys.stderr)
                    sys.exit(1)
                username = input("E-mail ou username: ").strip()

            password = args.password
            if not password:
                if args.export:
                    print("Erro: --password obrigatório com --export", file=sys.stderr)
                    sys.exit(1)
                password = getpass.getpass("Senha: ")

            login_data = call_login(base_url, username, md5_hash(password))
            store_id = login_data["store_id"]
            my_id = login_data["_id"]
            api_key = login_data["api_key"]
            display_name = username

        auth_data = call_authenticate(
            base_url=base_url,
            store_id=store_id,
            my_id=my_id,
            api_key=api_key,
        )

        session = {
            "store_id": str(store_id),
            "my_id": my_id,
            "api_key": api_key,
            "access_token": auth_data["access_token"],
            "expires": auth_data.get("expires", ""),
            "username": display_name,
        }
        save_session(session)

        if args.export:
            print_export(session)
        else:
            expires = session["expires"]
            print(f"Login OK — loja #{store_id} ({display_name}), token expira em {expires}")
            print(f"Sessão salva em {SESSION_FILE}")
            print()
            print("Para exportar as variáveis de ambiente:")
            print("  eval $(python scripts/refresh.py --export)")

    except AuthError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelado.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
