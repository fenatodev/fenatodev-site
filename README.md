# FenatoDev — Site institucional

Site estático da FenatoDev: engenharia de software, automação de processos e integrações com IA.

## O que é

Página institucional sem JavaScript, formulários, analytics ou cookies próprios. Todo o conteúdo é HTML + CSS local, sem dependências externas.

## Contato

- **WhatsApp**: [wa.me/5512987005078](https://wa.me/5512987005078)
- **LinkedIn**: [linkedin.com/in/fenatodev](https://www.linkedin.com/in/fenatodev/)
- **GitHub**: [github.com/fenatodev](https://github.com/fenatodev)

## Estrutura

| Arquivo | Descrição |
| --- | --- |
| `index.html` | Página principal com oferta, método, portfólio e contato |
| `styles.css` | Layout responsivo, tema escuro, acessibilidade |
| `favicon.svg` | Ícone local |

## Segurança

- CSP inline bloqueia scripts, formulários e conexões remotas
- Links externos abrem em nova aba com `noopener noreferrer`
- Sem cookies, analytics ou rastreamento

## Preview local

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Abrir `http://127.0.0.1:8000/` somente na máquina local.

## Validação

```bash
python3 -m pytest tests/ -q
```

## CI

GitHub Actions valida estrutura HTML, links e segurança a cada push.

## Privacidade

Esta página não contém formulários, analytics ou cookies próprios. Ao abrir links externos, valem as políticas dos respectivos serviços.

## Licença

Conteúdo institucional FenatoDev © 2026.
