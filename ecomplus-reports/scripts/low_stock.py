"""
Lista produtos com estoque abaixo de um limiar.

O endpoint /products.json retorna apenas _id, sku, slug — sem filtros nem fields.
A estratégia é: listar todos os IDs, buscar detalhes individuais, filtrar no cliente.

Uso:
    python low_stock.py
    python low_stock.py --threshold 10
    python low_stock.py --threshold 0   # apenas zerados
    python low_stock.py --format csv
"""
import argparse
import csv
import json
import sys
import time

from ecomplus_client import EcomplusClient, EcomplusError, format_brl

RATE_SLEEP = 0.2


def fetch_low_stock(client: EcomplusClient, threshold: int) -> list[dict]:
    stubs = list(client.list_all("products"))
    results = []
    for stub in stubs:
        product_id = stub["_id"]
        try:
            p = client.get(f"products/{product_id}")
        except EcomplusError:
            continue
        qty = p.get("quantity") or 0
        if qty <= threshold:
            results.append(p)
        time.sleep(RATE_SLEEP)
    results.sort(key=lambda x: x.get("quantity") or 0)
    return results


def render_markdown(rows: list[dict], threshold: int) -> str:
    lines = [
        f"## Estoque crítico — produtos com quantidade ≤ {threshold}\n",
        f"_{len(rows)} produto(s) encontrado(s)._\n",
        "| SKU | Produto | Estoque | Mínimo | Preço |",
        "|---|---|---:|---:|---:|",
    ]
    for p in rows:
        sku = p.get("sku", "—")
        name = str(p.get("name", ""))[:50]
        qty = p.get("quantity", 0)
        min_qty = p.get("min_quantity", "—")
        price = p.get("price", 0.0) or 0.0
        lines.append(f"| {sku} | {name} | {qty} | {min_qty} | {format_brl(price)} |")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=int, default=5,
                        help="Quantidade máxima para considerar crítico (padrão: 5)")
    parser.add_argument("--format", choices=["md", "json", "csv"], default="md")
    args = parser.parse_args()

    try:
        client = EcomplusClient.from_env()
        rows = fetch_low_stock(client, args.threshold)
    except EcomplusError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    elif args.format == "csv":
        fieldnames = ["sku", "name", "quantity", "min_quantity", "price"]
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for p in rows:
            p["name"] = (p.get("name") or {}).get("pt_br", "") or str(p.get("name", ""))
            writer.writerow(p)
    else:
        print(render_markdown(rows, args.threshold))


if __name__ == "__main__":
    main()
