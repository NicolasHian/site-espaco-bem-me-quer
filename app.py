"""
app.py - Servidor web da Calculadora de Orçamento
Espaço Bem Me Quer - Garden & Villa
"""

import csv  # usado para gravar os leads capturados em um arquivo .csv
import os  # usado para manipular caminhos de arquivo e checar existência de arquivos
from datetime import datetime  # usado para registrar a data/hora de cada lead

from flask import Flask, jsonify, render_template, request, url_for  # framework web e helpers de request/response

app = Flask(__name__)  # cria a aplicação Flask, usando este arquivo como referência de localização

LEADS_FILE = os.path.join(os.path.dirname(__file__), "leads.csv")  # caminho absoluto do CSV onde os leads são salvos


def formatar_moeda(valor):
    # formata um número float no padrão monetário brasileiro (1.234,56)
    texto = f"{valor:,.2f}"  # formata com vírgula como separador de milhar e ponto como decimal (padrão dos EUA)
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")  # troca os separadores para o padrão BR
    return texto  # devolve a string já formatada

app.jinja_env.filters["moeda"] = formatar_moeda  # registra a função acima como filtro Jinja "moeda", usável nos templates


@app.context_processor
def injetar_asset_url():
    """Gera a URL de um arquivo estático com a data de modificação como
    parâmetro (?v=...), forçando o navegador a buscar a versão nova sempre
    que o arquivo mudar, em vez de usar uma cópia antiga em cache."""
    def asset_url(filename):
        caminho = os.path.join(app.static_folder, filename)  # monta o caminho físico do arquivo dentro de /static
        try:
            versao = int(os.path.getmtime(caminho))  # usa o timestamp de última modificação como "versão" do arquivo
        except OSError:
            versao = 0  # se o arquivo não existir, usa uma versão fixa em vez de quebrar
        return f"{url_for('static', filename=filename)}?v={versao}"  # monta a URL final com o parâmetro de cache-busting

    return dict(asset_url=asset_url)  # disponibiliza a função asset_url() dentro de todos os templates Jinja


# ---------------------------------------------------
# TABELAS DE PREÇO
# ---------------------------------------------------

PRECOS_ESPACO = {  # preço de aluguel de cada espaço, por faixa de convidados e tipo de dia
    "garden": {
        100: {"semana": 3200.00, "fds": 4200.00},  # até 100 convidados: preço em dia de semana e fim de semana
        120: {"semana": 3500.00, "fds": 4600.00},  # até 120 convidados
        150: {"semana": 3900.00, "fds": 5100.00},  # até 150 convidados
        180: {"semana": 4300.00, "fds": 5600.00},  # até 180 convidados
        200: {"semana": 4600.00, "fds": 6000.00},  # até 200 convidados
    },
    "villa": {
        100: {"semana": 4100.00, "fds": 5400.00},  # até 100 convidados: preço em dia de semana e fim de semana
        120: {"semana": 4500.00, "fds": 5900.00},  # até 120 convidados
        150: {"semana": 5000.00, "fds": 6500.00},  # até 150 convidados
        180: {"semana": 5500.00, "fds": 7200.00},  # até 180 convidados
        200: {"semana": 5900.00, "fds": 7700.00},  # até 200 convidados
    },
}

PRECO_ALOJAMENTO = {  # preço fixo de cada tipo de alojamento
    "conjunto": 1000.00,  # alojamento em quarto conjunto
    "individual": 320.00,  # alojamento em quarto individual
}

DESCONTO_ALOJAMENTO = 0.10  # 10% de desconto no alojamento quando há locação de espaço junto

PRECO_ACAI = {  # preço por convidado do carrinho de açaí, por faixa de quantidade de convidados
    (60, 100): 20.00,  # de 60 a 100 convidados
    (101, 150): 17.00,  # de 101 a 150 convidados
    (151, 200): 15.00,  # de 151 a 200 convidados
}

PRECO_BUFFET_POR_PESSOA = 90.00  # valor cobrado por pessoa no buffet
PRECO_DJ = 2400.00  # valor fixo do serviço de DJ
PRECO_CABINE_FOTOGRAFICA = 1200.00  # valor fixo da cabine fotográfica

NOME_EXTRA = {  # nomes de exibição de cada extra, usados no ticket de orçamento
    "acai": "Carrinho de Açaí",
    "buffet": "Buffet",
    "dj": "DJ",
    "cabine": "Cabine Fotográfica",
}


# ---------------------------------------------------
# FUNÇÕES DE CÁLCULO
# ---------------------------------------------------

def arredondar_convidados(numero):
    # arredonda a quantidade exata de convidados para cima, para a faixa (degrau) de preço mais próxima
    degraus = [100, 120, 150, 180, 200]  # faixas de convidados disponíveis na tabela de preços
    for degrau in degraus:
        if numero <= degrau:
            return degrau  # retorna a primeira faixa que comporta o número de convidados
    return 200  # se passar de 200, usa a faixa máxima


def calcular_preco_espacos(espacos_escolhidos, convidados_tier, tipo_dia):
    # calcula o preço de cada espaço escolhido, para a faixa de convidados e tipo de dia informados
    detalhe = {}  # dicionário {nome_do_espaco: preco}
    for espaco in espacos_escolhidos:
        detalhe[espaco] = PRECOS_ESPACO[espaco][convidados_tier][tipo_dia]  # busca o preço na tabela
    return detalhe  # devolve o detalhamento por espaço


def calcular_preco_alojamento(alojamento_escolha, houve_locacao_espaco):
    # calcula o preço do alojamento, aplicando desconto se houver locação de espaço junto
    mapa = {  # traduz a escolha do usuário em quantidades de cada tipo de alojamento
        "nenhum": {"conjunto": 0, "individual": 0},
        "conjunto": {"conjunto": 1, "individual": 0},
        "individual": {"conjunto": 0, "individual": 1},
        "ambos": {"conjunto": 1, "individual": 1},
    }
    quantidades = mapa[alojamento_escolha]  # pega as quantidades correspondentes à escolha feita

    total = 0  # acumulador do valor total do alojamento
    for tipo, quantidade in quantidades.items():
        total += PRECO_ALOJAMENTO[tipo] * quantidade  # soma preço unitário multiplicado pela quantidade

    desconto_aplicado = False  # sinaliza se o desconto foi aplicado, para exibir no ticket
    if total > 0 and houve_locacao_espaco:
        total = total * (1 - DESCONTO_ALOJAMENTO)  # aplica os 10% de desconto sobre o total do alojamento
        desconto_aplicado = True  # marca que o desconto foi concedido

    return total, desconto_aplicado  # devolve o valor final e se houve desconto


def calcular_preco_acai(convidados_exato):
    # calcula o preço total do carrinho de açaí com base na quantidade exata de convidados
    for (inicio, fim), preco_pessoa in PRECO_ACAI.items():
        if convidados_exato >= inicio and convidados_exato <= fim:
            return preco_pessoa * convidados_exato  # multiplica o preço por pessoa pelo total de convidados
    return 0  # fora das faixas atendidas


def calcular_preco_buffet(convidados_exato):
    # calcula o preço total do buffet: valor fixo por pessoa vezes o número de convidados
    return PRECO_BUFFET_POR_PESSOA * convidados_exato


def calcular_extras(extras_escolhidos, convidados_exato):
    """
    Recebe a lista de extras marcados (ex: ["acai", "dj"]) e devolve
    um dicionário {nome_exibicao: valor} pronto pro ticket.
    """
    detalhe = {}  # dicionário final {nome do extra: valor cobrado}

    if "acai" in extras_escolhidos:
        detalhe[NOME_EXTRA["acai"]] = calcular_preco_acai(convidados_exato)  # adiciona o valor do açaí, se marcado

    if "buffet" in extras_escolhidos:
        detalhe[NOME_EXTRA["buffet"]] = calcular_preco_buffet(convidados_exato)  # adiciona o valor do buffet, se marcado

    if "dj" in extras_escolhidos:
        detalhe[NOME_EXTRA["dj"]] = PRECO_DJ  # adiciona o valor fixo do DJ, se marcado

    if "cabine" in extras_escolhidos:
        detalhe[NOME_EXTRA["cabine"]] = PRECO_CABINE_FOTOGRAFICA  # adiciona o valor fixo da cabine, se marcada

    return detalhe  # devolve todos os extras escolhidos com seus valores


# ---------------------------------------------------
# ROTAS
# ---------------------------------------------------

@app.route("/")
def pagina_inicial():
    # rota da página inicial (home)
    return render_template("home.html")  # renderiza o template home.html


@app.route("/orcamento")
def pagina_orcamento():
    # rota que exibe o formulário de orçamento vazio (sem resultado calculado ainda)
    return render_template("orcamento.html", resultado=None, form_data=None, erro=None)


@app.route("/lead", methods=["POST"])
def registrar_lead():
    # rota de API chamada via JS para salvar os dados de contato de um lead interessado
    dados = request.get_json(silent=True) or {}  # lê o corpo JSON da requisição; usa {} se vier vazio/inválido
    nome = (dados.get("nome") or "").strip()  # extrai o nome, removendo espaços extras
    telefone = (dados.get("telefone") or "").strip()  # extrai o telefone, removendo espaços extras
    email = (dados.get("email") or "").strip()  # extrai o e-mail, removendo espaços extras

    if not nome or not telefone or not email:
        return jsonify({"ok": False, "erro": "dados incompletos"}), 400  # rejeita se faltar algum campo obrigatório

    arquivo_novo = not os.path.exists(LEADS_FILE)  # verifica se o CSV ainda não existe, para saber se precisa do cabeçalho
    with open(LEADS_FILE, "a", newline="", encoding="utf-8") as f:  # abre o CSV em modo de anexar (append)
        writer = csv.writer(f)  # cria o escritor de CSV
        if arquivo_novo:
            writer.writerow(["data_hora", "nome", "telefone", "email"])  # escreve o cabeçalho apenas na primeira vez
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nome, telefone, email])  # grava a linha do lead

    return jsonify({"ok": True})  # confirma o sucesso para o JS que fez a chamada


FOTOS_GALERIA = [  # lista de fotos exibidas na página de galeria completa, cada uma com caminho e texto alternativo
    {"src": "img/final/hero.jpg", "alt": "Área externa decorada para evento ao entardecer"},
    {"src": "img/final/garden.jpg", "alt": "Piscina e jardim do Espaço Garden"},
    {"src": "img/final/villa.jpg", "alt": "Salão coberto da Villa"},
    {"src": "img/final/gallery-entrada.jpg", "alt": "Entrada decorada com painel de folhas naturais"},
    {"src": "img/final/gallery-festa.jpg", "alt": "Mesa de bolo decorada para festa de debutante"},
    {"src": "img/gallery/jantar-jardim.jpg", "alt": "Jantar ao ar livre no jardim, com mesas postas ao entardecer"},
    {"src": "img/gallery/salao-decorado.jpg", "alt": "Salão coberto decorado com arco de balões dourados"},
    {"src": "img/gallery/mesa-decorada.jpg", "alt": "Mesa posta com decoração de flores secas"},
    {"src": "img/gallery/pista-danca.jpg", "alt": "Pista de dança iluminada durante a festa à noite"},
    {"src": "img/gallery/arco-floral.jpg", "alt": "Arco floral e corredor de mesas ao entardecer"},
    {"src": "img/gallery/mesa-detalhe.jpg", "alt": "Detalhe de mesa posta com guardanapo vermelho"},
    {"src": "img/gallery/jardim-arvore.jpg", "alt": "Área verde e arborizada do espaço"},
    {"src": "img/gallery/mesa-bolo.jpg", "alt": "Mesa de bolo decorada com flores secas"},
    {"src": "img/gallery/noiva-mesa.jpg", "alt": "Debutante ao lado da mesa de bolo decorada"},
    {"src": "img/gallery/gramado-palmeiras.jpg", "alt": "Gramado amplo cercado de palmeiras"},
    {"src": "img/gallery/pista-vista.jpg", "alt": "Vista elevada da pista de dança e mesas do salão"},
    {"src": "img/gallery/salao-mesas.jpg", "alt": "Mesas decoradas no salão durante a festa"},
    {"src": "img/gallery/margaridas1.jpg", "alt": "Margaridas em primeiro plano com decoração ao fundo"},
    {"src": "img/gallery/margaridas2.jpg", "alt": "Margaridas próximas à entrada decorada"},
    {"src": "img/gallery/varanda-entardecer.jpg", "alt": "Varanda coberta com mesas postas ao entardecer"},
    {"src": "img/gallery/mesa-janela.jpg", "alt": "Mesa posta próxima à janela do salão"},
    {"src": "img/gallery/bolo-ambiente.jpg", "alt": "Ambiente decorado com mesa de bolo ao fundo"},
    {"src": "img/gallery/salao-noite.jpg", "alt": "Salão iluminado durante a festa à noite"},
    {"src": "img/gallery/caminho-jardim.jpg", "alt": "Caminho de pedras entre o jardim arborizado"},
    {"src": "img/gallery/noiva-salao.jpg", "alt": "Debutante no salão decorado para a festa"},
    {"src": "img/gallery/salao-led.jpg", "alt": "Salão decorado com painel de luzes coloridas"},
    {"src": "img/gallery/entrada-noite.jpg", "alt": "Fachada do espaço iluminada à noite"},
]


@app.route("/galeria")
def pagina_galeria():
    # rota da página de galeria completa; passa a lista de fotos para o template
    return render_template("galeria.html", fotos=FOTOS_GALERIA)


FOTOS_GARDEN = [  # fotos usadas no carrossel do espaço Garden, na página de espaços
    {"src": "img/final/hero.jpg", "alt": "Área externa decorada para evento ao entardecer"},
    {"src": "img/final/garden.jpg", "alt": "Piscina e jardim do Espaço Garden"},
    {"src": "img/gallery/jantar-jardim.jpg", "alt": "Jantar ao ar livre no jardim, com mesas postas ao entardecer"},
    {"src": "img/gallery/mesa-decorada.jpg", "alt": "Mesa posta com decoração de flores secas no jardim"},
    {"src": "img/gallery/arco-floral.jpg", "alt": "Arco floral e corredor de mesas ao entardecer"},
    {"src": "img/gallery/jardim-arvore.jpg", "alt": "Área verde e arborizada do jardim"},
    {"src": "img/gallery/gramado-palmeiras.jpg", "alt": "Gramado amplo cercado de palmeiras"},
    {"src": "img/gallery/caminho-jardim.jpg", "alt": "Caminho de pedras entre o jardim arborizado"},
    {"src": "img/final/gallery-entrada.jpg", "alt": "Entrada decorada com painel de folhas naturais"},
    {"src": "img/gallery/margaridas1.jpg", "alt": "Margaridas em primeiro plano com decoração ao fundo"},
]

FOTOS_VILLA = [  # fotos usadas no carrossel do espaço Villa, na página de espaços
    {"src": "img/final/villa.jpg", "alt": "Salão coberto da Villa"},
    {"src": "img/gallery/salao-decorado.jpg", "alt": "Salão coberto decorado com arco de balões dourados"},
    {"src": "img/gallery/pista-danca.jpg", "alt": "Pista de dança iluminada durante a festa à noite"},
    {"src": "img/gallery/mesa-detalhe.jpg", "alt": "Detalhe de mesa posta com guardanapo vermelho"},
    {"src": "img/gallery/mesa-bolo.jpg", "alt": "Mesa de bolo decorada com flores secas"},
    {"src": "img/gallery/noiva-mesa.jpg", "alt": "Debutante ao lado da mesa de bolo decorada"},
    {"src": "img/gallery/pista-vista.jpg", "alt": "Vista elevada da pista de dança e mesas do salão"},
    {"src": "img/gallery/salao-mesas.jpg", "alt": "Mesas decoradas no salão durante a festa"},
    {"src": "img/gallery/mesa-janela.jpg", "alt": "Mesa posta próxima à janela do salão"},
    {"src": "img/gallery/bolo-ambiente.jpg", "alt": "Ambiente decorado com mesa de bolo ao fundo"},
]

SERVICOS_ADICIONAIS = [  # dados dos cards de serviços adicionais exibidos na página de espaços
    {"nome": "Carrinho de Açaí", "icone": "🍧", "descricao": "Carrinho temático servindo açaí na hora, com montagem de toppings à escolha dos convidados.", "preco": "Cobrado por convidado"},
    {"nome": "Buffet", "icone": "🍽️", "descricao": "Cardápio completo sob medida para o seu evento, do entra e sai ao jantar servido.", "preco": "Cobrado por pessoa"},
    {"nome": "DJ", "icone": "🎧", "descricao": "Som profissional e trilha sonora personalizada para animar a pista a noite toda.", "preco": "Valor fixo"},
    {"nome": "Cabine Fotográfica", "icone": "📸", "descricao": "Cabine com props e impressão na hora — uma lembrança divertida para os convidados levarem para casa.", "preco": "Valor fixo"},
]


@app.route("/espacos")
def pagina_espacos():
    # rota da página de espaços; envia as fotos de cada espaço e a lista de serviços adicionais
    return render_template(
        "espacos.html",
        fotos_garden=FOTOS_GARDEN,
        fotos_villa=FOTOS_VILLA,
        servicos=SERVICOS_ADICIONAIS,
    )


@app.route("/calcular", methods=["POST"])
def calcular():
    # rota que recebe o formulário de orçamento e devolve a página com o resultado calculado
    convidados_raw = request.form.get("convidados", "")  # quantidade de convidados digitada (texto)
    dia = request.form.get("dia", "")  # tipo de dia escolhido: "semana" ou "fds"
    espacos = request.form.getlist("espacos")  # lista de espaços marcados (checkboxes)
    alojamento_escolha = request.form.get("alojamento", "nenhum")  # opção de alojamento selecionada
    extras = request.form.getlist("extras")  # lista de extras marcados (checkboxes)

    form_data = {  # guarda os dados enviados para reexibir o formulário preenchido em caso de erro
        "convidados": convidados_raw,
        "dia": dia,
        "espacos": espacos,
        "alojamento": alojamento_escolha,
        "extras": extras,
    }

    if not convidados_raw or not dia or not espacos:
        return render_template(  # se faltar campo obrigatório, reexibe o formulário com mensagem de erro
            "orcamento.html", resultado=None, form_data=form_data,
            erro="Preencha convidados, dia e ao menos um espaço."
        )

    convidados_exato = int(convidados_raw)  # converte a quantidade de convidados de texto para número
    convidados_tier = arredondar_convidados(convidados_exato)  # arredonda para a faixa de preço correspondente

    espacos_detalhe = calcular_preco_espacos(espacos, convidados_tier, dia)  # preço de cada espaço escolhido
    total_espacos = sum(espacos_detalhe.values())  # soma o preço de todos os espaços escolhidos

    total_alojamento, desconto_aplicado = calcular_preco_alojamento(
        alojamento_escolha, houve_locacao_espaco=len(espacos) > 0
    )  # calcula o preço do alojamento, com desconto se houve locação de espaço

    extras_detalhe = calcular_extras(extras, convidados_exato)  # preço de cada extra escolhido
    total_extras = sum(extras_detalhe.values())  # soma o preço de todos os extras escolhidos

    resultado = {  # dados finais que serão exibidos no ticket de orçamento
        "convidados_tier": convidados_tier,
        "tipo_dia": dia,
        "espacos_detalhe": espacos_detalhe,
        "total_alojamento": total_alojamento,
        "desconto_aplicado": desconto_aplicado,
        "extras_detalhe": extras_detalhe,
        "total": total_espacos + total_alojamento + total_extras,  # soma geral do orçamento
    }

    return render_template("orcamento.html", resultado=resultado, form_data=form_data, erro=None)  # exibe o resultado


if __name__ == "__main__":
    app.run(debug=True)  # inicia o servidor Flask em modo debug (recarrega sozinho e mostra erros detalhados)
