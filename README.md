# AI Browser HTML to Markdown Converter

Este projeto é uma ferramenta para capturar páginas web, destacar elementos interativos e converter o conteúdo para Markdown.

## Funcionalidades

- Captura de páginas web usando Playwright
- Destaque de elementos interativos (links, botões, campos de formulário, etc.)
- Extração e incorporação de conteúdo de iframes
- Conversão automática do HTML para Markdown

## Requisitos

- Python 3.7+
- Playwright
- Markdownify

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/ai-browser.git
cd ai-browser
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Instale os navegadores do Playwright:
```bash
playwright install
```

## Uso

Execute o script principal fornecendo a URL da página a ser processada:

```bash
python html_to_markdown.py https://exemplo.com
```

### Opções adicionais

```
--timeout TIMEOUT     Timeout em ms (default: 60000)
--wait {load,domcontentloaded,networkidle,commit}
                      Evento para aguardar (default: domcontentloaded)
--output-html PATH    Caminho para salvar o arquivo HTML consolidado
--output-md PATH      Caminho para salvar o arquivo Markdown
```

## Estrutura do Projeto

- `html_to_markdown.py`: Script principal
- `browser_config.py`: Configurações do navegador
- `page_processor.py`: Funções para processamento de páginas
- `html_processor.py`: Funções para processamento de HTML
- `static/highlight_script.js`: Script JavaScript para destacar elementos interativos
- `requirements.txt`: Dependências do projeto

## Como Funciona

1. O script abre a URL especificada em um navegador Chromium usando Playwright
2. Rola a página para carregar todo o conteúdo
3. Destaca elementos interativos com bordas vermelhas e rótulos numéricos
4. Extrai o conteúdo de iframes e o incorpora no HTML principal
5. Salva o HTML consolidado
6. Converte o HTML para Markdown e salva o resultado

## Personalização

Você pode personalizar o comportamento do script modificando a classe `ScraperConfig` em `html_to_markdown.py`.

## Licença

MIT 