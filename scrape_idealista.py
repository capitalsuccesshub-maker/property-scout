#!/usr/bin/env python3
"""
Idealista Property Scraper
Scrapes property listings from Idealista.com and sends them to Base44 API
"""

import os
import sys
import json
import logging
import argparse
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IdealistaScraper:
    def __init__(self, base44_api_key, base44_app_id):
        self.base44_api_key = base44_api_key
        self.base44_app_id = base44_app_id
        self.base44_url = f"https://app.base44.com/api/apps/{base44_app_id}/entities/BienImmobilier"
        
    def scrape_properties(self, city="madrid", operation="venta", max_pages=1):
        """
        Scrape properties from Idealista
        """
        logger.info(f"Starting scrape for {city} - {operation}")
        properties = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            for page_num in range(1, max_pages + 1):
                url = f"https://www.idealista.com/en/{operation}-viviendas/{city}-{city}/pagina-{page_num}.htm"
                if page_num == 1:
                    url = f"https://www.idealista.com/en/{operation}-viviendas/{city}-{city}/"
                
                logger.info(f"Scraping page {page_num}: {url}")
                
                try:
                    page.goto(url, wait_until="networkidle", timeout=60000)
                    time.sleep(3)
                    
                    html = page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find all property cards
                    property_cards = soup.find_all('article', class_='item')
                    logger.info(f"Found {len(property_cards)} properties on page {page_num}")
                    
                    for card in property_cards:
                        try:
                            property_data = self._parse_property(card)
                            if property_data:
                                properties.append(property_data)
                        except Exception as e:
                            logger.error(f"Error parsing property: {str(e)}")
                            continue
                    
                except Exception as e:
                    logger.error(f"Error scraping page {page_num}: {str(e)}")
                    continue
            
            browser.close()
        
        logger.info(f"Total properties scraped: {len(properties)}")
        return properties
    
    def _parse_property(self, card):
        """
        Parse individual property card
        """
        property_data = {}
        
        # Get title and URL
        title_elem = card.find('a', class_='item-link')
        if title_elem:
            property_data['titre'] = title_elem.get_text(strip=True)
            property_data['url'] = 'https://www.idealista.com' + title_elem.get('href', '')
        
        # Get price
        price_elem = card.find('span', class_='item-price')
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            # Extract numeric value
            price_numbers = re.findall(r'[\d,]+', price_text.replace('.', ''))
            if price_numbers:
                property_data['prix'] = float(price_numbers[0].replace(',', ''))
        
        # Get property details (surface, rooms, bathrooms)
        detail_elems = card.find_all('span', class_='item-detail')
        for detail in detail_elems:
            text = detail.get_text(strip=True)
            if 'm²' in text:
                numbers = re.findall(r'\d+', text)
                if numbers:
                    property_data['surface'] = int(numbers[0])
            elif 'room' in text.lower() or 'habitación' in text.lower() or 'hab' in text.lower():
                numbers = re.findall(r'\d+', text)
                if numbers:
                    property_data['chambres'] = int(numbers[0])
            elif 'bath' in text.lower() or 'baño' in text.lower():
                numbers = re.findall(r'\d+', text)
                if numbers:
                    property_data['sallesDeBain'] = int(numbers[0])
        
        # Get description
        desc_elem = card.find('div', class_='item-description')
        if desc_elem:
            property_data['description'] = desc_elem.get_text(strip=True)
        
        # Get location
        location_elem = card.find('span', class_='item-detail') or card.find('a', class_='item-link')
        if location_elem:
            # Try to extract location from various possible elements
            property_data['adresse'] = 'Madrid, Spain'  # Default
        
        # Add metadata
        property_data['source'] = 'Idealista'
        property_data['dateAjout'] = datetime.now().isoformat()
        property_data['pays'] = 'Spain'
        property_data['ville'] = 'Madrid'
        
        # Calculate rental potential (basic estimate: 4% annual return)
        if 'prix' in property_data:
            property_data['potentielLocatif'] = round(property_data['prix'] * 0.04 / 12, 2)
        
        return property_data if property_data.get('titre') else None
    
    def send_to_base44(self, properties):
        """
        Send properties to Base44 API
        """
        logger.info(f"Sending {len(properties)} properties to Base44...")
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.base44_api_key}'
        }
        
        success_count = 0
        error_count = 0
        
        for prop in properties:
            try:
                response = requests.post(
                    self.base44_url,
                    headers=headers,
                    json=prop,
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    success_count += 1
                    logger.info(f"✓ Sent: {prop.get('titre', 'Unknown')}")
                else:
                    error_count += 1
                    logger.error(f"✗ Failed to send property: {response.status_code} - {response.text}")
            
            except Exception as e:
                error_count += 1
                logger.error(f"✗ Error sending property: {str(e)}")
        
        logger.info(f"\nResults: {success_count} successful, {error_count} errors")
        return success_count, error_count

def main():
    parser = argparse.ArgumentParser(description='Scrape Idealista properties')
    parser.add_argument('--city', default='madrid', help='City to scrape')
    parser.add_argument('--operation', default='venta', choices=['venta', 'alquiler'], 
                        help='Operation type: venta (sale) or alquiler (rent)')
    parser.add_argument('--pages', type=int, default=1, help='Number of pages to scrape')
    parser.add_argument('--dry-run', action='store_true', help='Scrape but do not send to Base44')
    
    args = parser.parse_args()
    
    # Get credentials from environment variables
    api_key = os.getenv('BASE44_API_KEY')
    app_id = os.getenv('BASE44_APP_ID')
    
    if not api_key or not app_id:
        logger.error("Error: BASE44_API_KEY and BASE44_APP_ID environment variables are required")
        sys.exit(1)
    
    scraper = IdealistaScraper(api_key, app_id)
    
    # Scrape properties
    properties = scraper.scrape_properties(
        city=args.city,
        operation=args.operation,
        max_pages=args.pages
    )
    
    if not properties:
        logger.warning("No properties found")
        sys.exit(0)
    
    # Print summary
    logger.info(f"\n{'='*50}")
    logger.info(f"Scraped {len(properties)} properties")
    logger.info(f"{'='*50}\n")
    
    if args.dry_run:
        logger.info("DRY RUN - Not sending to Base44")
        for i, prop in enumerate(properties[:5], 1):
            logger.info(f"{i}. {prop.get('titre')} - €{prop.get('prix', 'N/A')}")
    else:
        # Send to Base44
        scraper.send_to_base44(properties)

if __name__ == "__main__":
    main()
