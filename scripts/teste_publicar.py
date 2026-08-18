# -*- coding: utf-8 -*-
"""Testes do publicador com um Meta falso -- nao toca na rede nem no Instagram.

    python scripts/teste_publicar.py

Cobre o que so se descobre tarde demais em producao: ordem das chamadas do
carrossel, espera do processamento, e o que acontece quando a conexao cai no
meio de uma publicacao.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import publicar
from publicar import ErroMeta, EstadoDoPost

BASE = "https://exemplo.github.io/repo/midia"


class MetaFalso:
    """Imita a Graph API. `falhar_em` derruba a n-esima chamada POST."""

    def __init__(self, falhar_em=None, publicados=None, atrasos=0):
        self.chamadas = []
        self.posts = 0
        self.falhar_em = falhar_em
        self.contador = 0
        self.publicados = publicados or []
        self.atrasos = atrasos
        self.consultas = {}

    def post(self, caminho, parametros=None):
        self.posts += 1
        self.chamadas.append(("POST", caminho, dict(parametros or {})))
        if self.falhar_em == self.posts:
            raise ErroMeta("conexao caiu")
        if caminho.endswith("/media"):
            self.contador += 1
            return {"id": "cont{}".format(self.contador)}
        return {"id": "media-publicada"}

    def get(self, caminho, parametros=None, tentativas=3):
        self.chamadas.append(("GET", caminho, dict(parametros or {})))
        if caminho.endswith("/media"):
            return {"data": self.publicados}
        vistas = self.consultas.get(caminho, 0) + 1
        self.consultas[caminho] = vistas
        if vistas <= self.atrasos:
            return {"status_code": "IN_PROGRESS"}
        return {"status_code": "FINISHED"}


def linha_de(post_id):
    for linha in publicar.ler_calendario():
        if linha["post_id"] == post_id:
            return dict(linha)
    raise AssertionError("post ausente no calendario: " + post_id)


def estado_limpo():
    caminho = os.path.join(tempfile.mkdtemp(), "estado.json")
    return EstadoDoPost(caminho)


def checar(condicao, mensagem):
    if not condicao:
        raise AssertionError(mensagem)


def teste_carrossel_cria_filhos_antes_do_pai():
    api = MetaFalso(atrasos=1)
    linha = linha_de("2026-08-17-carrossel")
    media_id = publicar.publicar_no_instagram(api, linha, "IG", BASE, 0, 30, estado_limpo())

    criacoes = [c for c in api.chamadas if c[0] == "POST" and c[1].endswith("/media")]
    checar(media_id == "media-publicada", "devia devolver o id publicado")
    checar(len(criacoes) == 7, "6 filhos + 1 pai; obteve {}".format(len(criacoes)))
    checar(all(c[2].get("is_carousel_item") == "true" for c in criacoes[:6]),
           "os 6 primeiros containers sao itens do carrossel")
    checar(criacoes[6][2]["media_type"] == "CAROUSEL", "o ultimo container e' o pai")
    checar(criacoes[6][2]["children"].count(",") == 5, "o pai referencia 6 filhos")
    checar("caption" not in criacoes[0][2], "item de carrossel nao leva legenda")
    checar(api.chamadas[-1][1].endswith("/media_publish"), "publish e' a ultima chamada")


def teste_espera_processamento_antes_de_publicar():
    api = MetaFalso(atrasos=2)
    linha = linha_de("2026-08-20-estatico")
    publicar.publicar_no_instagram(api, linha, "IG", BASE, 0, 30, estado_limpo())
    consultas = [c for c in api.chamadas if c[0] == "GET"]
    checar(len(consultas) == 3, "devia consultar ate FINISHED; obteve {}".format(len(consultas)))
    checar(api.chamadas[-1][1].endswith("/media_publish"), "publish vem depois do FINISHED")


def teste_container_e_reaproveitado_apos_queda():
    """Cair antes do publish nao pode gerar um segundo container do mesmo post."""
    estado = estado_limpo()
    linha = linha_de("2026-08-20-estatico")

    primeira = MetaFalso(falhar_em=2)   # cria container, cai no media_publish
    try:
        publicar.publicar_no_instagram(primeira, linha, "IG", BASE, 0, 30, estado)
        raise AssertionError("a primeira tentativa devia falhar")
    except ErroMeta:
        pass

    # A retomada nao pode republicar as cegas: consulta o feed primeiro.
    segunda = MetaFalso(publicados=[{"id": "ja-existia", "caption": publicar.legenda(linha)}])
    media_id = publicar.publicar_no_instagram(segunda, linha, "IG", BASE, 0, 30, estado)
    checar(media_id == "ja-existia", "devia reconciliar com o post que ja estava no perfil")
    checar(segunda.posts == 0, "reconciliacao nao pode fazer nenhuma escrita")


def teste_queda_ambigua_sem_post_no_perfil_para_tudo():
    estado = estado_limpo()
    linha = linha_de("2026-08-20-estatico")
    try:
        publicar.publicar_no_instagram(MetaFalso(falhar_em=2), linha, "IG", BASE, 0, 30, estado)
    except ErroMeta:
        pass
    try:
        publicar.publicar_no_instagram(MetaFalso(publicados=[]), linha, "IG", BASE, 0, 30, estado)
        raise AssertionError("sem prova de publicacao, devia parar e pedir revisao")
    except ErroMeta as exc:
        checar("duplicata" in str(exc), "o erro devia explicar por que nao reenviou")


def teste_post_ja_publicado_nao_repete():
    estado = estado_limpo()
    estado.gravar("2026-08-20-estatico", media_id="17999", etapa="publicado")
    api = MetaFalso()
    media_id = publicar.publicar_no_instagram(api, linha_de("2026-08-20-estatico"),
                                              "IG", BASE, 0, 30, estado)
    checar(media_id == "17999", "devia devolver o id ja gravado")
    checar(not api.chamadas, "nenhuma chamada para post ja publicado")


def teste_container_com_erro_interrompe():
    class MetaComErro(MetaFalso):
        def get(self, caminho, parametros=None, tentativas=3):
            return {"status_code": "ERROR", "status": "formato invalido"}

    api = MetaComErro()
    try:
        publicar.publicar_no_instagram(api, linha_de("2026-08-20-estatico"),
                                       "IG", BASE, 0, 30, estado_limpo())
        raise AssertionError("container em ERROR nao pode seguir para publish")
    except ErroMeta as exc:
        checar("ERROR" in str(exc), "o erro devia citar o estado do container")
    checar(not any(c[1].endswith("/media_publish") for c in api.chamadas),
           "nunca publicar um container que falhou")


def teste_stories_nao_manda_legenda():
    api = MetaFalso()
    publicar.publicar_no_instagram(api, linha_de("2026-08-19-stories"),
                                   "IG", BASE, 0, 30, estado_limpo())
    criacao = [c for c in api.chamadas if c[0] == "POST" and c[1].endswith("/media")][0]
    checar(criacao[2]["media_type"] == "STORIES", "stories precisa de media_type STORIES")
    checar("caption" not in criacao[2], "a API ignora legenda em stories")
    checar(criacao[2]["image_url"].startswith(BASE), "a URL do story sai da base publica")


def teste_reel_sem_video_falha_antes_de_qualquer_chamada():
    api = MetaFalso()
    try:
        publicar.publicar_no_instagram(api, linha_de("2026-08-18-reels"),
                                       "IG", BASE, 0, 30, estado_limpo())
        raise AssertionError("reel sem mp4 nao pode ser publicado")
    except ValueError:
        pass
    checar(not api.chamadas, "validacao acontece antes de falar com o Meta")


def teste_caminho_de_midia_nao_escapa_da_pasta():
    for perigoso in ("../segredo.jpg", "/etc/passwd", "a/../../fora.jpg"):
        try:
            publicar.caminhos_de_midia({"midia": perigoso})
            raise AssertionError("devia recusar caminho: " + perigoso)
        except ValueError:
            pass


def teste_url_publica_exige_https_e_codifica():
    try:
        publicar.url_publica("a/b.jpg", "http://inseguro.com")
        raise AssertionError("http simples devia ser recusado")
    except ValueError:
        pass
    url = publicar.url_publica("pasta com espaco/arte.jpg", BASE + "/")
    checar(url == BASE + "/pasta%20com%20espaco/arte.jpg", "espaco devia virar %20; veio " + url)


def teste_legenda_nao_duplica_hashtags():
    linha = linha_de("2026-08-17-carrossel")
    texto = publicar.legenda(linha)
    checar(texto.count("#dozeroaoreal") == 1, "hashtag nao pode aparecer duas vezes")
    checar(len(texto) <= 2200, "legenda dentro do limite do Instagram")


def teste_legenda_longa_e_recusada():
    try:
        publicar.legenda({"legenda": "x" * 2300, "hashtags": ""})
        raise AssertionError("legenda acima de 2200 devia falhar")
    except ValueError:
        pass


def main():
    testes = [v for k, v in sorted(globals().items()) if k.startswith("teste_")]
    falhas = 0
    for teste in testes:
        try:
            teste()
            print("ok   {}".format(teste.__name__))
        except AssertionError as exc:
            falhas += 1
            print("FALHA {}: {}".format(teste.__name__, exc))
    print("\n{}/{} testes passaram.".format(len(testes) - falhas, len(testes)))
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
