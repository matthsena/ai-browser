# 🌐 AI Browser - Interactive Elements Extractor

This project is a tool to capture web pages, highlight interactive elements, and extract them to a structured JSON format.

## ✨ Features

- 🔍 Captures web pages using Playwright
- 🎯 Highlights interactive elements (links, buttons, form fields, etc.)
- 📦 Extracts content from iframes
- 💾 Saves interactive elements data in structured JSON format
- 🚫 Automatically handles permission dialogs and popups

## 📋 Requirements

- Python 3.7+
- Playwright
- JSON handling capabilities

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/ai-browser.git
cd ai-browser
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install
```

## 🚀 Usage

Run the main script providing the URL of the page to be processed:

```bash
python main.py https://example.com
```

### ⚙️ Additional Options

```
--timeout TIMEOUT     Timeout in ms (default: 60000)
--wait {load,domcontentloaded,networkidle,commit}
                      Event to wait for (default: load)
--output-json PATH    Path to save the interactive elements JSON file
```

## 📁 Project Structure

- `main.py`: Main script
- `browser_config.py`: Browser configurations
- `page_processor.py`: Page processing functions
- `html_processor.py`: HTML processing functions
- `static/highlight_script.js`: JavaScript script to highlight interactive elements
- `requirements.txt`: Project dependencies

## 🔄 How It Works

1. The script opens the specified URL in a Chromium browser using Playwright
2. Scrolls the page to load all content
3. Highlights interactive elements with red borders and numeric labels
4. Extracts content from iframes
5. Identifies and analyzes all interactive elements on the page
6. Saves structured JSON data with information about all interactive elements

## 🎛️ Customization

You can customize the behavior of the script by modifying the `ScraperConfig` class in `main.py`.

## 📜 License

MIT 