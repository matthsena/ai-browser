import asyncio
import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import time
from markdownify import markdownify as md

# Import modules from our new structure
from browser_config import create_browser_context
from page_processor import highlight_interactive_elements, scroll_page_to_bottom
from html_processor import process_html_with_iframes

@dataclass
class ScraperConfig:
    """Data class for all scraper configuration values"""
    url: str
    timeout: int = 60000
    wait_until: str = "domcontentloaded"
    scroll_wait_time: float = 2.5
    max_scroll_height: int = 20000
    initial_wait: int = 3
    browser_args: List[str] = field(default_factory=lambda: [
        '--disable-web-security',
        '--disable-site-isolation-trials',
        '--disable-features=IsolateOrigins,site-per-process',
        '--no-sandbox',
        '--disable-blink-features=AutomationControlled',
        '--disable-infobars',
        '--disable-background-timer-throttling',
        '--disable-popup-blocking',
        '--disable-backgrounding-occluded-windows',
        '--disable-renderer-backgrounding',
        '--disable-window-activation',
        '--disable-focus-on-load',
        '--no-first-run',
        '--no-default-browser-check',
        '--no-startup-window',
        '--window-position=0,0',
        '--window-size=2000,2000'
    ])
    output_html_path: str = "output_consolidated.html"
    output_md_path: str = "output_consolidated.md"
    output_partial_path: str = "output_partial.html"
    final_wait_time: int = 100

async def process_webpage(config: ScraperConfig):
    """
    Processa uma página web conforme a configuração fornecida.
    
    Args:
        config: Objeto ScraperConfig com todas as configurações
    """
    print(f"Acessando {config.url} (aguardando evento '{config.wait_until}', timeout: {config.timeout}ms)")
    
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=config.browser_args)
        context = await create_browser_context(browser)
        page = await context.new_page()
        
        # Configura para fechar automaticamente diálogos
        page.on("dialog", lambda dialog: dialog.dismiss())
        
        try:
            # Inicia o cronômetro para medir o tempo de carregamento
            start_time = time.time()
            
            await page.goto(config.url, wait_until=config.wait_until, timeout=config.timeout)
            
            # Calcula o tempo de carregamento
            load_time = time.time() - start_time
            load_time_ms = load_time * 1000
            print(f"Página carregada em {load_time:.2f} segundos ({load_time_ms:.0f}ms)")
            
            # Calcula o tempo de espera para rolagem (30% do tempo de carregamento)
            adjusted_scroll_wait_time = max(1.0, load_time * 0.3)
            print(f"Tempo de espera para rolagem definido como {adjusted_scroll_wait_time:.2f} segundos (30% do tempo de carregamento)")
            
            # Aguarda um tempo adicional para carregamento inicial
            print("Aguardando carregamento inicial...")
            await asyncio.sleep(config.initial_wait)
            
            # Rola a página para carregar conteúdo
            print("Rolando toda a página para carregar conteúdo lazy...")
            await scroll_page_to_bottom(
                page, 
                max_scroll_height=config.max_scroll_height, 
                scroll_wait_time=adjusted_scroll_wait_time
            )
            
            # Executa o script para processar elementos interativos
            print("Executando script para processar elementos interativos...")
            result = await highlight_interactive_elements(page)
            
            # Processa o HTML e substitui iframes
            print("Gerando HTML consolidado...")
            consolidated_html = process_html_with_iframes(result)
            
            # Salva a versão HTML consolidada
            with open(config.output_html_path, 'w', encoding='utf-8') as f:
                f.write(consolidated_html)
                
            print(f"HTML consolidado com iframes substituídos salvo como {config.output_html_path}")
            print(f"Total de {len(result['iframeInfos'])} iframes processados e incorporados no HTML")
            
            # Converte o HTML para Markdown e salva
            print("Convertendo HTML para Markdown...")
            markdown_content = md(consolidated_html)
            
            with open(config.output_md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"Versão Markdown salva como {config.output_md_path}")

            # Mantém o browser aberto para visualização
            print("Processo concluído. Mantendo navegador aberto para visualização...")
            await asyncio.sleep(config.final_wait_time)
            
        except Exception as e:
            print(f"Erro durante o processamento: {str(e)}")
            print("Tentando capturar conteúdo disponível até o momento...")
            try:
                # Tenta capturar o conteúdo disponível até agora
                html = await page.content()
                with open(config.output_partial_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"Conteúdo parcial salvo como {config.output_partial_path}")
            except Exception as inner_e:
                print(f"Falha ao salvar conteúdo parcial: {str(inner_e)}")
        finally:
            await context.close()
            await browser.close()

async def main():
    parser = argparse.ArgumentParser(description='Captura e processa uma página web')
    parser.add_argument('url', help='URL da página a processar')
    parser.add_argument('--timeout', type=int, default=60000, help='Timeout em ms (default: 60000)')
    parser.add_argument('--wait', choices=['load', 'domcontentloaded', 'networkidle', 'commit'], 
                        default='domcontentloaded', help='Evento para aguardar (default: domcontentloaded)')
    parser.add_argument('--output-html', type=str, default='output_consolidated.html',
                        help='Caminho para salvar o arquivo HTML consolidado')
    parser.add_argument('--output-md', type=str, default='output_consolidated.md',
                        help='Caminho para salvar o arquivo Markdown')
    
    args = parser.parse_args()
    
    config = ScraperConfig(
        url=args.url,
        timeout=args.timeout,
        wait_until=args.wait,
        output_html_path=args.output_html,
        output_md_path=args.output_md
    )
    
    await process_webpage(config)

if __name__ == "__main__":
    asyncio.run(main())