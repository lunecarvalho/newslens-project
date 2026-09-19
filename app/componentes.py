from base64 import b64encode
from pathlib import Path

import streamlit as st


def exibir_tela_analisando(icone_lupa):
    """Feedback visual independente das operações internas do classificador."""
    caminho_estilos = Path(__file__).parent / "assets" / "analisando.css"
    st.markdown(f"<style>{caminho_estilos.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    etapas = ("Obtendo conteúdo...", "Preparando texto...", "Aplicando o modelo...", "Gerando classificação...")
    lista_etapas = "".join(
        f'<li class="analisando-etapa analisando-etapa-{indice}">'
        '<span class="analisando-marcador" aria-hidden="true">'
        '<span class="analisando-ativo">●</span><span class="analisando-concluido">✓</span>'
        f'</span><span>{etapa}</span></li>'
        for indice, etapa in enumerate(etapas, start=1)
    )
    barras = "".join('<span></span>' for _ in range(9))
    st.markdown(f'''
        <main class="analisando-pagina" aria-busy="true">
            <div class="analisando-conteudo">
                <div class="analisando-lupa" aria-hidden="true">
                    <span class="analisando-orbita"></span>
                    <span class="analisando-orbita analisando-orbita-interna"></span>
                    {icone_lupa}
                </div>
                <h1 role="status">Analisando notícia...</h1>
                <p>O NewsLens está processando o conteúdo e identificando padrões linguísticos.</p>
                <div class="analisando-barras" aria-hidden="true">{barras}</div>
                <ol class="analisando-etapas" aria-label="Etapas da análise">{lista_etapas}</ol>
            </div>
        </main>
    '''.replace('\n', ''), unsafe_allow_html=True)


def formatar_percentual(score):
    return f"{score * 100:.2f}%".replace(".", ",")


def criar_indicador_confianca(confianca, estado):
    percentual = confianca * 100
    cor = "#e83a43" if estado == "falsa" else "#12a64c"
    desenho = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 220">
        <style>
            .progresso {{ animation: preencher 1.5s ease-out both; }}
            @keyframes preencher {{ from {{ stroke-dashoffset: 100; }} to {{ stroke-dashoffset: {100 - percentual:.8f}; }} }}
            @media (prefers-reduced-motion: reduce) {{ .progresso {{ animation: none; }} }}
        </style>
        <circle cx="110" cy="110" r="100" fill="none" stroke="#e4e2f1" stroke-width="14"/>
        <circle class="progresso" cx="110" cy="110" r="100" fill="none" stroke="{cor}"
            stroke-width="14" stroke-linecap="round" pathLength="100" stroke-dasharray="100"
            stroke-dashoffset="{100 - percentual:.8f}" transform="rotate(-90 110 110)"/>
    </svg>'''
    imagem = b64encode(desenho.encode("utf-8")).decode("ascii")
    return f'''
        <div class="indicador-confianca" style="--resultado-percentual: {percentual:.8f};"
             role="img" aria-label="Confiança do modelo: {formatar_percentual(confianca)}">
            <img class="anel-confianca" src="data:image/svg+xml;base64,{imagem}" alt="" width="220" height="220">
            <div class="centro-confianca" aria-hidden="true">
                <span class="numero-confianca">{formatar_percentual(confianca)}</span>
                <span class="rotulo-confianca">Confiança</span>
            </div>
        </div>
    '''


def criar_detalhes_analise(resultado):
    detalhes = [
        ("Confiança", formatar_percentual(resultado["confianca"])),
        ("Método", "Análise de URL" if st.session_state.get("metodo_analise") == "url" else "Análise de texto"),
        ("Processamento", "NLP + ML"),
    ]
    cards = "".join(
        f'<div class="detalhe-analise"><span>{rotulo}</span><strong>{valor}</strong></div>'
        for rotulo, valor in detalhes
    )
    return f'<section class="secao-detalhes"><h2>DETALHES DA ANÁLISE</h2><div class="grade-detalhes">{cards}</div></section>'


def criar_distribuicao_predicoes(resultado):
    barras = ""
    for classe, rotulo, score in [
        ("verdadeira", "Possivelmente verdadeira", resultado["score_verdadeira"]),
        ("falsa", "Possivelmente falsa", resultado["score_falsa"]),
    ]:
        percentual = formatar_percentual(score)
        barras += f'''
            <div class="predicao {classe}">
                <div class="rotulo-predicao"><span>{rotulo}</span><span>{percentual}</span></div>
                <div class="trilha-predicao" role="meter" aria-label="Score do modelo: {rotulo}"
                     aria-valuemin="0" aria-valuemax="100" aria-valuenow="{score * 100:.8f}">
                    <div class="barra-predicao" style="width: {score * 100:.8f}%"></div>
                </div>
            </div>
        '''
    return f'''
        <section class="distribuicao-predicoes">
            <h2>DISTRIBUIÇÃO DAS PREDIÇÕES</h2>{barras}
            <p class="nota-scores">Scores do classificador, não probabilidades factuais calibradas.</p>
        </section>
    '''


def criar_aviso():
    desenho = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#dc8500" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3 10 18H2L12 3Zm0 6v5m0 3v.1"/></svg>'
    icone = b64encode(desenho.encode("utf-8")).decode("ascii")
    return f'''
        <aside class="aviso-resultado">
            <img src="data:image/svg+xml;base64,{icone}" alt="" width="20" height="20">
            <div><h2>Atenção</h2>
                <p>O resultado é uma predição realizada pelo modelo e não substitui a verificação das informações em fontes confiáveis. Consulte veículos jornalísticos de referência antes de compartilhar.</p>
            </div>
        </aside>
    '''


def nova_analise():
    for chave in ("resultado_analise", "texto_analisado", "texto_noticia", "resultado",
                  "url_noticia", "url_analisada", "metodo_analise", "erro_analise"):
        st.session_state.pop(chave, None)
    st.session_state.pagina_atual = "inicio"


def exibir_tela_resultado(resultado):
    classe = resultado["classe"]
    if classe not in ("Falsa", "Verdadeira"):
        raise ValueError("Classe não reconhecida pelo componente de resultado.")
    estado = "falsa" if classe == "Falsa" else "verdadeira"
    titulo = f"Provavelmente {estado}"
    tipo_conteudo = "falsos" if classe == "Falsa" else "verdadeiros"
    percentual = formatar_percentual(resultado["confianca"])

    caminho_estilos = Path(__file__).parent / "assets" / "resultado.css"
    st.markdown(f"<style>{caminho_estilos.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

    with st.container(key="tela_resultado"):
        st.button("← Nova análise", key="nova_analise", type="tertiary", on_click=nova_analise)
        st.markdown(f'''
            <main class="resultado-pagina resultado-analise {estado}">
                <h1>Resultado da análise</h1>
                <section class="card-resultado" aria-label="Classificação do modelo">
                    {criar_indicador_confianca(resultado["confianca"], estado)}
                    <div class="descricao-resultado">
                        <span class="pill-resultado">• {titulo}</span>
                        <h2>{titulo}</h2>
                        <p class="percentual-resultado">{percentual} de confiança</p>
                        <p class="explicacao-resultado">O modelo identificou características linguísticas e padrões semelhantes aos presentes em conteúdos classificados como {tipo_conteudo} no conjunto de treinamento.</p>
                    </div>
                </section>
                {criar_detalhes_analise(resultado)}
                {criar_distribuicao_predicoes(resultado)}
                {criar_aviso()}
            </main>
        '''.replace('\n', ''), unsafe_allow_html=True)
