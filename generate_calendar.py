from pathlib import Path
from datetime import date, timedelta
import csv

base = Path(r'C:/Users/ucask/OneDrive/Desktop/DIGITAL/do-zero-ao-real-PROJETO-COMPLETO/do-zero-ao-real')
outdir = base / '06-agendamento-instagram'
outdir.mkdir(parents=True, exist_ok=True)

start = date(2026, 8, 17)
end = date(2027, 2, 5)

hashtags_base = '#dozeroaoreal #rendacomhonestidade #infoproduto #marketingdigital #faceless #rendaextra #kiwify #conteudodigital'

formats = [
    ('Carrossel', '19:30'),
    ('Reels', '20:15'),
    ('Stories', '12:30'),
    ('Post estatico', '19:00'),
]

pillars = [
    'Educativo',
    'Jornada',
    'Conexao',
    'Bastidores / prova honesta',
    'Venda direta honesta',
]

phases = [
    (date(2026,8,17), date(2026,9,15), 'Aquecimento e autoridade', 'mostrar que da para comecar com estrutura, sem promessa milagrosa'),
    (date(2026,9,16), date(2026,10,15), 'Lancamento do guia', 'apresentar o guia, quebrar objecoes e levar para o checkout'),
    (date(2026,10,16), date(2026,12,31), 'Evergreen de trafego', 'ensinar fundamentos e manter desejo vivo todos os dias'),
    (date(2027,1,1), date(2027,2,5), 'Recomeco de janeiro', 'aproveitar energia de ano novo e transformar intencao em plano'),
]

topic_bank = {
    'Educativo': [
        '3 erros de quem comeca no marketing digital sem direcao',
        'O que e um infoproduto explicado sem enrolacao',
        'Por que comecar pequeno e melhor do que esperar o plano perfeito',
        'Como escolher uma plataforma sem travar na comparacao',
        'A diferenca entre conteudo que ensina e conteudo que so ocupa espaco',
        'Como pensar em oferta sem prometer resultado impossivel',
        'O basico de copywriting para quem esta comecando do zero',
        'Como montar uma rotina simples de producao de conteudo',
        'O que colocar numa bio que realmente explica o perfil',
        'Como usar prova honesta mesmo sem depoimentos ainda',
    ],
    'Jornada': [
        'O que eu faria se estivesse comecando hoje sem dinheiro para investir',
        'A parte invisivel de construir um projeto do zero',
        'Comecar sem aparecer tambem e uma escolha valida',
        'O dia em que eu percebi que precisava parar de esperar estar pronto',
        'O que mudou quando eu organizei o projeto em etapas',
        'Por que documentar o processo ajuda mais do que fingir perfeicao',
        'Bastidor real: fazer simples para conseguir terminar',
        'A diferenca entre estar perdido e estar no comeco',
    ],
    'Conexao': [
        'Se voce sente que esta atrasado, leia isso',
        'Nem todo mundo comeca com camera, equipe e dinheiro',
        'A vergonha de comecar pequeno trava mais do que a falta de ferramenta',
        'Voce nao precisa virar guru para vender algo util',
        'O medo de errar nao pode ser maior que a vontade de sair do lugar',
        'O comeco parece feio porque ainda e comeco',
        'Faceless nao e se esconder; e escolher um formato possivel',
        'O plano perfeito muitas vezes e so procrastinacao com nome bonito',
    ],
    'Bastidores / prova honesta': [
        'Como o guia foi organizado por etapas, nao por promessa',
        'O que tem por tras de uma landing page simples e honesta',
        'Por que nao uso depoimento falso nem print inventado',
        'Bastidor: o produto foi feito para quem precisa de clareza',
        'O que entra no guia e por que isso importa para iniciantes',
        'Como transformei duvidas comuns em capitulos praticos',
        'Por que a garantia existe, mas o esforco continua sendo seu',
        'Bastidor da VSL: direto ao ponto, sem teatro de riqueza',
    ],
    'Venda direta honesta': [
        'O Guia Do Zero ao Real e para quem quer comecar com um mapa',
        'Se voce trava no primeiro passo, o guia foi feito para isso',
        'O que voce recebe dentro do Do Zero ao Real',
        'Por que R$49,99 compra clareza, nao promessa de dinheiro',
        'Antes de comprar: para quem esse guia serve e para quem nao serve',
        'O guia nao faz por voce, mas te mostra o caminho com ordem',
        '7 dias de garantia para voce olhar com calma',
        'Quer comecar hoje? O checkout esta na bio',
    ],
}

visual_templates = {
    'Carrossel': [
        'Slide 1: titulo forte com fundo verde-noturno e palavra REAL em lima. Slides 2-6: um ponto por slide. Ultimo slide: CTA para ver o guia no link da bio.',
        'Slide 1: pergunta direta. Slides seguintes: resposta em passos curtos. Ultimo slide: "salva para fazer depois".',
        'Slide 1: "antes de comecar..." Slides 2-5: erros/ajustes. Ultimo slide: convite para o guia.',
    ],
    'Reels': [
        'Video faceless com texto na tela, cortes rapidos e b-roll simples de computador/celular. Sem aparecer. Narrativa opcional ou audio em alta baixo.',
        'Tela gravada mostrando checklist/rotina, com legendas grandes e ritmo rapido. Encerrar com CTA na bio.',
        'Reels silencioso com frases em tela e musica tendencia. 5 cenas, 2 segundos cada.',
    ],
    'Stories': [
        'Sequencia de 3 stories: 1) pergunta/enquete, 2) dica curta, 3) CTA para link da bio/check-out.',
        'Story unico com bastidor + caixa de pergunta: "qual etapa mais te trava?".',
        'Antes/depois conceitual: "antes: perdido / depois: com checklist". CTA discreto.',
    ],
    'Post estatico': [
        'Imagem unica com frase forte central, logo discreta e CTA na legenda.',
        'Card simples: titulo, subtitulo e elemento visual lima. Visual limpo, sem poluicao.',
        'Print/nota visual estilo checklist, com 3 bullets curtos.',
    ],
}

cta_by_pillar = {
    'Educativo': 'Salva esse post e segue o @dozero.aoreal para aprender o caminho sem promessa falsa.',
    'Jornada': 'Se voce tambem esta comecando, acompanha a jornada no @dozero.aoreal.',
    'Conexao': 'Comenta "REAL" se voce quer comecar do jeito possivel, nao do jeito perfeito.',
    'Bastidores / prova honesta': 'Quer ver o mapa completo? O Guia Do Zero ao Real esta no link da bio.',
    'Venda direta honesta': 'Para comecar com um passo a passo organizado, acesse o guia pelo link da bio.',
}

caption_openers = {
    'Educativo': [
        'Comecar do zero fica mais dificil quando voce tenta aprender tudo ao mesmo tempo.',
        'O problema nao e so falta de vontade. Muitas vezes e falta de ordem.',
        'Antes de pensar em vender, voce precisa entender o caminho basico.',
    ],
    'Jornada': [
        'Esse projeto nasceu do jeito que muita gente comeca: sem estrutura perfeita.',
        'Nem todo bastidor e bonito, mas e nele que o negocio comeca a ficar real.',
        'O comeco nao precisa ser impressionante. Precisa existir.',
    ],
    'Conexao': [
        'Se voce esta tentando comecar e sente que esta atrasado, respira.',
        'Tem muita gente vendendo uma vida perfeita. Aqui a conversa e outra.',
        'Voce nao precisa parecer expert para dar o primeiro passo com honestidade.',
    ],
    'Bastidores / prova honesta': [
        'Um bastidor importante: esse projeto nao usa promessa de resultado garantido.',
        'Por tras do guia existe uma escolha simples: clareza antes de hype.',
        'A construcao foi pensada para quem precisa sair da confusao e ir para um passo a passo.',
    ],
    'Venda direta honesta': [
        'O Guia Do Zero ao Real nao promete renda automatica. Ele entrega organizacao.',
        'Se voce quer comecar, mas sempre trava na proxima etapa, esse guia pode te ajudar.',
        'A proposta e simples: um mapa pratico para quem esta comecando sem nada.',
    ],
}

def get_phase(d):
    for s,e,name,angle in phases:
        if s <= d <= e:
            return name, angle
    return '', ''

def week_label(d):
    return f'Semana {(d - start).days // 7 + 1}'

def make_caption(d, idx, pillar, topic, phase_name, angle):
    opener = caption_openers[pillar][idx % len(caption_openers[pillar])]
    body_lines = []
    if pillar == 'Educativo':
        body_lines = [
            'Pensa nisso como uma escada: primeiro voce entende a base, depois monta a estrutura, depois publica, depois ajusta.',
            'Quando voce pula etapas, tudo parece confuso e qualquer ferramenta vira desculpa para travar.',
            'A meta aqui e fazer o simples bem feito: um produto claro, uma oferta honesta e conteudo constante.',
        ]
    elif pillar == 'Jornada':
        body_lines = [
            'Nao e sobre fingir que esta tudo pronto. E sobre documentar o processo e continuar mesmo quando ainda falta lapidar.',
            'A vantagem de comecar pequeno e que voce consegue corrigir rapido, sem depender de equipe, estudio ou orcamento.',
            'Feito com honestidade ainda vence muita ideia perfeita que nunca sai do papel.',
        ]
    elif pillar == 'Conexao':
        body_lines = [
            'Se o seu ponto de partida parece ruim, isso nao te elimina. So define qual e o proximo passo.',
            'Voce pode comecar sem aparecer, sem equipamento caro e sem discurso de guru.',
            'O que nao da e esperar coragem infinita para fazer a primeira publicacao.',
        ]
    elif pillar == 'Bastidores / prova honesta':
        body_lines = [
            'O conteudo foi pensado para ensinar a estrutura: plataformas, conteudo faceless, copy, organizacao e checklist de acao.',
            'Sem depoimento inventado. Sem print falso. Sem "ganhe X por dia". A ideia e ser util sem vender ilusao.',
            'Isso deixa a promessa menor -- e a entrega mais limpa.',
        ]
    else:
        body_lines = [
            'Dentro dele voce encontra fundamentos, cadastro em plataformas, conteudo faceless, noes de copy e organizacao financeira basica.',
            'Nao e uma formula magica. E um roteiro para parar de ficar perdido na primeira tela.',
            'Voce olha, aplica no seu ritmo e decide se faz sentido. Tem garantia de 7 dias conforme o checkout.',
        ]
    return '\n\n'.join([
        opener,
        f'Tema de hoje: {topic}.',
        *body_lines,
        cta_by_pillar[pillar],
        hashtags_base,
    ])

rows = []
d = start
i = 0
while d <= end:
    fmt, time = formats[i % len(formats)]
    pillar = pillars[i % len(pillars)]
    phase_name, angle = get_phase(d)
    topics = topic_bank[pillar]
    topic = topics[(i // len(pillars)) % len(topics)]
    visual = visual_templates[fmt][i % len(visual_templates[fmt])]
    caption = make_caption(d, i, pillar, topic, phase_name, angle)
    rows.append({
        'data': d.isoformat(),
        'dia_semana': ['segunda','terca','quarta','quinta','sexta','sabado','domingo'][d.weekday()],
        'horario_sugerido': time,
        'fase': phase_name,
        'semana': week_label(d),
        'formato': fmt,
        'pilar': pillar,
        'tema': topic,
        'gancho': topic,
        'legenda': caption,
        'cta': cta_by_pillar[pillar],
        'hashtags': hashtags_base,
        'direcao_visual': visual,
        'status_agendamento': 'Pendente',
        'observacoes': 'Agendar no Meta Business Suite. Revisar arte antes de publicar.',
    })
    d += timedelta(days=1)
    i += 1

csv_path = outdir / 'calendario-posts-2026-08-17-a-2027-02-05.csv'
with csv_path.open('w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

md_path = outdir / 'calendario-posts-2026-08-17-a-2027-02-05.md'
with md_path.open('w', encoding='utf-8') as f:
    f.write('# Calendario Instagram - do zero ao REAL\n\n')
    f.write('Periodo: 17/08/2026 a 05/02/2027.\n')
    f.write(f'Total: {len(rows)} posts diarios.\n')
    f.write('Plataforma: Instagram via Meta Business Suite.\n')
    f.write('Regra editorial: sem promessa de renda, sem depoimento falso, sem print inventado.\n\n')
    for r in rows:
        f.write(f"## {r['data']} - {r['dia_semana']} - {r['formato']}\n\n")
        f.write(f"**Horario sugerido:** {r['horario_sugerido']}  \n")
        f.write(f"**Fase:** {r['fase']}  \n")
        f.write(f"**Pilar:** {r['pilar']}  \n")
        f.write(f"**Tema/Gancho:** {r['tema']}\n\n")
        f.write('**Legenda:**\n\n')
        f.write(r['legenda'] + '\n\n')
        f.write('**Direcao visual:**\n\n')
        f.write(r['direcao_visual'] + '\n\n')
        f.write('---\n\n')

# Split by format for easier production
format_map = {
    'Carrossel': 'carrossel',
    'Reels': 'reels',
    'Stories': 'stories',
    'Post estatico': 'post-estatico',
}
for format_name, slug in format_map.items():
    path = outdir / f'{slug}.md'
    with path.open('w', encoding='utf-8') as f:
        f.write(f'# {format_name} - do zero ao REAL\n\n')
        for r in rows:
            if r['formato'] != format_name:
                continue
            f.write(f"## {r['data']} - {r['tema']}\n\n")
            f.write(f"**Horario:** {r['horario_sugerido']}  \n")
            f.write(f"**Pilar:** {r['pilar']}  \n\n")
            f.write('**Roteiro/Direcao:**\n')
            f.write(r['direcao_visual'] + '\n\n')
            f.write('**Legenda:**\n\n')
            f.write(r['legenda'] + '\n\n---\n\n')

# Meta scheduling instructions
instructions = outdir / 'como-agendar-no-meta-business-suite.md'
instructions.write_text(
    '# Como agendar no Meta Business Suite\n\n'
    '1. Entre no Meta Business Suite com a conta conectada ao Instagram @dozero.aoreal.\n'
    '2. Va em Conteudo ou Planejador.\n'
    '3. Clique em Criar publicacao.\n'
    '4. Escolha Instagram.\n'
    '5. Copie a legenda do arquivo calendario-posts-2026-08-17-a-2027-02-05.md ou da planilha CSV.\n'
    '6. Suba a arte/video correspondente.\n'
    '7. Clique em Agendar e use a data/horario sugeridos.\n'
    '8. No CSV, marque status_agendamento como Agendado depois de confirmar.\n\n'
    '## Fluxo recomendado\n\n'
    'Agendar em blocos de 7 dias por vez. Assim voce evita erro, consegue revisar artes e mantem consistencia sem passar horas todo dia.\n\n'
    '## Observacao importante\n\n'
    'O Meta Business Suite nao e garantido como ferramenta de upload em massa por CSV para Instagram em todas as contas. Por isso, este pacote foi montado como calendario mestre + copy pronta para agendamento manual/assistido em blocos.\n',
    encoding='utf-8'
)

print(f'Criados {len(rows)} posts')
for p in [csv_path, md_path, instructions]:
    print(p)