# -*- coding: utf-8 -*-
"""Identidade visual "do zero ao REAL" e primitivas de desenho.

Paleta e tipografia vem do brand sheet do projeto (03-instagram/marca/).
Tudo aqui e' Pillow puro -- sem servico externo, sem credito de ferramenta,
sem chave de API. Roda igual no PC do Kaio e no runner do GitHub Actions.
"""

import os

from PIL import Image, ImageDraw, ImageFont

from comum import FONTES

# --- paleta ---------------------------------------------------------------
VERDE_NOTURNO = (12, 15, 11)      # #0C0F0B  fundo
LIMA = (198, 255, 61)             # #C6FF3D  destaque
OFF_WHITE = (244, 244, 239)       # #F4F4EF  texto
# derivadas, para hierarquia sem sair da paleta
CINZA = (150, 156, 145)           # texto secundario
LIMA_FRACA = (198, 255, 61, 38)   # veus e halos

# --- formatos (px) --------------------------------------------------------
# 1080x1350 e' 4:5, a proporcao vertical maxima que o feed do Instagram aceita
# -- ocupa mais tela que 1:1 sem ser cortada.
FEED = (1080, 1350)
STORY = (1080, 1920)

MARGEM = 96


def fonte(nome, tamanho):
    caminho = os.path.join(FONTES, nome)
    if not os.path.exists(caminho):
        raise FileNotFoundError(
            "Fonte nao encontrada: {}\nAs fontes ficam em 07-automacao/fontes/"
            .format(caminho)
        )
    return ImageFont.truetype(caminho, tamanho)


def bold(t):     return fonte("Poppins-Bold.ttf", t)
def semibold(t): return fonte("Poppins-SemiBold.ttf", t)
def medium(t):   return fonte("Poppins-Medium.ttf", t)
def regular(t):  return fonte("Poppins-Regular.ttf", t)


# --- fundo ----------------------------------------------------------------

def tela(tamanho=FEED):
    """Fundo da marca com um halo lima suave no canto superior direito.

    O halo e' desenhado grande e com alpha baixo: da profundidade sem virar
    'gradiente de template'. Sem ele o fundo chapado fica sem vida no feed.
    """
    img = Image.new("RGB", tamanho, VERDE_NOTURNO)
    w, h = tamanho

    halo = Image.new("RGBA", tamanho, (0, 0, 0, 0))
    d = ImageDraw.Draw(halo)
    cx, cy = int(w * 0.86), int(h * 0.10)
    raio = int(w * 0.72)
    passos = 46
    for i in range(passos, 0, -1):
        r = int(raio * i / passos)
        alpha = int(16 * (1 - i / passos) ** 2)
        if alpha <= 0:
            continue
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=LIMA + (alpha,))
    img = Image.alpha_composite(img.convert("RGBA"), halo).convert("RGB")
    return img


def regua(draw, x, y, largura=104, espessura=8, cor=LIMA):
    """Barra lima curta -- ancora visual acima de um titulo."""
    draw.rounded_rectangle(
        [x, y, x + largura, y + espessura], radius=espessura // 2, fill=cor
    )


# --- texto ----------------------------------------------------------------

def _largura(draw, texto, f):
    return draw.textbbox((0, 0), texto, font=f)[2]


def quebrar(draw, texto, f, largura_max):
    """Quebra em linhas que cabem em largura_max. Palavra sozinha maior que a
    caixa fica na propria linha (melhor estourar 1 palavra que travar)."""
    linhas = []
    for paragrafo in texto.split("\n"):
        if not paragrafo.strip():
            linhas.append("")
            continue
        atual = ""
        for palavra in paragrafo.split():
            teste = (atual + " " + palavra).strip()
            if _largura(draw, teste, f) <= largura_max or not atual:
                atual = teste
            else:
                linhas.append(atual)
                atual = palavra
        if atual:
            linhas.append(atual)
    return linhas


def ajustar(draw, texto, criar_fonte, largura_max, altura_max,
            tam_max, tam_min, entrelinha=1.28):
    """Acha o maior corpo de fonte em que o texto cabe na caixa.

    Vai de tam_max para baixo em passos de 2px. Devolve (fonte, linhas, altura).
    No pior caso devolve tam_min mesmo estourando -- e' melhor entregar arte
    apertada que quebrar a publicacao do dia.
    """
    tamanho = tam_max
    while tamanho >= tam_min:
        f = criar_fonte(tamanho)
        linhas = quebrar(draw, texto, f, largura_max)
        altura = len(linhas) * int(tamanho * entrelinha)
        if altura <= altura_max:
            return f, linhas, altura
        tamanho -= 2
    f = criar_fonte(tam_min)
    linhas = quebrar(draw, texto, f, largura_max)
    return f, linhas, len(linhas) * int(tam_min * entrelinha)


# Palavras que sempre aparecem em lima: sao a assinatura da marca.
DESTAQUES = {"real", "real.", "real,", "real:", "real?", "real!", "zero"}


def escrever(draw, linhas, x, y, f, entrelinha=1.28, cor=OFF_WHITE,
             destacar=False):
    """Desenha linhas ja quebradas. Com destacar=True, pinta as palavras da
    marca em lima, token a token na mesma linha de base."""
    passo = int(f.size * entrelinha)
    for i, linha in enumerate(linhas):
        ly = y + i * passo
        if not destacar:
            draw.text((x, ly), linha, font=f, fill=cor)
            continue
        lx = x
        for palavra in linha.split(" "):
            limpa = palavra.lower().strip('"“”')
            tom = LIMA if limpa in DESTAQUES else cor
            draw.text((lx, ly), palavra, font=f, fill=tom)
            lx += _largura(draw, palavra + " ", f)
    return y + len(linhas) * passo


# --- elementos recorrentes ------------------------------------------------

def rodape(draw, tamanho, handle="@dozero.aoreal", direita=None):
    w, h = tamanho
    f = medium(30)
    y = h - MARGEM + 6
    draw.text((MARGEM, y), handle, font=f, fill=LIMA)
    if direita:
        fd = regular(28)
        draw.text((w - MARGEM - _largura(draw, direita, fd), y + 2),
                  direita, font=fd, fill=CINZA)


def pontos(draw, tamanho, indice, total):
    """Indicador de progresso do carrossel: bolinha cheia = slide atual."""
    if total <= 1:
        return
    w, h = tamanho
    r, gap = 7, 22
    largura = total * (r * 2) + (total - 1) * (gap - r * 2)
    x = (w - largura) // 2
    y = h - MARGEM - 44
    for i in range(total):
        cor = LIMA if i == indice else (58, 64, 55)
        draw.ellipse([x, y, x + r * 2, y + r * 2], fill=cor)
        x += gap


def etiqueta(draw, texto, x, y):
    """Pilula de contexto (pilar do post) no topo do slide."""
    f = semibold(26)
    pad_x, pad_y = 22, 12
    tw = _largura(draw, texto, f)
    th = draw.textbbox((0, 0), texto, font=f)[3]
    draw.rounded_rectangle(
        [x, y, x + tw + pad_x * 2, y + th + pad_y * 2 + 6],
        radius=(th + pad_y * 2 + 6) // 2,
        outline=(70, 78, 66), width=2,
    )
    draw.text((x + pad_x, y + pad_y), texto, font=f, fill=CINZA)
    return y + th + pad_y * 2 + 6


def salvar_jpeg(img, caminho):
    """A API do Instagram so aceita JPEG para imagem -- PNG e' recusado."""
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    img.convert("RGB").save(caminho, "JPEG", quality=92, optimize=True,
                            progressive=True)
    return caminho
