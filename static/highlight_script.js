// Function to highlight interactive elements on a webpage
async function highlightInteractiveElements() {
    try {
        console.log("Starting highlightInteractiveElements function");
        
        // Helper functions
        function applyHighlightStyles() {
            try {
                const styleElement = document.createElement('style');
                styleElement.textContent = `
                    .interactive-element-highlight {
                        border: 2px solid red !important;
                        box-shadow: 0 0 5px rgba(255, 0, 0, 0.7) !important;
                        position: relative !important;
                    }
                    
                    .interactive-label {
                        position: absolute !important;
                        background: red !important;
                        color: white !important;
                        padding: 2px 5px !important;
                        font-size: 12px !important;
                        z-index: 1000000000 !important;
                        pointer-events: none !important;
                        white-space: nowrap !important;
                        border-radius: 3px !important;
                        font-family: Arial, sans-serif !important;
                        top: -20px !important;
                        left: 0 !important;
                    }
                `;
                document.head.appendChild(styleElement);
                console.log("Applied highlight styles successfully");
            } catch (styleError) {
                console.error("Error in applyHighlightStyles:", styleError);
            }
        }
        
        function isVisible(element) {
            try {
                const style = window.getComputedStyle(element);
                return style.display !== 'none' && 
                       style.visibility !== 'hidden' && 
                       style.opacity !== '0' &&
                       element.getBoundingClientRect().width > 0 &&
                       element.getBoundingClientRect().height > 0;
            } catch (visibilityError) {
                console.error("Error checking visibility:", visibilityError);
                return false;
            }
        }
        
        function getElementTypeAndCategory(element) {
            try {
                const tagName = element.tagName.toLowerCase();
                
                let elementCategory = 'interactive';
                let type = 'interactive';
                
                // Category
                const isNavigation = tagName === 'a';
                const isForm = ['button', 'input', 'select', 'textarea', 'option'].includes(tagName);
                
                elementCategory = isNavigation ? 'navigation' : 
                                  isForm ? 'form' : 'interactive';
                
                // Type
                switch(tagName) {
                    case 'input':
                        type = `input-${element.type || 'text'}`;
                        break;
                    case 'a':
                        type = 'link';
                        break;
                    case 'button':
                        type = 'button';
                        break;
                    case 'select':
                        type = 'select';
                        break;
                    case 'textarea':
                        type = 'textarea';
                        break;
                    default:
                        if (element.hasAttribute('onclick')) {
                            type = 'clickable';
                        } else if (element.hasAttribute('href')) {
                            type = 'link';
                        } else {
                            type = 'interactive';
                        }
                        break;
                        
                }
                
                return {
                    category: elementCategory,
                    type: type
                };
            } catch (typeError) {
                console.error("Error in getElementTypeAndCategory:", typeError);
                return { category: 'unknown', type: 'unknown' };
            }
        }
        
        function getElementContent(element) {
            try {
                const tagName = element.tagName.toLowerCase();
                
                let content = { text: '' };
                
                switch(tagName) {
                    case 'input':
                    case 'textarea':
                        content = {
                            text: element.value || '',
                            placeholder: element.placeholder || '',
                            label: getAssociatedLabelText(element) || '',
                        };
                        break;
                    case 'select':
                        const selectedOptions = Array.from(element.selectedOptions || []);
                        const optionTexts = selectedOptions.map(opt => opt.text).join(', ');
                        const options = Array.from(element.options || []).map(opt => ({
                            value: opt.value,
                            text: opt.text,
                            selected: opt.selected
                        }));
                        
                        content = {
                            text: optionTexts,
                            label: getAssociatedLabelText(element) || '',
                            options: options,
                            multiple: element.multiple
                        };
                        break;
                    case 'a':
                        content = {
                            text: element.innerText || element.textContent || '',
                            href: element.href || '',
                            title: element.title || '',
                        };
                        break;
                    case 'button':
                        content = {
                            text: element.innerText || element.textContent || '',
                            type: element.type || 'button',
                            disabled: element.disabled,
                            title: element.title || '',
                        };
                        break;
                    default:
                        content = {
                            text: element.innerText || element.textContent || '',
                            href: element.href || '',
                            title: element.title || '',
                        };
                }
                
                return content;
            } catch (contentError) {
                console.error("Error in getElementContent:", contentError);
                return { text: '' };
            }
        }
        
        function getAssociatedLabelText(element) {
            try {
                let labelText = '';
                
                // Method 1: Check for label with 'for' attribute
                if (element.id) {
                    const label = document.querySelector(`label[for="${element.id}"]`);
                    if (label) {
                        labelText = label.innerText || label.textContent || '';
                        return labelText;
                    }
                }
                
                // Method 2: Check if element is inside a label
                const parentLabel = element.closest('label'); 
                if (parentLabel) {
                    const clone = parentLabel.cloneNode(true);
                    Array.from(clone.querySelectorAll('input, select, textarea, button')).forEach(el => {
                        el.textContent = '';
                    });
                    labelText = clone.innerText || clone.textContent || '';
                    return labelText;
                }
                
                // Method 3: Check if previous sibling is a label-like element
                const siblings = element.parentElement ? Array.from(element.parentElement.children) : [];
                const index = siblings.indexOf(element);
                
                if (index > 0) {
                    const prevSibling = siblings[index - 1];
                    if (
                        ['label', 'span', 'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
                        .includes(prevSibling.tagName.toLowerCase())
                    ) {
                        labelText = prevSibling.innerText || prevSibling.textContent || '';
                        return labelText;
                    }
                }
                
                return '';
            } catch (labelError) {
                console.error("Error in getAssociatedLabelText:", labelError);
                return '';
            }
        }
        
        function processElements(doc, iframeId = '') {
            try {
                console.log(`Processing elements in ${iframeId || 'main document'}`);
                applyHighlightStyles();
                
                const elements = doc.querySelectorAll(interactiveSelectors.join(','));
                console.log(`Found ${elements.length} potential interactive elements`);
                
                for (let i = 0; i < elements.length; i++) {
                    try {
                        const element = elements[i];
                        if (isVisible(element) && !processedElements.has(element)) {
                            const elementTypeInfo = getElementTypeAndCategory(element);
                            
                            element.classList.add('interactive-element-highlight');
                            element.setAttribute('data-interactive-id', `#${counter}`);
                            element.setAttribute('data-element-type', elementTypeInfo.category);
                            
                            const label = doc.createElement('span');
                            label.textContent = `#${counter}`;
                            label.classList.add('interactive-label');
                            label.setAttribute('data-element-type', elementTypeInfo.category);

                            element.style.position = element.style.position || 'relative';
                            element.appendChild(label);
                             
                            const elementContent = getElementContent(element);
                            const rect = element.getBoundingClientRect();
                            
                            const elementInfo = {
                                id: counter,
                                type: elementTypeInfo.type,
                                category: elementTypeInfo.category,
                                tagName: element.tagName.toLowerCase(),
                                className: element.className.replace('interactive-element-highlight', '').trim() || '',
                                htmlId: element.id || '',
                                content: elementContent,
                                position: {
                                    x: rect.x,
                                    y: rect.y,
                                }
                            };
                            interactiveElementsInfo.push(elementInfo);
                            processedElements.add(element);
                            counter++;
                        }
                    } catch (elementError) {
                        console.error(`Error processing individual element:`, elementError);
                    }
                }
            } catch (processError) {
                console.error(`Error in processElements:`, processError);
            }
        }
        
        // Define interactive selectors
        const interactiveSelectors = [
            'a[href]',
            'a[href^="mailto:"]',
            'a[href^="tel:"]',
            '[role="button"]',
            '[role="link"]',
            '[href]',
            'button',
            'input',
            'select',
            'option',
            'textarea',
            '[onclick]',
            '[onsubmit]',
        ];

        // Initialize variables
        let counter = 1;
        const processedElements = new Set();
        const interactiveElementsInfo = [];
        const formElements = new Map();
        const iframeInfos = [];
        const formsInfo = [];
        
        // Main processing
        console.log("🔍 Processing main document...");
        processElements(document);

        console.log("🖼️ Identifying iframes...");
        const iframes = document.getElementsByTagName('iframe');
        console.log(`🖼️ Found ${iframes.length} iframes`);
        
        // Process each iframe
        for (let i = 0; i < iframes.length; i++) {
            try {
                const iframe = iframes[i];
                console.log(`Processing iframe ${i+1}/${iframes.length} 🔄`);
                const frameDoc = iframe.contentDocument;
                const frameWin = iframe.contentWindow;
                if (frameDoc && frameWin) {
                    if (!iframe.id) {
                        iframe.id = `generated_iframe_${i}`;
                    }
                    
                    processElements(frameDoc, iframe.id);
                    
                    iframeInfos.push({
                        id: iframe.id,
                        name: iframe.name || '',
                        src: iframe.src || '',
                        index: i,
                        outerHTML: iframe.outerHTML,
                        content: frameDoc.documentElement.outerHTML
                    });
                    console.log(`Iframe ${i+1} processed successfully`);
                }
            } catch (iframeError) {
                console.log(`Error processing iframe ${i+1}: ${iframeError.message}`);
                try {
                    const iframe = iframes[i];
                    iframeInfos.push({
                        id: iframe.id || `iframe_error_${i}`,
                        name: iframe.name || '',
                        src: iframe.src || '',
                        index: i,
                        outerHTML: iframe.outerHTML,
                        content: '<!-- Unable to access content of this iframe -->'
                    });
                } catch (additionalError) {
                    console.error("Additional error gathering iframe info:", additionalError);
                }
            }
        }

        // Process forms
        for (const [form, info] of formElements.entries()) {
            try {
                formsInfo.push({
                    id: info.id,
                    index: info.index,
                    action: info.action,
                    method: info.method,
                    elements: info.elements
                });
            } catch (formError) {
                console.error("Error processing form:", formError);
            }
        }

        console.log(`Processing completed. Total: ${counter-1} interactive elements in ${iframeInfos.length} iframes and ${formsInfo.length} forms`);
        console.log("highlightInteractiveElements function completed successfully");
        
        return {
            mainContent: document.documentElement.outerHTML,
            iframeInfos: iframeInfos,
            interactiveElements: interactiveElementsInfo,
            forms: formsInfo
        };
    } catch (mainError) {
        console.error("Critical error in highlightInteractiveElements:", mainError);
        console.error("Error stack:", mainError.stack);
        return {
            error: mainError.toString(),
            mainContent: document.documentElement.outerHTML,
            iframeInfos: [],
            interactiveElements: [],
            forms: []
        };
    }
}

// Export the function in Node.js environment
try {
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { highlightInteractiveElements };
    }
} catch (e) {
    console.error("Export error:", e);
}
// Removing the automatic execution to prevent double execution
// The function will be explicitly called by the Python code 