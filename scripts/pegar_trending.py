"""Salva a lista oficial de https://github.com/trending (hoje) em JSON."""
import json
import os
import re
from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

URL = "https://github.com/trending?since=daily"
BRT = timezone(timedelta(hours=-3))


def numero(texto):
    digitos = re.sub(r"[^\d]", "", texto or "")
    return int(digitos) if digitos else None


def main():
    resp = requests.get(URL, headers={"User-Agent": "trending-diario"}, timeout=60)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    repos = []
    for pos, art in enumerate(soup.select("article.Box-row"), start=1):
        link = art.select_one("h2 a")
        if not link:
            continue
        nome = link["href"].strip("/")
        desc = art.select_one("p")
        lang = art.select_one('[itemprop="programmingLanguage"]')
        stars = art.select_one(f'a[href="/{nome}/stargazers"]')
        forks = art.select_one(f'a[href="/{nome}/forks"]')
        hoje = art.find(string=re.compile(r"stars? today"))
        repos.append({
            "posicao": pos,
            "repo": nome,
            "link": f"https://github.com/{nome}",
            "descricao": desc.get_text(" ", strip=True) if desc else "",
            "linguagem": lang.get_text(strip=True) if lang else None,
            "estrelas_total": numero(stars.get_text()) if stars else None,
            "forks": numero(forks.get_text()) if forks else None,
            "estrelas_hoje": numero(hoje) if hoje else None,
        })

    if not repos:
        raise SystemExit("A página veio sem repositórios — layout mudou ou acesso falhou.")

    agora = datetime.now(BRT)
    dados = {
        "fonte": URL,
        "coletado_em_brt": agora.isoformat(timespec="minutes"),
        "data": agora.date().isoformat(),
        "total": len(repos),
        "repos": repos,
    }

    os.makedirs("dados", exist_ok=True)
    for caminho in ("dados/latest.json", f"dados/{dados['data']}.json"):
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"{len(repos)} repositórios salvos em {dados['data']}")


if __name__ == "__main__":
    main()
