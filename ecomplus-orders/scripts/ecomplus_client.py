"""
Cliente HTTP para a API REST da E-Com Plus.

Lida com:
- autenticação via headers X-Store-ID, X-Access-Token, X-My-ID
- paginação automática (offset/limit)
- rate limit (6 req/s → sleep de 0.2s entre páginas)
- retry com backoff em 5xx/503
- erros 4xx levantados como exceção legível
- PATCH e POST para mutações

Uso:
    from ecomplus_client import EcomplusClient
    client = EcomplusClient.from_env()
    orders = list(client.list_all("orders", params={"financial_status.current": "paid"}))
    client.patch("orders/5cf...abc", {"financial_status": {"current": "paid"}})
"""
import os
import time
import urllib.parse
import requests
from urllib.parse import quote
from typing import Iterator, Optional


BASE_URL = "https://api.e-com.plus/v1"
PAGE_SIZE = 100
RATE_LIMIT_SLEEP = 0.2


class EcomplusError(Exception):
    pass


class EcomplusClient:
    def __init__(self, store_id: str, access_token: str, my_id: str):
        self.store_id = str(store_id)
        self.access_token = access_token
        self.my_id = my_id
        self.session = requests.Session()
        self.session.headers.update({
            "X-Store-ID": self.store_id,
            "X-Access-Token": self.access_token,
            "X-My-ID": self.my_id,
            "Content-Type": "application/json; charset=utf-8",
            "Accept-Encoding": "gzip",
        })

    @classmethod
    def from_env(cls) -> "EcomplusClient":
        """Lê credenciais das env vars. Fallback: ~/.ecomplus_session.json."""
        store_id = os.environ.get("ECOMPLUS_STORE_ID")
        access_token = os.environ.get("ECOMPLUS_ACCESS_TOKEN")
        my_id = os.environ.get("ECOMPLUS_MY_ID")
        if not (store_id and access_token and my_id):
            # Tenta carregar da sessão salva
            import json
            from pathlib import Path
            session_file = Path.home() / ".ecomplus_session.json"
            if session_file.exists():
                s = json.loads(session_file.read_text())
                store_id = store_id or s.get("store_id")
                access_token = access_token or s.get("access_token")
                my_id = my_id or s.get("my_id")
        missing = [k for k, v in [
            ("ECOMPLUS_STORE_ID", store_id),
            ("ECOMPLUS_ACCESS_TOKEN", access_token),
            ("ECOMPLUS_MY_ID", my_id),
        ] if not v]
        if missing:
            raise EcomplusError(
                f"Credenciais faltando: {', '.join(missing)}. "
                "Defina as env vars ou rode ecomplus-auth/scripts/login.py primeiro."
            )
        return cls(store_id, access_token, my_id)

    def _url(self, path: str) -> str:
        url = f"{BASE_URL}/{path.lstrip('/')}"
        if not url.split("?")[0].endswith(".json"):
            url = url.replace("?", ".json?", 1) if "?" in url else f"{url}.json"
        return url

    def _handle_error(self, response: requests.Response, context: str) -> None:
        try:
            body = response.json()
            msg = (body.get("user_message") or {}).get("pt_br") or body.get("message")
        except Exception:
            msg = response.text[:300]
        raise EcomplusError(f"HTTP {response.status_code} em {context}: {msg}")

    def get(self, path: str, params: Optional[dict] = None, max_retries: int = 3) -> dict:
        """GET com retry em 5xx."""
        url = self._url(path)
        if params:
            parts = []
            for k, v in params.items():
                sep = "" if k and k[-1] in (">", "<", "=", "!") else "="
                parts.append(f"{k}{sep}{quote(str(v), safe='')}")
            url = f"{url}?{'&'.join(parts)}"
        backoff = 1.0
        for attempt in range(max_retries):
            r = self.session.get(url, timeout=30)
            if r.status_code < 400:
                return r.json()
            if r.status_code in (502, 503, 504) and attempt < max_retries - 1:
                time.sleep(backoff)
                backoff *= 2
                continue
            self._handle_error(r, f"GET {path}")
        raise EcomplusError(f"Falha após {max_retries} tentativas em GET {path}")

    def list_all(self, resource: str, params: Optional[dict] = None) -> Iterator[dict]:
        """Itera todos os resultados paginando automaticamente."""
        params = dict(params or {})
        params.setdefault("limit", PAGE_SIZE)
        offset = 0
        while True:
            params["offset"] = offset
            body = self.get(resource, params=params)
            results = body.get("result", [])
            if not results:
                break
            yield from results
            if len(results) < params["limit"]:
                break
            offset += params["limit"]
            time.sleep(RATE_LIMIT_SLEEP)

    def patch(self, path: str, data: dict, max_retries: int = 3) -> dict:
        """PATCH parcial num recurso. Retorna o documento atualizado."""
        url = self._url(path)
        backoff = 1.0
        for attempt in range(max_retries):
            r = self.session.patch(url, json=data, timeout=30)
            if r.status_code < 400:
                # PATCH bem-sucedido retorna 204 No Content ou o doc atualizado
                return r.json() if r.content else {}
            if r.status_code in (502, 503, 504) and attempt < max_retries - 1:
                time.sleep(backoff)
                backoff *= 2
                continue
            self._handle_error(r, f"PATCH {path}")
        raise EcomplusError(f"Falha após {max_retries} tentativas em PATCH {path}")

    def find_order_by_number(self, number: int) -> dict:
        """Busca pedido pelo número humano. Levanta EcomplusError se não encontrar."""
        body = self.get("orders", params={"number": number, "limit": 1})
        results = body.get("result", [])
        if not results:
            raise EcomplusError(f"Pedido #{number} não encontrado.")
        return results[0]


def format_brl(value: float) -> str:
    """Formata float como R$ 1.234,56 (padrão brasileiro)."""
    s = f"{value:,.2f}"
    return f"R$ {s.replace(',', 'X').replace('.', ',').replace('X', '.')}"
