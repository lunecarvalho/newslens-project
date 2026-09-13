"""Conteúdo institucional do NewsLens, separado da inferência."""

from base64 import b64encode
from pathlib import Path

import streamlit as st


def criar_icone_sobre(nome):
    desenhos = {
        "missao": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/><path d="m12 12 9-9m-5 0h5v5"/>',
        "tecnologia": '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4m6-4v4M9 18v4m6-4v4M2 9h4m-4 6h4m12-6h4m-4 6h4M10 10h4v4h-4z"/>',
        "responsabilidade": '<path d="M12 2 3 6v6c0 5 9 10 9 10s9-5 9-10V6l-9-4ZM8 12l3 3 5-6"/>',
    }
    desenho = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#205bad" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{desenhos[nome]}</svg>'
    imagem = b64encode(desenho.encode("utf-8")).decode("ascii")
    return f'<img src="data:image/svg+xml;base64,{imagem}" width="32" height="32" alt="">'


def exibir_pagina_sobre(icone_lupa, navegar_para):
    caminho_estilos = Path(__file__).parent / "assets" / "sobre.css"
    st.markdown(f"<style>{caminho_estilos.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    cards = [
        ("missao", "Missão", "Auxiliar na análise de notícias por meio de Inteligência Artificial, tornando a identificação de padrões linguísticos mais acessível e transparente."),
        ("tecnologia", "Tecnologia", "Python · NLP · BERTimbau · Transformers · PyTorch · Streamlit"),
        ("responsabilidade", "Responsabilidade", "O resultado é apresentado como uma classificação acompanhada da confiança do modelo, incentivando a consulta a fontes confiáveis antes do compartilhamento."),
    ]
    etapas = [
        ("Inserção do conteúdo", "O usuário insere o texto da notícia para análise. O conteúdo é preparado para ser processado pelo modelo."),
        ("Preparação do texto", "O conteúdo passa pelas etapas necessárias de preparação e tokenização para utilização pelo modelo de linguagem."),
        ("Classificação com BERTimbau", "O texto é analisado por um modelo BERTimbau ajustado para classificação binária de notícias do Fake BR Corpus."),
        ("Resultado e confiança", "O NewsLens apresenta a classificação como possivelmente falsa ou possivelmente verdadeira, acompanhada do nível de confiança atribuído pelo modelo."),
    ]
    perguntas = [
        ("O NewsLens substitui a verificação humana?", "Não. O NewsLens realiza uma classificação baseada em padrões aprendidos pelo modelo. O resultado não confirma se uma informação é factualmente verdadeira ou falsa. Sempre consulte fontes confiáveis antes de compartilhar uma notícia.", ""),
        ("Quais idiomas são suportados?", "O modelo foi desenvolvido para analisar textos em português brasileiro. Conteúdos em outros idiomas estão fora do escopo de treinamento e podem produzir resultados não confiáveis.", ""),
        ("Os textos inseridos são armazenados?", "O NewsLens não mantém um histórico das análises nem armazena permanentemente os textos enviados para classificação.", ""),
        ("Qual é o desempenho do modelo?", "Na avaliação final realizada com 720 textos do conjunto de teste do Fake BR Corpus, o modelo obteve 99,44% de acurácia, classificando corretamente 716 exemplos.", "Esse resultado representa o desempenho no conjunto de teste utilizado no projeto e não garante a mesma precisão em notícias de outras fontes, períodos ou contextos."),
    ]
    conteudo_cards = "".join(
        f'<article class="sobre-card">{criar_icone_sobre(icone)}<h2>{titulo}</h2><p>{texto}</p></article>'
        for icone, titulo, texto in cards
    )
    conteudo_etapas = "".join(
        f'<li class="sobre-etapa"><span class="sobre-numero">{numero:02d}</span><div><h3>{titulo}</h3><p>{texto}</p></div></li>'
        for numero, (titulo, texto) in enumerate(etapas, start=1)
    )
    conteudo_perguntas = "".join(
        f'<article class="sobre-faq-item"><h3>{pergunta}</h3><p>{resposta}</p>'
        + (f'<p class="sobre-nota">{nota}</p>' if nota else "") + '</article>'
        for pergunta, resposta, nota in perguntas
    )
    with st.container(key="sobre_container"):
        st.button("← Voltar", key="sobre_voltar", type="tertiary", on_click=navegar_para, args=("inicio",))
        st.markdown(f'''
            <main class="sobre-pagina">
                <div class="sobre-titulo">{icone_lupa}<h1>Sobre o NewsLens</h1></div>
                <section class="sobre-introducao" aria-label="Apresentação">
                    <p>O <strong>NewsLens</strong> é uma ferramenta de análise de notícias desenvolvida para identificar padrões linguísticos associados a conteúdos falsos e verdadeiros. Utilizando técnicas de <strong>Processamento de Linguagem Natural (PLN)</strong> e <strong>Inteligência Artificial</strong>, o sistema classifica o texto informado com base nos padrões aprendidos pelo modelo.</p>
                    <p>O resultado representa uma predição do modelo e não uma verificação factual da notícia. Por isso, o NewsLens deve ser utilizado como ferramenta de apoio à análise, e não como substituto de fontes jornalísticas ou serviços profissionais de checagem de fatos.</p>
                </section>
                <section class="sobre-cards" aria-label="Princípios do NewsLens">{conteudo_cards}</section>
                <section class="sobre-como-funciona"><div class="sobre-titulo-secao" role="heading" aria-level="2">COMO FUNCIONA</div><ol class="sobre-timeline">{conteudo_etapas}</ol></section>
                <section class="sobre-faq"><div class="sobre-titulo-secao" role="heading" aria-level="2">PERGUNTAS FREQUENTES</div>{conteudo_perguntas}</section>
            </main>
        '''.replace('\n', ''), unsafe_allow_html=True)
