from agents import Agent, Runner
import asyncio
from agents.tool import function_tool
from browser.browser import Browser

@function_tool
async def navigate_to(url: str):
    """
    Navega para uma URL específica.
    """
    browser = Browser.get_instance()
    await browser.navigate_to(url)
    await asyncio.sleep(10)
    html_structure = await browser.process()
    
    return html_structure

@function_tool
async def click(selector: str):
    """
    Clica em um elemento específico.
    """
    browser = Browser.get_instance()
    await browser.click(selector)
    await asyncio.sleep(10)
    html_structure = await browser.process()
    return html_structure

@function_tool
async def fill(selector: str, value: str):
    """ 
    Preenche um campo específico com um valor específico.
    """
    browser = Browser.get_instance()
    await browser.fill(selector, value)
    await asyncio.sleep(10)
    html_structure = await browser.process()
    return html_structure

@function_tool
async def get_page_metadata():
    """
    Obtém os metadados da página atual.
    """
    browser = Browser.get_instance()
    metadata = await browser.get_page_metadata()
    return metadata


@function_tool
async def take_screenshot():
    """
    Tira um screenshot da página atual.
    """
    browser = Browser.get_instance()
    await browser.take_screenshot()
    return "Screenshot tirado com sucesso"

@function_tool
async def press_enter(selector: str):
    """
    Pressiona a tecla Enter para confirmar uma seleção.
    """
    browser = Browser.get_instance()
    await browser.press_enter(selector)
    return "Tecla Enter pressionada com sucesso"
    

worker_agent = Agent(
    name="Worker agent",
    instructions="""
    Você é um agente de IA avançado, projetado para executar tarefas utilizando um navegador web. Seu objetivo principal é ajudar o usuário a realizar solicitações de forma eficiente, criando planos detalhados antes de agir. Você tem as seguintes capacidades:
    - Acesso completo a um navegador web para pesquisar, navegar e interagir com sites.
    - Capacidade de analisar páginas web, extrair informações e seguir links.
    - Habilidade para planejar passo a passo como uma tarefa será executada, considerando os recursos disponíveis na web.
    """,
    model="gpt-4o-mini",
    tools=[navigate_to, click, fill, get_page_metadata, take_screenshot, press_enter]
)

planner_agent = Agent(
    name="""
     Você é um agente de IA avançado, projetado para planejar e executar tarefas utilizando um navegador web. Seu objetivo principal é ajudar o usuário a realizar solicitações de forma eficiente, criando planos detalhados antes de agir. Você tem as seguintes capacidades:
    - Acesso completo a um navegador web para pesquisar, navegar e interagir com sites.
    - Capacidade de analisar páginas web, extrair informações e seguir links.
    - Habilidade para planejar passo a passo como uma tarefa será executada, considerando os recursos disponíveis na web.
    - Pode realizar buscas em tempo real e ajustar o plano com base em novas informações encontradas.
    
    # Instruções:
    - Planejamento: Sempre que o usuário solicitar uma tarefa, antes de executá-la, crie um plano claro e estruturado. O plano deve incluir:
        - Objetivo da tarefa.
        - Passos específicos a serem seguidos no navegador (ex.: URLs a visitar, termos de busca, ações a tomar).
        - Ferramentas ou recursos da web que serão utilizados.
        - Possíveis desafios e como superá-los.
    - Execução: Após apresentar o plano ao usuário, peça confirmação para prosseguir. Somente execute a tarefa no navegador após aprovação explícita.
    - Flexibilidade: Se o usuário fornecer detalhes adicionais ou mudar o escopo da tarefa, ajuste o plano imediatamente e informe as alterações.
    - Clareza: Use linguagem simples e objetiva ao descrever o plano. Numere os passos para facilitar o entendimento.
     - Exemplo de Resposta:
        - Se o usuário pedir: "Encontre o preço de um voo de São Paulo para Nova York", você deve responder algo como:
    "Objetivo: Encontrar o preço de um voo de São Paulo (GRU) para Nova York (JFK).
        - Plano:
            - Abrir o navegador
            - Acessar o site Google Flights (https://www.google.com/flights).
            - Inserir 'São Paulo (GRU)' como origem e 'Nova York (JFK)' como destino.
            - Selecionar datas de ida e volta (ou perguntar ao usuário se não especificado).
            - Filtrar resultados por preço mais baixo e registrar as opções.
            - Verificar um segundo site (ex.: Kayak ou Decolar) para comparar preços.
            - Apresentar os resultados encontrados.
      - Exemplo de Resposta 2:
        - Se o usuário pedir: "Compre uma geladeira no Magalu", você deve responder algo como:
            - "Objetivo: Comprar uma geladeira no Magalu.
            - Plano:
                - Abrir o navegador
                - Acessar o Google (https://www.google.com/)
                - Pesquisar no Google "Magalu"
                - Selecionar o primeiro resultado
                - Selecionar a categoria "Eletrodomésticos"
                - Selecionar a subcategoria "Geladeiras"
                - Filtrar por preço mais baixo
                - Clicar no produto
                - Adicionar ao carrinho
                - Preencha os dados do usuário
                - Preencha os dados de pagamento
                - Finalizar a compra
    Nota 1: Quero apenas que você crie o plano, não execute nenhuma ação além de criar o plano.
    Nota 2: Nunca execute nenhuma ação além de criar o plano.
    Nota 3: Cada etapa do plano deve ser extremamente clara e detalhada.
    Nota 4: Quebre o plano em etapas mínimas e fáceis de serem executadas.
    
    O usuário irá te pedir em breve uma tarefa, você deve planejar a tarefa e responder ao usuário com o plano.
    """,
    instructions="Plan the next step in the task",
    handoffs=[worker_agent],
    model="gpt-4o-mini"
)


async def main():
    result = await Runner.run(planner_agent, input="Encontre o preço de um voo de São Paulo para Nova Iorque para 10/04/2025 e volta para 15/04/2025")
    print(result.final_output)
    # ¡Hola! Estoy bien, gracias por preguntar. ¿Y tú, cómo estás?


if __name__ == "__main__":
    asyncio.run(main())