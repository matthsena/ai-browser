"""
HTML processing module.
Contains functions for processing HTML content and managing iframes.
"""

def process_html_with_iframes(result):
    """
    Processa o HTML principal substituindo iframes pelo seu conteúdo.
    
    Args:
        result: Dicionário contendo o conteúdo principal e informações sobre iframes
        
    Returns:
        String contendo o HTML consolidado
    """
    # Pega o conteúdo HTML principal
    consolidated_html = result['mainContent']
    
    # Para cada iframe, substitui a tag pelo conteúdo do iframe
    for iframe_data in result['iframeInfos']:
        # Formato para buscar o iframe exato no HTML
        iframe_pattern = iframe_data['outerHTML']
        
        # Prepara o conteúdo de substituição com comentários para identificação
        replacement = f"""
<!-- INÍCIO DO CONTEÚDO DO IFRAME: {iframe_data['id']} (src: {iframe_data['src']}) -->
{iframe_data['content']}
<!-- FIM DO CONTEÚDO DO IFRAME: {iframe_data['id']} -->
"""
        # Realiza a substituição no HTML consolidado
        consolidated_html = consolidated_html.replace(iframe_pattern, replacement)
    
    return consolidated_html 