"""Validacao estrutural e de seguranca do site estatico fenatodev.

Testes independentes — nao dependem do core Business Automation.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
HTML = (PUBLIC / "index.html").read_text(encoding="utf-8")
CSS = (PUBLIC / "styles.css").read_text(encoding="utf-8")


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


def test_public_folder_has_exactly_4_files() -> None:
    """Issue #1: public/ must contain exactly 4 approved files."""
    public_files = sorted(f.name for f in PUBLIC.iterdir() if f.is_file())
    assert public_files == ["_headers", "favicon.svg", "index.html", "styles.css"]


def test_headers_restored() -> None:
    """Issue #1: _headers must be restored from the approved source."""
    headers = (PUBLIC / "_headers").read_text(encoding="utf-8")
    assert "Content-Security-Policy" in headers
    assert "default-src 'none'" in headers
    assert "X-Content-Type-Options: nosniff" in headers
    assert "X-Frame-Options: DENY" in headers


def test_assets_exist() -> None:
    assert (PUBLIC / "index.html").is_file()
    assert (PUBLIC / "styles.css").is_file()
    favicon = (PUBLIC / "favicon.svg").read_text(encoding="utf-8")
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
APPROVED_WHATSAPP = "https://wa.me/5512987005078"


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
            # Issue #1: validate exact approved WhatsApp number, not just any digits
            assert href == APPROVED_WHATSAPP, f"Unexpected WhatsApp: {href}"
        assert link.get("target") == "_blank", href
        assert {"noopener", "noreferrer"}.issubset(
            set((link.get("rel") or "").split())
        ), href
        external += 1
    assert external >= 5


def test_whatsapp_is_primary_contact() -> None:
    links = [a.get("href") for a in parsed().selected("a")]
    assert APPROVED_WHATSAPP in links
    # WhatsApp must appear in both contact section and footer
    count = links.count(APPROVED_WHATSAPP)
    assert count >= 2


def test_linkedin_and_github_preserved() -> None:
    links = [a.get("href") for a in parsed().selected("a")]
    assert "https://www.linkedin.com/in/fenatodev/" in links
    assert "https://github.com/fenatodev" in links


def test_brand_is_lowercase() -> None:
    """Issue #1: brand must use lowercase 'fenatodev' throughout."""
    for file in (PUBLIC / "index.html", PUBLIC / "styles.css", PUBLIC / "favicon.svg"):
        content = file.read_text(encoding="utf-8")
        assert "FenatoDev" not in content, f"Uppercase brand found in {file.name}"
        assert "FENATODEV" not in content, f"ALL-CAPS brand found in {file.name}"
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "FenatoDev" not in readme


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
    for file in (PUBLIC / "index.html", PUBLIC / "styles.css", PUBLIC / "favicon.svg"):
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
    assert "DEMO EXECUTAVEL" in HTML or "DEMO EXECUTÁVEL" in HTML
    assert "DADOS FICTICIOS" in HTML or "DADOS FICTÍCIOS" in HTML
    assert "Nao e uma integracao de cliente" in HTML or "Não é uma integração de cliente" in HTML
    assert "Nao implicam clientes atendidos" in HTML or "Não implicam clientes atendidos" in HTML


def test_root_allowlist() -> None:
    """Root must not contain stray site files or unexpected directories.

    Only public/, tests/, .github/, README.md and .git are allowed at the
    repository root. No HTML, CSS, or SVG files should sit outside public/.
    Tool caches (e.g. .pytest_cache, __pycache__) are ignored.
    """
    root_entries = sorted(entry.name for entry in ROOT.iterdir())
    allowed_root = {".git", ".github", "README.md", "public", "tests"}
    # Ignore tool-generated caches that start with a dot but aren't tracked dirs
    tool_cache_prefixes = (".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache")
    for entry in root_entries:
        if entry.startswith(tool_cache_prefixes):
            continue
        assert entry in allowed_root, f"Unexpected root entry: {entry}"
    # Ensure no site asset files leak to the root
    for ext in (".html", ".css", ".svg"):
        stray = [f for f in ROOT.iterdir() if f.is_file() and f.name.endswith(ext)]
        assert not stray, f"Stray {ext} files at root: {[p.name for p in stray]}"


def test_accessibility_rules() -> None:
    assert any(
        a.get("href") == "#conteudo" and a.get("class") == "skip-link"
        for a in parsed().selected("a")
    )
    assert ":focus-visible" in CSS
    assert "prefers-reduced-motion: reduce" in CSS
    assert "@media (max-width: 680px)" in CSS
