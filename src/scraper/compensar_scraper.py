"""
Compensar Tienda Scraper
========================
Scrapes product and service data from https://www.tiendacompensar.com
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import time
import json
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CompensarScraper:
    """
    Scraper for Tienda Compensar website.
    Extracts products and services from all categories.
    """
    
    BASE_URL = "https://www.tiendacompensar.com"
    CATEGORY_URL = f"{BASE_URL}/navegacion/category"
    
    # Categories based on the website structure (Adulto Mayor section shown in image)
    MAIN_CATEGORIES = [
        "embarazadas",
        "bebes", 
        "ninos",
        "adolescentes",
        "adultos",
        "adulto-mayor",
        "promociones"
    ]
    
    # Subcategories for Adulto Mayor (from your image)
    ADULTO_MAYOR_SUBCATEGORIES = [
        "activacion-adulto-mayor",
        "actividades-culturales",
        "actividades-recreativas",
        "biblioteca",
        "bienestar-y-armonia",
        "bolos",
        "cine-y-entretenimiento",
        "cocina",
        "clases-personalizadas",
        "cuidado-adulto-mayor",
        "cursos",
        "gimnasio",
        "manualidades",
        "musica",
        "natacion-y-buceo",
        "pasadias",
        "practicas-dirigidas",
        "practicas-libres",
        "planes",
        "sistemas",
        "salud-para-adulto-mayor",
        "spa",
        "turismo"
    ]
    
    # General categories to scrape
    CATEGORIES_TO_SCRAPE = [
        "turismo",
        "spa",
        "gimnasio",
        "natacion-y-buceo",
        "cursos",
        "planes",
        "musica",
        "actividades-recreativas",
        "actividades-culturales",
        "salud-para-adulto-mayor",
        "cocina",
        "bienestar-y-armonia",
        "pasadias",
        "practicas-dirigidas",
        "practicas-libres",
        "sistemas",
        "biblioteca",
        "bolos",
        "cine-y-entretenimiento",
        "manualidades"
    ]
    
    def __init__(self, delay: float = 1.0):
        """
        Initialize the scraper.
        
        Args:
            delay: Time to wait between requests (in seconds) to be respectful
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-CO,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        self.scraped_data: List[Dict] = []
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch a page and return BeautifulSoup object.
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            raise
    
    def _extract_products_from_category(self, soup: BeautifulSoup, category: str) -> List[Dict]:
        """
        Extract product/service information from a category page.
        
        Args:
            soup: BeautifulSoup object of the page
            category: Category name
            
        Returns:
            List of product dictionaries
        """
        products = []
        
        # Try different selectors based on common e-commerce patterns
        # These may need adjustment based on actual HTML structure
        
        # Look for product cards/items
        product_containers = soup.find_all(['div', 'article'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['product', 'item', 'card', 'servicio', 'resultado']
        ))
        
        if not product_containers:
            # Try generic approach
            product_containers = soup.select('.product-card, .item-card, .service-card, .resultado-item')
        
        for container in product_containers:
            try:
                product = self._parse_product_container(container, category)
                if product and product.get('name'):
                    products.append(product)
            except Exception as e:
                logger.warning(f"Error parsing product: {e}")
                continue
        
        # Also try to find products in a list/grid format
        if not products:
            products = self._extract_products_alternative(soup, category)
        
        return products
    
    def _parse_product_container(self, container, category: str) -> Optional[Dict]:
        """
        Parse a single product container.
        
        Args:
            container: BeautifulSoup element containing product info
            category: Category name
            
        Returns:
            Product dictionary or None
        """
        product = {
            'category': category,
            'name': None,
            'description': None,
            'price': None,
            'price_from': None,
            'image_url': None,
            'product_url': None,
            'availability': None,
            'rating': None,
            'location': None
        }
        
        # Extract name
        name_elem = container.find(['h2', 'h3', 'h4', 'span', 'a'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['name', 'title', 'nombre', 'titulo']
        ))
        if name_elem:
            product['name'] = name_elem.get_text(strip=True)
        else:
            # Try first heading
            heading = container.find(['h2', 'h3', 'h4'])
            if heading:
                product['name'] = heading.get_text(strip=True)
        
        # Extract price (looking for patterns like "$10.300" or "Desde: $65.000")
        price_elem = container.find(string=lambda x: x and '$' in str(x))
        if price_elem:
            price_text = str(price_elem).strip()
            product['price'] = price_text
            if 'desde' in price_text.lower():
                product['price_from'] = True
        
        # Also look for price in specific elements
        price_container = container.find(class_=lambda x: x and 'price' in str(x).lower())
        if price_container and not product['price']:
            product['price'] = price_container.get_text(strip=True)
        
        # Extract description
        desc_elem = container.find(['p', 'span'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['desc', 'detail', 'info']
        ))
        if desc_elem:
            product['description'] = desc_elem.get_text(strip=True)
        
        # Extract image
        img = container.find('img')
        if img:
            product['image_url'] = img.get('src') or img.get('data-src')
            if product['image_url'] and not product['image_url'].startswith('http'):
                product['image_url'] = f"{self.BASE_URL}{product['image_url']}"
        
        # Extract product URL
        link = container.find('a', href=True)
        if link:
            href = link.get('href')
            if href and not href.startswith('http'):
                product['product_url'] = f"{self.BASE_URL}{href}"
            else:
                product['product_url'] = href
        
        return product if product['name'] else None
    
    def _extract_products_alternative(self, soup: BeautifulSoup, category: str) -> List[Dict]:
        """
        Alternative extraction method for different page structures.
        
        Args:
            soup: BeautifulSoup object
            category: Category name
            
        Returns:
            List of products
        """
        products = []
        
        # Look for any links with prices nearby
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '')
            if '/producto/' in href or '/servicio/' in href:
                product = {
                    'category': category,
                    'name': link.get_text(strip=True),
                    'product_url': href if href.startswith('http') else f"{self.BASE_URL}{href}",
                    'description': None,
                    'price': None,
                    'image_url': None
                }
                
                # Look for price nearby
                parent = link.parent
                if parent:
                    price_text = parent.find(string=lambda x: x and '$' in str(x))
                    if price_text:
                        product['price'] = str(price_text).strip()
                
                if product['name']:
                    products.append(product)
        
        return products
    
    def scrape_category(self, category: str) -> List[Dict]:
        """
        Scrape all products from a specific category.
        
        Args:
            category: Category slug (e.g., 'turismo', 'spa')
            
        Returns:
            List of product dictionaries
        """
        url = f"{self.CATEGORY_URL}/{category}"
        logger.info(f"Scraping category: {category} ({url})")
        
        try:
            soup = self._fetch_page(url)
            if soup:
                products = self._extract_products_from_category(soup, category)
                logger.info(f"Found {len(products)} products in {category}")
                
                # Check for pagination
                products.extend(self._handle_pagination(soup, category))
                
                return products
        except Exception as e:
            logger.error(f"Failed to scrape category {category}: {e}")
        
        return []
    
    def _handle_pagination(self, soup: BeautifulSoup, category: str) -> List[Dict]:
        """
        Handle pagination if present.
        
        Args:
            soup: BeautifulSoup object of first page
            category: Category name
            
        Returns:
            List of additional products from other pages
        """
        additional_products = []
        
        # Look for pagination links
        pagination = soup.find(class_=lambda x: x and 'pagination' in str(x).lower())
        if pagination:
            page_links = pagination.find_all('a', href=True)
            for page_link in page_links:
                href = page_link.get('href')
                if href and 'page=' in href:
                    time.sleep(self.delay)
                    try:
                        page_soup = self._fetch_page(href if href.startswith('http') else f"{self.BASE_URL}{href}")
                        if page_soup:
                            additional_products.extend(
                                self._extract_products_from_category(page_soup, category)
                            )
                    except Exception as e:
                        logger.warning(f"Error fetching pagination: {e}")
        
        return additional_products
    
    def scrape_all_categories(self, categories: Optional[List[str]] = None) -> List[Dict]:
        """
        Scrape all specified categories.
        
        Args:
            categories: List of category slugs. If None, uses default list.
            
        Returns:
            List of all scraped products
        """
        categories = categories or self.CATEGORIES_TO_SCRAPE
        all_products = []
        
        for category in tqdm(categories, desc="Scraping categories"):
            products = self.scrape_category(category)
            all_products.extend(products)
            time.sleep(self.delay)  # Be respectful to the server
        
        self.scraped_data = all_products
        logger.info(f"Total products scraped: {len(all_products)}")
        
        return all_products
    
    def discover_all_categories(self) -> List[str]:
        """
        Discover all available categories from the website navigation.
        
        Returns:
            List of category slugs
        """
        logger.info("Discovering categories from website...")
        categories = set()
        
        try:
            soup = self._fetch_page(self.BASE_URL)
            if soup:
                # Find all navigation links
                nav_links = soup.find_all('a', href=True)
                for link in nav_links:
                    href = link.get('href', '')
                    if '/navegacion/category/' in href:
                        # Extract category slug
                        parts = href.split('/navegacion/category/')
                        if len(parts) > 1:
                            category = parts[1].split('/')[0].split('?')[0].split('#')[0]
                            if category:
                                categories.add(category)
        except Exception as e:
            logger.error(f"Error discovering categories: {e}")
        
        logger.info(f"Discovered {len(categories)} categories")
        return list(categories)
    
    def save_to_json(self, filepath: str) -> None:
        """
        Save scraped data to JSON file.
        
        Args:
            filepath: Path to save JSON file
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Data saved to {filepath}")
    
    def get_scraped_data(self) -> List[Dict]:
        """Get all scraped data."""
        return self.scraped_data


if __name__ == "__main__":
    # Test the scraper
    scraper = CompensarScraper(delay=1.5)
    
    # First, discover categories
    categories = scraper.discover_all_categories()
    print(f"Discovered categories: {categories}")
    
    # Scrape turismo as a test
    products = scraper.scrape_category("turismo")
    print(f"Found {len(products)} products in turismo")
    
    for product in products[:5]:
        print(f"  - {product['name']}: {product['price']}")
