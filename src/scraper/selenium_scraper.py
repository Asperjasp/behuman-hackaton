"""
Selenium-based Scraper for Compensar
====================================
For JavaScript-rendered content that BeautifulSoup can't handle.
Supports WSL with Windows Chrome/Brave browsers.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from typing import Dict, List, Optional
import subprocess
import time
import logging
import json
import shutil
import os

logger = logging.getLogger(__name__)


def is_wsl() -> bool:
    """Check if running in WSL."""
    try:
        with open('/proc/version', 'r') as f:
            return 'microsoft' in f.read().lower()
    except:
        return False


def get_windows_chrome_path() -> Optional[str]:
    """Get the path to Chrome in Windows from WSL."""
    common_paths = [
        '/mnt/c/Program Files/Google/Chrome/Application/chrome.exe',
        '/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe',
        '/mnt/c/Users/*/AppData/Local/Google/Chrome/Application/chrome.exe',
    ]
    
    for path in common_paths:
        if '*' in path:
            # Handle wildcard paths
            import glob
            matches = glob.glob(path)
            if matches:
                return matches[0]
        elif os.path.exists(path):
            return path
    
    return None


def get_windows_brave_path() -> Optional[str]:
    """Get the path to Brave in Windows from WSL."""
    common_paths = [
        '/mnt/c/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe',
        '/mnt/c/Program Files (x86)/BraveSoftware/Brave-Browser/Application/brave.exe',
        '/mnt/c/Users/*/AppData/Local/BraveSoftware/Brave-Browser/Application/brave.exe',
    ]
    
    for path in common_paths:
        if '*' in path:
            import glob
            matches = glob.glob(path)
            if matches:
                return matches[0]
        elif os.path.exists(path):
            return path
    
    return None


class SeleniumCompensarScraper:
    """
    Selenium-based scraper for dynamic content.
    Use this when the regular scraper doesn't find products
    (indicates JavaScript-rendered content).
    Supports WSL with Windows Chrome/Brave.
    """
    
    BASE_URL = "https://www.tiendacompensar.com"
    CATEGORY_URL = f"{BASE_URL}/navegacion/category"
    
    def __init__(self, headless: bool = True, browser: str = "auto"):
        """
        Initialize Selenium scraper.
        
        Args:
            headless: Run browser in headless mode
            browser: Browser to use: "chrome", "brave", "firefox", or "auto" (detect available)
        """
        self.headless = headless
        self.browser = browser
        self.driver = None
        self.scraped_data: List[Dict] = []
        self.is_wsl = is_wsl()
    
    def _detect_browser(self) -> str:
        """Detect which browser is available."""
        # If in WSL, check for Windows browsers first
        if self.is_wsl:
            if get_windows_chrome_path():
                logger.info("Detected Windows Chrome in WSL")
                return "chrome"
            if get_windows_brave_path():
                logger.info("Detected Windows Brave in WSL")
                return "brave"
        
        # Check for native Linux browsers
        if shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser"):
            return "chrome"
        if shutil.which("firefox"):
            return "firefox"
        
        # Default to Chrome
        return "chrome"
    
    def _init_chrome_driver(self, binary_path: Optional[str] = None):
        """Initialize Chrome WebDriver."""
        options = ChromeOptions()
        
        # Set binary location for WSL
        if binary_path:
            options.binary_location = binary_path
            logger.info(f"Using Chrome binary at: {binary_path}")
        elif self.is_wsl:
            chrome_path = get_windows_chrome_path()
            if chrome_path:
                options.binary_location = chrome_path
                logger.info(f"Using Windows Chrome at: {chrome_path}")
        
        if self.headless:
            options.add_argument('--headless=new')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        options.add_argument('--lang=es-CO')
        options.add_argument('--remote-debugging-port=9222')
        
        # Disable images for faster loading
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
        
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10)
        
        return driver
    
    def _init_brave_driver(self):
        """Initialize Brave WebDriver (uses Chrome driver with Brave binary)."""
        options = ChromeOptions()
        
        # Set Brave binary location
        if self.is_wsl:
            brave_path = get_windows_brave_path()
            if brave_path:
                options.binary_location = brave_path
                logger.info(f"Using Windows Brave at: {brave_path}")
        else:
            # Try native Linux Brave
            brave_linux = shutil.which("brave-browser") or shutil.which("brave")
            if brave_linux:
                options.binary_location = brave_linux
        
        if self.headless:
            options.add_argument('--headless=new')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        options.add_argument('--lang=es-CO')
        
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
        
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10)
        
        return driver
    
    def _init_firefox_driver(self):
        """Initialize Firefox WebDriver."""
        options = FirefoxOptions()
        
        if self.headless:
            options.add_argument('--headless')
        
        options.set_preference('intl.accept_languages', 'es-CO')
        options.set_preference('permissions.default.image', 2)  # Disable images
        
        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
        driver.implicitly_wait(10)
        driver.set_window_size(1920, 1080)
        
        return driver
    
    def _init_driver(self):
        """Initialize WebDriver (Chrome, Brave, or Firefox)."""
        browser = self.browser if self.browser != "auto" else self._detect_browser()
        
        logger.info(f"Initializing {browser} driver (WSL: {self.is_wsl})...")
        
        if browser == "firefox":
            return self._init_firefox_driver()
        elif browser == "brave":
            return self._init_brave_driver()
        else:
            return self._init_chrome_driver()
    
    def start(self) -> None:
        """Start the browser."""
        if not self.driver:
            self.driver = self._init_driver()
            logger.info("Selenium driver started")
    
    def stop(self) -> None:
        """Stop the browser."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Selenium driver stopped")
    
    def scrape_category(self, category: str, scroll_times: int = 3) -> List[Dict]:
        """
        Scrape a category page with JavaScript rendering.
        
        Args:
            category: Category slug
            scroll_times: Number of times to scroll for lazy loading
            
        Returns:
            List of product dictionaries
        """
        if not self.driver:
            self.start()
        
        url = f"{self.CATEGORY_URL}/{category}"
        logger.info(f"Selenium scraping: {url}")
        
        products = []
        
        try:
            self.driver.get(url)
            
            # Wait for content to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll to load lazy content
            for _ in range(scroll_times):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)
            
            # Try to find product cards with various selectors
            product_elements = self._find_product_elements()
            
            for element in product_elements:
                try:
                    product = self._extract_product_data(element, category)
                    if product and product.get('name'):
                        products.append(product)
                except Exception as e:
                    logger.warning(f"Error extracting product: {e}")
            
            # Handle pagination
            products.extend(self._handle_pagination(category))
            
        except TimeoutException:
            logger.error(f"Timeout loading {url}")
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
        
        logger.info(f"Found {len(products)} products in {category}")
        return products
    
    def _find_product_elements(self):
        """Find product elements using various selectors."""
        selectors = [
            ".product-card",
            ".item-card",
            ".service-card",
            "[class*='product']",
            "[class*='item']",
            ".card",
            ".resultado",
            "article",
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and len(elements) > 1:  # More than 1 to avoid false positives
                    return elements
            except Exception:
                continue
        
        # Fallback: find by price pattern
        try:
            # Find elements that contain prices
            elements = self.driver.find_elements(
                By.XPATH, 
                "//*[contains(text(), '$') and contains(text(), '.')]/.."
            )
            return elements
        except Exception:
            pass
        
        return []
    
    def _extract_product_data(self, element, category: str) -> Optional[Dict]:
        """Extract product data from a Selenium WebElement."""
        product = {
            'category': category,
            'name': None,
            'description': None,
            'price': None,
            'price_from': False,
            'image_url': None,
            'product_url': None
        }
        
        try:
            # Try to get name from headings
            for tag in ['h2', 'h3', 'h4', 'h5']:
                try:
                    heading = element.find_element(By.TAG_NAME, tag)
                    if heading and heading.text.strip():
                        product['name'] = heading.text.strip()
                        break
                except NoSuchElementException:
                    continue
            
            # Try to get name from links if no heading found
            if not product['name']:
                try:
                    link = element.find_element(By.TAG_NAME, 'a')
                    if link.text.strip():
                        product['name'] = link.text.strip()
                except NoSuchElementException:
                    pass
            
            # Get price
            try:
                price_text = element.text
                if '$' in price_text:
                    # Extract price portion
                    import re
                    price_match = re.search(r'(?:Desde:?\s*)?\$[\d.,]+', price_text)
                    if price_match:
                        product['price'] = price_match.group()
                        if 'desde' in product['price'].lower():
                            product['price_from'] = True
            except Exception:
                pass
            
            # Get image
            try:
                img = element.find_element(By.TAG_NAME, 'img')
                src = img.get_attribute('src') or img.get_attribute('data-src')
                if src:
                    product['image_url'] = src if src.startswith('http') else f"{self.BASE_URL}{src}"
            except NoSuchElementException:
                pass
            
            # Get link
            try:
                link = element.find_element(By.TAG_NAME, 'a')
                href = link.get_attribute('href')
                if href:
                    product['product_url'] = href
            except NoSuchElementException:
                pass
            
            # Get description
            try:
                paragraphs = element.find_elements(By.TAG_NAME, 'p')
                for p in paragraphs:
                    if p.text.strip() and '$' not in p.text:
                        product['description'] = p.text.strip()
                        break
            except Exception:
                pass
            
        except Exception as e:
            logger.warning(f"Error extracting product data: {e}")
        
        return product if product.get('name') else None
    
    def _handle_pagination(self, category: str) -> List[Dict]:
        """Handle pagination for category pages."""
        additional_products = []
        
        try:
            # Look for "next" or pagination buttons
            next_buttons = self.driver.find_elements(
                By.XPATH,
                "//a[contains(@class, 'next') or contains(text(), 'Siguiente') or contains(@aria-label, 'next')]"
            )
            
            for _ in range(10):  # Max 10 pages
                if not next_buttons:
                    break
                
                try:
                    next_btn = next_buttons[0]
                    if next_btn.is_displayed() and next_btn.is_enabled():
                        next_btn.click()
                        time.sleep(2)
                        
                        product_elements = self._find_product_elements()
                        for element in product_elements:
                            product = self._extract_product_data(element, category)
                            if product and product.get('name'):
                                additional_products.append(product)
                        
                        # Look for next button again
                        next_buttons = self.driver.find_elements(
                            By.XPATH,
                            "//a[contains(@class, 'next') or contains(text(), 'Siguiente')]"
                        )
                    else:
                        break
                except Exception:
                    break
        except Exception as e:
            logger.warning(f"Error handling pagination: {e}")
        
        return additional_products
    
    def scrape_all_categories(self, categories: List[str]) -> List[Dict]:
        """Scrape multiple categories."""
        all_products = []
        
        self.start()
        
        try:
            for category in categories:
                products = self.scrape_category(category)
                all_products.extend(products)
                time.sleep(2)  # Delay between categories
        finally:
            self.stop()
        
        self.scraped_data = all_products
        return all_products
    
    def save_to_json(self, filepath: str) -> None:
        """Save scraped data to JSON."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Data saved to {filepath}")
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


if __name__ == "__main__":
    # Test Selenium scraper
    with SeleniumCompensarScraper(headless=True) as scraper:
        products = scraper.scrape_category("turismo")
        print(f"Found {len(products)} products")
        for p in products[:5]:
            print(f"  - {p['name']}: {p['price']}")
