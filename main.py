"""
Main application for Browser-JSONfy.
This script imports and uses the BrowserJsonfy class to process a web page.
"""

import asyncio
import argparse
import logging
import traceback
from browser_jsonfy.browser_jsonfy import BrowserJsonfy

# Configure logger
logger = logging.getLogger('main')
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s | %(levelname)s | %(name)s - %(message)s')

async def main():
    """Main entry point for the application."""
    # Create argument parser for URL only
    parser = argparse.ArgumentParser(
        description='Extracts interactive elements and HTML structure from web pages'
    )
    parser.add_argument('url', help='URL of the page to process')
    
    args = parser.parse_args()
    print(args.url)
    # Create BrowserJsonfy instance with URL
    browser_jsonfy = BrowserJsonfy(args.url)
    
    # Process the page
    try:
        result = await browser_jsonfy.process()
        logger.info(f"Process completed successfully with {result['interactive_elements_count']} interactive elements found")
    except Exception as e:
        logger.error(f"Failed to process page: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())