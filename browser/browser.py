import asyncio
import json
import os
import time
import logging
from typing import Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Browser, BrowserContext
import datetime

logger = logging.getLogger('browser_jsonfy')
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    format='%(asctime)s | %(levelname)s | %(funcName)s - %(message)s',
    level=getattr(logging, log_level)
)

load_dotenv()

class Browser:
    """Classe referente ao navegador e todas as operações feitas nele.
    
    PADRÃO SINGLETON PARA UMA UNICA INSTANCIA DO BROWSER
    """
    _instance = None
    _initialized = False
    
    def __new__(cls, url: str = "about:blank"):
        try:
            if cls._instance is None:
                logger.info("🔰 Criando nova instância singleton do BrowserJsonfy")
                cls._instance = super(Browser, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
        except Exception as e:
            logger.error(f"❌ Erro ao criar instância do BrowserJsonfy: {str(e)}")
            raise Exception(f"Erro ao criar instância do BrowserJsonfy: {str(e)}")
    
    def __init__(self, url: str = "about:blank"):
        try:
            if self._initialized:
                return
                
            self.url = url
            self.timeout = int(os.getenv("TIMEOUT", "60000"))
            self.wait_until = os.getenv("WAIT_UNTIL", "load")
            self.initial_wait = int(os.getenv("INITIAL_WAIT", "3"))
            self.headless = os.getenv("HEADLESS", "false").lower() == "true"
            self.devtools = os.getenv("DEVTOOLS", "false").lower() == "true"
            self.final_wait_time = int(os.getenv("FINAL_WAIT_TIME", "100"))
            self.output_json_path = os.getenv("OUTPUT_JSON_PATH", "interactive_elements.json")
            self.structure_json_path = os.getenv("STRUCTURE_JSON_PATH", "html_structure.json")
            self.screenshot_path = os.getenv("SCREENSHOT_PATH", "screenshots/screenshot.png")
                
            # Inicializar componentes do Playwright
            self.browser = None
            self.context = None
            self.page = None
            
            self.html_structured = None
                
            # configurações do Playwright
            self.browser_args = [
                "--disable-web-security",
                "--disable-site-isolation-trials",
                "--disable-features=IsolateOrigins,site-per-process",
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-breakpad",
                "--disable-component-extensions-with-background-pages",
                "--disable-extensions",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection",
                "--disable-renderer-backgrounding",
                "--enable-automation",
                "--password-store=basic"
            ]
            
            logger.debug(f"🔧 Configuração: timeout={self.timeout}, wait_until={self.wait_until}")
            
            self._initialized = True
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar BrowserJsonfy: {str(e)}")
            raise Exception(f"Erro ao inicializar BrowserJsonfy: {str(e)}")
    
    async def __create_browser_context(self, browser: Browser) -> BrowserContext:
        try:
            logger.debug("🔒 Criando contexto do navegador com configurações de segurança")
            
            context = await browser.new_context(
                permissions=[],
                geolocation=None,
                ignore_https_errors=True,
                java_script_enabled=True,
                bypass_csp=True
            )
            
            permissions_to_deny = [
                'geolocation', 'microphone', 'camera', 'notifications', 'midi',
                'background-sync', 'ambient-light-sensor', 'accelerometer', 
                'gyroscope', 'magnetometer', 'accessibility-events',
                'clipboard-read', 'clipboard-write', 'payment-handler', 'midi-sysex'
            ]
            
            for permission in permissions_to_deny:
                await context.route('**/*', lambda route: route.continue_())
                try:
                    await context.set_permission(permission, 'denied')
                except Exception as e:
                    logger.debug(f"⚠️ Não foi possível definir a permissão {permission}: {str(e)}")
                    pass
            
            return context
        except Exception as e:
            logger.error(f"❌ Erro ao criar contexto do navegador: {str(e)}")
            raise Exception(f"Erro ao criar contexto do navegador: {str(e)}")
    
    async def __highlight_interactive_elements(self) -> List[Dict[str, Any]]:
        try:
            logger.info("🔍 Executando script de elementos interativos...")
            
            if not self.page:
                raise ValueError("Página não inicializada")
            
            script_path = Path(__file__).parent / "static" / "highlight_script.js"
            
            with open(script_path, 'r', encoding='utf-8') as f:
                js_script = f.read()

            await self.page.evaluate(js_script)
            
            func_check = await self.page.evaluate("typeof highlightInteractiveElements")
            logger.debug(f"✓ Função de destaque disponível? {func_check}")
            
            if func_check != "function":
                error_msg = "Função de destaque não disponível no contexto da página"
                logger.error(error_msg)
                raise Exception(error_msg)

            elements = await self.page.evaluate("highlightInteractiveElements()")
            logger.info(f"✅ {len(elements)} elementos interativos identificados")
            
            return elements
        except Exception as e:
            logger.error(f"❌ Erro ao destacar elementos interativos: {str(e)}")
            raise Exception(f"Erro ao destacar elementos interativos: {str(e)}")
    
    async def __save_json_structure(self) -> Dict[str, Any]:
        try:
            if not self.page:
                raise ValueError("Página não inicializada")
            
            from bs4 import BeautifulSoup
            
            logger.info("📋 Extraindo estrutura HTML hierárquica do corpo visível...")
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
                raise Exception("Não foi possível encontrar o elemento body no conteúdo HTML")
                
            html_structure = {
                "document": {
                    "title": soup.title.text if soup.title else None,
                    "url": self.page.url,
                    "body": process_element(body_element)
                }
            }
            
            logger.info(f"💾 Estrutura HTML do corpo visível salva em {self.structure_json_path}")
            return html_structure
        except Exception as e:
            logger.error(f"❌ Erro ao extrair estrutura HTML: {str(e)}")
            raise Exception(f"Erro ao extrair estrutura HTML: {str(e)}")
    
    async def process(self) -> Dict[str, Any]:
        try:
            logger.info(f"🔄 Processando {self.url} (aguardando evento '{self.wait_until}', timeout: {self.timeout}ms)")
            
            result = {}
            
            if not self.page:
                await self._initialize_browser()
            
            if self.page.url != self.url:
                await self.navigate_to(self.url)
            
            logger.info("⏳ Aguardando carregamento inicial...")
            await asyncio.sleep(self.initial_wait)
            
            logger.info("🔍 Processando elementos interativos...")
            
            interactive_elements = await self.__highlight_interactive_elements()
            
            logger.info(f"💾 Dados de elementos interativos salvos em {self.output_json_path}")
            
            html_structure = await self.__save_json_structure()
            
            logger.info("✅ Processamento concluído com sucesso")
            
            result = html_structure
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro fatal durante o processamento: {str(e)}")
            raise Exception(f"Erro fatal durante o processamento: {str(e)}")

    @classmethod
    def get_instance(cls, url: str = "about:blank"):
        try:
            return cls(url)
        except Exception as e:
            logger.error(f"❌ Erro ao obter instância singleton: {str(e)}")
            raise Exception(f"Erro ao obter instância singleton: {str(e)}")

    async def navigate_to(self, url: str, wait_until: str = None, timeout: int = None) -> None:
        try:
            if not self.page:
                await self._initialize_browser()
                
            wait_until = wait_until or self.wait_until
            timeout = timeout or self.timeout
            
            logger.info(f"🌐 Navegando para: {url} (wait_until: {wait_until}, timeout: {timeout}ms)")
            start_time = time.time()
            
            await self.page.goto(url, wait_until=wait_until, timeout=timeout)
            
            load_time = time.time() - start_time
            load_time_ms = load_time * 1000
            logger.info(f"⏱️ Página carregada em {load_time:.2f} segundos ({load_time_ms:.0f}ms)")
            
            self.url = url
        except Exception as e:
            logger.error(f"❌ Erro ao navegar para {url}: {str(e)}")
            raise Exception(f"Erro ao navegar para {url}: {str(e)}")
    
    async def click(self, selector: str, timeout: int = None) -> None:
        try:
            if not self.page:
                raise ValueError("Página não inicializada. Chame process() ou navigate_to() primeiro.")
                
            timeout = timeout or self.timeout
            logger.info(f"🖱️ Clicando no elemento com seletor: {selector}")
            
            await self.page.click(selector, timeout=timeout)
            logger.debug(f"✅ Elemento clicado: {selector}")
        except Exception as e:
            logger.error(f"❌ Erro ao clicar no elemento {selector}: {str(e)}")
            raise Exception(f"Erro ao clicar no elemento {selector}: {str(e)}")
    
    async def fill(self, selector: str, value: str, timeout: int = None) -> None:
        try:
            if not self.page:
                raise ValueError("Página não inicializada. Chame process() ou navigate_to() primeiro.")
                
            timeout = timeout or self.timeout
            logger.info(f"✏️ Preenchendo elemento com seletor: {selector}")
            
            await self.page.fill(selector, value, timeout=timeout)
            logger.debug(f"✅ Elemento preenchido: {selector} com valor: {value}")
        except Exception as e:
            logger.error(f"❌ Erro ao preencher o elemento {selector}: {str(e)}")
            raise Exception(f"Erro ao preencher o elemento {selector}: {str(e)}")
    
    async def get_page_metadata(self) -> Dict[str, Any]:
        try:
            if not self.page:
                raise ValueError("Página não inicializada. Chame process() ou navigate_to() primeiro.")
            
            title = await self.page.title()
            
            metrics = await self.page.evaluate("""() => {
                return {
                    windowWidth: window.innerWidth,
                    windowHeight: window.innerHeight,
                    documentHeight: document.body.scrollHeight,
                    userAgent: navigator.userAgent,
                    loadTime: performance.timing ? 
                        (performance.timing.loadEventEnd - performance.timing.navigationStart) : null
                }
            }""")
            
            metadata = {
                "title": title,
                "url": self.page.url,
                "metrics": metrics,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            logger.info(f"📊 Metadados da página obtidos: {title}")
            return metadata
        
        except Exception as e:
            logger.error(f"❌ Erro ao obter metadados da página: {str(e)}")
            raise Exception(f"Erro ao obter metadados da página: {str(e)}")
    
    async def press_enter(self, selector: str, timeout: int = None) -> None:
        try:
            if not self.page:
                raise ValueError("Página não inicializada. Chame process() ou navigate_to() primeiro.")
                
            timeout = timeout or self.timeout
            
            await self.page.press(selector, "Enter", timeout=timeout)
            logger.debug(f"✅ Tecla Enter pressionada: {selector}")
        except Exception as e:
            logger.error(f"❌ Erro ao pressionar a tecla Enter no elemento {selector}: {str(e)}")
            raise Exception(f"Erro ao pressionar a tecla Enter no elemento {selector}: {str(e)}")
    
    async def take_screenshot(self, path: str = None, full_page: bool = True) -> str:
        try:
            if not self.page:
                raise ValueError("Página não inicializada. Chame process() ou navigate_to() primeiro.")
                
            screenshot_path = path or self.screenshot_path
            
            logger.info(f"📸 Tirando captura de tela {'da página inteira' if full_page else 'da viewport'}: {screenshot_path}")
            
            await self.page.screenshot(path=screenshot_path, full_page=full_page)
            
            logger.info(f"✅ Captura de tela salva em: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            logger.error(f"❌ Erro ao tirar captura de tela: {str(e)}")
            raise Exception(f"Erro ao tirar captura de tela: {str(e)}")
    
    async def _initialize_browser(self) -> None:
        try:
            if self.browser and self.context and self.page:
                return
                
            logger.info("🚀 Inicializando navegador...")
            
            playwright = await async_playwright().start()
            
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=self.browser_args,
                devtools=self.devtools
            )
            self.context = await self.__create_browser_context(self.browser)
            self.page = await self.context.new_page()
            
            self.page.on("dialog", lambda dialog: dialog.dismiss())
            
            if self.url:
                await self.navigate_to(self.url)
                
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar navegador: {str(e)}")
            raise Exception(f"Erro ao inicializar navegador: {str(e)}") 