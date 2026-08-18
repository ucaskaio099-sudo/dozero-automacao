# -*- coding: utf-8 -*-
"""Mapa explicito de acentuacao do corpus do calendario.

O CSV de origem (06-agendamento-instagram) foi gerado sem nenhum acento --
173 posts, zero acentos. Legenda de Instagram sem acento parece descuido, entao
aqui esta a correcao.

Por que um mapa frase-a-frase e nao um regex de palavras: "e"/"e'", "esta"/"esta'"
e "so"/"so'" sao ambiguos em portugues (conjuncao vs verbo, pronome vs verbo,
adverbio vs adjetivo). Trocar por palavra erraria. O corpus tem so 142 frases
unicas, entao da pra mapear cada uma na mao e ter 100% de certeza.

Regra de seguranca: `corrigir()` levanta erro se receber uma frase que nao esta
no mapa. Assim nada passa batido sem acento -- se o calendario mudar, o script
para e avisa em vez de publicar texto errado.
"""

# Frases que NAO mudam ficam de fora do mapa e sao listadas aqui, para que a
# checagem "toda frase foi analisada" continue valendo.
SEM_ALTERACAO = {
    "#dozeroaoreal #rendacomhonestidade #infoproduto #marketingdigital #faceless #rendaextra #kiwify #conteudodigital",
    'Antes/depois conceitual: "antes: perdido / depois: com checklist". CTA discreto.',
    "Aquecimento e autoridade",
    "Bastidor da VSL: direto ao ponto, sem teatro de riqueza",
    "Bastidor real: fazer simples para conseguir terminar",
    "Bastidor: o produto foi feito para quem precisa de clareza",
    "Bastidores / prova honesta",
    "Como usar prova honesta mesmo sem depoimentos ainda",
    "Educativo",
    "Feito com honestidade ainda vence muita ideia perfeita que nunca sai do papel.",
    "Jornada",
    "O dia em que eu percebi que precisava parar de esperar estar pronto",
    "O que colocar numa bio que realmente explica o perfil",
    "O que entra no guia e por que isso importa para iniciantes",
    "O que mudou quando eu organizei o projeto em etapas",
    "Print/nota visual estilo checklist, com 3 bullets curtos.",
    "Salva esse post e segue o @dozero.aoreal para aprender o caminho sem promessa falsa.",
    "Venda direta honesta",
}

# frase sem acento -> frase correta
MAPA = {
    "3 erros de quem comeca no marketing digital sem direcao":
        "3 erros de quem começa no marketing digital sem direção",
    "7 dias de garantia para voce olhar com calma":
        "7 dias de garantia para você olhar com calma",
    "A construcao foi pensada para quem precisa sair da confusao e ir para um passo a passo.":
        "A construção foi pensada para quem precisa sair da confusão e ir para um passo a passo.",
    "A diferenca entre conteudo que ensina e conteudo que so ocupa espaco":
        "A diferença entre conteúdo que ensina e conteúdo que só ocupa espaço",
    "A diferenca entre estar perdido e estar no comeco":
        "A diferença entre estar perdido e estar no começo",
    "A meta aqui e fazer o simples bem feito: um produto claro, uma oferta honesta e conteudo constante.":
        "A meta aqui é fazer o simples bem feito: um produto claro, uma oferta honesta e conteúdo constante.",
    "A parte invisivel de construir um projeto do zero":
        "A parte invisível de construir um projeto do zero",
    "A proposta e simples: um mapa pratico para quem esta comecando sem nada.":
        "A proposta é simples: um mapa prático para quem está começando sem nada.",
    "A vantagem de comecar pequeno e que voce consegue corrigir rapido, sem depender de equipe, estudio ou orcamento.":
        "A vantagem de começar pequeno é que você consegue corrigir rápido, sem depender de equipe, estúdio ou orçamento.",
    "A vergonha de comecar pequeno trava mais do que a falta de ferramenta":
        "A vergonha de começar pequeno trava mais do que a falta de ferramenta",
    "Antes de comprar: para quem esse guia serve e para quem nao serve":
        "Antes de comprar: para quem esse guia serve e para quem não serve",
    "Antes de pensar em vender, voce precisa entender o caminho basico.":
        "Antes de pensar em vender, você precisa entender o caminho básico.",
    "Card simples: titulo, subtitulo e elemento visual lima. Visual limpo, sem poluicao.":
        "Card simples: título, subtítulo e elemento visual lima. Visual limpo, sem poluição.",
    "Comecar do zero fica mais dificil quando voce tenta aprender tudo ao mesmo tempo.":
        "Começar do zero fica mais difícil quando você tenta aprender tudo ao mesmo tempo.",
    "Comecar sem aparecer tambem e uma escolha valida":
        "Começar sem aparecer também é uma escolha válida",
    'Comenta "REAL" se voce quer comecar do jeito possivel, nao do jeito perfeito.':
        'Comenta "REAL" se você quer começar do jeito possível, não do jeito perfeito.',
    "Como escolher uma plataforma sem travar na comparacao":
        "Como escolher uma plataforma sem travar na comparação",
    "Como montar uma rotina simples de producao de conteudo":
        "Como montar uma rotina simples de produção de conteúdo",
    "Como o guia foi organizado por etapas, nao por promessa":
        "Como o guia foi organizado por etapas, não por promessa",
    "Como pensar em oferta sem prometer resultado impossivel":
        "Como pensar em oferta sem prometer resultado impossível",
    "Como transformei duvidas comuns em capitulos praticos":
        "Como transformei dúvidas comuns em capítulos práticos",
    "Conexao": "Conexão",
    "Dentro dele voce encontra fundamentos, cadastro em plataformas, conteudo faceless, noes de copy e organizacao financeira basica.":
        "Dentro dele você encontra fundamentos, cadastro em plataformas, conteúdo faceless, noções de copy e organização financeira básica.",
    "Esse projeto nasceu do jeito que muita gente comeca: sem estrutura perfeita.":
        "Esse projeto nasceu do jeito que muita gente começa: sem estrutura perfeita.",
    "Evergreen de trafego": "Evergreen de tráfego",
    "Faceless nao e se esconder; e escolher um formato possivel":
        "Faceless não é se esconder; é escolher um formato possível",
    "Imagem unica com frase forte central, logo discreta e CTA na legenda.":
        "Imagem única com frase forte central, logo discreta e CTA na legenda.",
    "Isso deixa a promessa menor -- e a entrega mais limpa.":
        "Isso deixa a promessa menor — e a entrega mais limpa.",
    "Lancamento do guia": "Lançamento do guia",
    "Nao e sobre fingir que esta tudo pronto. E sobre documentar o processo e continuar mesmo quando ainda falta lapidar.":
        "Não é sobre fingir que está tudo pronto. É sobre documentar o processo e continuar mesmo quando ainda falta lapidar.",
    "Nao e uma formula magica. E um roteiro para parar de ficar perdido na primeira tela.":
        "Não é uma fórmula mágica. É um roteiro para parar de ficar perdido na primeira tela.",
    "Nem todo bastidor e bonito, mas e nele que o negocio comeca a ficar real.":
        "Nem todo bastidor é bonito, mas é nele que o negócio começa a ficar real.",
    "Nem todo mundo comeca com camera, equipe e dinheiro":
        "Nem todo mundo começa com câmera, equipe e dinheiro",
    "O Guia Do Zero ao Real e para quem quer comecar com um mapa":
        "O Guia Do Zero ao Real é para quem quer começar com um mapa",
    "O Guia Do Zero ao Real nao promete renda automatica. Ele entrega organizacao.":
        "O Guia Do Zero ao Real não promete renda automática. Ele entrega organização.",
    "O basico de copywriting para quem esta comecando do zero":
        "O básico de copywriting para quem está começando do zero",
    "O comeco nao precisa ser impressionante. Precisa existir.":
        "O começo não precisa ser impressionante. Precisa existir.",
    "O comeco parece feio porque ainda e comeco":
        "O começo parece feio porque ainda é começo",
    "O conteudo foi pensado para ensinar a estrutura: plataformas, conteudo faceless, copy, organizacao e checklist de acao.":
        "O conteúdo foi pensado para ensinar a estrutura: plataformas, conteúdo faceless, copy, organização e checklist de ação.",
    "O guia nao faz por voce, mas te mostra o caminho com ordem":
        "O guia não faz por você, mas te mostra o caminho com ordem",
    "O medo de errar nao pode ser maior que a vontade de sair do lugar":
        "O medo de errar não pode ser maior que a vontade de sair do lugar",
    "O plano perfeito muitas vezes e so procrastinacao com nome bonito":
        "O plano perfeito muitas vezes é só procrastinação com nome bonito",
    "O problema nao e so falta de vontade. Muitas vezes e falta de ordem.":
        "O problema não é só falta de vontade. Muitas vezes é falta de ordem.",
    "O que e um infoproduto explicado sem enrolacao":
        "O que é um infoproduto explicado sem enrolação",
    "O que eu faria se estivesse comecando hoje sem dinheiro para investir":
        "O que eu faria se estivesse começando hoje sem dinheiro para investir",
    "O que nao da e esperar coragem infinita para fazer a primeira publicacao.":
        "O que não dá é esperar coragem infinita para fazer a primeira publicação.",
    "O que tem por tras de uma landing page simples e honesta":
        "O que tem por trás de uma landing page simples e honesta",
    "O que voce recebe dentro do Do Zero ao Real":
        "O que você recebe dentro do Do Zero ao Real",
    "Para comecar com um passo a passo organizado, acesse o guia pelo link da bio.":
        "Para começar com um passo a passo organizado, acesse o guia pelo link da bio.",
    "Pensa nisso como uma escada: primeiro voce entende a base, depois monta a estrutura, depois publica, depois ajusta.":
        "Pensa nisso como uma escada: primeiro você entende a base, depois monta a estrutura, depois publica, depois ajusta.",
    "Por que R$49,99 compra clareza, nao promessa de dinheiro":
        "Por que {PRECO} compra clareza, não promessa de dinheiro",
    "Por que a garantia existe, mas o esforco continua sendo seu":
        "Por que a garantia existe, mas o esforço continua sendo seu",
    "Por que comecar pequeno e melhor do que esperar o plano perfeito":
        "Por que começar pequeno é melhor do que esperar o plano perfeito",
    "Por que documentar o processo ajuda mais do que fingir perfeicao":
        "Por que documentar o processo ajuda mais do que fingir perfeição",
    "Por que nao uso depoimento falso nem print inventado":
        "Por que não uso depoimento falso nem print inventado",
    "Por tras do guia existe uma escolha simples: clareza antes de hype.":
        "Por trás do guia existe uma escolha simples: clareza antes de hype.",
    "Quando voce pula etapas, tudo parece confuso e qualquer ferramenta vira desculpa para travar.":
        "Quando você pula etapas, tudo parece confuso e qualquer ferramenta vira desculpa para travar.",
    "Quer comecar hoje? O checkout esta na bio":
        "Quer começar hoje? O checkout está na bio",
    "Quer ver o mapa completo? O Guia Do Zero ao Real esta no link da bio.":
        "Quer ver o mapa completo? O Guia Do Zero ao Real está no link da bio.",
    "Recomeco de janeiro": "Recomeço de janeiro",
    "Reels silencioso com frases em tela e musica tendencia. 5 cenas, 2 segundos cada.":
        "Reels silencioso com frases em tela e música tendência. 5 cenas, 2 segundos cada.",
    "Se o seu ponto de partida parece ruim, isso nao te elimina. So define qual e o proximo passo.":
        "Se o seu ponto de partida parece ruim, isso não te elimina. Só define qual é o próximo passo.",
    "Se voce esta tentando comecar e sente que esta atrasado, respira.":
        "Se você está tentando começar e sente que está atrasado, respira.",
    "Se voce quer comecar, mas sempre trava na proxima etapa, esse guia pode te ajudar.":
        "Se você quer começar, mas sempre trava na próxima etapa, esse guia pode te ajudar.",
    "Se voce sente que esta atrasado, leia isso":
        "Se você sente que está atrasado, leia isso",
    "Se voce tambem esta comecando, acompanha a jornada no @dozero.aoreal.":
        "Se você também está começando, acompanha a jornada no @dozero.aoreal.",
    "Se voce trava no primeiro passo, o guia foi feito para isso":
        "Se você trava no primeiro passo, o guia foi feito para isso",
    'Sem depoimento inventado. Sem print falso. Sem "ganhe X por dia". A ideia e ser util sem vender ilusao.':
        'Sem depoimento inventado. Sem print falso. Sem "ganhe X por dia". A ideia é ser útil sem vender ilusão.',
    "Sequencia de 3 stories: 1) pergunta/enquete, 2) dica curta, 3) CTA para link da bio/check-out.":
        "Sequência de 3 stories: 1) pergunta/enquete, 2) dica curta, 3) CTA para link da bio/check-out.",
    'Slide 1: "antes de comecar..." Slides 2-5: erros/ajustes. Ultimo slide: convite para o guia.':
        'Slide 1: "antes de começar..." Slides 2-5: erros/ajustes. Último slide: convite para o guia.',
    'Slide 1: pergunta direta. Slides seguintes: resposta em passos curtos. Ultimo slide: "salva para fazer depois".':
        'Slide 1: pergunta direta. Slides seguintes: resposta em passos curtos. Último slide: "salva para fazer depois".',
    "Slide 1: titulo forte com fundo verde-noturno e palavra REAL em lima. Slides 2-6: um ponto por slide. Ultimo slide: CTA para ver o guia no link da bio.":
        "Slide 1: título forte com fundo verde-noturno e palavra REAL em lima. Slides 2-6: um ponto por slide. Último slide: CTA para ver o guia no link da bio.",
    'Story unico com bastidor + caixa de pergunta: "qual etapa mais te trava?".':
        'Story único com bastidor + caixa de pergunta: "qual etapa mais te trava?".',
    "Tela gravada mostrando checklist/rotina, com legendas grandes e ritmo rapido. Encerrar com CTA na bio.":
        "Tela gravada mostrando checklist/rotina, com legendas grandes e ritmo rápido. Encerrar com CTA na bio.",
    "Tem muita gente vendendo uma vida perfeita. Aqui a conversa e outra.":
        "Tem muita gente vendendo uma vida perfeita. Aqui a conversa é outra.",
    "Um bastidor importante: esse projeto nao usa promessa de resultado garantido.":
        "Um bastidor importante: esse projeto não usa promessa de resultado garantido.",
    "Video faceless com texto na tela, cortes rapidos e b-roll simples de computador/celular. Sem aparecer. Narrativa opcional ou audio em alta baixo.":
        "Vídeo faceless com texto na tela, cortes rápidos e b-roll simples de computador/celular. Sem aparecer. Narrativa opcional ou áudio em alta baixo.",
    "Voce nao precisa parecer expert para dar o primeiro passo com honestidade.":
        "Você não precisa parecer expert para dar o primeiro passo com honestidade.",
    "Voce nao precisa virar guru para vender algo util":
        "Você não precisa virar guru para vender algo útil",
    "Voce olha, aplica no seu ritmo e decide se faz sentido. Tem garantia de 7 dias conforme o checkout.":
        "Você olha, aplica no seu ritmo e decide se faz sentido. Tem garantia de 7 dias conforme o checkout.",
    "Voce pode comecar sem aparecer, sem equipamento caro e sem discurso de guru.":
        "Você pode começar sem aparecer, sem equipamento caro e sem discurso de guru.",
}

PREFIXO_TEMA = "Tema de hoje: "


class FraseDesconhecida(ValueError):
    """Frase do calendario que nao esta no mapa nem na lista de inalteradas."""


def corrigir(frase):
    """Devolve a frase acentuada. Levanta FraseDesconhecida se nao souber."""
    frase = frase.strip()
    if not frase:
        return frase
    if frase in MAPA:
        return MAPA[frase]
    if frase in SEM_ALTERACAO:
        return frase

    # "Tema de hoje: <tema>." e derivado do campo tema (que ja esta no mapa),
    # entao resolve pelo tema base em vez de duplicar 42 entradas.
    if frase.startswith(PREFIXO_TEMA):
        base = frase[len(PREFIXO_TEMA):].rstrip(".")
        return PREFIXO_TEMA + corrigir(base) + "."

    raise FraseDesconhecida(
        "Frase fora do mapa de acentuacao -- adicione em scripts/acentuacao.py:\n"
        "  " + repr(frase)
    )


def corrigir_bloco(texto):
    """Aplica `corrigir` linha a linha, preservando as quebras de linha."""
    if not texto:
        return texto
    return "\n".join(
        corrigir(linha) if linha.strip() else linha
        for linha in texto.split("\n")
    )
