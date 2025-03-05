"""
Page processing module for web scraping.
Contains functions for highlighting interactive elements and extracting structured information.
"""

import asyncio
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

async def highlight_interactive_elements(page):
    """
    Highlights and extracts detailed information about interactive elements on the page.
    Inspired by the browser-use project for better accessibility and interaction with AI agents.
    
    Args:
        page: Playwright page object
        
    Returns:
        A dictionary containing the main content, information about interactive elements
        and structured metadata to facilitate analysis by AI agents.
    """
    # Get main HTML and basic metadata for fallback
    try:
        html_content = await page.content()
        page_title = await page.title()
        page_url = page.url
        
        # Basic result structure in case the main script fails
        fallback_result = {
            "mainContent": html_content,
            "pageTitle": page_title,
            "pageUrl": page_url,
            "interactiveElements": [],
            "iframeInfos": []
        }
    except Exception as fallback_error:
        print(f"🔴 Error preparing alternative result: {str(fallback_error)}")
        fallback_result = {"mainContent": "<html><body>Error</body></html>"}
    
    # Try to get metadata
    try:
        page_metadata = await extract_page_metadata(page)
    except Exception as e:
        print(f"🔴 Error extracting metadata: {str(e)}")
        page_metadata = {}
    
    print("🚀 Running interactive elements script...")
    
    # Load the complete JavaScript script
    script_path = Path(__file__).parent / "static" / "highlight_script.js"
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            js_script = f.read()
        
        # Clear console and add diagnostics
        await page.evaluate("""
            console.clear();
            console.log('Loading highlight script...');
        """)
        
        # Load the complete script
        await page.evaluate(js_script)
        
        # Check if the function is available
        func_check = await page.evaluate("typeof highlightInteractiveElements")
        print(f"🔍 Highlight function available? {func_check}")
        
        if func_check == "function":
            # Try to execute the function
            result = await page.evaluate("highlightInteractiveElements()")
            print("✅ Script executed successfully!")
            
            # If there was an error in the script, return the fallback
            if result and 'error' in result:
                print(f"🔴 Error in script: {result.get('error')}")
                return {**fallback_result, 'error': result.get('error')}
            
            # Enrich the output with structured metadata
            enriched_result = {
                "mainContent": result.get("mainContent", ""),
                "iframeInfos": result.get("iframeInfos", []),
                "interactiveElements": result.get("interactiveElements", []),
                "metadata": page_metadata,
                "timestamp": await page.evaluate("new Date().toISOString()"),
                "pageUrl": await page.evaluate("window.location.href"),
                "pageTitle": await page.evaluate("document.title"),
            }
            
            if 'error' in result:
                enriched_result["error"] = result["error"]
            
            # Add analysis and categorization of interactive elements
            enriched_result["elementCategories"] = categorize_elements(
                enriched_result.get("interactiveElements", [])
            )
            
            return enriched_result
        else:
            print("⚠️ Highlight function not available, using fallback")
            return fallback_result
    except Exception as script_error:
        print(f"🔴 Error executing highlight script: {str(script_error)}")
        return fallback_result

async def extract_page_metadata(page) -> Dict[str, Any]:
    """
    Extrai metadados úteis da página atual.
    
    Args:
        page: Objeto page do Playwright
        
    Returns:
        Dicionário com metadados da página
    """
    metadata_script = """
    () => {
        const metadata = {};
        
        // Coleta meta tags
        const metaTags = Array.from(document.getElementsByTagName('meta'));
        metadata.meta = metaTags.map(tag => {
            const attributes = {};
            Array.from(tag.attributes).forEach(attr => {
                attributes[attr.name] = attr.value;
            });
            return attributes;
        });
        
        // Coleta dados de Open Graph
        metadata.openGraph = {};
        metaTags.forEach(tag => {
            const property = tag.getAttribute('property');
            if (property && property.startsWith('og:')) {
                metadata.openGraph[property.substring(3)] = tag.getAttribute('content');
            }
        });
        
        // Coleta dados de Schema.org (JSON-LD)
        metadata.jsonLd = [];
        const jsonLdScripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
        jsonLdScripts.forEach(script => {
            try {
                const data = JSON.parse(script.textContent);
                metadata.jsonLd.push(data);
            } catch (e) {
                // Ignora erros de parsing
            }
        });
        
        // Tamanho da viewport e página
        metadata.dimensions = {
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            page: {
                width: Math.max(
                    document.body.scrollWidth,
                    document.documentElement.scrollWidth,
                    document.body.offsetWidth,
                    document.documentElement.offsetWidth,
                    document.body.clientWidth,
                    document.documentElement.clientWidth
                ),
                height: Math.max(
                    document.body.scrollHeight,
                    document.documentElement.scrollHeight,
                    document.body.offsetHeight,
                    document.documentElement.offsetHeight,
                    document.body.clientHeight,
                    document.documentElement.clientHeight
                )
            }
        };
        
        return metadata;
    }
    """
    
    return await page.evaluate(metadata_script)

def categorize_elements(elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Categoriza elementos interativos para facilitar análise e interação.
    
    Args:
        elements: Lista de elementos interativos
        
    Returns:
        Dicionário com elementos categorizados
    """
    categories = {
        "navigation": [],    # Links de navegação
        "forms": {           # Elementos de formulário
            "inputs": [],
            "buttons": [],
            "selects": [],
            "checkboxes": [],
            "radios": [],
        },
        "media": [],         # Elementos de mídia
        "interactive": []    # Outros elementos interativos
    }
    
    form_elements = []
    
    # Primeiro passo: identificar os formulários e seus elementos
    for element in elements:
        element_type = element.get("type", "")
        tag_name = element.get("tagName", "")
        
        # Verifica se está dentro de um formulário
        form_id = element.get("formId", "")
        if form_id:
            form_elements.append({
                "formId": form_id,
                "elementId": element.get("id"),
                "type": element_type
            })
        
        # Categoriza por tipo de elemento
        if tag_name == "a" or element_type == "link":
            categories["navigation"].append(element.get("id"))
        elif tag_name in ["input", "textarea", "select", "button"] or element_type.startswith("input-"):
            if element_type == "input-checkbox":
                categories["forms"]["checkboxes"].append(element.get("id"))
            elif element_type == "input-radio":
                categories["forms"]["radios"].append(element.get("id"))
            elif element_type.startswith("input-"):
                categories["forms"]["inputs"].append(element.get("id"))
            elif tag_name == "button" or element_type == "button":
                categories["forms"]["buttons"].append(element.get("id"))
            elif tag_name == "select":
                categories["forms"]["selects"].append(element.get("id"))
        elif tag_name in ["audio", "video", "img", "picture", "canvas"]:
            categories["media"].append(element.get("id"))
        else:
            categories["interactive"].append(element.get("id"))
    
    # Agrupa elementos por formulário
    form_groups = {}
    for form_element in form_elements:
        form_id = form_element["formId"]
        if form_id not in form_groups:
            form_groups[form_id] = []
        form_groups[form_id].append(form_element["elementId"])
    
    categories["forms"]["formGroups"] = form_groups
    
    return categories

async def extract_semantic_structure(page) -> Dict[str, Any]:
    """
    Extrai a estrutura semântica da página (cabeçalhos, navegação, etc.)
    
    Args:
        page: Objeto page do Playwright
        
    Returns:
        Dicionário com estrutura semântica da página
    """
    semantic_script = """
    () => {
        const structure = {
            headings: [],
            landmarks: {
                navigation: [],
                main: null,
                footer: null,
                header: null,
                aside: [],
                search: null
            }
        };
        
        // Extrai cabeçalhos organizados hierarquicamente
        const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
        headings.forEach(heading => {
            structure.headings.push({
                level: parseInt(heading.tagName[1]),
                text: heading.innerText,
                id: heading.id || null
            });
        });
        
        // Extrai landmarks da página (elementos com roles semânticos)
        const navs = Array.from(document.querySelectorAll('nav, [role="navigation"]'));
        navs.forEach(nav => {
            structure.landmarks.navigation.push({
                id: nav.id || null,
                ariaLabel: nav.getAttribute('aria-label') || null,
                position: nav.getBoundingClientRect()
            });
        });
        
        const main = document.querySelector('main, [role="main"]');
        if (main) {
            structure.landmarks.main = {
                id: main.id || null,
                position: main.getBoundingClientRect()
            };
        }
        
        const footer = document.querySelector('footer, [role="contentinfo"]');
        if (footer) {
            structure.landmarks.footer = {
                id: footer.id || null,
                position: footer.getBoundingClientRect()
            };
        }
        
        const header = document.querySelector('header, [role="banner"]');
        if (header) {
            structure.landmarks.header = {
                id: header.id || null,
                position: header.getBoundingClientRect()
            };
        }
        
        const asides = Array.from(document.querySelectorAll('aside, [role="complementary"]'));
        asides.forEach(aside => {
            structure.landmarks.aside.push({
                id: aside.id || null,
                ariaLabel: aside.getAttribute('aria-label') || null,
                position: aside.getBoundingClientRect()
            });
        });
        
        const search = document.querySelector('[role="search"]');
        if (search) {
            structure.landmarks.search = {
                id: search.id || null,
                position: search.getBoundingClientRect()
            };
        }
        
        return structure;
    }
    """
    
    return await page.evaluate(semantic_script) 