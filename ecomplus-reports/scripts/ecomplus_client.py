"""
Cliente HTTP minimalista para a API REST da E-Com Plus.

Lida com:
- autenticação via headers X-Store-ID, X-Access-Token, X-My-ID
- paginação automática (offset/limit)
- rate limit (6 req/s autenticadas → sleep de 0.2s entre páginas)
- retry com backoff em 5xx e 503
- erros 4xx levantados como exceção legível

Uso:
    from ecomplus_client import EcomplusClient
    client = EcomplusClient.from_env()
    orders = client.list_all("orders", params={"status": "open"})
"""
import os
import time
import urllib.parse
import requests
from typing import Iterator, Optional


BASE_URL = "https://api.e-com.plus/v1"
PAGE_SIZE = 100  # máximo permitido pela API
RATE_LIMIT_SLEEP = 0.2  # 5 req/s, com folga em relação ao limite de 6/s


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
        try:
            return cls(
                store_id=os.environ["ECOMPLUS_STORE_ID"],
                access_token=os.environ["ECOMPLUS_ACCESS_TOKEN"],
                my_id=os.environ["ECOMPLUS_MY_ID"],
            )
        except KeyError as e:
            raise EcomplusError(
                f"Variável de ambiente obrigatória faltando: {e}. "
                "Defina ECOMPLUS_STORE_ID, ECOMPLUS_ACCESS_TOKEN e ECOMPLUS_MY_ID."
            )

    def get(self, path: str, params: Optional[dict] = None, max_retries: int = 3) -> dict:
        """GET único, com retry em 5xx."""
        url = f"{BASE_URL}/{path.lstrip('/')}"
        if not url.endswith(".json"):
            # API exige .json no final
            if "?" in url:
                url = url.replace("?", ".json?", 1)
            else:
                url = f"{url}.json"
        if params:
            # A API espera filtros literais como created_at>=VALUE (sem encoding).
            # Chaves que terminam com = já incluem o separador; demais usam =.
            parts = []
            for k, v in params.items():
                parts.append(str(k) + str(v) if str(k).endswith("=") else f"{k}={v}")
            url = f"{url}?{'&'.join(parts)}"

        backoff = 1.0
        for attempt in range(max_retries):
            response = self.session.get(url, timeout=30)
            if response.status_code < 400:
                return response.json()
            if response.status_code in (502, 503, 504):
                if attempt < max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
            # Erro definitivo
            try:
                body = response.json()
                msg = body.get("user_message", {}).get("pt_br") or body.get("message")
            except Exception:
                msg = response.text[:300]
            raise EcomplusError(
                f"HTTP {response.status_code} em GET {path}: {msg}"
            )
        raise EcomplusError(f"Falha após {max_retries} tentativas em GET {path}")

    def list_all(self, resource: str, params: Optional[dict] = None) -> Iterator[dict]:
        """
        Itera por todos os resultados de uma listagem paginando automaticamente.
        Ex.: client.list_all("orders", params={"status": "open"})
        """
        params = dict(params or {})
        params.setdefault("limit", PAGE_SIZE)
        offset = 0
        while True:
            params["offset"] = offset
            body = self.get(resource, params=params)
            results = body.get("result", [])
            if not results:
                break
            for item in results:
                yield item
            if len(results) < params["limit"]:
                break
            offset += params["limit"]
            time.sleep(RATE_LIMIT_SLEEP)


def format_brl(value: float) -> str:
    """Formata um float como R$ 1.234,56 (padrão brasileiro)."""
    s = f"{value:,.2f}"
    return f"R$ {s.replace(',', 'X').replace('.', ',').replace('X', '.')}"
