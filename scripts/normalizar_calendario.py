# -*- coding: utf-8 -*-
"""Converte o CSV original de 06-agendamento-instagram no calendario de trabalho.

Origem: calendario-posts-2026-08-17-a-2027-02-05.csv (173 posts, sem acento,
sem id, sem status).
Destino: conteudo/calendario.csv (acentuado, com post_id estavel e colunas de
controle de publicacao).

Roda uma vez. Se precisar rodar de novo, os status ja gravados sao preservados
-- nao republica nem perde historico.

    python scripts/normalizar_calendario.py
"""

import csv
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import acentuacao
from comum import (CALENDARIO, CONTEUDO, COLUNAS, RAIZ, STATUS_PENDENTE,
                   carregar_config, escrever_calendario, ler_calendario)

ORIGEM = os.path.join(
    os.path.dirname(RAIZ), "06-agendamento-instagram",
    "calendario-posts-2026-08-17-a-2027-02-05.csv",
)

# O CSV de origem escreve o formato por extenso; internamente uso o slug.
FORMATOS = {
    "Carrossel": "carrossel",
    "Reels": "reels",
    "Stories": "stories",
    "Post estatico": "estatico",
}

# A observacao original ("Agendar no Meta Business Suite") descreve o fluxo
# manual, que e' justamente o que esta automacao substitui.
OBSERVACAO_ANTIGA = "Agendar no Meta Business Suite. Revisar arte antes de publicar."


def campos_de_texto(linha, preco):
    """Aplica acentuacao em todos os campos de texto livre."""
    saida = {}
    for campo in ("fase", "pilar", "tema", "gancho", "legenda", "cta",
                  "direcao_visual"):
        corrigido = acentuacao.corrigir_bloco(linha.get(campo, "") or "")
        saida[campo] = corrigido.replace("{PRECO}", preco)
    return saida


def main():
    if not os.path.exists(ORIGEM):
        sys.exit("Nao achei o CSV de origem em:\n  " + ORIGEM)

    config = carregar_config()
    preco = config.get("preco", "R$49,99")

    with io.open(ORIGEM, encoding="utf-8-sig", newline="") as f:
        origem = list(csv.DictReader(f))

    # Preserva status de execucoes anteriores, casando por post_id.
    anterior = {}
    if os.path.exists(CALENDARIO):
        anterior = {l["post_id"]: l for l in ler_calendario()}
        print("Calendario existente encontrado: {} linhas, status preservado."
              .format(len(anterior)))

    linhas = []
    formatos_desconhecidos = set()

    for bruto in origem:
        formato_bruto = (bruto.get("formato") or "").strip()
        formato = FORMATOS.get(formato_bruto)
        if not formato:
            formatos_desconhecidos.add(formato_bruto)
            continue

        data = (bruto.get("data") or "").strip()
        post_id = "{}-{}".format(data, formato)
        texto = campos_de_texto(bruto, preco)

        observacoes = (bruto.get("observacoes") or "").strip()
        if observacoes == OBSERVACAO_ANTIGA:
            observacoes = ""

        antes = anterior.get(post_id, {})

        linhas.append({
            "post_id": post_id,
            "data": data,
            "hora": (bruto.get("horario_sugerido") or "").strip(),
            "formato": formato,
            "pilar": texto["pilar"],
            "fase": texto["fase"],
            "semana": (bruto.get("semana") or "").strip(),
            "tema": texto["tema"],
            "gancho": texto["gancho"],
            "legenda": texto["legenda"],
            "cta": texto["cta"],
            "hashtags": (bruto.get("hashtags") or "").strip(),
            "direcao_visual": texto["direcao_visual"],
            # midia fica vazia: gerar_arte.py preenche para imagens e o Kaio
            # preenche na mao para reels (video nao da pra gerar do nada).
            "midia": antes.get("midia", ""),
            "status": antes.get("status", STATUS_PENDENTE),
            "ig_media_id": antes.get("ig_media_id", ""),
            "publicado_em": antes.get("publicado_em", ""),
            "erro": antes.get("erro", ""),
        })

    if formatos_desconhecidos:
        sys.exit("Formato nao mapeado no CSV de origem: {}"
                 .format(sorted(formatos_desconhecidos)))

    linhas.sort(key=lambda l: (l["data"], l["hora"]))

    os.makedirs(CONTEUDO, exist_ok=True)
    escrever_calendario(linhas)

    por_formato = {}
    for l in linhas:
        por_formato[l["formato"]] = por_formato.get(l["formato"], 0) + 1

    print("OK: {} posts em {}".format(len(linhas), CALENDARIO))
    print("   por formato: {}".format(por_formato))
    print("   periodo: {} -> {}".format(linhas[0]["data"], linhas[-1]["data"]))
    print("   preco aplicado nos textos: {}".format(preco))


if __name__ == "__main__":
    main()
