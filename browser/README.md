# Browser-JSONfy

A Python module for extracting interactive elements and HTML structure from web pages using Playwright.

## Features

- Extract interactive elements from web pages (buttons, links, inputs, etc.)
- Generate JSON representation of the HTML structure
- Configurable settings through environment variables (.env file)
- Proper logging for debugging and monitoring
- Secure browser context with denied permissions

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### As a CLI command

```bash
python -m browser_jsonfy "https://example.com"
```

### As a module in your code

```python
import asyncio
from browser_jsonfy import BrowserJsonfy

async def main():
    browser = BrowserJsonfy("https://example.com")
    result = await browser.process()
    print(f"Found {result['interactive_elements_count']} interactive elements")

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

All configuration is done through environment variables in a `.env` file:

```
# Browser Settings
TIMEOUT=60000
WAIT_UNTIL=load
INITIAL_WAIT=3
HEADLESS=false
DEVTOOLS=false
FINAL_WAIT_TIME=100

# Output Paths
OUTPUT_JSON_PATH=interactive_elements.json
STRUCTURE_JSON_PATH=html_structure.json

# Browser Args
BROWSER_ARGS=--disable-web-security,--disable-site-isolation-trials,...

# Log Settings
LOG_LEVEL=INFO
```

## License

MIT 