"""Validação estrutural e de segurança do site estático FenatoDev.

Testes independentes — não dependem do core Business Automation.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


class Elements(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append((tag, dict(attrs)))

    def selected(self, name: str) -> list[dict[str, str | None]]:
        return [attrs for tag, attrs in self.tags if tag == name]


def parsed() -> Elements:
    document = Elements()
    document.feed(HTML)
    document.close()
    return document


def test_assets_exist() -> None:
    assert (ROOT / "index.html").is_file()
    assert (ROOT / "styles.css").is_file()
    favicon = (ROOT / "favicon.svg").read_text(encoding="utf-8")
    assert "<svg" in favicon and 'xmlns="http://www.w3.org/2000/svg"' in favicon
    assert not (ROOT / "node_modules").exists()
    assert not (ROOT / ".env").exists()


def test_html_structure() -> None:
    doc = parsed()
    assert doc.selected("html")[0].get("lang") == "pt-BR"
    assert len(doc.selected("title")) == 1
    assert len(doc.selected("h1")) == 1
    assert len(doc.selected("main")) == 1
    assert len(doc.selected("nav")) == 1
    assert any(meta.get("name") == "viewport" for meta in doc.selected("meta"))
    assert any(meta.get("name") == "description" for meta in doc.selected("meta"))


def test_in_page_links_resolve() -> None:
    doc = parsed()
    identifiers = [attrs["id"] for _, attrs in doc.tags if attrs.get("id")]
    assert len(identifiers) == len(set(identifiers))
    for link in doc.selected("a"):
        href = link.get("href")
        assert href is not None
        if href.startswith("#"):
            assert href[1:] in identifiers, href
    assert {"inicio", "servicos", "metodo", "evidencias", "contato", "conteudo"}.issubset(
        set(identifiers)
    )


ALLOWED_HOSTS = {"github.com", "www.linkedin.com", "wa.me"}


def test_outgoing_links_are_safe() -> None:
    doc = parsed()
    external = 0
    for link in doc.selected("a"):
        href = link["href"]
        if href is None or href.startswith("#"):
            continue
        parsed_url = urlparse(href)
        assert parsed_url.scheme == "https", href
        assert parsed_url.username is None and parsed_url.password is None, href
        assert parsed_url.query == "" and parsed_url.fragment == "", href
        assert parsed_url.hostname in ALLOWED_HOSTS, href
        if parsed_url.hostname == "github.com":
            assert parsed_url.path.startswith("/fenatodev"), href
        elif parsed_url.hostname == "www.linkedin.com":
            assert parsed_url.path == "/in/fenatodev/", href
        elif parsed_url.hostname == "wa.me":
            assert re.match(r"^/\d{11,15}$", parsed_url.path), href
        assert link.get("target") == "_blank", href
        assert {"noopener", "noreferrer"}.issubset(
            set((link.get("rel") or "").split())
        ), href
        external += 1
    assert external >= 5


def test_whatsapp_is_primary_contact() -> None:
    links = [a.get("href") for a in parsed().selected("a")]
    assert "https://wa.me/5512987005078" in links
    # WhatsApp must appear in both contact section and footer
    count = links.count("https://wa.me/5512987005078")
    assert count >= 2


def test_linkedin_and_github_preserved() -> None:
    links = [a.get("href") for a in parsed().selected("a")]
    assert "https://www.linkedin.com/in/fenatodev/" in links
    assert "https://github.com/fenatodev" in links


def test_no_scripts_forms_or_trackers() -> None:
    doc = parsed()
    prohibited = {"script", "form", "iframe", "video", "audio", "object", "embed"}
    assert not any(tag in prohibited for tag, _ in doc.tags)
    assert all(tag != "input" for tag, _ in doc.tags)
    for tag, attrs in doc.tags:
        assert not any(k.startswith("on") for k in attrs), tag
        assert "style" not in attrs, tag
    for asset in doc.selected("link"):
        href = asset.get("href") or ""
        assert href in {"./styles.css", "./favicon.svg"}
    for file in (ROOT / "index.html", ROOT / "styles.css", ROOT / "favicon.svg"):
        value = file.read_text(encoding="utf-8")
        assert "127.0.0.1" not in value
        assert "localhost" not in value
        assert "DATABASE_URL" not in value
    assert "@import" not in CSS
    assert not re.search(r"url\(\s*['\"]?https?://", CSS)


def test_csp_blocks_scripts() -> None:
    doc = parsed()
    policies = [
        meta.get("content") or ""
        for meta in doc.selected("meta")
        if (meta.get("http-equiv") or "").lower() == "content-security-policy"
    ]
    assert len(policies) == 1
    policy = policies[0]
    for fragment in (
        "default-src 'none'",
        "style-src 'self'",
        "img-src 'self'",
        "connect-src 'none'",
        "form-action 'none'",
        "object-src 'none'",
    ):
        assert fragment in policy


def test_demo_disclaimers_present() -> None:
    assert "DEMO EXECUTÁVEL" in HTML
    assert "DADOS FICTÍCIOS" in HTML
    assert "Não é uma integração de cliente" in HTML
    assert "Não implicam clientes atendidos" in HTML


def test_accessibility_rules() -> None:
    assert any(
        a.get("href") == "#conteudo" and a.get("class") == "skip-link"
        for a in parsed().selected("a")
    )
    assert ":focus-visible" in CSS
    assert "prefers-reduced-motion: reduce" in CSS
    assert "@media (max-width: 680px)" in CSS
