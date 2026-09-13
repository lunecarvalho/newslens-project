import streamlit as st

from model import classificar_noticia

st.set_page_config(
    page_title="NewsLens",
    page_icon="📰",
    layout="centered"
)

st.title("NewsLens")

st.write(
    "Analise padrões linguísticos de uma notícia "
    "utilizando Inteligência Artificial."
)

texto = st.text_area(
    "Insira o texto da notícia:",
    height=250,
    placeholder="Cole aqui o conteúdo da notícia..."
)

if st.button("Analisar notícia"):
    if not texto.strip():
        st.warning("Insira um texto antes de realizar a análise.")
    else:
        with st.spinner("Analisando notícia..."):
            resultado = classificar_noticia(texto)

        st.subheader("Resultado")

        if resultado == "Falsa":
            st.error("Possivelmente falsa")
        else:
            st.success("Possivelmente verdadeira")

        st.caption(
            "O resultado representa uma classificação do modelo "
            "e não substitui uma verificação factual em fontes confiáveis."
        )