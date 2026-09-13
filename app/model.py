import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODELO = "lunecarvalho/newslens-bertimbau"

tokenizer = AutoTokenizer.from_pretrained(MODELO)

modelo = AutoModelForSequenceClassification.from_pretrained(MODELO)

modelo.eval()


def classificar_noticia(texto):
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

    return classes[classe]


if __name__ == "__main__":
    texto_teste = """
    O governo anunciou nesta quarta-feira uma nova medida
    voltada ao setor da educação.
    """

    resultado = classificar_noticia(texto_teste)

    print(f"Resultado: {resultado}")