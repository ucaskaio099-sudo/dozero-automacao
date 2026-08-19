# -*- coding: utf-8 -*-
"""Gera as artes JPEG de cada post a partir do calendario.

    python scripts/gerar_arte.py                 # so o que falta
    python scripts/gerar_arte.py --refazer       # regera tudo
    python scripts/gerar_arte.py --post 2026-08-17-carrossel
    python scripts/gerar_arte.py --ate 2026-09-30

Cobre carrossel (6 slides), post estatico e stories. Reels precisa de video --
esses ficam de fora e sao listados no fim como pendencia manual.

As artes saem de midia/<post_id>/ e o caminho volta pra coluna `midia` do
calendario, que e' o que o publicador le depois.
"""

import argparse
import os
import sys
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import ImageDraw

import marca
from comum import (MIDIA, RAIZ, escrever_calendario, ler_calendario,
                   carregar_config)

SLIDES_CARROSSEL = 6
REEL_FPS = 30
REEL_DURATION_PER_SLIDE = 3  # segundos
REEL_SLIDE_DURATION = 4


# --- decomposicao da legenda ----------------------------------------------

def blocos_da_legenda(legenda):
    """Quebra a legenda em paragrafos, fora hashtags.

    A legenda tem forma fixa: gancho / "Tema de hoje: X." / 3 paragrafos de
    corpo / CTA / hashtags. A arte reaproveita esses mesmos paragrafos, entao
    slide e legenda nunca saem de sincronia.
    """
    blocos = [b.strip() for b in legenda.split("\n\n") if b.strip()]
    return [b for b in blocos if not b.lstrip().startswith("#")]


def partes(linha):
    blocos = blocos_da_legenda(linha["legenda"])
    corpo = [b for b in blocos if not b.startswith("Tema de hoje:")]
    gancho = corpo[0] if corpo else linha["gancho"]
    cta = corpo[-1] if len(corpo) > 1 else linha["cta"]
    meio = corpo[1:-1] if len(corpo) > 2 else []
    return gancho, meio, cta


# --- slides ---------------------------------------------------------------

def slide_capa(linha, indice, total):
    img = marca.tela(marca.FEED)
    d = ImageDraw.Draw(img)
    w, h = marca.FEED
    caixa = w - marca.MARGEM * 2

    y = marca.etiqueta(d, linha["pilar"].upper(), marca.MARGEM, marca.MARGEM)
    y += 54
    marca.regua(d, marca.MARGEM, y)
    y += 46

    f, linhas, altura = marca.ajustar(
        d, linha["tema"], marca.bold, caixa,
        h - y - marca.MARGEM - 150, tam_max=92, tam_min=46, entrelinha=1.16,
    )
    marca.escrever(d, linhas, marca.MARGEM, y, f, entrelinha=1.16,
                   destacar=True)

    marca.pontos(d, marca.FEED, indice, total)
    marca.rodape(d, marca.FEED, direita="arrasta →")
    return img


def slide_texto(texto, indice, total, destaque=False):
    img = marca.tela(marca.FEED)
    d = ImageDraw.Draw(img)
    w, h = marca.FEED
    caixa = w - marca.MARGEM * 2
    topo = marca.MARGEM + 40
    disponivel = h - topo - marca.MARGEM - 150

    criar = marca.semibold if destaque else marca.medium
    f, linhas, altura = marca.ajustar(
        d, texto, criar, caixa, disponivel,
        tam_max=68 if destaque else 58, tam_min=34, entrelinha=1.36,
    )
    y = topo + max(0, (disponivel - altura) // 2)

    marca.regua(d, marca.MARGEM, y - 52, largura=72, espessura=6)
    marca.escrever(d, linhas, marca.MARGEM, y, f, entrelinha=1.36,
                   destacar=True)

    marca.pontos(d, marca.FEED, indice, total)
    marca.rodape(d, marca.FEED, direita="arrasta →")
    return img


def slide_cta(texto, indice, total, config):
    img = marca.tela(marca.FEED)
    d = ImageDraw.Draw(img)
    w, h = marca.FEED
    caixa = w - marca.MARGEM * 2
    topo = marca.MARGEM + 60
    disponivel = h - topo - marca.MARGEM - 220

    f, linhas, altura = marca.ajustar(
        d, texto, marca.semibold, caixa, disponivel,
        tam_max=64, tam_min=34, entrelinha=1.34,
    )
    y = topo + max(0, (disponivel - altura) // 2)
    marca.regua(d, marca.MARGEM, y - 56, largura=104)
    y = marca.escrever(d, linhas, marca.MARGEM, y, f, entrelinha=1.34,
                       destacar=True)

    # botao-assinatura: nao e' clicavel no Instagram, e' so o lembrete visual
    # de onde esta o link (a bio).
    y += 46
    rotulo = config.get("link_bio", "link na bio")
    fb = marca.semibold(34)
    tw = d.textbbox((0, 0), rotulo, font=fb)[2]
    pad_x, pad_y = 40, 22
    d.rounded_rectangle(
        [marca.MARGEM, y, marca.MARGEM + tw + pad_x * 2, y + 34 + pad_y * 2],
        radius=(34 + pad_y * 2) // 2, fill=marca.LIMA,
    )
    d.text((marca.MARGEM + pad_x, y + pad_y - 4), rotulo, font=fb,
           fill=marca.VERDE_NOTURNO)

    marca.pontos(d, marca.FEED, indice, total)
    marca.rodape(d, marca.FEED)
    return img


def arte_carrossel(linha, config):
    gancho, meio, cta = partes(linha)
    # capa + gancho + corpo, completado ate 6 e cortado se passar
    conteudo = [gancho] + meio
    conteudo = conteudo[:SLIDES_CARROSSEL - 2]
    total = len(conteudo) + 2

    imagens = [slide_capa(linha, 0, total)]
    for i, texto in enumerate(conteudo, start=1):
        imagens.append(slide_texto(texto, i, total, destaque=(i == 1)))
    imagens.append(slide_cta(cta, total - 1, total, config))
    return imagens


def arte_estatica(linha, config):
    """Um card so: a frase forte no centro, CTA na legenda (nao na arte)."""
    img = marca.tela(marca.FEED)
    d = ImageDraw.Draw(img)
    w, h = marca.FEED
    caixa = w - marca.MARGEM * 2

    marca.etiqueta(d, linha["pilar"].upper(), marca.MARGEM, marca.MARGEM)

    topo = marca.MARGEM + 160
    disponivel = h - topo - marca.MARGEM - 130
    f, linhas, altura = marca.ajustar(
        d, linha["gancho"], marca.bold, caixa, disponivel,
        tam_max=86, tam_min=40, entrelinha=1.2,
    )
    y = topo + max(0, (disponivel - altura) // 2)
    marca.regua(d, marca.MARGEM, y - 58)
    marca.escrever(d, linhas, marca.MARGEM, y, f, entrelinha=1.2,
                   destacar=True)

    marca.rodape(d, marca.FEED, direita=config.get("link_bio", "link na bio"))
    return [img]


def arte_stories(linha, config):
    """9:16. Texto na faixa central segura -- topo e base ficam livres pra
    interface do Instagram (avatar em cima, 'enviar mensagem' embaixo)."""
    img = marca.tela(marca.STORY)
    d = ImageDraw.Draw(img)
    w, h = marca.STORY
    caixa = w - marca.MARGEM * 2

    topo = 380
    disponivel = 900
    f, linhas, altura = marca.ajustar(
        d, linha["gancho"], marca.bold, caixa, disponivel,
        tam_max=84, tam_min=40, entrelinha=1.22,
    )
    y = topo + max(0, (disponivel - altura) // 2)
    marca.regua(d, marca.MARGEM, y - 60)
    y = marca.escrever(d, linhas, marca.MARGEM, y, f, entrelinha=1.22,
                       destacar=True)

    y += 60
    fs = marca.medium(38)
    d.text((marca.MARGEM, y), config.get("link_bio", "link na bio"),
           font=fs, fill=marca.LIMA)

    marca.rodape(d, marca.STORY)
    return [img]


GERADORES = {
    "carrossel": arte_carrossel,
    "estatico": arte_estatica,
    "stories": arte_stories,
}


def _ffmpeg_gerar_mp4(ffmpeg_bin, entrada, mp4_saida, fps=30):
    """Gera MP4 a partir de imagem única via zoompan."""
    cmd = [
        ffmpeg_bin, "-y", "-loop", "1", "-i", entrada,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,"
               "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,format=yuv420p,"
               "zoompan=z='min(zoom+0.001,1.2)':d={}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920"
               .format(fps * 8),
        "-r", str(fps), "-t", "8",
        "-pix_fmt", "yuv420p", mp4_saida,
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)


def gerar_reels(linha, config):
    """Gera MP4 simples a partir dos slides do carrossel (se existirem).
    Usa imageio-ffmpeg que traz o binário embutido."""
    try:
        import imageio_ffmpeg
    except ImportError:
        return None

    pasta_carrossel = os.path.join(MIDIA, linha["post_id"])
    # procura slides 1..6
    slides = []
    for i in range(1, SLIDES_CARROSSEL + 1):
        nome = "{}-{}.jpg".format(linha["post_id"], i)
        caminho = os.path.join(pasta_carrossel, nome)
        if os.path.exists(caminho):
            slides.append(caminho)
    if not slides:
        return None

    pasta_reels = os.path.join(MIDIA, linha["post_id"])
    os.makedirs(pasta_reels, exist_ok=True)
    mp4_saida = os.path.join(pasta_reels, "{}-1.mp4".format(linha["post_id"]))

    ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
    # usa o primeiro slide com efeito Ken Burns
    try:
        _ffmpeg_gerar_mp4(ffmpeg_bin, slides[0], mp4_saida)
    except Exception:
        return None

    return ["{}/{}".format(linha["post_id"], os.path.basename(mp4_saida))]


def gerar_reels_texto(linha, config):
    """Gera MP4 para reel sem carrossel: cria um slide de texto e aplica Ken Burns."""
    try:
        import imageio_ffmpeg
    except ImportError:
        return None

    pasta_reels = os.path.join(MIDIA, linha["post_id"])
    os.makedirs(pasta_reels, exist_ok=True)
    mp4_saida = os.path.join(pasta_reels, "{}-1.mp4".format(linha["post_id"]))

    # cria slide temporário com gancho
    img = marca.tela(marca.STORY)
    d = ImageDraw.Draw(img)
    w, h = marca.STORY
    caixa = w - marca.MARGEM * 2
    topo = 380
    disponivel = 900
    f, linhas, altura = marca.ajustar(
        d, linha["gancho"], marca.bold, caixa, disponivel,
        tam_max=84, tam_min=36, entrelinha=1.22,
    )
    y = topo + max(0, (disponivel - altura) // 2)
    marca.regua(d, marca.MARGEM, y - 58)
    marca.escrever(d, linhas, marca.MARGEM, y, f, entrelinha=1.22, destacar=True)
    marca.rodape(d, marca.STORY, direita=config.get("link_bio", "link na bio"))

    tmp_slide = os.path.join(pasta_reels, "_reel_slide.jpg")
    marca.salvar_jpeg(img, tmp_slide)

    ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
    try:
        _ffmpeg_gerar_mp4(ffmpeg_bin, tmp_slide, mp4_saida)
    except Exception as e:
        print("Erro gerando reel de texto:", e)
        return None
    finally:
        if os.path.exists(tmp_slide):
            os.remove(tmp_slide)

    return ["{}/{}".format(linha["post_id"], os.path.basename(mp4_saida))]


# --- orquestracao ---------------------------------------------------------

def gerar(linha, config, refazer=False):
    """Gera as artes de um post. Devolve lista de caminhos relativos a midia/."""
    formato = linha["formato"]
    gerador = GERADORES.get(formato)
    if gerador is None:
        return None  # reels: video, tratado fora

    pasta = os.path.join(MIDIA, linha["post_id"])

    if not refazer and linha.get("midia"):
        arquivos = linha["midia"].split(";")
        if all(os.path.exists(os.path.join(MIDIA, a)) for a in arquivos if a):
            return arquivos

    imagens = gerador(linha, config)
    caminhos = []
    for i, img in enumerate(imagens, start=1):
        nome = "{}-{}.jpg".format(linha["post_id"], i)
        marca.salvar_jpeg(img, os.path.join(pasta, nome))
        caminhos.append("{}/{}".format(linha["post_id"], nome))
    return caminhos


def main():
    p = argparse.ArgumentParser(description="Gera as artes do calendario.")
    p.add_argument("--refazer", action="store_true",
                   help="regera mesmo se a arte ja existir")
    p.add_argument("--post", help="gera so um post_id")
    p.add_argument("--ate", help="gera so ate esta data (AAAA-MM-DD)")
    args = p.parse_args()

    config = carregar_config()
    linhas = ler_calendario()
    alvo = linhas
    if args.post:
        alvo = [l for l in linhas if l["post_id"] == args.post]
        if not alvo:
            sys.exit("post_id nao encontrado: " + args.post)
    if args.ate:
        alvo = [l for l in alvo if l["data"] <= args.ate]

    feitos = 0
    pulados = 0
    reels_sem_video = []

    for linha in alvo:
        if linha["formato"] == "reels":
            if linha.get("midia"):
                # já tem vídeo, verifica se existe
                arquivos = linha["midia"].split(";")
                if all(os.path.exists(os.path.join(MIDIA, a)) for a in arquivos if a):
                    pulados += 1
                    continue
            # tenta gerar a partir do carrossel
            caminhos = gerar_reels(linha, config)
            if not caminhos:
                # fallback: gera a partir do próprio texto do reel
                caminhos = gerar_reels_texto(linha, config)
            if caminhos:
                linha["midia"] = ";".join(caminhos)
                feitos += 1
            else:
                reels_sem_video.append(linha)
            continue
        antes = linha.get("midia", "")
        caminhos = gerar(linha, config, refazer=args.refazer)
        if caminhos is None:
            continue
        novo = ";".join(caminhos)
        if novo != antes or args.refazer:
            linha["midia"] = novo
            feitos += 1
        else:
            pulados += 1

    escrever_calendario(linhas)

    print("Artes geradas: {}".format(feitos))
    if pulados:
        print("Ja existiam (use --refazer pra regerar): {}".format(pulados))
    print("Saida: {}".format(MIDIA))

    if reels_sem_video:
        print("\n{} reels sem video/imagens base. O gerador tenta criar a partir do carrossel."
              .format(len(reels_sem_video)))
        print("Se não tiver carrossel correspondente, coloque o .mp4 em midia/<post_id>/")
        print("e preencha a coluna `midia` do calendario.")
        print("Proximos 5:")
        for l in reels_sem_video[:5]:
            print("   {}  {}".format(l["post_id"], l["tema"][:58]))


if __name__ == "__main__":
    main()
