from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import model


class ModeloTest(unittest.TestCase):
    def setUp(self):
        model.carregar_modelo.clear()
        self.tokenizer = Mock(return_value={"input_ids": torch.tensor([[1, 2]])})
        self.modelo = Mock()
        self.modelo.return_value = SimpleNamespace(logits=torch.tensor([[2.0, 1.0]]))
        self.tokenizer_carregado = patch.object(
            model.AutoTokenizer, "from_pretrained", return_value=self.tokenizer
        )
        self.modelo_carregado = patch.object(
            model.AutoModelForSequenceClassification,
            "from_pretrained",
            return_value=self.modelo,
        )
        self.tokenizer_carregado.start()
        self.modelo_carregado.start()
        self.addCleanup(patch.stopall)

    def carregar(self):
        return model.carregar_modelo()

    def classificar(self, logits):
        self.modelo.return_value = SimpleNamespace(logits=torch.tensor([logits]))
        return model.classificar_noticia("Texto válido para classificação.")

    def test_carrega_tokenizer_modelo_e_modo_avaliacao(self):
        tokenizer, modelo = self.carregar()

        model.AutoTokenizer.from_pretrained.assert_called_once_with(model.MODELO)
        model.AutoModelForSequenceClassification.from_pretrained.assert_called_once_with(
            model.MODELO
        )
        modelo.eval.assert_called_once_with()
        self.assertIs(tokenizer, self.tokenizer)
        self.assertIs(modelo, self.modelo)

    def test_cache_evita_carregamentos_repetidos(self):
        primeira_carga = self.carregar()
        segunda_carga = self.carregar()

        self.assertIs(primeira_carga, segunda_carga)
        model.AutoTokenizer.from_pretrained.assert_called_once_with(model.MODELO)
        model.AutoModelForSequenceClassification.from_pretrained.assert_called_once_with(
            model.MODELO
        )

    def test_entrada_valida_usa_truncamento_e_maximo(self):
        resultado = self.classificar([2.0, 1.0])

        self.tokenizer.assert_called_once_with(
            "Texto válido para classificação.",
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )
        self.assertEqual(resultado["classe"], "Falsa")

    def test_classe_zero_e_scores(self):
        resultado = self.classificar([2.0, 1.0])

        esperado_falsa, esperado_verdadeira = torch.softmax(
            torch.tensor([2.0, 1.0]), dim=0
        ).tolist()
        self.assertEqual(resultado["classe"], "Falsa")
        self.assertAlmostEqual(resultado["score_falsa"], esperado_falsa)
        self.assertAlmostEqual(resultado["score_verdadeira"], esperado_verdadeira)
        self.assertAlmostEqual(resultado["confianca"], esperado_falsa)
        self.assertAlmostEqual(
            resultado["score_falsa"] + resultado["score_verdadeira"], 1.0
        )

    def test_classe_um_e_confianca(self):
        resultado = self.classificar([1.0, 3.0])

        esperado = torch.softmax(torch.tensor([1.0, 3.0]), dim=0).tolist()
        self.assertEqual(resultado["classe"], "Verdadeira")
        self.assertAlmostEqual(resultado["score_falsa"], esperado[0])
        self.assertAlmostEqual(resultado["score_verdadeira"], esperado[1])
        self.assertAlmostEqual(resultado["confianca"], esperado[1])

    def test_rejeita_entrada_vazia(self):
        with self.assertRaises(ValueError):
            model.classificar_noticia("")
        self.tokenizer.assert_not_called()

    def test_rejeita_entrada_com_apenas_espacos(self):
        with self.assertRaises(ValueError):
            model.classificar_noticia("   \n\t  ")
        self.tokenizer.assert_not_called()

    def test_rejeita_none(self):
        with self.assertRaises(TypeError):
            model.classificar_noticia(None)
        self.tokenizer.assert_not_called()

    def test_rejeita_tipo_invalido(self):
        with self.assertRaises(TypeError):
            model.classificar_noticia(["texto"])
        self.tokenizer.assert_not_called()


if __name__ == "__main__":
    unittest.main()