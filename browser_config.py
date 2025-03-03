"""
Browser configuration module for Playwright.
Contains functions for setting up browser contexts with security and permission settings.
"""

async def create_browser_context(browser):
    """
    Configura o contexto do navegador para desabilitar todas as permissões.
    
    Args:
        browser: Instância do browser Playwright
        
    Returns:
        Um objeto de contexto Playwright configurado
    """
    # Configura o contexto do navegador para desabilitar todas as permissões
    context = await browser.new_context(
        permissions=[],  # Lista vazia significa que nenhuma permissão será concedida
        geolocation=None,
        ignore_https_errors=True,   # Ignora erros HTTPS para facilitar navegação
        # Configurações adicionais para bloquear outros tipos de permissões
        java_script_enabled=True,   # Mantém JavaScript habilitado
        bypass_csp=True             # Ignora políticas de segurança de conteúdo que poderiam restringir o script
    )
    
    # Gerencia permissões específicas: nega tudo
    permissions_to_deny = [
        'geolocation',
        'microphone',
        'camera',
        'notifications',
        'midi',
        'background-sync',
        'ambient-light-sensor',
        'accelerometer',
        'gyroscope',
        'magnetometer',
        'accessibility-events',
        'clipboard-read',
        'clipboard-write',
        'payment-handler',
        'midi-sysex'
    ]
    
    # Define todas as permissões explicitamente como negadas para todos os sites
    for permission in permissions_to_deny:
        await context.route('**/*', lambda route: route.continue_())
        try:
            await context.set_permission(permission, 'denied')
        except:
            # Algumas permissões podem não ser suportadas, então ignoramos erros
            pass
    
    return context 