/**
 * Script para destacar elementos interativos em uma página web.
 * Este script identifica elementos clicáveis e interativos, adicionando
 * bordas vermelhas e rótulos numéricos para facilitar a visualização.
 */

async function highlightInteractiveElements() {
    // Função para carregar e aplicar o CSS de destaque
    const applyHighlightStyles = () => {
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
                z-index: 100000 !important;
                pointer-events: none !important;
                white-space: nowrap !important;
                border-radius: 3px !important;
                font-family: Arial, sans-serif !important;
                top: -20px !important;
                left: 0 !important;
            }
        `;
        document.head.appendChild(styleElement);
    };
    
    // Função para verificar se o elemento é visível
    const isVisible = (element) => {
        const style = window.getComputedStyle(element);
        return style.display !== 'none' && 
               style.visibility !== 'hidden' && 
               style.opacity !== '0' &&
               element.getBoundingClientRect().width > 0 &&
               element.getBoundingClientRect().height > 0;
    };

    // Seletores de elementos interativos
    const interactiveSelectors = [
        'a[href]',
        'button',
        'input:not([type="hidden"])',
        'select',
        'textarea',
        '[onclick]',
        '[role="button"]',
        '[tabindex]:not([tabindex="-1"])'
    ];

    let counter = 1;
    const processedElements = new Set();

    // Função para processar elementos em um documento
    const processElements = (doc, win) => {
        // Certifique-se de que o estilo seja aplicado em cada documento
        applyHighlightStyles();
        
        const elements = doc.querySelectorAll(interactiveSelectors.join(','));
        for (const element of elements) {
            if (isVisible(element) && !processedElements.has(element)) {
                // Usa classes em vez de inline styles para melhor organização
                element.classList.add('interactive-element-highlight');
                element.setAttribute('data-interactive-id', `#${counter}`);

                // Cria o label com classe
                const label = doc.createElement('span');
                label.textContent = `#${counter}`;
                label.classList.add('interactive-label');

                // Adiciona o label como filho do elemento
                element.style.position = element.style.position || 'relative';
                element.appendChild(label);

                processedElements.add(element);
                counter++;
            }
        }
    };

    // Estrutura para guardar informações dos iframes
    const iframeInfos = [];
    
    // Aplica estilos ao documento principal
    applyHighlightStyles();
    
    // Processa o documento principal
    console.log("Processando documento principal...");
    processElements(document, window);

    // Processa iframes e captura seu conteúdo
    console.log("Identificando iframes...");
    const iframes = document.getElementsByTagName('iframe');
    console.log(`Encontrados ${iframes.length} iframes`);
    
    for (let i = 0; i < iframes.length; i++) {
        const iframe = iframes[i];
        try {
            console.log(`Processando iframe ${i+1}/${iframes.length}`);
            const frameDoc = iframe.contentDocument;
            const frameWin = iframe.contentWindow;
            if (frameDoc && frameWin) {
                processElements(frameDoc, frameWin);
                
                // Cria um ID único para o iframe se não tiver um
                if (!iframe.id) {
                    iframe.id = `generated_iframe_${i}`;
                }
                
                // Salva informações sobre o iframe
                iframeInfos.push({
                    id: iframe.id,
                    name: iframe.name || '',
                    src: iframe.src || '',
                    index: i,
                    outerHTML: iframe.outerHTML,
                    content: frameDoc.documentElement.outerHTML
                });
                console.log(`Iframe ${i+1} processado com sucesso`);
            }
        } catch (e) {
            console.log(`Erro ao processar iframe ${i+1}: ${e.message}`);
            // Mesmo com erro, registra o iframe
            iframeInfos.push({
                id: iframe.id || `iframe_error_${i}`,
                name: iframe.name || '',
                src: iframe.src || '',
                index: i,
                outerHTML: iframe.outerHTML,
                content: '<!-- Não foi possível acessar o conteúdo deste iframe -->'
            });
        }
    }

    console.log(`Processamento concluído. Total: ${counter-1} elementos interativos em ${iframeInfos.length} iframes`);
    return {
        mainContent: document.documentElement.outerHTML,
        iframeInfos: iframeInfos
    };
}

// Exporta a função para uso pelo módulo Python
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { highlightInteractiveElements };
} else {
    // Auto-executa se carregar diretamente no navegador
    highlightInteractiveElements();
} 