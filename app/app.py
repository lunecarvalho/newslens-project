from pathlib import Path
import time
from base64 import b64encode
import streamlit as st
from sobre import exibir_pagina_sobre

from componentes import (
    exibir_tela_analisando,
    exibir_tela_resultado,
)


DURACAO_SPLASH = 1.0
DURACAO_MINIMA_ANALISE = 1.5

st.set_page_config(page_title="NewsLens", page_icon=":material/search:", layout="wide")


def carregar_estilos():
    caminho_estilos = Path(__file__).parent / "assets" / "style.css"
    st.html(f"<style>{caminho_estilos.read_text(encoding='utf-8')}</style>")


def criar_icone(nome, classe="icone"):
    desenhos = {
        "lupa": '<circle cx="10.5" cy="10.5" r="3.5" fill="#d5e5f4" stroke="none"/><circle cx="10.5" cy="10.5" r="7" stroke-width="1.9"/><path d="m16 16 5 5" stroke="#2272ca" stroke-width="2.2"/>',
        "ia": '<path d="M12 5c-2-4-6-2-6 1-3 0-4 4-2 6-2 3 0 6 3 6 0 4 5 4 5 0V5Zm0 0c2-4 6-2 6 1 3 0 4 4 2 6 2 3 0 6-3 6 0 4-5 4-5 0M6 6l2 2m-4 4h3m0 6 1-3m10-9-2 2m4 4h-3m0 6-1-3"/>',
        "texto": '<path d="M5 3h9l5 5v13H5zM14 3v5h5M8 12h8m-8 4h8M8 8h2"/>',
        "classificacao": '<path d="M4 3v17h17M7 13l4-5 4 4 5-5"/>',
    }
    desenho_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2064b6" '
        'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true">{desenhos[nome]}</svg>'
    )
    imagem_codificada = b64encode(desenho_svg.encode("utf-8")).decode("ascii")
    return f'<img class="{classe}" src="data:image/svg+xml;base64,{imagem_codificada}" alt="" aria-hidden="true">'


def exibir_abertura():
    if not st.session_state.get("tela_abertura_exibida", False):
        st.html(f'''
            <section class="abertura" aria-label="Bem-vindo ao NewsLens">
                <div class="abertura-conteudo">
                    {criar_icone("lupa")}
                    <h1>NewsLens</h1>
                    <p>ANALISE · ENTENDA · VERIFIQUE</p>
                </div>
            </section>
        ''')
        time.sleep(DURACAO_SPLASH)
        st.session_state.tela_abertura_exibida = True
        st.rerun()


def navegar_para(pagina):
    st.session_state.pagina_atual = pagina


def exibir_cabecalho():
    caminho_estilos = Path(__file__).parent / "assets" / "navegacao.css"
    st.markdown(f"<style>{caminho_estilos.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    pagina_ativa = "sobre" if st.session_state.get("pagina_atual") == "sobre" else "inicio"
    with st.container(key="cabecalho_navegavel", horizontal=True, vertical_alignment="center"):
        st.html(f'<div class="marca-navegavel">{criar_icone("lupa")}<span>NewsLens</span></div>')
        with st.container(key=f"menu_{pagina_ativa}", horizontal=True, width="content", gap="small"):
            st.button("Início", key="navegar_inicio", type="tertiary", on_click=navegar_para, args=("inicio",))
            st.button("Sobre", key="navegar_sobre", type="tertiary", on_click=navegar_para, args=("sobre",))


def exibir_formulario():
    aba_url, aba_texto = st.tabs(
        ["URL da notícia", "Texto da notícia"], default="Texto da notícia"
    )
    with aba_url:
        with st.container(border=True, key="cartao_url"):
            st.text_input(
                "URL DA NOTÍCIA", placeholder="https://exemplo.com/noticia",
                disabled=True, icon=":material/language:",
            )
            st.button(
                "Analisar URL", disabled=True, type="primary", width="stretch",
                help="Em breve", icon=":material/arrow_forward:", icon_position="right",
            )
    with aba_texto:
        with st.form("formulario_noticia", border=True):
            texto_noticia = st.text_area(
                "TEXTO DA NOTÍCIA",
                height=230,
                placeholder="Cole aqui o texto da notícia que deseja analisar...",
                key="texto_noticia",
            )
            analisar = st.form_submit_button(
                "Analisar notícia", type="primary", width="stretch"
            )
        if analisar:
            st.session_state.pop("resultado_analise", None)
            if not texto_noticia.strip():
                st.warning("Insira o texto da notícia para iniciar a análise.")
            else:
                st.session_state.texto_analisado = texto_noticia
                st.session_state.pagina_atual = "analisando"
                st.rerun()


def exibir_cards_informativos():
    informacoes = [
        ("ia", "Análise com IA", "Processamento automatizado com modelos de linguagem modernos."),
        ("texto", "Análise linguística", "Identificação de padrões e marcadores presentes no texto."),
        ("classificacao", "Resultado probabilístico", "Classificação acompanhada do nível de confiança do modelo."),
    ]
    cards = "".join(
        f'<article class="card-informativo"><div class="icone-card">{criar_icone(icone)}</div>'
        f'<h2><strong>{titulo}</strong></h2><p>{descricao}</p></article>'
        for icone, titulo, descricao in informacoes
    )
    st.html(f'<section class="cards-informativos" aria-label="Como funciona">{cards}</section>')


def exibir_rodape():
    st.html('<footer class="rodape">NewsLens · Projeto Integrador IV · UNIVESP · 2026</footer>')


carregar_estilos()
exibir_abertura()
if st.session_state.get("pagina_atual", "inicio") == "resultado":
    exibir_tela_resultado(st.session_state.resultado_analise)
elif st.session_state.get("pagina_atual") == "sobre":
    exibir_cabecalho()
    exibir_pagina_sobre(criar_icone("lupa", "sobre-titulo-icone"), navegar_para)
elif st.session_state.get("pagina_atual") == "analisando":
    inicio_analise = time.perf_counter()
    exibir_cabecalho()
    exibir_tela_analisando(criar_icone("lupa"))
    try:
        from model import classificar_noticia

        resultado_analise = classificar_noticia(st.session_state.texto_analisado)
    except Exception:
        st.session_state.erro_analise = True
        st.session_state.pagina_atual = "inicio"
    else:
        tempo_decorrido = time.perf_counter() - inicio_analise
        tempo_restante = max(0.0, DURACAO_MINIMA_ANALISE - tempo_decorrido)
        if tempo_restante > 0:
            time.sleep(tempo_restante)
        st.session_state.resultado_analise = resultado_analise
        st.session_state.pagina_atual = "resultado"
    st.rerun()
else:
    exibir_cabecalho()
    with st.container(key="conteudo_principal"):
        st.html('''
            <section class="introducao" id="inicio">
                <h1>Analise uma notícia</h1>
                <p>Insira o texto ou a URL da notícia para verificar a veracidade do conteúdo com IA.</p>
            </section>
        ''')
        if st.session_state.pop("erro_analise", False):
            st.error("Não foi possível concluir a análise. Tente novamente em instantes.")
        exibir_formulario()
        exibir_cards_informativos()

exibir_rodape()
