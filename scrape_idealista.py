62
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
from datetime  import datetime
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
                    # Wait for property listings to appear
                    time.sleep(5)  # Additional wait for JavaScript content
                    
                    html = page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find all property cards - use contains for class matching
                    property_cards = soup.find_all('div', class_=', attrs={'class': lambda x: x and 'item' in x})
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
        try:
            # Title and URL
            title_elem = card.find('a', class_='item-link')
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            url = "https://www.idealista.com" + title_elem.get('href', '')
            
            # Price
            price_elem = card.find('span', class_='item-price')
            price_text = price_elem.get_text(strip=True) if price_elem else "0"
            price = int(re.sub(r'[^0-9]', '', price_text)) if price_text else 0
            
            # Property details
            details = []
        detail_elems = card.find_all('span', class_='item-detail-char')
            for detail in detail_elems:
                details.append(detail.get_text(strip=True))
            
            # Extract rooms, surface, bathrooms from details
            rooms = 0
            surface = 0
            bathrooms = 0
            
            for detail in details:
                if 'hab' in detail.lower() or 'ch.' in detail.lower():
                    rooms = int(re.findall(r'\d+', detail)[0]) if re.findall(r'\d+', detail) else 0
                elif 'm²' in detail or 'm2' in detail:
                    surface = int(re.findall(r'\d+', detail)[0]) if re.findall(r'\d+', detail) else 0
                elif 'ba' in detail.lower():
                    bathrooms = int(re.findall(r'\d+', detail)[0]) if re.findall(r'\d+', detail) else 0
            
            # Description
            desc_elem = card.find('div', class_='item-description')
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # Address (from title or separate element)
            address_parts = title.split(' - ')
            address = address_parts[-1] if len(address_parts) > 1 else title
            
            # Calculate rental yield estimate (simplified)
            rental_yield = round((price * 0.05) / 12, 2) if price > 0 else 0
            
            return {
                "titre": title,
                "prix": price,
                "surface": surface,
                "chambres": rooms,
                "sallesDeBain": bathrooms,
                "adresse": address,
                "description": description[:500],  # Limit description length
                "url": url,
                "source": "Idealista",
                "dateAjout": datetime.now().isoformat(),
                "potentielLocatif": rental_yield,
                "noteInteret": self._calculate_interest_score(price, surface, rooms)
            }
        except Exception as e:
            logger.error(f"Error in _parse_property: {str(e)}")
            return None
    
    def _calculate_interest_score(self, price, surface, rooms):
        """
        Calculate interest score (0-10) based on property characteristics
        """
        score = 5.0  # Base score
        
        # Price per m² analysis
        if surface > 0:
            price_per_m2 = price / surface
            if price_per_m2 < 3000:
                score += 2
            elif price_per_m2 < 4000:
                score += 1
            elif price_per_m2 > 6000:
                score -= 1
        
        # Size bonus
        if surface >= 80:
            score += 1
        
        # Rooms bonus
        if rooms >= 3:
            score += 1
        
        return min(10.0, max(0.0, round(score, 1)))
    
    def send_to_base44(self, properties):
        """
        Send properties to Base44 API
        """
        if not properties:
            logger.warning("No properties to send")
            return
        
        headers = {
            "x-api-key": self.base44_api_key,
            "Content-Type": "application/json"
        }
        
        success_count = 0
        for prop in properties:
            try:
                response = requests.post(self.base44_url, json=prop, headers=headers)
                if response.status_code in [200, 201]:
                    success_count += 1
                    logger.info(f"Successfully sent: {prop['titre'][:50]}...")
                else:
                    logger.error(f"Failed to send property: {response.status_code} - {response.text}")
            except Exception as e:
                logger.error(f"Error sending to Base44: {str(e)}")
        
        logger.info(f"Successfully sent {success_count}/{len(properties)} properties to Base44")

def main():
    parser = argparse.ArgumentParser(description='Scrape Idealista properties')
    parser.add_argument('--city', default='madrid', help='City to scrape')
    parser.add_argument('--operation', default='venta', help='Operation type (venta/alquiler)')
    parser.add_argument('--pages', type=int, default=2, help='Number of pages to scrape')
    args = parser.parse_args()
    
    # Get credentials from environment
    api_key = os.getenv('BASE44_API_KEY')
    app_id = os.getenv('BASE44_APP_ID')
    
    if not api_key or not app_id:
        logger.error("Missing BASE44_API_KEY or BASE44_APP_ID environment variables")
        sys.exit(1)
    
    # Initialize scraper
    scraper = IdealistaScraper(api_key, app_id)
    
    # Scrape properties
    properties = scraper.scrape_properties(
        city=args.city,
        operation=args.operation,
        max_pages=args.pages
    )
    
    # Send to Base44
    if properties:
        scraper.send_to_base44(properties)
    else:
        logger.warning("No properties found")

if __name__ == "__main__":
    main()
