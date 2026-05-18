"""
Utilitário de sessão E-Com Plus — importado pelos demais scripts de auth.

Carrega credenciais em ordem: env vars > ~/.ecomplus_session.json
"""
import json
import os
from pathlib import Path
from typing import Tuple

import requests

BASE_URL_PROD = "https://api.e-com.plus/v1"
BASE_URL_SANDBOX = "https://sandbox.e-com.plus/v1"
SESSION_FILE = Path.home() / ".ecomplus_session.json"


class AuthError(Exception):
    pass


def get_base_url(sandbox: bool = False) -> str:
    return BASE_URL_SANDBOX if sandbox else BASE_URL_PROD


def load_session() -> dict:
    if not SESSION_FILE.exists():
        raise AuthError(
            f"Sessão não encontrada em {SESSION_FILE}. "
            "Execute python scripts/login.py primeiro."
        )
    return json.loads(SESSION_FILE.read_text())


def save_session(data: dict) -> None:
    SESSION_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    SESSION_FILE.chmod(0o600)


def get_credentials() -> Tuple[str, str, str]:
    """Retorna (store_id, access_token, my_id). Env vars primeiro, session file como fallback."""
    store_id = os.environ.get("ECOMPLUS_STORE_ID")
    access_token = os.environ.get("ECOMPLUS_ACCESS_TOKEN")
    my_id = os.environ.get("ECOMPLUS_MY_ID")
    if store_id and access_token and my_id:
        return store_id, access_token, my_id
    s = load_session()
    return s["store_id"], s["access_token"], s["my_id"]


def call_authenticate(store_id, my_id: str, api_key: str, base_url: str) -> dict:
    """POST /_authenticate.json → {access_token, my_id, expires}."""
    r = requests.post(
        f"{base_url}/_authenticate.json",
        json={"_id": my_id, "api_key": api_key},
        headers={
            "X-Store-ID": str(store_id),
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
        raise AuthError(f"Erro na autenticação ({r.status_code}): {msg}")
    return r.json()


def print_export(session: dict) -> None:
    """Imprime comandos export para o shell (uso com eval)."""
    print(f"export ECOMPLUS_STORE_ID={session['store_id']}")
    print(f"export ECOMPLUS_ACCESS_TOKEN={session['access_token']}")
    print(f"export ECOMPLUS_MY_ID={session['my_id']}")
