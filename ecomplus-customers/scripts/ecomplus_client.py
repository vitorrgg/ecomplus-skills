"""
Cliente HTTP para a API REST da E-Com Plus.
Credenciais: env vars > ~/.ecomplus_session.json
"""
import json
import os
import time
from pathlib import Path
from typing import Iterator, Optional

import requests
from urllib.parse import quote

BASE_URL = "https://api.e-com.plus/v1"
PAGE_SIZE = 100
RATE_LIMIT_SLEEP = 0.2


class EcomplusError(Exception):
    pass


class EcomplusClient:
    def __init__(self, store_id: str, access_token: str, my_id: str):
        self.store_id = str(store_id)
        self.session = requests.Session()
        self.session.headers.update({
            "X-Store-ID": self.store_id,
            "X-Access-Token": access_token,
            "X-My-ID": my_id,
            "Content-Type": "application/json; charset=utf-8",
            "Accept-Encoding": "gzip",
        })

    @classmethod
    def from_env(cls) -> "EcomplusClient":
        store_id = os.environ.get("ECOMPLUS_STORE_ID")
        access_token = os.environ.get("ECOMPLUS_ACCESS_TOKEN")
        my_id = os.environ.get("ECOMPLUS_MY_ID")
        if not (store_id and access_token and my_id):
            sf = Path.home() / ".ecomplus_session.json"
            if sf.exists():
                s = json.loads(sf.read_text())
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
                "Rode ecomplus-auth/scripts/login.py primeiro."
            )
        return cls(store_id, access_token, my_id)

    def _url(self, path: str) -> str:
        url = f"{BASE_URL}/{path.lstrip('/')}"
        if not url.split("?")[0].endswith(".json"):
            url = url.replace("?", ".json?", 1) if "?" in url else f"{url}.json"
        return url

    def _raise_for(self, r: requests.Response, ctx: str) -> None:
        try:
            body = r.json()
            msg = (body.get("user_message") or {}).get("pt_br") or body.get("message")
        except Exception:
            msg = r.text[:300]
        raise EcomplusError(f"HTTP {r.status_code} em {ctx}: {msg}")

    def get(self, path: str, params: Optional[dict] = None, max_retries: int = 3) -> dict:
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
                time.sleep(backoff); backoff *= 2; continue
            self._raise_for(r, f"GET {path}")
        raise EcomplusError(f"Falha após {max_retries} tentativas em GET {path}")

    def list_all(self, resource: str, params: Optional[dict] = None) -> Iterator[dict]:
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
        url = self._url(path)
        backoff = 1.0
        for attempt in range(max_retries):
            r = self.session.patch(url, json=data, timeout=30)
            if r.status_code < 400:
                return r.json() if r.content else {}
            if r.status_code in (502, 503, 504) and attempt < max_retries - 1:
                time.sleep(backoff); backoff *= 2; continue
            self._raise_for(r, f"PATCH {path}")
        raise EcomplusError(f"Falha após {max_retries} tentativas em PATCH {path}")

    def find_customer(self, email: Optional[str] = None,
                      doc: Optional[str] = None) -> dict:
        """Busca cliente por e-mail ou CPF/CNPJ. Levanta EcomplusError se não encontrar."""
        if email:
            params = {"main_email": email, "limit": 1}
        elif doc:
            params = {"doc_number": doc.replace(".", "").replace("-", "").replace("/", ""),
                      "limit": 1}
        else:
            raise EcomplusError("Informe --email ou --doc.")
        body = self.get("customers", params=params)
        results = body.get("result", [])
        if not results:
            key = f"e-mail '{email}'" if email else f"doc '{doc}'"
            raise EcomplusError(f"Cliente com {key} não encontrado.")
        return results[0]


def format_brl(value: float) -> str:
    s = f"{value:,.2f}"
    return f"R$ {s.replace(',', 'X').replace('.', ',').replace('X', '.')}"
