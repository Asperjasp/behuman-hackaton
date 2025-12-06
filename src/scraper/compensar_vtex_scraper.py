"""
🎯 Scraper VTEX para Tienda Compensar
=====================================
Usa la API VTEX directamente - ¡No necesita Selenium!

La estructura de datos que extraemos:
- Categoría principal: Embarazadas, Bebés, Niños, Adolescentes, Adultos, Adulto Mayor
- Subcategoría: Turismo, Música, Gimnasio, etc.
- Nombre del curso/servicio
- Precios: Categoría A, B, C, No afiliado
"""

import requests
import json
import re
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import time
from tqdm import tqdm


@dataclass
class Precio:
    """Precios por categoría de afiliación"""
    desde: Optional[str] = None
    categoria_a: Optional[str] = None
    categoria_b: Optional[str] = None
    categoria_c: Optional[str] = None
    no_afiliado: Optional[str] = None
    precio_original: Optional[float] = None
    precio_oferta: Optional[float] = None


@dataclass
class Producto:
    """Producto/Servicio de Compensar"""
    id: str
    nombre: str
    categoria_principal: str
    subcategoria: str
    precio: Precio
    descripcion: Optional[str] = None
    url: Optional[str] = None
    imagen_url: Optional[str] = None
    promocion: bool = False
    disponible: bool = True
    
    def to_dict(self) -> dict:
        return asdict(self)


class CompensarVTEXScraper:
    """
    Scraper que usa la API VTEX de Tienda Compensar.
    Más rápido y confiable que Selenium.
    """
    
    BASE_URL = "https://www.tiendacompensar.com"
    API_URL = f"{BASE_URL}/api/catalog_system/pub"
    SEARCH_API = f"{API_URL}/products/search"
    
    # Mapeo de categorías
    CATEGORIAS = {
        "embarazadas": {"nombre": "Embarazadas", "id": None},
        "bebes": {"nombre": "Bebés", "id": None},
        "ninos": {"nombre": "Niños", "id": None},
        "adolescentes": {"nombre": "Adolescentes", "id": None},
        "adultos": {"nombre": "Adultos", "id": None},
        "adulto-mayor": {"nombre": "Adulto Mayor", "id": None},
    }
    
    SUBCATEGORIAS = [
        "turismo", "spa", "gimnasio", "natacion-y-buceo", "cursos",
        "planes", "musica", "actividades-recreativas", "actividades-culturales",
        "cocina", "bienestar-y-armonia", "pasadias", "practicas-dirigidas",
        "practicas-libres", "sistemas", "biblioteca", "bolos",
        "cine-y-entretenimiento", "manualidades", "salud-para-adulto-mayor",
        "clases-personalizadas", "cuidado-adulto-mayor"
    ]
    
    def __init__(self, delay: float = 0.5):
        """
        Args:
            delay: Segundos entre requests
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'es-CO,es;q=0.9',
            'Referer': self.BASE_URL,
        })
        self.productos: List[Producto] = []
    
    def _get_category_tree(self) -> List[Dict]:
        """Obtiene el árbol de categorías de VTEX"""
        url = f"{self.API_URL}/category/tree/10"
        try:
            resp = self.session.get(url, timeout=30)
            if resp.status_code == 200:
                return resp.json() if resp.headers.get('content-type', '').startswith('application/json') else []
        except:
            pass
        return []
    
    def _search_products(self, query: str = "", category_id: Optional[int] = None, 
                         from_: int = 0, to: int = 50) -> Dict:
        """
        Busca productos usando la API VTEX.
        
        Args:
            query: Término de búsqueda
            category_id: ID de categoría VTEX
            from_: Índice inicial
            to: Índice final
        """
        params = {
            '_from': from_,
            '_to': to,
        }
        
        if category_id:
            params['fq'] = f'C:/{category_id}/'
        
        url = f"{self.SEARCH_API}/{query}" if query else self.SEARCH_API
        
        try:
            resp = self.session.get(url, params=params, timeout=30)
            
            # Verificar si es JSON
            content_type = resp.headers.get('content-type', '')
            if 'application/json' in content_type:
                return {'products': resp.json(), 'total': len(resp.json())}
            else:
                # Puede ser HTML de la página, intentar parsear
                return self._parse_search_page(resp.text)
                
        except Exception as e:
            print(f"⚠️ Error en búsqueda: {e}")
            return {'products': [], 'total': 0}
    
    def _parse_search_page(self, html: str) -> Dict:
        """Parsea HTML de página de búsqueda si la API devuelve HTML"""
        from bs4 import BeautifulSoup
        
        products = []
        soup = BeautifulSoup(html, 'lxml')
        
        # Intentar encontrar JSON embebido
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Buscar datos de productos
                matches = re.findall(r'\"productName\"\s*:\s*\"([^\"]+)\"', script.string)
                for match in matches:
                    products.append({'productName': match})
        
        return {'products': products, 'total': len(products)}
    
    def scrape_via_navigation(self, subcategoria: str, categoria_principal: str = "General") -> List[Producto]:
        """
        Scrapea una subcategoría usando la URL de navegación.
        """
        productos = []
        url = f"{self.BASE_URL}/navegacion/category/{subcategoria}"
        
        print(f"\n📂 Scrapeando: {subcategoria}")
        
        try:
            resp = self.session.get(url, timeout=30)
            html = resp.text
            
            # La página carga con JavaScript, pero podemos encontrar
            # datos embebidos en el HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            
            # Buscar en scripts
            for script in soup.find_all('script'):
                if script.string:
                    text = script.string
                    
                    # Buscar productos en el JavaScript
                    # VTEX a menudo embebe datos en __STATE__ o similar
                    product_matches = re.findall(
                        r'\{[^{}]*"productName"\s*:\s*"([^"]+)"[^{}]*"Price"\s*:\s*([\d.]+)[^{}]*\}',
                        text
                    )
                    
                    for match in product_matches:
                        name, price = match
                        productos.append(Producto(
                            id=f"{subcategoria}-{len(productos)}",
                            nombre=name,
                            categoria_principal=categoria_principal,
                            subcategoria=subcategoria,
                            precio=Precio(desde=f"${float(price):,.0f}".replace(',', '.')),
                            url=url
                        ))
            
            print(f"   ✅ Encontrados: {len(productos)} productos")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        return productos
    
    def scrape_buscapagina(self, subcategoria: str, categoria_principal: str = "General") -> List[Producto]:
        """
        Usa el endpoint buscapagina de VTEX para obtener productos.
        Este es el endpoint que usa la página para cargar contenido.
        """
        productos = []
        
        # El endpoint buscapagina requiere conocer el ID de colección o categoría
        # Podemos intentar con diferentes parámetros
        
        url = f"{self.BASE_URL}/buscapagina"
        params = {
            'sl': subcategoria,
            'PS': 50,  # Page Size
            'cc': 50,
            'sm': 0,
            'O': 'OrderByTopSaleDESC'
        }
        
        try:
            resp = self.session.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                # Parsear HTML de productos
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, 'lxml')
                
                # Buscar elementos de producto
                items = soup.find_all('li')
                for item in items:
                    name_elem = item.find(['h2', 'h3', '.productName', '.product-name'])
                    price_elem = item.find(class_=lambda x: x and 'price' in str(x).lower())
                    
                    if name_elem:
                        nombre = name_elem.get_text(strip=True)
                        precio_str = price_elem.get_text(strip=True) if price_elem else None
                        
                        productos.append(Producto(
                            id=f"{subcategoria}-{len(productos)}",
                            nombre=nombre,
                            categoria_principal=categoria_principal,
                            subcategoria=subcategoria,
                            precio=Precio(desde=precio_str),
                            url=f"{self.BASE_URL}/navegacion/category/{subcategoria}"
                        ))
                
        except Exception as e:
            print(f"⚠️ Error en buscapagina: {e}")
        
        return productos
    
    def scrape_all(self, subcategorias: Optional[List[str]] = None,
                   categoria_principal: str = "General") -> List[Producto]:
        """
        Scrapea todas las subcategorías.
        """
        subcategorias = subcategorias or self.SUBCATEGORIAS
        
        for subcat in tqdm(subcategorias, desc="Scrapeando categorías"):
            # Intentar primero con navegación
            productos = self.scrape_via_navigation(subcat, categoria_principal)
            
            # Si no encontró nada, intentar buscapagina
            if not productos:
                productos = self.scrape_buscapagina(subcat, categoria_principal)
            
            self.productos.extend(productos)
            time.sleep(self.delay)
        
        print(f"\n📊 Total productos scrapeados: {len(self.productos)}")
        return self.productos
    
    def save_to_json(self, filepath: str):
        """Guarda productos en JSON"""
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        
        data = [p.to_dict() for p in self.productos]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Guardados {len(data)} productos en: {filepath}")


def demo():
    """Demo del scraper VTEX"""
    print("=" * 70)
    print("🎯 Demo: Scraper VTEX para Tienda Compensar")
    print("=" * 70)
    
    scraper = CompensarVTEXScraper()
    
    # Intentar obtener el árbol de categorías
    print("\n📂 Obteniendo árbol de categorías...")
    tree = scraper._get_category_tree()
    if tree:
        print(f"   ✅ Encontradas {len(tree)} categorías principales")
        for cat in tree[:5]:
            print(f"      - {cat.get('name', 'N/A')}")
    else:
        print("   ⚠️ No se pudo obtener el árbol de categorías")
    
    # Probar scraping de turismo
    print("\n📂 Probando scraping de TURISMO...")
    productos = scraper.scrape_via_navigation("turismo", "Adulto Mayor")
    
    if productos:
        print(f"\n✅ Encontrados {len(productos)} productos:")
        for p in productos[:5]:
            print(f"   - {p.nombre}: {p.precio.desde}")
    else:
        print("\n⚠️ No se encontraron productos con este método")
        print("   La página requiere JavaScript para cargar contenido.")
        print("   Usa el scraper de Selenium: compensar_selenium_scraper.py")


if __name__ == "__main__":
    demo()
