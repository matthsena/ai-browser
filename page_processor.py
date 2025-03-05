"""
Page processing module for web scraping.
Contains functions for highlighting interactive elements and extracting structured information.
"""

from pathlib import Path
from typing import Dict, Any
import json
from bs4 import BeautifulSoup

async def highlight_interactive_elements(page):
    """
    Highlights interactive elements on the page.
    
    Args:
        page: Playwright page object
        
    Returns:
        A dictionary containing the information about interactive elements
        
    Raises:
        Exception: If any error occurs during the highlighting process
    """
    print("🚀 Running interactive elements script...")
    
    # Load the complete JavaScript script
    script_path = Path(__file__).parent / "static" / "highlight_script.js"
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            js_script = f.read()

        # Load the complete script
        await page.evaluate(js_script)
        
        # Check if the function is available
        func_check = await page.evaluate("typeof highlightInteractiveElements")
        print(f"🔍 Highlight function available? {func_check}")
        
        if func_check != "function":
            error_msg = "Highlight function not available in the page context"
            print(f"🔴 Error: {error_msg}")
            raise Exception(error_msg)
        
        # Execute the function
        result = await page.evaluate("highlightInteractiveElements()")
        print("✅ Script executed successfully!")
        
        # If there was an error in the script, raise an exception
        if result and 'error' in result:
            error_msg = f"Error in highlight script: {result.get('error')}"
            print(f"🔴 {error_msg}")
            raise Exception(error_msg)
        
        
        return result.get("interactiveElements", [])
        
    except Exception as script_error:
        print(f"🔴 Error executing highlight script: {str(script_error)}")
        raise

async def save_json_structure(page, output_path: str = "html_structure.json") -> Dict[str, Any]:
    """
    Creates a JSON representation of the HTML that preserves the DOM hierarchy
    
    Args:
        page: Playwright page object
        output_path: Path to save the HTML structure JSON file
        
    Returns:
        Dictionary with the hierarchical HTML structure of the visible body content
        
    Raises:
        Exception: If an error occurs during the extraction process
    """
    try:
        html_content = await page.content()
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
                "url": page.url,
                "body": process_element(body_element)
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(html_structure, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Visible body HTML structure with preserved hierarchy saved to {output_path}")
        
        return html_structure
    
    except Exception as e:
        print(f"🔴 Error extracting HTML structure: {str(e)}")
        raise