"""
BrowserJsonfy class for extracting interactive elements and HTML structure from web pages.
"""

import asyncio
import json
import os
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# Configure logger
logger = logging.getLogger('browser_jsonfy')
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    format='%(asctime)s | %(levelname)s | %(funcName)s - %(message)s',
    level=getattr(logging, log_level)
)

# Load environment variables
load_dotenv()

class BrowserJsonfy:
    """Class for extracting interactive elements and HTML structure from web pages."""
    
    def __init__(self, url: str):
        """
        Initialize BrowserJsonfy with URL.
        
        Args:
            url: URL of the page to process
        """
        self.url = url
        self.timeout = int(os.getenv("TIMEOUT", "60000"))
        self.wait_until = os.getenv("WAIT_UNTIL", "load")
        self.initial_wait = int(os.getenv("INITIAL_WAIT", "3"))
        self.headless = os.getenv("HEADLESS", "false").lower() == "true"
        self.devtools = os.getenv("DEVTOOLS", "false").lower() == "true"
        self.final_wait_time = int(os.getenv("FINAL_WAIT_TIME", "100"))
        self.output_json_path = os.getenv("OUTPUT_JSON_PATH", "interactive_elements.json")
        self.structure_json_path = os.getenv("STRUCTURE_JSON_PATH", "html_structure.json")
        
        # Hard-coded browser arguments instead of reading from environment
        # Include only arguments that are compatible with Playwright
        self.browser_args = [
            "--disable-web-security",
            "--disable-site-isolation-trials",
            "--disable-features=IsolateOrigins,site-per-process",
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--disable-background-timer-throttling",
            "--disable-popup-blocking",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-window-activation",
            "--disable-focus-on-load",
            "--no-first-run",
            "--no-default-browser-check",
            "--window-position=0,0",
            "--window-size=2000,2000",
            "--start-maximized"
        ]
        
        logger.debug(f"Using browser arguments: {self.browser_args}")
        
        # Playwright components
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        logger.debug(f"BrowserJsonfy initialized with URL: {url}")
        logger.debug(f"Configuration: timeout={self.timeout}, wait_until={self.wait_until}")
    
    async def __create_browser_context(self, browser: Browser) -> BrowserContext:
        """
        Configures the browser context to disable all permissions.
        
        Args:
            browser: Playwright browser instance
            
        Returns:
            A configured Playwright context object
        """
        logger.debug("Creating browser context with security settings")
        
        # Configure the browser context to disable all permissions
        context = await browser.new_context(
            permissions=[],  # Empty list means no permissions will be granted
            geolocation=None,
            ignore_https_errors=True,   # Ignore HTTPS errors to facilitate navigation
            java_script_enabled=True,   # Keep JavaScript enabled
            bypass_csp=True             # Ignore content security policies that could restrict the script
        )
        
        # Manage specific permissions: deny everything
        permissions_to_deny = [
            'geolocation', 'microphone', 'camera', 'notifications', 'midi',
            'background-sync', 'ambient-light-sensor', 'accelerometer', 
            'gyroscope', 'magnetometer', 'accessibility-events',
            'clipboard-read', 'clipboard-write', 'payment-handler', 'midi-sysex'
        ]
        
        # Explicitly set all permissions as denied for all sites
        for permission in permissions_to_deny:
            await context.route('**/*', lambda route: route.continue_())
            try:
                await context.set_permission(permission, 'denied')
            except Exception as e:
                logger.debug(f"Could not set permission {permission}: {str(e)}")
                # Some permissions may not be supported, so we ignore errors
                pass
        
        return context
    
    async def __highlight_interactive_elements(self) -> List[Dict[str, Any]]:
        """
        Highlights interactive elements on the page.
        
        Returns:
            A list of dictionaries containing information about interactive elements
            
        Raises:
            Exception: If any error occurs during the highlighting process
        """
        logger.info("Running interactive elements script...")
        
        if not self.page:
            raise ValueError("Page not initialized")
        
        # Load the complete JavaScript script
        script_path = Path(__file__).parent / "static" / "highlight_script.js"
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                js_script = f.read()

            # Load the complete script
            await self.page.evaluate(js_script)
            
            # Check if the function is available
            func_check = await self.page.evaluate("typeof highlightInteractiveElements")
            logger.debug(f"Highlight function available? {func_check}")
            
            if func_check != "function":
                error_msg = "Highlight function not available in the page context"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            # Execute the function
            result = await self.page.evaluate("highlightInteractiveElements()")
            logger.info("Script executed successfully!")
            
            # If there was an error in the script, raise an exception
            if result and 'error' in result:
                error_msg = f"Error in highlight script: {result.get('error')}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            return result.get("interactiveElements", [])
            
        except Exception as script_error:
            logger.error(f"Error executing highlight script: {str(script_error)}")
            raise
    
    async def __save_json_structure(self) -> Dict[str, Any]:
        """
        Creates a JSON representation of the HTML that preserves the DOM hierarchy
        
        Returns:
            Dictionary with the hierarchical HTML structure of the visible body content
            
        Raises:
            Exception: If an error occurs during the extraction process
        """
        try:
            if not self.page:
                raise ValueError("Page not initialized")
            
            from bs4 import BeautifulSoup
            
            html_content = await self.page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            def process_element(element):
                if (element.name is None or 
                    element.name in ['script', 'style', 'noscript']):
                    return None
                    
                if element.name == 'input' and element.get('type') == 'hidden':
                    return None
                                  
                if isinstance(element, str):
                    text = element.strip()
                    if text:
                        return {"type": "text", "content": text}
                    return None
                
                result = {
                    "tag": element.name,
                    "children": []
                }
                
                allowed_attrs = ['value', 'placeholder', 'selected', 'checked', 'multiple', 
                               'href', 'title', 'type', 'disabled', 'readonly', 'required']
                
                if 'data-interactive-id' in element.attrs:
                    result['data-interactive-id'] = element.attrs['data-interactive-id']
                    
                for attr in allowed_attrs:
                    if attr in element.attrs:
                        result[attr] = element.attrs[attr]
                
                text_content = element.get_text(strip=True)
                if text_content:
                    result["innerText"] = text_content
                
                for child in element.children:
                    child_data = process_element(child)
                    if child_data is not None:
                        result["children"].append(child_data)
                
                if not result["children"] and not element.get_text(strip=True):
                    if element.name in ['img', 'br', 'hr', 'input', 'link', 'meta', 'source', 'track', 'wbr']:
                        pass
                    else:
                        return None
                
                return result
                
            body_element = soup.body
            
            if not body_element:
                raise Exception("Could not find body element in the HTML content")
                
            html_structure = {
                "document": {
                    "title": soup.title.text if soup.title else None,
                    "url": self.page.url,
                    "body": process_element(body_element)
                }
            }
            
            with open(self.structure_json_path, 'w', encoding='utf-8') as f:
                json.dump(html_structure, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Visible body HTML structure with preserved hierarchy saved to {self.structure_json_path}")
            
            return html_structure
        
        except Exception as e:
            logger.error(f"Error extracting HTML structure: {str(e)}")
            raise
    
    async def process(self) -> Dict[str, Any]:
        """
        Process the web page - Launch browser, navigate to URL, extract interactive
        elements and HTML structure, then close browser.
        
        Returns:
            Dictionary containing interactive elements and HTML structure
        """
        logger.info(f"Accessing {self.url} (waiting for '{self.wait_until}' event, timeout: {self.timeout}ms)")
        
        result = {}
        
        async with async_playwright() as p:
            self.browser = None
            self.context = None
            self.page = None
            
            try:
                logger.debug(f"Browser launch arguments: {self.browser_args}")
                
                # Use the hard-coded browser arguments
                self.browser = await p.chromium.launch(
                    headless=self.headless,
                    args=self.browser_args,
                    devtools=self.devtools
                )
                self.context = await self.__create_browser_context(self.browser)
                self.page = await self.context.new_page()
                
                self.page.on("dialog", lambda dialog: dialog.dismiss())
                
                start_time = time.time()
                
                await self.page.goto(self.url, wait_until=self.wait_until, timeout=self.timeout)
                
                load_time = time.time() - start_time
                load_time_ms = load_time * 1000
                logger.info(f"Page loaded in {load_time:.2f} seconds ({load_time_ms:.0f}ms)")
                
                logger.info("Waiting for initial loading...")
                await asyncio.sleep(self.initial_wait)
                
                logger.info("Processing interactive elements...")
                
                interactive_elements = await self.__highlight_interactive_elements()
                
                with open(self.output_json_path, 'w', encoding='utf-8') as f:
                    json.dump(interactive_elements, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Interactive elements data saved as {self.output_json_path}")
                logger.info(f"Total of {len(interactive_elements)} interactive elements identified")
                
                logger.info("Extracting hierarchical visible body HTML structure...")
                html_structure = await self.__save_json_structure()
                
                result = {
                    "url": self.url,
                    "interactive_elements_count": len(interactive_elements),
                    "interactive_elements_path": self.output_json_path,
                    "html_structure_path": self.structure_json_path,
                    "load_time_ms": load_time_ms
                }
                
                logger.info("Process completed. Keeping browser open for viewing...")
                logger.info("Press Ctrl+C when you want to close.")
                
                try:
                    while True:
                        await asyncio.sleep(self.final_wait_time)
                        logger.info("Browser still open. Press Ctrl+C to exit.")
                except KeyboardInterrupt:
                    logger.info("Received KeyboardInterrupt. Closing browser...")
                
                return result
                
            except Exception as e:
                logger.error(f"Fatal error during processing: {str(e)}")
                raise
                
            finally:
                try:
                    if self.page:
                        await self.page.close()
                    if self.context:
                        await self.context.close()
                    if self.browser:
                        await self.browser.close()
                    logger.info("Browser resources released. Program finished.")
                except Exception as close_error:
                    logger.error(f"Error closing browser resources: {str(close_error)}") 