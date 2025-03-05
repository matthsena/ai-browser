import asyncio
import argparse
from dataclasses import dataclass, field
from typing import List, Optional
import time
import json

# Import modules from our new structure
from browser_config import create_browser_context
from page_processor import highlight_interactive_elements
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
        '--start-fullscreen'
    ])
    output_interactive_elements_json_path: str = "interactive_elements.json"
    final_wait_time: int = 100

def generate_interactive_elements_table(interactive_elements):
    """
    Generates a table in markdown format with information about interactive elements.
    
    Args:
        interactive_elements: List of interactive elements collected during processing
        
    Returns:
        String containing the table in markdown format
    """
    if not interactive_elements:
        return "No interactive elements found on the page."
    
    # Table header
    markdown_table = "# Interactive Elements Table\n\n"
    markdown_table += "| ID | Type | Text | Placeholder | Label | Element | HTML ID | Iframe |\n"
    markdown_table += "|-----|------------|------------|--------------|----------|----------|----------|----------|\n"
    
    # Add each element to the table
    for element in interactive_elements:
        # Get the field values for the table
        id_value = f"#{element['id']}"
        element_type = element['type']
        
        # Get the main text of the element
        content = element['content']
        text = content.get('text', '') if isinstance(content, dict) else ''
        
        # Get the placeholder if available
        placeholder = ''
        if isinstance(content, dict) and 'placeholder' in content:
            placeholder = content['placeholder']
        elif 'attributes' in element and 'placeholder' in element['attributes']:
            placeholder = element['attributes']['placeholder']
            
        # Get the associated label if available
        label = ''
        if isinstance(content, dict) and 'label' in content:
            label = content['label']
            
        # Format the iframe ID (if any)
        iframe_id = element.get('iframeId', '')
        
        # Format the HTML ID (if any)
        html_id = element.get('htmlId', '')
        
        # Format the HTML element type
        html_element = element.get('tagName', '')
        
        # Escape pipes and line breaks to avoid breaking the table formatting
        text = text.replace('|', '\\|').replace('\n', ' ')
        placeholder = placeholder.replace('|', '\\|').replace('\n', ' ')
        label = label.replace('|', '\\|').replace('\n', ' ')
        
        # Limit the text length to avoid making the table too large
        if len(text) > 50:
            text = text[:47] + "..."
        if len(placeholder) > 30:
            placeholder = placeholder[:27] + "..."
        if len(label) > 30:
            label = label[:27] + "..."
            
        # Add the row to the table
        markdown_table += f"| {id_value} | {element_type} | {text} | {placeholder} | {label} | {html_element} | {html_id} | {iframe_id} |\n"
    
    # Add statistics at the end
    markdown_table += f"\n\n## Statistics\n\n"
    markdown_table += f"- **Total interactive elements:** {len(interactive_elements)}\n"
    
    # Count element types
    element_types = {}
    for element in interactive_elements:
        element_type = element['type']
        element_types[element_type] = element_types.get(element_type, 0) + 1
    
    markdown_table += "- **Element types:**\n"
    for element_type, count in element_types.items():
        markdown_table += f"  - {element_type}: {count}\n"
    
    return markdown_table

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
            # Launch browser in full screen without devtools
            browser = await p.chromium.launch(
                headless=False, 
                args=config.browser_args,
                devtools=False  # Keep DevTools closed
            )
            context = await create_browser_context(browser)
            page = await context.new_page()
            
            # Configure to automatically close dialogs
            page.on("dialog", lambda dialog: dialog.dismiss())
            
            # Start timer to measure loading time
            start_time = time.time()
            
            await page.goto(config.url, wait_until=config.wait_until, timeout=config.timeout)
            
            # Calculate loading time
            load_time = time.time() - start_time
            load_time_ms = load_time * 1000
            print(f"⏱️ Page loaded in {load_time:.2f} seconds ({load_time_ms:.0f}ms)")
            
            # Wait additional time for initial loading
            print("⏳ Waiting for initial loading...")
            await asyncio.sleep(config.initial_wait)
            
            # Process interactive elements
            print("🔍 Running script to process interactive elements...")
            
            # Open dev tools console for debugging
            await page.evaluate("""
                console.clear();
                console.log('Starting interactive elements processing...');
                window.onerror = function(msg, url, line, col, error) {
                    console.error('Global JavaScript error:', msg, 'in', url, 'line:', line);
                    console.error('Stack:', error ? error.stack : 'Not available');
                    return false;
                };
            """)
            
            result = await highlight_interactive_elements(page)
            
            # If there was an error, warn, but try to continue with the main content
            if result and 'error' in result:
                print(f"⚠️ WARNING: There was an error processing interactive elements: {result['error']}")
                print("🔄 Continuing with processing...")
            
            # Save interactive elements data as JSON if available
            if 'interactiveElements' in result and result['interactiveElements']:
                try:
                    print("📊 Processing interactive elements...")
                    interactive_elements = result['interactiveElements']
                    
                    # Save the complete interactive elements data as JSON
                    with open(config.output_interactive_elements_json_path, 'w', encoding='utf-8') as f:
                        json.dump(interactive_elements, f, ensure_ascii=False, indent=2)
                    
                    print(f"💾 Interactive elements data saved as {config.output_interactive_elements_json_path}")
                    print(f"🔢 Total of {len(interactive_elements)} interactive elements identified")
                except Exception as interactive_error:
                    print(f"🔴 Error processing interactive elements: {str(interactive_error)}")
            else:
                print("ℹ️ No information about interactive elements was found in the results.")
            
            # Keep browser open for viewing
            print("✅ Process completed. Keeping browser open for viewing...")
            print("⌨️ Press Ctrl+C when you want to close.")
            try:
                while True:
                    await asyncio.sleep(config.final_wait_time)
                    print("🔄 Browser still open. Press Ctrl+C to exit.")
            except KeyboardInterrupt:
                pass
            
        except Exception as e:
            print(f"🔴 Error during processing: {str(e)}")
            print("🔄 Trying to capture available data...")
            
            # Even on error, try to extract any interactive elements that may be available
            if page:
                try:
                    # Try to extract any interactive elements still available
                    result = await highlight_interactive_elements(page)
                    
                    if result and 'interactiveElements' in result and result['interactiveElements']:
                        with open(config.output_interactive_elements_json_path, 'w', encoding='utf-8') as f:
                            json.dump(result['interactiveElements'], f, ensure_ascii=False, indent=2)
                        
                        print(f"💾 Partial interactive elements data saved as {config.output_interactive_elements_json_path}")
                    
                    # Keep the browser open to allow manual inspection
                    print("🔍 Keeping browser open for analysis. Press Ctrl+C to exit when finished.")
                    
                    try:
                        while True:
                            await asyncio.sleep(10)
                            print("🔄 Browser still open. Press Ctrl+C to exit.")
                    except KeyboardInterrupt:
                        pass
                except Exception as inner_e:
                    print(f"🔴 Error: Failed to extract interactive elements: {str(inner_e)}")
            else:
                print("🔴 Unable to capture data: page was not properly initialized")
            
            # Try to keep the browser open for manual analysis
            print("🔍 Trying to keep the browser open for manual analysis...")
            try:
                while browser and not browser.is_closed():
                    await asyncio.sleep(10)
                    print("🔄 Browser still open. Press Ctrl+C to exit.")
            except (KeyboardInterrupt, Exception):
                pass
        finally:
            # Release all browser resources when the program exits
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
    
    args = parser.parse_args()
    
    config = ScraperConfig(
        url=args.url,
        timeout=args.timeout,
        wait_until=args.wait,
        output_interactive_elements_json_path=args.output_json
    )
    
    await process_webpage(config)

if __name__ == "__main__":
    asyncio.run(main())