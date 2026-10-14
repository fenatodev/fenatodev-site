# fenatodev — Site institucional

Site estático da fenatodev: engenharia de software, automação de processos e integrações com IA.

## O que é

Página institucional sem JavaScript, formulários, analytics ou cookies próprios. Todo o conteúdo é HTML + CSS local, sem dependências externas.

## Contato

- **WhatsApp**: [wa.me/5512987005078](https://wa.me/5512987005078)
- **LinkedIn**: [linkedin.com/in/fenatodev](https://www.linkedin.com/in/fenatodev/)
- **GitHub**: [github.com/fenatodev](https://github.com/fenatodev)

## Estrutura

| Arquivo | Descrição |
| --- | --- |
| `public/index.html` | Página principal com oferta, método, portfólio e contato |
| `public/styles.css` | Layout responsivo, tema escuro, acessibilidade |
| `public/favicon.svg` | Ícone local |
| `public/_headers` | Cabeçalhos de segurança (Cloudflare Pages) |

A pasta `public/` contém exatamente 4 arquivos aprovados.

## Segurança

- CSP inline bloqueia scripts, formulários e conexões remotas
- Links externos abrem em nova aba com `noopener noreferrer`
- Sem cookies, analytics ou rastreamento
- `_headers` configura CSP, X-Frame-Options e Permissions-Policy para deploy Cloudflare

## Preview local

```bash
cd public && python3 -m http.server 8000 --bind 127.0.0.1
```

Abrir `http://127.0.0.1:8000/` somente na máquina local.

## Validação

```bash
python3 -m pytest tests/ -q
```

## CI

GitHub Actions valida estrutura HTML, links e segurança a cada push e pull request.

## Privacidade

Esta página não contém formulários, analytics ou cookies próprios. Ao abrir links externos, valem as políticas dos respectivos serviços.

## Licença

Conteúdo institucional fenatodev © 2026.
