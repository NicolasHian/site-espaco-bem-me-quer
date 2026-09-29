# Espaço Bem Me Quer — Garden & Villa

Site do trabalho de D.I para o espaço de eventos "Bem Me Quer" (Garden & Villa), feito com Python (Flask) no back-end e HTML/CSS/JS no front-end.

---

## 1. O que eu fiz

Fiquei responsável pela **Home Page** (`templates/home.html`, `static/style.css` e `static/home.js`). Ela inclui:

- Tela de carregamento inicial (loader com animação de "cortina")
- Menu fixo no topo que muda de aparência ao rolar a página + barra de progresso de leitura
- Rolagem suave com inércia (smooth scroll)
- Seção "Sobre" com contadores animados (números que sobem)
- Cards dos espaços Garden e Villa, seção de serviços adicionais e prévia da galeria
- Efeitos de paralaxe, "pétalas" seguindo o cursor, botões magnéticos e animações de entrada ao rolar (scroll reveal)
- Lightbox (visualização ampliada) para as fotos da galeria

## 2. Sobre o uso de IA

Sim, usei IA (**Claude Code**) como apoio, principalmente para me ajudar a construir as **animações** (loader, scroll reveal, parallax, contadores, efeitos de cursor etc.) em `static/home.js` e `static/style.css`. A estrutura, o conteúdo e as decisões do site foram guiadas por mim — a IA foi usada como ferramenta de apoio, não para "fazer o trabalho sozinha".

## 3. O que é cada pasta/arquivo

```
home/
├── app.py                → servidor Flask: rotas do site e a lógica da calculadora de orçamento
├── templates/             → páginas HTML (renderizadas pelo Flask com Jinja2)
│   └── home.html          → a Home Page
├── static/                → arquivos estáticos servidos direto pelo navegador
│   ├── style.css          → todo o CSS do site (visual, cores, animações)
│   ├── home.js            → todo o JavaScript da Home Page (as animações e interações)
│   └── img/                → imagens usadas no site
│       ├── final/          → fotos "principais" (hero, garden, villa, destaques da galeria)
│       └── gallery/        → demais fotos da galeria completa
├── .venv/                 → ambiente virtual Python (não sobe pro Git, veja o .gitignore)
├── __pycache__/           → cache do Python (gerado automaticamente, ignorar)
└── .gitignore             → arquivos/pastas que o Git deve ignorar
```

> Observação: `app.py` já referencia outras páginas (`orcamento.html`, `espacos.html`, `galeria.html`), mas esses templates ainda precisam ser criados por quem ficar responsável por eles — hoje só existe o `home.html`.

## 4. Sobre o `app.py`

O `app.py` **já tem pronta toda a lógica da calculadora de orçamento** (tabelas de preço do Garden e da Villa, alojamento com desconto, carrinho de açaí, buffet, DJ, cabine fotográfica, etc.) e as rotas do Flask (`/`, `/espacos`, `/galeria`, `/orcamento`, `/calcular`, `/lead`). Ou seja, a parte de cálculo já está funcionando — falta principalmente montar o HTML das páginas que ainda não existem (`orcamento.html`, `espacos.html`, `galeria.html`) usando os dados que o `app.py` já envia pra elas.

## 5. Como baixar e rodar em qualquer computador

Pré-requisito: ter **Python 3** instalado ([python.org](https://www.python.org/downloads/)).

```bash
# 1. Clonar o repositório
git clone https://github.com/NicolasHian/Trabalho-D.I.git
cd Trabalho-D.I/home

# 2. Criar e ativar um ambiente virtual
python -m venv .venv

# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (cmd):
.venv\Scripts\activate.bat
# Linux/Mac:
source .venv/bin/activate

# 3. Instalar o Flask
pip install flask

# 4. Rodar o servidor
python app.py
```

Depois é só abrir **http://127.0.0.1:5000** no navegador. Qualquer alteração no código reinicia o servidor sozinho (modo debug já está ligado).

## 6. Podem usar IA também

Podem usar IA para ajudar no que for preciso, igual eu usei. Só que eu usei de um jeito específico: com um **prompt de "professor"** (que guia a IA a explicar e ensinar em vez de só entregar o código pronto). Se vocês quiserem usar esse mesmo prompt, é só **me chamar** que eu passo pra vocês.

## 7. Dúvidas

Qualquer dúvida sobre o código, a estrutura ou como rodar o projeto, podem me chamar direto no WhatsApp/grupo.
