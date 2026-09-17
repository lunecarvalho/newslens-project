import json
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import extrator_noticia as extrator
import urllib3


TEXTO = (
    "A universidade anunciou nesta quarta-feira um projeto de pesquisa sobre transporte urbano. "
    "Os pesquisadores vão acompanhar os deslocamentos dos moradores durante seis meses. "
    "Segundo a equipe, os resultados serão apresentados em reuniões públicas para discutir melhorias "
    "nas linhas de ônibus e nas condições de acesso aos bairros da cidade."
)
HTML = (f'<html><head><title>Universidade anuncia pesquisa</title>'
        '<meta name="author" content="Maria Silva"></head><body><nav>Menu</nav>'
        f'<article><h1>Universidade anuncia pesquisa</h1><p>{TEXTO}</p>'
        '<p>O trabalho contará com estudantes e professores de diferentes departamentos. '
        'A coleta de dados começa na próxima semana e seguirá um calendário divulgado pela instituição.</p>'
        '</article><footer>Contato</footer></body></html>').encode()


def resposta(status=200, headers=None, body=HTML):
    mock = MagicMock()
    mock.status = status
    mock.headers = {"Content-Type": "text/html"} if headers is None else headers
    mock.read1.side_effect = [body, b""]
    return mock


class ExtratorTest(unittest.TestCase):
    def setUp(self):
        self.dns = patch.object(socket, "getaddrinfo", return_value=[
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ]).start()
        self.http = patch.object(urllib3, "HTTPConnectionPool").start()
        self.https = patch.object(urllib3, "HTTPSConnectionPool").start()
        self.pool = MagicMock()
        self.http.return_value = self.https.return_value = self.pool
        self.response = resposta()
        self.pool.urlopen.return_value = self.response
        self.addCleanup(patch.stopall)

    def erro(self, url, mensagem):
        with self.assertRaisesRegex(extrator.ErroExtracao, mensagem):
            extrator.extrair_noticia_url(url)

    def test_http_valida(self):
        self.assertIn(TEXTO, extrator.extrair_noticia_url("http://example.org/noticia")["texto"])
        self.http.assert_called_once()

    def test_https_valida_e_conexao_ip_com_tls(self):
        dados = extrator.extrair_noticia_url("https://example.org/noticia")
        self.assertIn("pesquisa", dados["texto"])
        self.https.assert_called_once_with("93.184.216.34", port=443,
            server_hostname="example.org", assert_hostname="example.org", cert_reqs="CERT_REQUIRED")
        kwargs = self.pool.urlopen.call_args.kwargs
        self.assertFalse(kwargs["redirect"])
        self.assertFalse(kwargs["retries"])
        self.assertFalse(kwargs["preload_content"])
        self.assertEqual(kwargs["headers"]["Host"], "example.org")
        self.dns.assert_called_once()
        self.response.close.assert_called_once()
        self.pool.close.assert_called_once()

    def test_normalizacao(self):
        self.assertEqual(extrator.validar_url(" HTTPS://EXAMPLE.ORG./ação#titulo "),
                         "https://example.org/a%C3%A7%C3%A3o")

    def test_url_vazia(self):
        for url in ("", "  ", None):
            with self.subTest(url=url):
                self.erro(url, "Insira uma URL para analisar")
        self.pool.urlopen.assert_not_called()

    def test_urls_invalidas(self):
        for url in ("noticia", "ftp://example.org", "https:///foo", "https://", "https://a:abc",
                    "https://a:0", "https://a:99999", "https://a:", "https://[::1", "https://a b",
                    "https://user:pass@example.org", "https://a\\b", "https://a/\nfoo"):
            with self.subTest(url=url):
                self.erro(url, "Insira uma URL válida")
        self.pool.urlopen.assert_not_called()

    def test_destinos_bloqueados(self):
        for host in ("localhost", "LOCALHOST.", "x.localhost", "127.0.0.1", "10.0.0.1",
                     "172.16.0.1", "192.168.1.1", "169.254.169.254", "0.0.0.0", "224.0.0.1",
                     "240.0.0.1", "100.64.0.1", "[::1]", "[::]", "[fe80::1]", "[fc00::1]",
                     "[ff02::1]", "[::ffff:127.0.0.1]", "[2002:7f00:1::]"):
            with self.subTest(host=host):
                self.erro(f"http://{host}/", "Esta URL não pode ser acessada")
        self.pool.urlopen.assert_not_called()

    def test_dns_privado_e_misto(self):
        for ips in (["192.168.1.5"], ["93.184.216.34", "10.0.0.2"]):
            self.dns.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 80)) for ip in ips]
            self.erro("https://example.org", "Esta URL não pode ser acessada")
        self.pool.urlopen.assert_not_called()

    def test_ip_numerico_alternativo_resolvido_como_privado(self):
        self.dns.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))]
        self.erro("http://2130706433", "Esta URL não pode ser acessada")

    def test_redirect_bloqueado(self):
        self.response.status = 302
        self.response.headers = {"Location": "http://127.0.0.1/segredo"}
        self.erro("https://example.org", "Esta URL não pode ser acessada")
        self.pool.urlopen.assert_called_once()
        self.response.close.assert_called_once()

    def test_redirect_dns_privado(self):
        self.pool.urlopen.return_value = resposta(302, {"Location": "https://interno.example/"})
        self.dns.side_effect = [self.dns.return_value,
            [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 443))]]
        self.erro("https://example.org", "Esta URL não pode ser acessada")
        self.pool.urlopen.assert_called_once()

    def test_redirect_relativo_valido(self):
        self.pool.urlopen.side_effect = [resposta(302, {"Location": "/artigo"}), resposta()]
        self.assertEqual(extrator.extrair_noticia_url("https://example.org")["url"], "https://example.org/artigo")
        self.assertEqual(self.dns.call_count, 2)

    def test_limite_redirects(self):
        self.pool.urlopen.return_value = resposta(302, {"Location": "/outro"})
        self.erro("https://example.org", "Não foi possível acessar")
        self.assertEqual(self.pool.urlopen.call_count, extrator.MAX_REDIRECTS + 1)

    def test_timeout(self):
        self.pool.urlopen.side_effect = urllib3.exceptions.ReadTimeoutError(None, "/", "segredo")
        self.erro("https://example.org", "A página demorou muito")

    def test_timeout_leitura(self):
        self.response.read1.side_effect = TimeoutError("segredo")
        self.erro("https://example.org", "A página demorou muito")
        self.response.close.assert_called_once()

    def test_timeout_dns(self):
        with patch.object(extrator.queue.Queue, "get", side_effect=extrator.queue.Empty):
            self.erro("https://example.org", "A página demorou muito")
        self.pool.urlopen.assert_not_called()

    def test_erro_dns(self):
        self.dns.side_effect = socket.gaierror("segredo")
        self.erro("https://example.org", "Não foi possível acessar")

    def test_erro_http(self):
        for status in (204, 206, 401, 403, 404, 429, 500):
            self.response.status = status
            self.erro("https://example.org", "Não foi possível acessar")
        self.response.read1.assert_not_called()

    def test_content_type_nao_suportado(self):
        for tipo in ("application/pdf", "application/zip", "image/png", "video/mp4", "application/octet-stream", ""):
            self.response.headers = {"Content-Type": tipo}
            self.erro("https://example.org", "Este tipo de conteúdo")
        self.response.read1.assert_not_called()

    def test_conteudo_binario_disfarcado(self):
        self.response.read1.side_effect = [b"%PDF-1.4 conteudo", b""]
        self.erro("https://example.org", "Este tipo de conteúdo")

    def test_compressao_nao_solicitada(self):
        self.response.headers["Content-Encoding"] = "gzip"
        self.erro("https://example.org", "Este tipo de conteúdo")
        self.response.read1.assert_not_called()

    def test_limite_tamanho_header_e_stream(self):
        self.response.headers["Content-Length"] = str(extrator.MAX_BYTES + 1)
        self.erro("https://example.org", "Este tipo de conteúdo")
        self.response.read1.assert_not_called()
        del self.response.headers["Content-Length"]
        with patch.object(extrator, "MAX_BYTES", 10):
            self.response.read1.side_effect = [b"a" * 11]
            self.erro("https://example.org", "Este tipo de conteúdo")

    def test_limite_tempo_total(self):
        with patch.object(extrator.time, "monotonic", side_effect=[0, 0, 0, 26]):
            self.erro("https://example.org", "A página demorou muito")

    def test_html_sem_artigo(self):
        self.response.read1.side_effect = [b"<html><body><nav>Menu</nav></body></html>", b""]
        self.erro("https://example.org", "Não foi possível (extrair|identificar texto suficiente)")

    def test_texto_vazio(self):
        for valor in (None, "", json.dumps({"text": ""}), json.dumps({"text": None})):
            self.response.read1.side_effect = [HTML, b""]
            with patch("trafilatura.extract", return_value=valor):
                self.erro("https://example.org", "Não foi possível extrair")

    def test_texto_insuficiente(self):
        for texto in ("Notícia muito curta", "palavra " * 100):
            self.response.read1.side_effect = [HTML, b""]
            with patch("trafilatura.extract", return_value=json.dumps({"text": texto})):
                self.erro("https://example.org", "texto suficiente")

    def test_artigo_valido_com_titulo(self):
        dados = extrator.extrair_noticia_url("https://example.org")
        self.assertEqual(dados["titulo"], "Universidade anuncia pesquisa")
        self.assertEqual(dados["autor"], "Maria Silva")
        self.assertIn(TEXTO, dados["texto"])
        self.assertNotIn("Menu", dados["texto"])
        self.assertNotIn("Contato", dados["texto"])

    def test_metadados_opcionais_e_opcoes_extracao(self):
        with patch("trafilatura.extract", return_value=json.dumps({"text": TEXTO})) as extrair:
            dados = extrator.extrair_noticia_url("https://example.org")
        self.assertIsNone(dados["titulo"])
        self.assertIsNone(dados["autor"])
        self.assertIsNone(dados["data"])
        self.assertEqual(dados["texto"], TEXTO)
        self.assertFalse(extrair.call_args.kwargs["include_comments"])
        self.assertTrue(extrair.call_args.kwargs["favor_precision"])


if __name__ == "__main__":
    unittest.main()
