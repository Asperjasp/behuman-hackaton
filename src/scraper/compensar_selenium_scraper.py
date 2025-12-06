"""
Compensar Scraper con Selenium para WSL
========================================
Usa Chrome de Windows a través de WSL para scraping.

Estructura de datos a extraer:
- Categoría principal: Embarazadas, Bebés, Niños, Adolescentes, Adultos, Adulto Mayor
- Subcategoría: Turismo, Música, Gimnasio, etc.
- Nombre del curso/servicio
- Precios: Categoría A, B, C, No afiliado
"""

import subprocess
import time
import json
import os
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from bs4 import BeautifulSoup

# Intentar importar selenium
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️ Selenium no instalado. Ejecuta: pip install selenium")


@dataclass
class Precio:
    """Estructura de precios por categoría de afiliación"""
    categoria_a: Optional[str] = None
    categoria_b: Optional[str] = None
    categoria_c: Optional[str] = None
    no_afiliado: Optional[str] = None
    desde: Optional[str] = None  # Precio "Desde" mostrado en cards


@dataclass
class Producto:
    """Estructura de un producto/servicio de Compensar"""
    nombre: str
    categoria_principal: str  # Embarazadas, Niños, Adultos, etc.
    subcategoria: str  # Turismo, Música, etc.
    precio: Precio
    descripcion: Optional[str] = None
    url: Optional[str] = None
    imagen_url: Optional[str] = None
    promocion: bool = False
    fecha_limite: Optional[str] = None  # "Hasta 31 dic."
    
    def to_dict(self) -> dict:
        """Convierte a diccionario para JSON"""
        return asdict(self)


class CompensarSeleniumScraper:
    """
    Scraper para Tienda Compensar usando Selenium.
    Diseñado para funcionar en WSL con Chrome de Windows.
    """
    
    BASE_URL = "https://www.tiendacompensar.com"
    NAVIGATION_URL = f"{BASE_URL}/navegacion/category"
    
    # Categorías principales del menú
    CATEGORIAS_PRINCIPALES = {
        "embarazadas": "Embarazadas",
        "bebes": "Bebés",
        "ninos": "Niños",
        "adolescentes": "Adolescentes",
        "adultos": "Adultos",
        "adulto-mayor": "Adulto Mayor"
    }
    
    # Subcategorías conocidas (del menú de la imagen)
    SUBCATEGORIAS = [
        "activacion-adulto-mayor", "actividades-culturales", "actividades-recreativas",
        "biblioteca", "bienestar-y-armonia", "bolos", "cine-y-entretenimiento",
        "clases-personalizadas", "cocina", "cuidado-adulto-mayor", "cursos",
        "gimnasio", "manualidades", "musica", "natacion-y-buceo", "pasadias",
        "planes", "practicas-dirigidas", "practicas-libres", "salud-para-adulto-mayor",
        "sistemas", "spa", "turismo"
    ]
    
    def __init__(self, headless: bool = False, timeout: int = 20):
        """
        Inicializa el scraper.
        
        Args:
            headless: Si True, ejecuta Chrome sin ventana visible
            timeout: Segundos a esperar por elementos
        """
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.productos: List[Producto] = []
        
    def _is_wsl(self) -> bool:
        """Detecta si estamos en WSL"""
        try:
            with open('/proc/version', 'r') as f:
                return 'microsoft' in f.read().lower()
        except:
            return False
    
    def _find_chrome_path(self) -> Optional[str]:
        """Encuentra el path de Chrome en WSL/Windows"""
        if self._is_wsl():
            # Probar aliases y paths comunes de Windows
            paths_to_try = [
                # Alias comunes
                "google-chrome",
                "chrome",
                # Paths de Windows a través de WSL
                "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe",
                "/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe",
            ]
            
            for path in paths_to_try:
                try:
                    # Verificar si el comando existe
                    result = subprocess.run(
                        ["which", path] if not path.startswith("/mnt") else ["test", "-f", path],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        return path
                except:
                    continue
                    
            # Intentar con los aliases
            try:
                result = subprocess.run(["which", "google"], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
            except:
                pass
                
        return None
    
    def start_driver(self) -> bool:
        """
        Inicia el driver de Selenium.
        
        Returns:
            True si se inició correctamente
        """
        if not SELENIUM_AVAILABLE:
            print("❌ Selenium no está instalado")
            return False
            
        try:
            options = Options()
            
            if self.headless:
                options.add_argument('--headless=new')
            
            # Opciones para mejor rendimiento y compatibilidad
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            # En WSL, puede ser necesario especificar el path
            if self._is_wsl():
                chrome_path = self._find_chrome_path()
                if chrome_path:
                    print(f"🔍 Usando Chrome en: {chrome_path}")
                    options.binary_location = chrome_path
            
            # Usar webdriver-manager para manejar el chromedriver
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            except Exception as e:
                print(f"⚠️ webdriver-manager falló: {e}")
                # Intentar sin webdriver-manager
                self.driver = webdriver.Chrome(options=options)
            
            self.driver.set_page_load_timeout(self.timeout)
            print("✅ Chrome iniciado correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error iniciando Chrome: {e}")
            print("\n💡 Soluciones posibles:")
            print("   1. Asegúrate de tener Chrome instalado")
            print("   2. Instala chromedriver: pip install webdriver-manager")
            print("   3. En WSL, puede ser necesario usar Chrome de Windows")
            return False
    
    def stop_driver(self):
        """Cierra el driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            print("🛑 Chrome cerrado")
    
    def _wait_for_products(self) -> bool:
        """
        Espera a que los productos se carguen en la página.
        
        Returns:
            True si se encontraron productos
        """
        try:
            # Esperar a que desaparezca el loader o aparezcan productos
            selectors = [
                ".product-card",
                ".resultado-item", 
                "[class*='card']",
                "[class*='product']",
                ".vtex-search-result-3-x-galleryItem"
            ]
            
            for selector in selectors:
                try:
                    WebDriverWait(self.driver, self.timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    return True
                except TimeoutException:
                    continue
            
            # Esperar un poco más por si hay animaciones
            time.sleep(3)
            return True
            
        except Exception as e:
            print(f"⚠️ Timeout esperando productos: {e}")
            return False
    
    def _extract_price(self, text: str) -> str:
        """Extrae y limpia el precio de un texto"""
        # Buscar patrón de precio colombiano: $10.300 o $1.234.567
        match = re.search(r'\$[\d.,]+', text)
        if match:
            return match.group()
        return text.strip()
    
    def _parse_product_card(self, card_html: str, categoria_principal: str, subcategoria: str) -> Optional[Producto]:
        """
        Parsea una tarjeta de producto y extrae la información.
        
        Args:
            card_html: HTML de la tarjeta
            categoria_principal: Categoría principal (Adultos, Niños, etc.)
            subcategoria: Subcategoría (Turismo, Música, etc.)
            
        Returns:
            Objeto Producto o None
        """
        soup = BeautifulSoup(card_html, 'lxml')
        
        # Extraer nombre
        nombre = None
        for selector in ['h2', 'h3', 'h4', '.product-name', '.title', '[class*="name"]', '[class*="title"]']:
            elem = soup.select_one(selector)
            if elem:
                nombre = elem.get_text(strip=True)
                if nombre:
                    break
        
        if not nombre:
            return None
        
        # Extraer precio "Desde:"
        precio = Precio()
        price_text = soup.get_text()
        
        # Buscar "Desde: $X.XXX"
        desde_match = re.search(r'Desde[:\s]*(\$[\d.,]+)', price_text, re.IGNORECASE)
        if desde_match:
            precio.desde = desde_match.group(1)
        else:
            # Buscar cualquier precio
            price_match = re.search(r'\$[\d.,]+', price_text)
            if price_match:
                precio.desde = price_match.group()
        
        # Verificar si es promoción
        promocion = bool(soup.find(string=re.compile(r'promoci[oó]n', re.IGNORECASE)))
        
        # Extraer fecha límite
        fecha_limite = None
        fecha_match = re.search(r'Hasta\s+\d+\s+\w+\.?', price_text, re.IGNORECASE)
        if fecha_match:
            fecha_limite = fecha_match.group()
        
        # Extraer URL
        url = None
        link = soup.find('a', href=True)
        if link:
            href = link.get('href', '')
            if href.startswith('/'):
                url = f"{self.BASE_URL}{href}"
            elif href.startswith('http'):
                url = href
        
        # Extraer imagen
        imagen_url = None
        img = soup.find('img')
        if img:
            imagen_url = img.get('src') or img.get('data-src')
            if imagen_url and imagen_url.startswith('/'):
                imagen_url = f"{self.BASE_URL}{imagen_url}"
        
        return Producto(
            nombre=nombre,
            categoria_principal=categoria_principal,
            subcategoria=subcategoria,
            precio=precio,
            url=url,
            imagen_url=imagen_url,
            promocion=promocion,
            fecha_limite=fecha_limite
        )
    
    def scrape_category_page(self, url: str, categoria_principal: str, subcategoria: str) -> List[Producto]:
        """
        Scrapea una página de categoría.
        
        Args:
            url: URL de la categoría
            categoria_principal: Nombre de la categoría principal
            subcategoria: Nombre de la subcategoría
            
        Returns:
            Lista de productos encontrados
        """
        productos = []
        
        try:
            print(f"\n📂 Scrapeando: {subcategoria}")
            print(f"   URL: {url}")
            
            self.driver.get(url)
            self._wait_for_products()
            
            # Obtener el HTML renderizado
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'lxml')
            
            # Buscar tarjetas de productos con varios selectores
            cards = []
            card_selectors = [
                '[class*="product-card"]',
                '[class*="resultado"]',
                '[class*="gallery"] > div',
                '[class*="Card"]',
                'article',
            ]
            
            for selector in card_selectors:
                cards = soup.select(selector)
                if cards:
                    print(f"   ✅ Encontradas {len(cards)} tarjetas con selector: {selector}")
                    break
            
            if not cards:
                # Método alternativo: buscar por estructura de precio
                print("   ⚠️ Buscando por estructura de precios...")
                price_containers = soup.find_all(string=re.compile(r'\$[\d.,]+'))
                for price in price_containers:
                    parent = price.find_parent(['div', 'article', 'li'])
                    if parent and parent not in cards:
                        cards.append(parent)
                print(f"   📦 Encontrados {len(cards)} contenedores con precios")
            
            # Parsear cada tarjeta
            for card in cards:
                try:
                    producto = self._parse_product_card(str(card), categoria_principal, subcategoria)
                    if producto:
                        productos.append(producto)
                except Exception as e:
                    print(f"   ⚠️ Error parseando tarjeta: {e}")
            
            print(f"   📊 Productos extraídos: {len(productos)}")
            
            # Scroll para cargar más (lazy loading)
            self._scroll_page()
            
        except Exception as e:
            print(f"   ❌ Error en {subcategoria}: {e}")
        
        return productos
    
    def _scroll_page(self):
        """Hace scroll para cargar contenido lazy-loaded"""
        try:
            # Scroll gradual
            for i in range(3):
                self.driver.execute_script(f"window.scrollTo(0, {(i+1) * 800});")
                time.sleep(0.5)
            
            # Volver arriba
            self.driver.execute_script("window.scrollTo(0, 0);")
        except:
            pass
    
    def scrape_all(self, subcategorias: Optional[List[str]] = None, categoria_principal: str = "General") -> List[Producto]:
        """
        Scrapea todas las subcategorías.
        
        Args:
            subcategorias: Lista de subcategorías a scrapear (None = todas)
            categoria_principal: Categoría principal para asignar
            
        Returns:
            Lista de todos los productos
        """
        if not self.driver:
            if not self.start_driver():
                return []
        
        subcategorias = subcategorias or self.SUBCATEGORIAS
        
        for subcat in subcategorias:
            url = f"{self.NAVIGATION_URL}/{subcat}"
            productos = self.scrape_category_page(url, categoria_principal, subcat)
            self.productos.extend(productos)
            
            # Pausa entre requests para no sobrecargar
            time.sleep(1)
        
        return self.productos
    
    def save_to_json(self, filepath: str):
        """Guarda los productos en JSON"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        data = [p.to_dict() for p in self.productos]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Guardados {len(data)} productos en: {filepath}")
    
    def save_to_csv(self, filepath: str):
        """Guarda los productos en CSV"""
        import csv
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            if self.productos:
                # Obtener todas las keys
                sample = self.productos[0].to_dict()
                fieldnames = []
                for key, value in sample.items():
                    if isinstance(value, dict):
                        for subkey in value.keys():
                            fieldnames.append(f"{key}_{subkey}")
                    else:
                        fieldnames.append(key)
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for producto in self.productos:
                    row = {}
                    data = producto.to_dict()
                    for key, value in data.items():
                        if isinstance(value, dict):
                            for subkey, subvalue in value.items():
                                row[f"{key}_{subkey}"] = subvalue
                        else:
                            row[key] = value
                    writer.writerow(row)
        
        print(f"💾 Guardados {len(self.productos)} productos en: {filepath}")


def demo_scraping():
    """
    Demo del scraper - muestra cómo extraer datos paso a paso
    """
    print("=" * 70)
    print("🎓 DEMO: Web Scraping de Tienda Compensar con Selenium")
    print("=" * 70)
    
    print("""
    Este demo muestra cómo:
    1. Selenium abre un navegador real
    2. Espera a que JavaScript cargue el contenido
    3. BeautifulSoup parsea el HTML renderizado
    4. Extraemos los datos estructurados
    """)
    
    scraper = CompensarSeleniumScraper(headless=False)  # headless=False para ver el navegador
    
    try:
        if not scraper.start_driver():
            print("\n❌ No se pudo iniciar el navegador")
            print("   Asegúrate de tener Chrome y chromedriver instalados")
            return
        
        # Scrapear solo turismo como ejemplo
        print("\n" + "=" * 70)
        print("📌 SCRAPEANDO CATEGORÍA: TURISMO")
        print("=" * 70)
        
        productos = scraper.scrape_category_page(
            url="https://www.tiendacompensar.com/navegacion/category/turismo",
            categoria_principal="Adulto Mayor",
            subcategoria="turismo"
        )
        
        print("\n" + "=" * 70)
        print("📊 RESULTADOS")
        print("=" * 70)
        
        if productos:
            print(f"\n✅ Se encontraron {len(productos)} productos:\n")
            
            for i, prod in enumerate(productos[:10], 1):  # Mostrar primeros 10
                print(f"  {i}. {prod.nombre}")
                print(f"     💰 Precio: {prod.precio.desde or 'No disponible'}")
                if prod.promocion:
                    print(f"     🏷️ ¡PROMOCIÓN! {prod.fecha_limite or ''}")
                print(f"     📂 Categoría: {prod.categoria_principal} > {prod.subcategoria}")
                print()
        else:
            print("\n⚠️ No se encontraron productos")
            print("   Esto puede deberse a:")
            print("   - La estructura del HTML cambió")
            print("   - El contenido tarda más en cargar")
            print("   - Se necesitan otros selectores CSS")
        
        # Guardar resultados
        if productos:
            scraper.productos = productos
            scraper.save_to_json("data/compensar/turismo_demo.json")
            
    finally:
        print("\n⏳ Cerrando navegador en 5 segundos...")
        time.sleep(5)
        scraper.stop_driver()
    
    print("\n✅ Demo completado!")


if __name__ == "__main__":
    demo_scraping()
