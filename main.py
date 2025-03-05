import asyncio
import argparse
from dataclasses import dataclass, field
from typing import List
import time
import json

# Import modules from our new structure
from browser_config import create_browser_context
from page_processor import highlight_interactive_elements, save_json_structure
from playwright.async_api import async_playwright

@dataclass
class ScraperConfig:
    """Data class for all scraper configuration values"""
    url: str
    timeout: int = 60000
    wait_until: str = "load"
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
        '--window-size=2000,2000',
        '--start-maximized'
    ])
    output_json_path: str = "interactive_elements.json"
    structure_json_path: str = "html_structure.json"
    final_wait_time: int = 100

async def process_webpage(config: ScraperConfig):
    """
    Process a web page according to the configuration provided.
    
    Args:
        config: ScraperConfig object with all settings
    """
    print(f"🌐 Accessing {config.url} (waiting for '{config.wait_until}' event, timeout: {config.timeout}ms)")
    
    
    async with async_playwright() as p:
        browser = None
        context = None
        page = None
        
        try:
            browser = await p.chromium.launch(
                headless=False, 
                args=config.browser_args,
                devtools=False
            )
            context = await create_browser_context(browser)
            page = await context.new_page()
            
            page.on("dialog", lambda dialog: dialog.dismiss())
            
            start_time = time.time()
            
            await page.goto(config.url, wait_until=config.wait_until, timeout=config.timeout)
            
            load_time = time.time() - start_time
            load_time_ms = load_time * 1000
            print(f"⏱️ Page loaded in {load_time:.2f} seconds ({load_time_ms:.0f}ms)")
            
            print("⏳ Waiting for initial loading...")
            await asyncio.sleep(config.initial_wait)
            
            print("🔍 Running script to process interactive elements...")
            
            try:
                result = await highlight_interactive_elements(page)
            except Exception as e:
                print(f"🔴 Error during interactive elements processing: {str(e)}")
                raise
            try:
                print("🔍 Extracting hierarchical visible body HTML structure...")
                await save_json_structure(page, config.structure_json_path)
                print(f"📊 Extracted hierarchical visible body HTML structure preserving DOM relationships")
            except Exception as structure_error:
                print(f"🔴 Error extracting hierarchical visible body HTML structure: {str(structure_error)}")
                raise 
            
            try:
                print("📊 Processing interactive elements...")
                
                with open(config.output_json_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                print(f"💾 Interactive elements data saved as {config.output_json_path}")
                print(f"🔢 Total of {len(result)} interactive elements identified")
            except Exception as save_error:
                print(f"🔴 Error saving interactive elements data: {str(save_error)}")
                raise 
                        
            print("✅ Process completed. Keeping browser open for viewing...")
            print("⌨️ Press Ctrl+C when you want to close.")
            try:
                while True:
                    await asyncio.sleep(config.final_wait_time)
                    print("🔄 Browser still open. Press Ctrl+C to exit.")
            except KeyboardInterrupt:
                pass
            
        except Exception as e:
            print(f"🔴 Fatal error during processing: {str(e)}")
            raise
        finally:
            try:
                if page:
                    await page.close()
                if context:
                    await context.close()
                if browser:
                    await browser.close()
                print("🧹 Browser resources released. Program finished.")
            except Exception:
                pass

async def main():
    parser = argparse.ArgumentParser(description='Captures and processes a web page to extract interactive elements')
    parser.add_argument('url', help='URL of the page to process')
    parser.add_argument('--timeout', type=int, default=60000, help='Timeout in ms (default: 60000)')
    parser.add_argument('--wait', choices=['load', 'domcontentloaded', 'networkidle', 'commit'], 
                        default='load', help='Event to wait for (default: load)')
    parser.add_argument('--output-json', type=str, default='interactive_elements.json',
                        help='Path to save the interactive elements JSON file')
    parser.add_argument('--semantic-json', type=str, default='semantic_html.json',
                        help='Path to save the semantic HTML structure JSON file')
    parser.add_argument('--structure-json', type=str, default='html_structure.json',
                        help='Path to save the hierarchical visible body HTML structure JSON file')
    
    args = parser.parse_args()
    
    config = ScraperConfig(
        url=args.url,
        timeout=args.timeout,
        wait_until=args.wait,
        output_json_path=args.output_json,
        structure_json_path=args.structure_json
    )
    
    await process_webpage(config)

if __name__ == "__main__":
    asyncio.run(main())