#!/usr/bin/env python3
"""
Renova o access_token da E-Com Plus usando a api_key salva em ~/.ecomplus_session.json.

A api_key é permanente. O access_token dura ~1h. Use este script quando outra skill
retornar 401 por token expirado.

Uso:
  python refresh.py
  eval $(python refresh.py --export)
  eval $(python refresh.py --export --sandbox)
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from auth_session import (
    AuthError, get_base_url, load_session, save_session, print_export, call_authenticate
)


def main():
    parser = argparse.ArgumentParser(description="Renova o access_token da E-Com Plus")
    parser.add_argument("--sandbox", action="store_true", help="Usar sandbox")
    parser.add_argument("--export", action="store_true",
                        help="Imprimir apenas 'export VAR=val' (para uso com eval)")
    args = parser.parse_args()

    base_url = get_base_url(args.sandbox)

    try:
        session = load_session()

        missing = [k for k in ("store_id", "my_id", "api_key") if not session.get(k)]
        if missing:
            print(
                f"Erro: sessão incompleta — falta {', '.join(missing)}. "
                "Refaça o login com login.py.",
                file=sys.stderr,
            )
            sys.exit(1)

        auth_data = call_authenticate(
            base_url=base_url,
            store_id=session["store_id"],
            my_id=session["my_id"],
            api_key=session["api_key"],
        )

        session["access_token"] = auth_data["access_token"]
        session["expires"] = auth_data.get("expires", "")
        save_session(session)

        if args.export:
            print_export(session)
        else:
            print(f"Token renovado — expira em {session['expires']}")
            print("Para exportar as variáveis de ambiente:")
            print("  eval $(python scripts/refresh.py --export)")

    except AuthError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
