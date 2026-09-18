import torch
import streamlit as st
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODELO = "lunecarvalho/newslens-bertimbau"


@st.cache_resource
def carregar_modelo():
    tokenizer = AutoTokenizer.from_pretrained(MODELO)
    modelo = AutoModelForSequenceClassification.from_pretrained(MODELO)
    modelo.eval()
    return tokenizer, modelo


def classificar_noticia(texto):
    if not isinstance(texto, str):
        raise TypeError("O texto da notícia deve ser uma string.")
    if not texto.strip():
        raise ValueError("O texto da notícia não pode estar vazio.")

    tokenizer, modelo = carregar_modelo()
    entradas = tokenizer(
        texto,
        return_tensors="pt",
        truncation=True,
        max_length=512
    )

    with torch.no_grad():
        saida = modelo(**entradas)

    classe = torch.argmax(saida.logits, dim=1).item()

    classes = {
        0: "Falsa",
        1: "Verdadeira"
    }

    scores = torch.softmax(saida.logits, dim=1)[0]

    return {
        "classe": classes[classe],
        "confianca": scores[classe].item(),
        "score_falsa": scores[0].item(),
        "score_verdadeira": scores[1].item(),
    }


if __name__ == "__main__":
    texto_teste = """
    O governo anunciou nesta quarta-feira uma nova medida
    voltada ao setor da educação.
    """

    resultado = classificar_noticia(texto_teste)

    print(f"Resultado: {resultado}")
