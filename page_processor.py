"""
Page processing module for web scraping.
Contains functions for scrolling pages and highlighting interactive elements.
"""

import asyncio
import os
from pathlib import Path

async def scroll_page_to_bottom(page, max_scroll_height=20000, scroll_wait_time=2.5):
    """
    Rola a página até o final ou até atingir o limite máximo de altura.
    
    Args:
        page: Objeto page do Playwright
        max_scroll_height: Altura máxima em pixels para rolagem (padrão: 20000)
        scroll_wait_time: Tempo de espera em segundos após cada rolagem (padrão: 2.5)
    """
    # Obtém a altura do documento
    previous_height = 0
    current_height = await page.evaluate('document.body.scrollHeight')
    
    print(f"Iniciando rolagem da página (altura atual: {current_height}px, limite: {max_scroll_height}px)")
    print(f"Tempo de espera entre rolagens: {scroll_wait_time:.2f} segundos")
    
    # Verifica se a página já excede o limite máximo
    if current_height > max_scroll_height:
        print(f"Altura da página ({current_height}px) excede o limite de {max_scroll_height}px")
        # Rola até o limite máximo em vez de até o fim
        await page.evaluate(f'window.scrollTo(0, {max_scroll_height})')
        await asyncio.sleep(scroll_wait_time)
        print(f"Rolagem limitada a {max_scroll_height}px concluída")
        
        # Volta ao topo da página
        await page.evaluate('window.scrollTo(0, 0)')
        await asyncio.sleep(1)
        return
    
    # Rola até o final da página em etapas, aguardando carregamento de conteúdo
    while previous_height < current_height and current_height <= max_scroll_height:
        previous_height = current_height
        
        # Rola para baixo em incrementos
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        
        # Aguarda um momento para carregar conteúdo
        await asyncio.sleep(scroll_wait_time)
        
        # Vê se aumentou a altura devido a novo conteúdo carregado
        current_height = await page.evaluate('document.body.scrollHeight')
        
        # Informa progresso da rolagem
        print(f"Rolando a página... ({previous_height}px -> {current_height}px)")
        
        # Verifica se atingiu o limite máximo
        if current_height > max_scroll_height:
            print(f"Atingido limite de rolagem de {max_scroll_height}px")
            # Rola até o limite máximo em vez de até o fim
            await page.evaluate(f'window.scrollTo(0, {max_scroll_height})')
            await asyncio.sleep(1)
            break
        
        # Se não mudou a altura depois de algumas tentativas, sai do loop
        if previous_height == current_height:
            # Rolagens extras para garantir que a página foi totalmente carregada
            for _ in range(3):
                await page.evaluate('window.scrollBy(0, 300)')  # rolagem adicional
                await asyncio.sleep(1)
                # Verifica novamente
                new_height = await page.evaluate('document.body.scrollHeight')
                if new_height > current_height:
                    if new_height > max_scroll_height:
                        print(f"Atingido limite de rolagem de {max_scroll_height}px durante verificação adicional")
                        await page.evaluate(f'window.scrollTo(0, {max_scroll_height})')
                        await asyncio.sleep(1)
                        break
                    current_height = new_height
                    break
            else:
                # Se após as tentativas extras ainda não mudou, consideramos que chegamos ao fim
                print("Fim da página alcançado.")
                break
    
    # Volta ao topo da página
    await page.evaluate('window.scrollTo(0, 0)')
    
    # Pequena pausa para estabilizar
    await asyncio.sleep(1)

async def highlight_interactive_elements(page):
    """
    Destaca elementos interativos na página e coleta informações sobre iframes.
    
    Args:
        page: Objeto page do Playwright
        
    Returns:
        Um dicionário contendo o conteúdo principal e informações sobre iframes
    """
    # Carrega o script JavaScript do arquivo externo
    script_path = Path(__file__).parent / "static" / "highlight_script.js"
    
    with open(script_path, 'r', encoding='utf-8') as f:
        js_script = f.read()
    
    # Adiciona código para executar a função e retornar o resultado
    js_script += """
    // Executa a função e retorna o resultado
    highlightInteractiveElements();
    """
    
    # Executa o script e retorna o resultado
    return await page.evaluate(js_script) 