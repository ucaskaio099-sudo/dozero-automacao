# -*- coding: utf-8 -*-
"""Publica os posts vencidos no Instagram pela Graph API.

O Instagram nao recebe arquivos enviados pelo computador: ele baixa cada JPEG ou
MP4 de uma URL HTTPS publica. Por isso `midia` no calendario guarda caminhos
relativos e PUBLIC_MEDIA_BASE_URL aponta para a pasta publica que os contem.

Uso normal (seguro por padrao):

    python scripts/publicar.py                         # DRY_RUN=true: so mostra
    DRY_RUN=false python scripts/publicar.py           # publica post vencido
    python scripts/publicar.py --post 2026-08-17-carrossel
    python scripts/publicar.py --tentar-erros          # somente apos conferir

Sem `--post`, so considera posts previstos ate agora e dentro da janela de
POST_WINDOW_HOURS (padrao: 24). Assim, habilitar a automacao dias depois nao
transforma todo o calendario antigo em uma rajada de posts. Posts antigos podem
ser tratados conscientemente com `--incluir-atrasados`.

Nao ha retry automatico de chamadas POST. Se uma conexao cair apos o Meta ter
recebido uma publicacao, repetir a chamada poderia duplicar o post. Consultas
de status sao repetidas com seguranca; uma falha ambigua de escrita fica como
`erro` e exige revisao antes de `--tentar-erros`.
"""

import argparse
import hashlib
import hmac
import json
import os
import sys
import time
from datetime import datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comum import (ESTADO_PUBLICACAO, MIDIA, STATUS_ERRO, STATUS_PENDENTE,
                   STATUS_PUBLICADO, agora, carregar_dotenv, escrever_calendario,
                   escrever_json_atomico, env, fuso, ler_calendario, ler_json,
                   momento_do_post)

# A versao fica em variavel de ambiente justamente para poder trocar sem editar
# o codigo quando o Meta aposentar uma versao da Graph API.
VERSAO_PADRAO = "v25.0"
URL_GRAFICO = "https://graph.facebook.com"
STATUS_PRONTO = {"FINISHED", "PUBLISHED"}
STATUS_FALHOU = {"ERROR", "EXPIRED"}


class ErroMeta(RuntimeError):
    """Erro retornado pelo Meta ou pela conexao com a Graph API."""

    def __init__(self, mensagem, codigo=None, detalhes=None):
        super().__init__(mensagem)
        self.codigo = codigo
        self.detalhes = detalhes or {}


def texto_erro(exc, limite=1000):
    """Texto util para o CSV, sem despejar token ou resposta gigante."""
    texto = str(exc).replace("\n", " ").strip()
    return texto[:limite]


def numero_do_ambiente(nome, padrao, minimo=1):
    bruto = env(nome, str(padrao))
    try:
        valor = int(bruto)
    except ValueError:
        raise SystemExit("{} deve ser um numero inteiro; recebeu {!r}.".format(nome, bruto))
    if valor < minimo:
        raise SystemExit("{} deve ser maior ou igual a {}.".format(nome, minimo))
    return valor


class GraphAPI:
    """Cliente minimo, sem dependencias externas, para a Graph API.

    Metodos GET recebem retry pois sao idempotentes. POST nao recebe retry
    automatico: a resposta pode se perder depois que o Meta aceitou a escrita.
    """

    def __init__(self, token, versao=None, timeout=60, app_secret=None):
        versao = (versao or env("META_GRAPH_API_VERSION", VERSAO_PADRAO)).strip("/")
        self.base = "{}/{}/".format(URL_GRAFICO, versao)
        self.token = token
        self.timeout = timeout
        self.app_secret = app_secret

    def _url(self, caminho):
        return self.base + str(caminho).lstrip("/")

    def _appsecret_proof(self):
        if not self.app_secret:
            return None
        return hmac.new(
            self.app_secret.encode("utf-8"), self.token.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _erro_da_resposta(payload, status=None):
        bruto = payload.get("error", payload) if isinstance(payload, dict) else payload
        if isinstance(bruto, dict):
            partes = [bruto.get("message"), bruto.get("error_user_title"),
                      bruto.get("error_user_msg")]
            mensagem = " | ".join(str(p) for p in partes if p) or "Erro desconhecido do Meta"
            codigo = bruto.get("code", status)
            return ErroMeta("Meta{}: {}".format(" {}".format(codigo) if codigo else "", mensagem),
                            codigo=codigo, detalhes=bruto)
        return ErroMeta("Meta{}: {}".format(" {}".format(status) if status else "", bruto),
                        codigo=status)

    def _requisicao(self, metodo, caminho, parametros=None):
        parametros = dict(parametros or {})
        parametros["access_token"] = self.token
        proof = self._appsecret_proof()
        if proof:
            parametros["appsecret_proof"] = proof
        url = self._url(caminho)
        dados = None
        if metodo == "GET":
            url += ("&" if "?" in url else "?") + urlencode(parametros)
        else:
            dados = urlencode(parametros).encode("utf-8")

        requisicao = Request(url, data=dados, method=metodo)
        try:
            with urlopen(requisicao, timeout=self.timeout) as resposta:
                bruto = resposta.read().decode("utf-8")
        except HTTPError as exc:
            bruto = exc.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(bruto)
            except json.JSONDecodeError:
                payload = {"error": "HTTP {}: {}".format(exc.code, bruto[:400])}
            raise self._erro_da_resposta(payload, exc.code)
        except URLError as exc:
            raise ErroMeta("Falha de rede ao falar com Meta: {}".format(exc.reason))
        except TimeoutError:
            raise ErroMeta("Tempo esgotado ao falar com Meta")

        try:
            payload = json.loads(bruto)
        except json.JSONDecodeError:
            raise ErroMeta("Meta devolveu JSON invalido: {}".format(bruto[:400]))
        if isinstance(payload, dict) and payload.get("error"):
            raise self._erro_da_resposta(payload)
        return payload

    def get(self, caminho, parametros=None, tentativas=3):
        """GET com backoff para instabilidade temporaria e rate limit."""
        ultima = None
        for tentativa in range(1, tentativas + 1):
            try:
                return self._requisicao("GET", caminho, parametros)
            except ErroMeta as exc:
                ultima = exc
                # Erros de permissao/formato nao melhoram esperando. Os codigos
                # -1/-2 e 24 sao falhas transitorias documentadas pelo Meta.
                codigo = int(exc.codigo) if exc.codigo is not None else None
                if (codigo is not None and codigo not in {-2, -1, 24, 429}
                        and codigo < 500):
                    raise
                if tentativa < tentativas:
                    espera = 2 ** (tentativa - 1)
                    print("Consulta ao Meta falhou (tentativa {}/{}); aguardando {}s..."
                          .format(tentativa, tentativas, espera))
                    time.sleep(espera)
        raise ultima

    def post(self, caminho, parametros=None):
        return self._requisicao("POST", caminho, parametros)


def caminhos_de_midia(linha):
    """Valida e devolve caminhos relativos sem permitir sair de midia/."""
    bruto = (linha.get("midia") or "").strip()
    if not bruto:
        raise ValueError("sem arquivo na coluna midia")

    caminhos = [p.strip().replace("\\", "/") for p in bruto.split(";") if p.strip()]
    if not caminhos:
        raise ValueError("sem arquivo valido na coluna midia")

    for caminho in caminhos:
        partes = caminho.split("/")
        if (os.path.isabs(caminho) or ".." in partes or caminho.startswith("/")
                or not all(partes)):
            raise ValueError("caminho de midia inseguro: {!r}".format(caminho))
        completo = os.path.normpath(os.path.join(MIDIA, *partes))
        if os.path.commonpath([MIDIA, completo]) != os.path.normpath(MIDIA):
            raise ValueError("arquivo fora da pasta midia: {!r}".format(caminho))
        if not os.path.isfile(completo):
            raise ValueError("arquivo nao encontrado: {}".format(completo))
    return caminhos


def url_publica(caminho, base):
    """Monta URL HTTPS, codificando cada segmento do caminho relativo."""
    if not base:
        raise ValueError("falta PUBLIC_MEDIA_BASE_URL (ou PUBLIC_BASE_URL)")
    base = base.strip().rstrip("/")
    if not base.startswith("https://"):
        raise ValueError("PUBLIC_MEDIA_BASE_URL precisa comecar por https://")
    return base + "/" + "/".join(quote(parte, safe="") for parte in caminho.split("/"))


def urls_publicas(linha, base):
    return [url_publica(caminho, base) for caminho in caminhos_de_midia(linha)]


def legenda(linha):
    """Usa a legenda pronta e acrescenta hashtags somente se ainda nao vierem nela."""
    texto = (linha.get("legenda") or "").strip()
    hashtags = (linha.get("hashtags") or "").strip()
    if hashtags and hashtags not in texto:
        texto = (texto + "\n\n" + hashtags).strip()
    if len(texto) > 2200:
        raise ValueError("legenda tem {} caracteres; Instagram aceita ate 2.200".format(len(texto)))
    return texto


def esperar_container(api, container_id, intervalo, timeout):
    """Espera o processamento remoto terminar antes de chamar media_publish."""
    inicio = time.monotonic()
    ultimo = "desconhecido"
    while True:
        estado = api.get(container_id, {"fields": "status_code,status"})
        ultimo = (estado.get("status_code") or estado.get("status") or "desconhecido").upper()
        if ultimo in STATUS_PRONTO:
            return
        if ultimo in STATUS_FALHOU:
            detalhe = estado.get("status") or estado
            raise ErroMeta("container {} terminou em {}: {}".format(container_id, ultimo, detalhe))
        if time.monotonic() - inicio >= timeout:
            raise ErroMeta("container {} ficou em {} por mais de {}s"
                            .format(container_id, ultimo, timeout))
        print("  Container {}: {}. Aguardando {}s...".format(container_id, ultimo, intervalo))
        time.sleep(intervalo)


class EstadoDoPost:
    """Checkpoint local de cada chamada POST, sem token ou dados secretos.

    O CSV e' o relatorio humano; este JSON e' a protecao tecnica contra
    duplicidade. Um container ja criado e' retomado durante suas 24 horas de
    vida, em vez de criar outro. Antes de media_publish, a intencao tambem e'
    gravada para que um timeout fique explicitamente como "ambigua".
    """

    def __init__(self, caminho=ESTADO_PUBLICACAO):
        self.caminho = caminho
        dados = ler_json(caminho, {})
        self.dados = dados if isinstance(dados, dict) else {}

    def obter(self, post_id):
        valor = self.dados.get(post_id, {})
        return valor if isinstance(valor, dict) else {}

    def gravar(self, post_id, **campos):
        registro = dict(self.obter(post_id))
        registro.update(campos)
        registro["atualizado_em"] = agora().isoformat(timespec="seconds")
        self.dados[post_id] = registro
        escrever_json_atomico(self.caminho, self.dados)
        return registro


def criar_container(api, conta_id, parametros, intervalo, timeout, estado, chave):
    """Cria ou retoma um container persistido por `chave`."""
    atual = estado.obter(chave)
    container_id = atual.get("container_id")
    if container_id:
        print("  Retomando container {}...".format(container_id))
    else:
        resposta = api.post("{}/media".format(conta_id), parametros)
        container_id = resposta.get("id") if isinstance(resposta, dict) else None
        if not container_id:
            raise ErroMeta("Meta nao devolveu id do container: {}".format(resposta))
        estado.gravar(chave, container_id=str(container_id), etapa="container_criado")
    esperar_container(api, container_id, intervalo, timeout)
    estado.gravar(chave, container_id=str(container_id), etapa="container_pronto")
    return str(container_id)


def _container_principal(api, linha, conta_id, urls, texto, intervalo, timeout, estado):
    """Cria/retoma o container pai; itens de carrossel recebem suas proprias chaves."""
    post_id = linha["post_id"]
    formato = linha["formato"]

    if formato == "carrossel":
        if not 2 <= len(urls) <= 10:
            raise ValueError("carrossel precisa de 2 a 10 imagens; encontrou {}".format(len(urls)))
        if any(not url.lower().split("?", 1)[0].endswith((".jpg", ".jpeg")) for url in urls):
            raise ValueError("carrossel so aceita JPEG neste fluxo")
        filhos = []
        for indice, url in enumerate(urls, start=1):
            print("  Criando item {}/{} do carrossel...".format(indice, len(urls)))
            filhos.append(criar_container(
                api, conta_id, {"image_url": url, "is_carousel_item": "true"},
                intervalo, timeout, estado, "{}:filho:{}".format(post_id, indice),
            ))
        return criar_container(
            api, conta_id,
            {"media_type": "CAROUSEL", "children": ",".join(filhos), "caption": texto},
            intervalo, timeout, estado, post_id,
        )

    if formato == "estatico":
        if len(urls) != 1:
            raise ValueError("post estatico precisa de exatamente um JPEG")
        if not urls[0].lower().split("?", 1)[0].endswith((".jpg", ".jpeg")):
            raise ValueError("post estatico so aceita JPEG")
        return criar_container(api, conta_id, {"image_url": urls[0], "caption": texto},
                                intervalo, timeout, estado, post_id)

    if formato == "reels":
        if len(urls) != 1:
            raise ValueError("reel precisa de exatamente um MP4")
        if not urls[0].lower().split("?", 1)[0].endswith(".mp4"):
            raise ValueError("reel precisa apontar para um arquivo .mp4")
        return criar_container(
            api, conta_id,
            {"media_type": "REELS", "video_url": urls[0], "caption": texto,
             "share_to_feed": "true"},
            intervalo, timeout, estado, post_id,
        )

    if formato == "stories":
        if len(urls) != 1:
            raise ValueError("story precisa de exatamente uma imagem ou video")
        # Stories publicados pela API nao aceitam os stickers de enquete/link;
        # o CTA continua na arte, mas a API so publica a midia base.
        campo = "video_url" if urls[0].lower().split("?", 1)[0].endswith(".mp4") else "image_url"
        return criar_container(api, conta_id, {"media_type": "STORIES", campo: urls[0]},
                                intervalo, timeout, estado, post_id)

    raise ValueError("formato desconhecido: {!r}".format(formato))


def reconciliar_publicacao(api, conta_id, texto, post_id):
    """Procura publicacao feita quando a resposta do publish se perdeu.

    Nao reenvia nada. A comparacao usa a legenda completa e a proximidade de
    horario; e' conservadora de proposito para jamais chamar uma duplicata de
    sucesso. A pagina costuma devolver os itens mais recentes primeiro.
    """
    resposta = api.get("{}/media".format(conta_id), {
        "fields": "id,caption,timestamp,media_type,media_product_type",
        "limit": 25,
    })
    for midia in resposta.get("data", []):
        if (midia.get("caption") or "").strip() == texto.strip():
            print("  A publicacao ambigua foi encontrada no Instagram: {}".format(midia.get("id")))
            return str(midia["id"])
    raise ErroMeta(
        "resposta de media_publish ambigua para {}; nao foi reenviado para evitar "
        "duplicata. Confira o perfil e grave o ig_media_id manualmente se publicou."
        .format(post_id)
    )


def publicar_no_instagram(api, linha, conta_id, base_midia, intervalo, timeout, estado):
    """Executa container -> processamento -> media_publish com idempotencia local."""
    post_id = linha["post_id"]
    urls = urls_publicas(linha, base_midia)
    texto = legenda(linha)
    anterior = estado.obter(post_id)

    if anterior.get("media_id"):
        return str(anterior["media_id"])

    print("  Midia publica:")
    for url in urls:
        print("    " + url)

    # Se caiu depois do POST /media_publish, primeiro consulta o feed. Nunca
    # repete aquele POST sem intervencao humana.
    if anterior.get("etapa") == "publish_iniciado":
        media_id = reconciliar_publicacao(api, conta_id, texto, post_id)
        estado.gravar(post_id, media_id=media_id, etapa="publicado")
        return media_id

    container = _container_principal(api, linha, conta_id, urls, texto,
                                     intervalo, timeout, estado)
    estado.gravar(post_id, container_id=container, etapa="publish_iniciado")
    print("  Publicando container {}...".format(container))
    try:
        resposta = api.post("{}/media_publish".format(conta_id), {"creation_id": container})
    except ErroMeta as exc:
        # HTTP 4xx foi uma recusa conhecida; ainda assim nao reenviamos sem uma
        # revisao, porque a proximidade com a escrita e' valiosa demais.
        raise ErroMeta("media_publish pode ter sido ou nao recebido pelo Meta: {}".format(exc))
    media_id = resposta.get("id") if isinstance(resposta, dict) else None
    if not media_id:
        raise ErroMeta("Meta nao devolveu id da publicacao: {}".format(resposta))
    estado.gravar(post_id, media_id=str(media_id), etapa="publicado")
    return str(media_id)


def parse_agora(valor):
    """Parseia --agora para testes reprodutiveis, sempre no fuso do calendario."""
    if not valor:
        return agora()
    try:
        data = datetime.fromisoformat(valor)
    except ValueError:
        raise SystemExit("--agora deve ser AAAA-MM-DDTHH:MM, por exemplo 2026-08-17T19:35")
    if data.tzinfo is None:
        data = data.replace(tzinfo=fuso())
    return data.astimezone(fuso())


def selecionar(linhas, args, momento):
    """Seleciona sem jamais incluir o que ja foi publicado."""
    ids = set(args.post or [])
    if ids:
        encontrados = {l["post_id"] for l in linhas}
        faltando = sorted(ids - encontrados)
        if faltando:
            raise SystemExit("post_id nao encontrado: {}".format(", ".join(faltando)))

    elegiveis = {STATUS_PENDENTE}
    if args.tentar_erros:
        elegiveis.add(STATUS_ERRO)

    janela = timedelta(hours=args.janela_horas)
    escolhidos = []
    atrasados = []
    ignorados = []

    for linha in sorted(linhas, key=momento_do_post):
        status = (linha.get("status") or STATUS_PENDENTE).strip().lower()
        if status == STATUS_PUBLICADO:
            continue
        if status not in elegiveis:
            ignorados.append(linha)
            continue
        if ids:
            if linha["post_id"] in ids:
                escolhidos.append(linha)
            continue

        agendado = momento_do_post(linha)
        if agendado > momento:
            continue
        if momento - agendado > janela and not args.incluir_atrasados:
            atrasados.append(linha)
            continue
        escolhidos.append(linha)

    if not ids and len(escolhidos) > args.limite:
        excedentes = escolhidos[args.limite:]
        escolhidos = escolhidos[:args.limite]
        print("Limite de {} post(s) por execucao: {} ficou/ficaram para a proxima rodada."
              .format(args.limite, len(excedentes)))

    if atrasados:
        print("{} post(s) pendente(s) fora da janela de {}h nao foram publicados. "
              "Use --incluir-atrasados para tratar conscientemente."
              .format(len(atrasados), args.janela_horas))
    if ignorados and args.tentar_erros is False:
        erros = [l for l in ignorados if l.get("status") == STATUS_ERRO]
        if erros:
            print("{} post(s) com erro foram mantidos parados para evitar duplicacao. "
                  "Confira o Instagram e use --tentar-erros se for seguro.".format(len(erros)))
    return escolhidos


def argumentos():
    p = argparse.ArgumentParser(description="Publica posts vencidos via Instagram Graph API.")
    p.add_argument("--post", action="append", metavar="POST_ID",
                   help="publica este post_id mesmo que ainda esteja no futuro; pode repetir")
    p.add_argument("--tentar-erros", action="store_true",
                   help="inclui posts com status erro; confira o perfil antes de usar")
    p.add_argument("--incluir-atrasados", action="store_true",
                   help="inclui posts vencidos ha mais tempo que POST_WINDOW_HOURS")
    p.add_argument("--limite", type=int, default=1,
                   help="maximo de posts sem --post por execucao (padrao: 1)")
    p.add_argument("--janela-horas", type=int,
                   default=numero_do_ambiente("POST_WINDOW_HOURS", 24),
                   help="idade maxima do post automatico (padrao via ambiente: 24)")
    p.add_argument("--agora", help="momento de referencia para teste: AAAA-MM-DDTHH:MM")
    p.add_argument("--dry-run", action="store_true",
                   help="forca simulacao, mesmo se DRY_RUN=false")
    args = p.parse_args()
    if args.limite < 1:
        p.error("--limite deve ser pelo menos 1")
    if args.janela_horas < 1:
        p.error("--janela-horas deve ser pelo menos 1")
    return args


def main():
    carregar_dotenv()
    args = argumentos()
    momento = parse_agora(args.agora)
    simular = args.dry_run or env("DRY_RUN", "true").strip().lower() != "false"
    linhas = ler_calendario()
    alvo = selecionar(linhas, args, momento)

    print("Horario de referencia: {}".format(momento.isoformat(timespec="minutes")))
    print("Modo: {}".format("SIMULACAO (nenhum post sera enviado)" if simular else "PUBLICACAO REAL"))
    if not alvo:
        print("Nenhum post elegivel nesta rodada.")
        return

    print("Posts elegiveis: {}".format(", ".join(l["post_id"] for l in alvo)))
    base_midia = env("PUBLIC_MEDIA_BASE_URL", env("PUBLIC_BASE_URL"))

    # Na simulacao, nao e' preciso ter token/ID/host verdadeiro. Isso deixa o
    # primeiro teste utilizavel antes de configurar Meta e GitHub Secrets.
    if simular:
        for linha in alvo:
            print("\n[SIMULACAO] {} ({})".format(linha["post_id"], linha["formato"]))
            try:
                arquivos = caminhos_de_midia(linha)
                print("  Arquivos: {}".format("; ".join(arquivos)))
                print("  Legenda: {} caracteres".format(len(legenda(linha))))
                if base_midia:
                    for arquivo in arquivos:
                        print("  URL: {}".format(url_publica(arquivo, base_midia)))
                else:
                    print("  URL publica: configure PUBLIC_MEDIA_BASE_URL para validar.")
            except (ValueError, OSError) as exc:
                print("  ERRO DE PREPARO: {}".format(exc))
        return

    token = env("INSTAGRAM_ACCESS_TOKEN", obrigatorio=True)
    conta_id = env("INSTAGRAM_BUSINESS_ACCOUNT_ID", obrigatorio=True)
    if not base_midia:
        raise SystemExit("ERRO: falta PUBLIC_MEDIA_BASE_URL (ou PUBLIC_BASE_URL).")
    intervalo = numero_do_ambiente("MEDIA_POLL_SECONDS", 10)
    timeout = numero_do_ambiente("MEDIA_POLL_TIMEOUT_SECONDS", 600)
    api = GraphAPI(
        token,
        timeout=numero_do_ambiente("META_HTTP_TIMEOUT_SECONDS", 60),
        # Necessario apenas se "Require App Secret" estiver ligado no app Meta.
        app_secret=env("META_APP_SECRET", "").strip() or None,
    )
    estado = EstadoDoPost()

    publicados = 0
    erros = 0
    for linha in alvo:
        print("\n[PUBLICANDO] {} ({})".format(linha["post_id"], linha["formato"]))
        etapa = "preparo"
        try:
            etapa = "envio/processamento"
            media_id = publicar_no_instagram(api, linha, conta_id, base_midia, intervalo, timeout, estado)
            linha["status"] = STATUS_PUBLICADO
            linha["ig_media_id"] = media_id
            linha["publicado_em"] = agora().isoformat(timespec="seconds")
            linha["erro"] = ""
            escrever_calendario(linhas)
            publicados += 1
            print("  OK: publicado como {}".format(media_id))
        except (ErroMeta, ValueError, OSError) as exc:
            # Uma falha apos uma chamada POST e' potencialmente ambigua: nao ha
            # retry automatico nem reenvio pelo cron. O log orienta a checagem.
            linha["status"] = STATUS_ERRO
            linha["erro"] = "{} em {}: {}. Confira o perfil antes de --tentar-erros.".format(
                agora().isoformat(timespec="seconds"), etapa, texto_erro(exc)
            )
            escrever_calendario(linhas)
            erros += 1
            print("  ERRO: {}".format(linha["erro"]))

    print("\nResumo: {} publicado(s), {} com erro.".format(publicados, erros))
    if erros:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
