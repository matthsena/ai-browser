"""
Browser configuration module for Playwright.
Contains functions for setting up browser contexts with security and permission settings.
"""

async def create_browser_context(browser):
    """
    Configures the browser context to disable all permissions.
    
    Args:
        browser: Playwright browser instance
        
    Returns:
        A configured Playwright context object
    """
    # Configure the browser context to disable all permissions
    context = await browser.new_context(
        permissions=[],  # Empty list means no permissions will be granted
        geolocation=None,
        ignore_https_errors=True,   # Ignore HTTPS errors to facilitate navigation
        # Additional settings to block other types of permissions
        java_script_enabled=True,   # Keep JavaScript enabled
        bypass_csp=True             # Ignore content security policies that could restrict the script
    )
    
    # Manage specific permissions: deny everything
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
    
    # Explicitly set all permissions as denied for all sites
    for permission in permissions_to_deny:
        await context.route('**/*', lambda route: route.continue_())
        try:
            await context.set_permission(permission, 'denied')
        except:
            # Some permissions may not be supported, so we ignore errors
            pass
    
    return context 