"""Obtenção transitória de notícias, sem acesso irrestrito a URLs ou persistência."""

import ipaddress
import json
import queue
import re
import socket
import threading
import time
from urllib.parse import quote, urljoin, urlsplit, urlunsplit

import urllib3


MAX_BYTES = 3 * 1024 * 1024
MAX_REDIRECTS = 3
TIMEOUT_DNS = 5.0
TIMEOUT_CONEXAO = 5.0
TIMEOUT_LEITURA = 5.0
TIMEOUT_TOTAL = 25.0
MENSAGEM_TIMEOUT = "A página demorou muito para responder. Tente novamente."


class ErroExtracao(ValueError):
    """Erro cuja mensagem pode ser apresentada diretamente na interface."""


def validar_url(url: str) -> str:
    """Valida sintaxe sem realizar requisições; não presume um esquema ausente."""
    if not isinstance(url, str) or not url.strip():
        raise ErroExtracao("Insira uma URL para analisar.")
    url = url.strip()
    try:
        if len(url) > 8192 or re.search(r"[\s\x00-\x1f\x7f\\]", url):
            raise ValueError
        partes = urlsplit(url)
        host = partes.hostname
        if partes.scheme not in ("http", "https") or not host:
            raise ValueError
        if partes.username is not None or partes.password is not None or "%" in host:
            raise ValueError
        porta = partes.port
        if porta == 0 or partes.netloc.endswith(":"):
            raise ValueError
        host = host.rstrip(".").encode("idna").decode("ascii").lower()
        if ":" in host:
            ipaddress.IPv6Address(host)
            host = f"[{host}]"
        elif len(host) > 253 or any(
            not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", parte)
            for parte in host.split(".")
        ):
            raise ValueError
        autoridade = host + (f":{porta}" if porta is not None else "")
        return urlunsplit((partes.scheme, autoridade,
                           quote(partes.path or "/", safe="/%:@!$&'()*+,;=-._~"),
                           quote(partes.query, safe="%/?@:!$&'()*+,;=-._~"), ""))
    except (ValueError, UnicodeError):
        raise ErroExtracao("Insira uma URL válida.") from None


def _validar_ip(endereco):
    ip = ipaddress.ip_address(endereco)
    if (not ip.is_global or ip.is_private or ip.is_loopback or ip.is_link_local
            or ip.is_multicast or ip.is_reserved or ip.is_unspecified
            or getattr(ip, "ipv4_mapped", None) is not None
            or getattr(ip, "sixtofour", None) is not None
            or getattr(ip, "teredo", None) is not None):
        raise ErroExtracao("Esta URL não pode ser acessada.")
    return str(ip)


def _resolver_destino(host, porta, restante):
    if host == "localhost" or host.endswith(".localhost"):
        raise ErroExtracao("Esta URL não pode ser acessada.")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        return _validar_ip(host)

    # getaddrinfo não oferece timeout: a espera é limitada e o worker não faz HTTP.
    respostas = queue.Queue(maxsize=1)

    def resolver():
        try:
            respostas.put(socket.getaddrinfo(host, porta, type=socket.SOCK_STREAM))
        except OSError as erro:
            respostas.put(erro)

    threading.Thread(target=resolver, daemon=True).start()
    try:
        registros = respostas.get(timeout=min(TIMEOUT_DNS, restante))
    except queue.Empty:
        raise ErroExtracao(MENSAGEM_TIMEOUT) from None
    if isinstance(registros, OSError) or not registros:
        raise ErroExtracao("Não foi possível acessar esta página.")
    # Rejeita inclusive respostas DNS mistas (IP público + IP privado).
    enderecos = [_validar_ip(registro[4][0]) for registro in registros]
    return enderecos[0]


def _tempo_restante(limite):
    restante = limite - time.monotonic()
    if restante <= 0:
        raise ErroExtracao(MENSAGEM_TIMEOUT)
    return restante


def _baixar_html(url):
    limite = time.monotonic() + TIMEOUT_TOTAL
    for salto in range(MAX_REDIRECTS + 1):
        url = validar_url(url)
        partes = urlsplit(url)
        porta = partes.port or (443 if partes.scheme == "https" else 80)
        ip = _resolver_destino(partes.hostname, porta, _tempo_restante(limite))
        opcoes = {}
        tipo_pool = urllib3.HTTPConnectionPool
        if partes.scheme == "https":
            tipo_pool = urllib3.HTTPSConnectionPool
            opcoes = dict(server_hostname=partes.hostname,
                          assert_hostname=partes.hostname, cert_reqs="CERT_REQUIRED")
        # Conecta ao IP aprovado, preservando Host, SNI e validação do certificado.
        # Pools diretos não leem proxies do ambiente nem refazem DNS do hostname.
        pool = tipo_pool(ip, port=porta, **opcoes)
        resposta = None
        try:
            restante = _tempo_restante(limite)
            resposta = pool.urlopen(
                "GET", urlunsplit(("", "", partes.path, partes.query, "")),
                headers={"Host": partes.netloc, "User-Agent": "NewsLens/1.0 (article text extraction)",
                         "Accept": "text/html, application/xhtml+xml, text/plain;q=0.8",
                         "Accept-Encoding": "identity"},
                timeout=urllib3.Timeout(connect=min(TIMEOUT_CONEXAO, restante),
                                        read=min(TIMEOUT_LEITURA, restante)),
                retries=False, redirect=False, preload_content=False,
            )
            if resposta.status in (301, 302, 303, 307, 308):
                destino = resposta.headers.get("Location")
                if not destino or salto == MAX_REDIRECTS:
                    raise ErroExtracao("Não foi possível acessar esta página.")
                url = urljoin(url, destino)
                continue
            if resposta.status != 200:
                raise ErroExtracao("Não foi possível acessar esta página.")
            tipo = resposta.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if tipo not in ("text/html", "application/xhtml+xml", "text/plain"):
                raise ErroExtracao("Este tipo de conteúdo não pode ser analisado.")
            # Recusa compressão não solicitada para evitar bombas de descompressão.
            if resposta.headers.get("Content-Encoding", "identity").lower() not in ("", "identity"):
                raise ErroExtracao("Este tipo de conteúdo não pode ser analisado.")
            tamanho = resposta.headers.get("Content-Length")
            if tamanho is not None and (not tamanho.isdigit() or int(tamanho) > MAX_BYTES):
                raise ErroExtracao("Este tipo de conteúdo não pode ser analisado.")
            conteudo = bytearray()
            while True:
                _tempo_restante(limite)
                bloco = resposta.read1(min(65536, MAX_BYTES + 1 - len(conteudo)), decode_content=False)
                _tempo_restante(limite)
                if not bloco:
                    break
                conteudo.extend(bloco)
                if len(conteudo) > MAX_BYTES:
                    raise ErroExtracao("Este tipo de conteúdo não pode ser analisado.")
            inicio = bytes(conteudo[:512]).lstrip()
            if b"\x00" in conteudo or inicio.startswith((b"%PDF-", b"PK\x03\x04", b"\x89PNG", b"GIF8", b"\xff\xd8", b"MZ")):
                raise ErroExtracao("Este tipo de conteúdo não pode ser analisado.")
            return url, bytes(conteudo)
        except (urllib3.exceptions.TimeoutError, TimeoutError):
            raise ErroExtracao(MENSAGEM_TIMEOUT) from None
        except (urllib3.exceptions.HTTPError, OSError, ValueError) as erro:
            if isinstance(erro, ErroExtracao):
                raise
            raise ErroExtracao("Não foi possível acessar esta página.") from None
        finally:
            if resposta is not None:
                resposta.close()
            pool.close()


def extrair_noticia_url(url: str) -> dict:
    """Retorna URL final, metadados opcionais e texto para o pipeline existente."""
    url = validar_url(url)
    try:
        import trafilatura
    except ImportError:
        raise ErroExtracao("A análise por URL está temporariamente indisponível.") from None
    url_final, html = _baixar_html(url)
    try:
        extraido = trafilatura.extract(
            html, url=url_final, output_format="json", with_metadata=True,
            include_comments=False, include_tables=False, include_links=False,
            include_images=False, favor_precision=True,
        )
        dados = json.loads(extraido) if extraido else {}
        texto = dados.get("text") or ""
        texto = "\n".join(" ".join(linha.split()) for linha in texto.splitlines()).strip()
    except Exception:
        raise ErroExtracao("Não foi possível extrair o conteúdo da notícia.") from None
    if not texto:
        raise ErroExtracao("Não foi possível extrair o conteúdo da notícia.")
    palavras = re.findall(r"[^\W\d_]+", texto, flags=re.UNICODE)
    # Apenas um piso de conteúdo útil; não é um detector de gênero jornalístico.
    if len(palavras) < 30 or len(set(p.lower() for p in palavras)) < 10:
        raise ErroExtracao("Não foi possível identificar texto suficiente para realizar a análise.")
    return {"url": url_final, "titulo": dados.get("title"), "autor": dados.get("author"),
            "data": dados.get("date"), "texto": texto}
