# -*- coding: utf-8 -*-
"""Caminhos, configuracao e leitura/escrita do calendario.

Tudo que mais de um script precisa mora aqui, pra nao ter duas versoes da
mesma verdade sobre onde ficam os arquivos ou como o CSV e' lido.
"""

import csv
import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTEUDO = os.path.join(RAIZ, "conteudo")
MIDIA = os.path.join(RAIZ, "midia")
FONTES = os.path.join(RAIZ, "fontes")
PAINEL = os.path.join(RAIZ, "painel")
CALENDARIO = os.path.join(CONTEUDO, "calendario.csv")
# Registro de idempotencia sem segredos. Persiste containers e IDs publicados
# entre execucoes do GitHub Actions para evitar post duplicado apos timeout.
ESTADO_PUBLICACAO = os.path.join(CONTEUDO, "estado_publicacao.json")

COLUNAS = [
    "post_id",       # identificador estavel: 2026-08-17-carrossel
    "data",          # AAAA-MM-DD
    "hora",          # HH:MM no fuso de Sao Paulo
    "formato",       # carrossel | reels | stories | estatico
    "pilar",
    "fase",
    "semana",
    "tema",
    "gancho",
    "legenda",
    "cta",
    "hashtags",
    "direcao_visual",
    "midia",         # arquivos separados por ";" relativos a midia/
    "status",        # pendente | publicado | erro | pulado
    "ig_media_id",   # id retornado pelo Instagram
    "publicado_em",  # timestamp ISO de quando publicou
    "erro",          # ultima mensagem de erro, se houver
]

STATUS_PENDENTE = "pendente"
STATUS_PUBLICADO = "publicado"
STATUS_ERRO = "erro"
STATUS_PULADO = "pulado"


def carregar_config():
    with open(os.path.join(RAIZ, "config.json"), encoding="utf-8") as f:
        return json.load(f)


def fuso():
    return ZoneInfo(carregar_config().get("fuso", "America/Sao_Paulo"))


def agora():
    return datetime.now(fuso())


def momento_do_post(linha):
    """datetime com fuso do horario agendado de uma linha do calendario."""
    return datetime.strptime(
        linha["data"] + " " + linha["hora"], "%Y-%m-%d %H:%M"
    ).replace(tzinfo=fuso())


def ler_calendario(caminho=CALENDARIO):
    with open(caminho, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def escrever_calendario(linhas, caminho=CALENDARIO):
    """Escrita atomica: grava num .tmp e troca, pra nunca deixar o CSV pela
    metade se o processo morrer no meio (o Actions mata job por timeout)."""
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS, lineterminator="\n")
        w.writeheader()
        for linha in linhas:
            w.writerow({c: linha.get(c, "") for c in COLUNAS})
    os.replace(tmp, caminho)


def ler_json(caminho, padrao=None):
    """Le JSON local; arquivo ausente e' o estado inicial esperado."""
    if not os.path.exists(caminho):
        return {} if padrao is None else padrao
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def escrever_json_atomico(caminho, dados):
    """Persiste estado de trabalho sem deixar JSON truncado apos um timeout."""
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, caminho)


def env(nome, padrao=None, obrigatorio=False):
    valor = os.environ.get(nome, padrao)
    if obrigatorio and not valor:
        sys.exit(
            "ERRO: falta a variavel de ambiente {}.\n"
            "Em local: copie .env.example para .env e preencha.\n"
            "No GitHub: Settings > Secrets and variables > Actions.".format(nome)
        )
    return valor


def dry_run():
    """Sem DRY_RUN=false explicito, nada e' publicado de verdade.

    Padrao seguro de proposito: um erro de configuracao vira um log, nao um
    post indevido no perfil."""
    return env("DRY_RUN", "true").strip().lower() != "false"


def carregar_dotenv():
    """Le o .env local se existir. No GitHub Actions as variaveis ja vem do
    ambiente, entao a ausencia do arquivo nao e' problema."""
    caminho = os.path.join(RAIZ, ".env")
    if not os.path.exists(caminho):
        return
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, _, valor = linha.partition("=")
            os.environ.setdefault(chave.strip(), valor.strip())
