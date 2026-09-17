from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
import componentes
import extrator_noticia

from test_extrator_noticia import TEXTO, resposta


RESULTADO = {"classe": "Verdadeira", "confianca": 0.8,
             "score_falsa": 0.2, "score_verdadeira": 0.8}


class FluxoStreamlitTest(unittest.TestCase):
    def setUp(self):
        self.eventos = []

        def classificar(texto):
            self.assertEqual(st.session_state.pagina_atual, "analisando")
            self.assertIsInstance(texto, str)
            self.eventos.append("modelo")
            return dict(RESULTADO)

        self.classificador = Mock(side_effect=classificar)
        modelo = types.ModuleType("model")
        modelo.classificar_noticia = self.classificador
        patch.dict(sys.modules, {"model": modelo}).start()
        tela_real = componentes.exibir_tela_analisando

        def tela(icone):
            self.eventos.append("analisando")
            tela_real(icone)

        patch.object(componentes, "exibir_tela_analisando", side_effect=tela).start()
        self.addCleanup(patch.stopall)
        self.app = AppTest.from_file(str(ROOT / "app/app.py"), default_timeout=15)
        self.app.session_state["tela_abertura_exibida"] = True
        self.app.run()
        self.assertEqual(len(self.app.exception), 0)

    def clicar(self, label):
        next(b for b in self.app.button if b.label == label).click().run()
        self.assertEqual(len(self.app.exception), 0)

    def verificar_resultado(self, metodo):
        self.assertEqual(self.app.session_state["pagina_atual"], "resultado")
        self.assertEqual(self.app.session_state["metodo_analise"], metodo)
        self.assertEqual(self.app.session_state["resultado_analise"], RESULTADO)
        html = " ".join(m.value for m in self.app.markdown)
        self.assertIn("Análise de URL" if metodo == "url" else "Análise de texto", html)
        self.assertEqual(self.eventos, ["analisando", "modelo"])

    def test_texto_analisando_resultado(self):
        self.app.text_area[0].input(TEXTO)
        self.clicar("Analisar notícia")
        self.classificador.assert_called_once_with(TEXTO)
        self.verificar_resultado("texto")

    def test_url_analisando_resultado_com_extracao_real(self):
        import socket
        import urllib3
        with patch.object(socket, "getaddrinfo", return_value=[
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ]), patch.object(urllib3, "HTTPSConnectionPool") as pool:
            pool.return_value.urlopen.return_value = resposta()
            self.app.text_input[0].input("https://example.org/noticia")
            self.clicar("Analisar URL")
            self.verificar_resultado("url")
            texto_modelo = self.classificador.call_args.args[0]
            self.assertIn(TEXTO, texto_modelo)
            self.assertNotEqual(texto_modelo, "https://example.org/noticia")
            self.app.run()
            pool.return_value.urlopen.assert_called_once()
            self.classificador.assert_called_once()
        self.clicar("← Nova análise")
        for chave in ("url_analisada", "texto_analisado", "resultado_analise", "metodo_analise"):
            self.assertNotIn(chave, self.app.session_state)
        self.app.text_area[0].input(TEXTO)
        self.clicar("Analisar notícia")
        self.assertEqual(self.app.session_state["metodo_analise"], "texto")

    def test_url_invalida_nao_executa_modelo(self):
        self.app.text_input[0].input("nao-e-url")
        self.clicar("Analisar URL")
        self.assertEqual(self.app.warning[0].value, "Insira uma URL válida.")
        self.classificador.assert_not_called()
        self.assertEqual(self.eventos, [])

    def test_url_bloqueada_volta_inicio(self):
        self.app.text_input[0].input("http://127.0.0.1/segredo")
        self.clicar("Analisar URL")
        self.assertEqual(self.app.session_state["pagina_atual"], "inicio")
        self.assertEqual(self.app.error[0].value, "Esta URL não pode ser acessada.")
        self.classificador.assert_not_called()
        self.assertEqual(self.eventos, ["analisando"])

    def test_falha_extracao_nao_executa_modelo(self):
        with patch.object(extrator_noticia, "extrair_noticia_url", side_effect=
                          extrator_noticia.ErroExtracao("Não foi possível extrair o conteúdo da notícia.")):
            self.app.text_input[0].input("https://example.org")
            self.clicar("Analisar URL")
        self.assertEqual(self.app.session_state["pagina_atual"], "inicio")
        self.assertIn("Não foi possível extrair", self.app.error[0].value)
        self.classificador.assert_not_called()

    def test_falha_modelo_nao_expoe_detalhes(self):
        self.classificador.side_effect = RuntimeError("detalhes internos secretos")
        self.app.text_area[0].input(TEXTO)
        self.clicar("Analisar notícia")
        self.assertEqual(self.app.error[0].value,
                         "Não foi possível concluir a análise. Tente novamente em instantes.")


if __name__ == "__main__":
    unittest.main()
