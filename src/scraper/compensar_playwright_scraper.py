"""
🎯 Scraper Profesional para Tienda Compensar
=============================================
Usa Playwright para cargar JavaScript y BeautifulSoup para parsear.

TUTORIAL EDUCATIVO INCLUIDO:
Este script te muestra paso a paso cómo funciona el web scraping moderno.

Estructura de datos a extraer:
├── Categoría Principal (Embarazadas, Bebés, Niños, Adolescentes, Adultos, Adulto Mayor)
│   └── Subcategoría (Turismo, Música, Gimnasio, etc.)
│       └── Producto/Servicio
│           ├── Nombre
│           ├── Precio "Desde"
│           ├── Precios por categoría (A, B, C, No afiliado)
│           ├── Imagen
│           ├── URL
│           └── Promoción (si aplica)
"""

import asyncio
import json
import os
import re
import sqlite3
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️ Playwright no instalado. Ejecuta:")
    print("   pip install playwright")
    print("   playwright install chromium")


# ============================================================================
# ESTRUCTURAS DE DATOS
# ============================================================================

@dataclass
class Precio:
    """Estructura de precios"""
    desde: Optional[str] = None          # Precio "Desde:" mostrado en cards
    categoria_a: Optional[str] = None    # Precio para afiliados categoría A
    categoria_b: Optional[str] = None    # Precio para afiliados categoría B
    categoria_c: Optional[str] = None    # Precio para afiliados categoría C
    no_afiliado: Optional[str] = None    # Precio para no afiliados
    valor_numerico: Optional[float] = None  # Valor numérico para ordenar


@dataclass
class Producto:
    """Producto o servicio de Compensar"""
    id: str
    nombre: str
    categoria_principal: str
    subcategoria: str
    precio: Precio = field(default_factory=Precio)
    descripcion: Optional[str] = None
    url: Optional[str] = None
    imagen_url: Optional[str] = None
    promocion: bool = False
    fecha_limite_promocion: Optional[str] = None
    fecha_scraping: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        d = asdict(self)
        return d


# ============================================================================
# SCRAPER PRINCIPAL
# ============================================================================

class CompensarPlaywrightScraper:
    """
    Scraper profesional para Tienda Compensar.
    
    🎓 CÓMO FUNCIONA:
    1. Playwright abre un navegador Chromium headless
    2. Navega a cada categoría y espera que JavaScript cargue
    3. Obtiene el HTML renderizado completo
    4. BeautifulSoup parsea el HTML
    5. Extraemos los datos estructurados
    """
    
    BASE_URL = "https://www.tiendacompensar.com"
    NAVIGATION_URL = f"{BASE_URL}/navegacion/category"
    
    # Categorías principales del menú de Compensar
    CATEGORIAS_PRINCIPALES = {
        "embarazadas": "Embarazadas",
        "bebes": "Bebés", 
        "ninos": "Niños",
        "adolescentes": "Adolescentes",
        "adultos": "Adultos",
        "adulto-mayor": "Adulto Mayor"
    }
    
    # Todas las subcategorías encontradas en el menú
    SUBCATEGORIAS = [
        "activacion-adulto-mayor",
        "actividades-culturales",
        "actividades-recreativas",
        "biblioteca",
        "bienestar-y-armonia",
        "bolos",
        "cine-y-entretenimiento",
        "clases-personalizadas",
        "cocina",
        "cuidado-adulto-mayor",
        "cursos",
        "gimnasio",
        "manualidades",
        "musica",
        "natacion-y-buceo",
        "pasadias",
        "planes",
        "practicas-dirigidas",
        "practicas-libres",
        "salud-para-adulto-mayor",
        "sistemas",
        "spa",
        "turismo",
    ]
    
    def __init__(self, headless: bool = True, slow_mo: int = 0):
        """
        Inicializa el scraper.
        
        Args:
            headless: True = navegador invisible, False = ver navegador
            slow_mo: Milisegundos de retraso entre acciones (para debug)
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.browser: Optional[Browser] = None
        self.productos: List[Producto] = []
        
    async def start(self):
        """Inicia el navegador"""
        print("🚀 Iniciando navegador Chromium...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )
        print("✅ Navegador iniciado")
        
    async def stop(self):
        """Cierra el navegador"""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        print("🛑 Navegador cerrado")
    
    def _extract_price(self, text: str) -> Optional[str]:
        """
        Extrae precio de un texto.
        
        🎓 EXPRESIONES REGULARES:
        \$ = Caracter $ literal
        [\d.,]+ = Uno o más dígitos, puntos o comas
        
        Ejemplos:
        - "$10.300" → "$10.300"
        - "Desde: $65.000" → "$65.000"
        """
        match = re.search(r'\$[\d.,]+', text)
        return match.group() if match else None
    
    def _price_to_number(self, price_str: str) -> Optional[float]:
        """
        Convierte precio string a número.
        
        🎓 PROCESO:
        "$10.300" → "10300" → 10300.0
        """
        if not price_str:
            return None
        # Remover $ y convertir formato colombiano
        clean = re.sub(r'[^\d]', '', price_str)
        try:
            return float(clean)
        except:
            return None
    
    async def _wait_for_products(self, page: Page) -> bool:
        """
        Espera a que los productos se carguen.
        
        🎓 POR QUÉ ESPERAR:
        JavaScript carga el contenido dinámicamente.
        Debemos esperar a que termine antes de extraer datos.
        """
        try:
            # Intentar varios selectores
            selectors = [
                # Selectores comunes de VTEX/ecommerce
                '[class*="vtex"][class*="gallery"]',
                '[class*="product"]',
                '[class*="card"]',
                'article',
                # Selectores por precio (más específicos)
                'text=$',
            ]
            
            for selector in selectors:
                try:
                    await page.wait_for_selector(selector, timeout=10000)
                    return True
                except:
                    continue
            
            # Esperar un poco más por si hay animaciones
            await page.wait_for_timeout(3000)
            return True
            
        except Exception as e:
            print(f"   ⚠️ Timeout esperando contenido: {e}")
            return False
    
    async def _scroll_page(self, page: Page):
        """
        Hace scroll para cargar contenido lazy-loaded.
        
        🎓 LAZY LOADING:
        Muchas páginas cargan imágenes/contenido solo cuando
        el usuario hace scroll hacia abajo. Simulamos esto.
        """
        await page.evaluate("""
            async () => {
                await new Promise((resolve) => {
                    let totalHeight = 0;
                    const distance = 300;
                    const timer = setInterval(() => {
                        window.scrollBy(0, distance);
                        totalHeight += distance;
                        if (totalHeight >= document.body.scrollHeight) {
                            clearInterval(timer);
                            resolve();
                        }
                    }, 100);
                });
            }
        """)
        await page.wait_for_timeout(1000)
    
    async def _extract_category_prices(self, page: Page) -> Dict[str, Optional[str]]:
        """
        Extrae precios por categoría haciendo hover sobre los botones A, B, C, No afiliado.
        
        🎓 CÓMO FUNCIONA:
        1. Playwright puede simular hover con element.hover()
        2. Los precios se muestran cuando el mouse está sobre el botón
        3. Capturamos el precio visible después de cada hover
        
        Returns:
            Dict con precios: {'a': '$X', 'b': '$Y', 'c': '$Z', 'no_afiliado': '$W'}
        """
        precios = {
            'categoria_a': None,
            'categoria_b': None,
            'categoria_c': None,
            'no_afiliado': None
        }
        
        try:
            # Selectores para los botones de categoría
            # Basado en la imagen: botones con texto A, B, C, No afiliado
            button_selectors = {
                'categoria_a': [
                    'button:has-text("A"):not(:has-text("No"))',
                    '[class*="category"] button:first-child',
                    'button[class*="active"]:has-text("A")',
                    'div:has-text("A"):not(:has-text("No afiliado"))',
                ],
                'categoria_b': [
                    'button:has-text("B")',
                    '[class*="category"] button:nth-child(2)',
                ],
                'categoria_c': [
                    'button:has-text("C")',
                    '[class*="category"] button:nth-child(3)',
                ],
                'no_afiliado': [
                    'button:has-text("No afiliado")',
                    '[class*="category"] button:last-child',
                    'button:has-text("no afiliado")',
                ]
            }
            
            # Selector para el precio que cambia
            price_selectors = [
                '[class*="price"]:not([class*="from"])',
                '[class*="Price"]',
                'span:has-text("$")',
                'div > span:has-text("$")',
            ]
            
            for cat_key, selectors in button_selectors.items():
                for selector in selectors:
                    try:
                        button = page.locator(selector).first
                        if await button.count() > 0:
                            # Hacer hover sobre el botón
                            await button.hover()
                            await page.wait_for_timeout(300)  # Esperar animación
                            
                            # Buscar el precio visible
                            for price_selector in price_selectors:
                                try:
                                    price_elem = page.locator(price_selector).first
                                    if await price_elem.count() > 0:
                                        price_text = await price_elem.text_content()
                                        if price_text and '$' in price_text:
                                            precios[cat_key] = self._extract_price(price_text)
                                            break
                                except:
                                    continue
                            
                            if precios[cat_key]:
                                break
                    except:
                        continue
                        
        except Exception as e:
            pass  # Silenciar errores, los precios quedarán como None
        
        return precios
    
    async def _scrape_product_detail(self, page: Page, product_url: str) -> Dict[str, Optional[str]]:
        """
        Navega a la página de detalle del producto y extrae los precios por categoría.
        
        🎓 CÓMO FUNCIONA EL HOVER EN COMPENSAR:
        - Los botones A, B, C, No afiliado son elementos <SPAN>
        - Al hacer hover, el precio cambia mostrando un rango (ej: $33.800 - $74.000)
        - Buscamos por texto exacto: 'A', 'B', 'C', 'No afiliado'
        
        Args:
            page: Página de Playwright
            product_url: URL del producto
            
        Returns:
            Dict con precios por categoría
        """
        precios = {
            'categoria_a': None,
            'categoria_b': None,
            'categoria_c': None,
            'no_afiliado': None,
            'modalidad': None
        }
        
        try:
            # Navegar a la página del producto
            await page.goto(product_url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)
            
            # Mapeo de categorías a selectores
            # Los botones son <span> con texto exacto
            category_map = {
                'categoria_a': 'A',
                'categoria_b': 'B', 
                'categoria_c': 'C',
                'no_afiliado': 'No afiliado'
            }
            
            for cat_key, text_to_find in category_map.items():
                try:
                    # Buscar el elemento con el texto exacto
                    # Usamos text="" para match exacto
                    selector = f'text="{text_to_find}"' if len(text_to_find) > 1 else f'span:text-is("{text_to_find}")'
                    
                    element = page.locator(selector).first
                    
                    if await element.count() > 0:
                        # Hacer hover sobre el elemento
                        await element.hover()
                        await page.wait_for_timeout(400)  # Esperar que se actualice el precio
                        
                        # Buscar el precio visible
                        # El precio está en un elemento que contiene "$"
                        # Formato: "$33.800 - $74.000" o simplemente "$33.800"
                        
                        # Obtener todo el texto de la página y buscar precios
                        html = await page.content()
                        soup = BeautifulSoup(html, 'lxml')
                        
                        # Buscar elementos con precios
                        for elem in soup.find_all(['span', 'div', 'p']):
                            text = elem.get_text(strip=True)
                            
                            # Buscar patrón de rango de precios: $XX.XXX - $XX.XXX
                            range_match = re.search(r'\$[\d.,]+\s*-\s*\$[\d.,]+', text)
                            if range_match:
                                # Tomar el primer precio del rango (más bajo)
                                first_price = re.search(r'\$[\d.,]+', range_match.group())
                                if first_price:
                                    precios[cat_key] = first_price.group()
                                break
                            
                            # Buscar precio único
                            single_match = re.match(r'^\$[\d.,]+$', text)
                            if single_match:
                                precios[cat_key] = single_match.group()
                                break
                        
                except Exception as e:
                    continue
            
            # Si solo encontramos categoría A, intentar método alternativo
            if precios['categoria_a'] and not precios['categoria_b']:
                # Intentar encontrar todos los precios de una vez
                try:
                    # Buscar la sección completa de precios
                    price_section = await page.locator('[class*="price"], [class*="tarifa"]').all()
                    
                    for elem in price_section:
                        text = await elem.text_content()
                        if text and '$' in text:
                            # Extraer todos los precios del texto
                            all_prices = re.findall(r'\$[\d.,]+', text)
                            if len(all_prices) >= 4:
                                precios['categoria_a'] = all_prices[0]
                                precios['categoria_b'] = all_prices[1]
                                precios['categoria_c'] = all_prices[2]
                                precios['no_afiliado'] = all_prices[3]
                                break
                except:
                    pass
                        
        except Exception as e:
            pass
        
        return precios
    
    def _parse_product_card(self, card_html: str, categoria: str, subcategoria: str) -> Optional[Producto]:
        """
        Parsea una tarjeta de producto.
        
        🎓 BEAUTIFULSOUP:
        1. BeautifulSoup(html, 'lxml') → Crea el árbol del DOM
        2. soup.find('tag') → Busca primer elemento
        3. soup.find_all('tag') → Busca todos
        4. soup.select('css.selector') → Usa selectores CSS
        5. element.get_text(strip=True) → Obtiene texto limpio
        """
        soup = BeautifulSoup(card_html, 'lxml')
        
        # === EXTRAER NOMBRE ===
        nombre = None
        # Buscar en orden de especificidad
        for selector in ['h2', 'h3', 'h4', '[class*="name"]', '[class*="title"]', 'a']:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if text and len(text) > 3:  # Evitar texto muy corto
                    nombre = text
                    break
        
        if not nombre:
            return None
        
        # === EXTRAER PRECIO ===
        precio = Precio()
        full_text = soup.get_text()
        
        # Buscar "Desde: $X.XXX"
        desde_match = re.search(r'Desde[:\s]*(\$[\d.,]+)', full_text, re.IGNORECASE)
        if desde_match:
            precio.desde = desde_match.group(1)
        else:
            # Cualquier precio
            price_match = re.search(r'\$[\d.,]+', full_text)
            if price_match:
                precio.desde = price_match.group()
        
        precio.valor_numerico = self._price_to_number(precio.desde)
        
        # === DETECTAR PROMOCIÓN ===
        promocion = bool(re.search(r'promoci[oó]n', full_text, re.IGNORECASE))
        
        # === FECHA LÍMITE ===
        fecha_limite = None
        fecha_match = re.search(r'Hasta\s+\d+\s+\w+\.?', full_text)
        if fecha_match:
            fecha_limite = fecha_match.group()
        
        # === EXTRAER URL ===
        url = None
        link = soup.find('a', href=True)
        if link:
            href = link.get('href', '')
            if href.startswith('/'):
                url = f"{self.BASE_URL}{href}"
            elif href.startswith('http'):
                url = href
        
        # === EXTRAER IMAGEN ===
        imagen_url = None
        img = soup.find('img')
        if img:
            imagen_url = img.get('src') or img.get('data-src') or img.get('srcset', '').split()[0]
            if imagen_url and not imagen_url.startswith('http'):
                if imagen_url.startswith('//'):
                    imagen_url = f"https:{imagen_url}"
                elif imagen_url.startswith('/'):
                    imagen_url = f"{self.BASE_URL}{imagen_url}"
        
        # === CREAR PRODUCTO ===
        return Producto(
            id=f"{subcategoria}-{hash(nombre) % 10000}",
            nombre=nombre,
            categoria_principal=categoria,
            subcategoria=subcategoria,
            precio=precio,
            url=url,
            imagen_url=imagen_url,
            promocion=promocion,
            fecha_limite_promocion=fecha_limite
        )
    
    async def scrape_category(self, subcategoria: str, categoria_principal: str = "General", 
                               fetch_detail_prices: bool = True) -> List[Producto]:
        """
        Scrapea una subcategoría completa.
        
        🎓 FLUJO:
        1. Abrir nueva pestaña
        2. Navegar a la URL de la categoría
        3. Esperar carga de JS
        4. Hacer scroll (lazy loading)
        5. Obtener HTML y parsear tarjetas
        6. (NUEVO) Visitar cada producto y hacer hover para obtener precios A/B/C
        7. Extraer cada producto con precios completos
        
        Args:
            subcategoria: Slug de la subcategoría
            categoria_principal: Nombre de la categoría principal
            fetch_detail_prices: Si True, visita cada producto para obtener precios por categoría
        """
        productos = []
        url = f"{self.NAVIGATION_URL}/{subcategoria}"
        
        print(f"\n📂 Scrapeando: {subcategoria}")
        print(f"   URL: {url}")
        
        try:
            # Crear nueva página/pestaña
            page = await self.browser.new_page()
            
            # Navegar
            await page.goto(url, wait_until='networkidle')
            
            # Esperar productos
            await self._wait_for_products(page)
            
            # Scroll para cargar todo
            await self._scroll_page(page)
            
            # Obtener HTML completo
            html = await page.content()
            soup = BeautifulSoup(html, 'lxml')
            
            # === BUSCAR TARJETAS DE PRODUCTOS ===
            cards = []
            
            # Selectores a probar (del más específico al más general)
            card_selectors = [
                '[class*="vtex"][class*="gallery"] > div',
                '[class*="ProductCard"]',
                '[class*="product-card"]',
                '[class*="resultado"]',
                'article',
                '[class*="Card"]',
            ]
            
            for selector in card_selectors:
                cards = soup.select(selector)
                if len(cards) > 0:
                    print(f"   ✅ Selector: {selector} ({len(cards)} elementos)")
                    break
            
            # Si no encontramos con selectores, buscar por precio
            if not cards:
                print("   🔍 Buscando por patrón de precios...")
                # Buscar elementos que contengan precios
                all_elements = soup.find_all(['div', 'article', 'li', 'section'])
                for elem in all_elements:
                    text = elem.get_text()
                    if '$' in text and len(text) < 500:  # Evitar elementos muy grandes
                        # Verificar que tenga nombre y precio
                        if re.search(r'\$[\d.,]+', text):
                            cards.append(elem)
                
                # Limpiar duplicados (elementos anidados)
                unique_cards = []
                for card in cards:
                    # Verificar que no sea hijo de otro card ya agregado
                    is_child = False
                    for uc in unique_cards:
                        if card in uc.descendants:
                            is_child = True
                            break
                    if not is_child:
                        unique_cards.append(card)
                cards = unique_cards[:50]  # Limitar
                
                print(f"   📦 Encontrados {len(cards)} contenedores con precios")
            
            # === PARSEAR CADA TARJETA ===
            for card in cards:
                try:
                    producto = self._parse_product_card(
                        str(card), 
                        categoria_principal, 
                        subcategoria
                    )
                    if producto:
                        productos.append(producto)
                except Exception as e:
                    continue
            
            print(f"   📊 Productos extraídos: {len(productos)}")
            
            # === OBTENER PRECIOS POR CATEGORÍA (HOVER) ===
            if fetch_detail_prices and productos:
                print(f"   🔍 Obteniendo precios por categoría (A/B/C/No afiliado)...")
                
                for i, producto in enumerate(productos):
                    if producto.url:
                        try:
                            print(f"      [{i+1}/{len(productos)}] {producto.nombre[:40]}...", end=" ")
                            
                            # Visitar página de detalle y extraer precios con hover
                            detail_precios = await self._scrape_product_detail(page, producto.url)
                            
                            # Actualizar precios del producto
                            if detail_precios.get('categoria_a'):
                                producto.precio.categoria_a = detail_precios['categoria_a']
                            if detail_precios.get('categoria_b'):
                                producto.precio.categoria_b = detail_precios['categoria_b']
                            if detail_precios.get('categoria_c'):
                                producto.precio.categoria_c = detail_precios['categoria_c']
                            if detail_precios.get('no_afiliado'):
                                producto.precio.no_afiliado = detail_precios['no_afiliado']
                            
                            # Mostrar resultado
                            found = sum(1 for k in ['categoria_a', 'categoria_b', 'categoria_c', 'no_afiliado'] 
                                       if detail_precios.get(k))
                            print(f"✅ {found}/4 precios")
                            
                            # Pequeña pausa entre productos
                            await asyncio.sleep(0.5)
                            
                        except Exception as e:
                            print(f"❌ Error")
                            continue
            
            # Cerrar pestaña
            await page.close()
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        return productos
    
    async def scrape_all(self, 
                         subcategorias: Optional[List[str]] = None,
                         categoria_principal: str = "General",
                         fetch_detail_prices: bool = True) -> List[Producto]:
        """
        Scrapea todas las subcategorías.
        
        Args:
            subcategorias: Lista de subcategorías a scrapear
            categoria_principal: Categoría principal
            fetch_detail_prices: Si True, visita cada producto para precios A/B/C
        """
        if not self.browser:
            await self.start()
        
        subcategorias = subcategorias or self.SUBCATEGORIAS
        
        for i, subcat in enumerate(subcategorias, 1):
            print(f"\n[{i}/{len(subcategorias)}]", end="")
            productos = await self.scrape_category(
                subcat, 
                categoria_principal,
                fetch_detail_prices=fetch_detail_prices
            )
            self.productos.extend(productos)
            
            # Pequeña pausa para no sobrecargar
            await asyncio.sleep(1)
        
        print(f"\n\n{'='*60}")
        print(f"📊 TOTAL PRODUCTOS SCRAPEADOS: {len(self.productos)}")
        print(f"{'='*60}")
        
        return self.productos
    
    def save_to_json(self, filepath: str):
        """Guarda en JSON"""
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        
        data = [p.to_dict() for p in self.productos]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Guardado en: {filepath}")
    
    def save_to_sqlite(self, filepath: str):
        """Guarda en base de datos SQLite"""
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        
        conn = sqlite3.connect(filepath)
        cursor = conn.cursor()
        
        # Crear tabla
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                categoria_principal TEXT,
                subcategoria TEXT,
                precio_desde TEXT,
                precio_categoria_a TEXT,
                precio_categoria_b TEXT,
                precio_categoria_c TEXT,
                precio_no_afiliado TEXT,
                valor_numerico REAL,
                descripcion TEXT,
                url TEXT,
                imagen_url TEXT,
                promocion INTEGER,
                fecha_limite_promocion TEXT,
                fecha_scraping TEXT
            )
        ''')
        
        # Insertar productos
        for p in self.productos:
            cursor.execute('''
                INSERT OR REPLACE INTO productos VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            ''', (
                p.id,
                p.nombre,
                p.categoria_principal,
                p.subcategoria,
                p.precio.desde,
                p.precio.categoria_a,
                p.precio.categoria_b,
                p.precio.categoria_c,
                p.precio.no_afiliado,
                p.precio.valor_numerico,
                p.descripcion,
                p.url,
                p.imagen_url,
                1 if p.promocion else 0,
                p.fecha_limite_promocion,
                p.fecha_scraping
            ))
        
        conn.commit()
        conn.close()
        
        print(f"💾 Base de datos guardada en: {filepath}")


# ============================================================================
# EJECUCIÓN
# ============================================================================

async def main():
    """Función principal"""
    print("=" * 70)
    print("🎯 SCRAPER DE TIENDA COMPENSAR")
    print("=" * 70)
    print("""
    Este scraper extrae:
    - Nombre del producto/servicio
    - Categoría y subcategoría
    - Precio "Desde"
    - Precios por categoría: A, B, C, No afiliado (con hover!)
    - URL del producto
    - Imagen
    - Si está en promoción
    """)
    
    scraper = CompensarPlaywrightScraper(
        headless=True,  # True = sin ventana, False = ver navegador
        slow_mo=0       # Milisegundos de delay (para debug)
    )
    
    try:
        await scraper.start()
        
        # Scrapear solo turismo como demo (tiene productos visibles)
        demo_subcategorias = ["turismo"]
        
        print(f"\n📋 Scrapeando categorías demo: {demo_subcategorias}")
        
        await scraper.scrape_all(
            subcategorias=demo_subcategorias,
            categoria_principal="Adulto Mayor",
            fetch_detail_prices=True  # ⭐ Obtener precios A/B/C con hover
        )
        
        # Guardar resultados
        if scraper.productos:
            scraper.save_to_json("data/compensar/productos.json")
            scraper.save_to_sqlite("data/compensar/compensar.db")
            
            # Mostrar algunos ejemplos con precios completos
            print("\n📦 PRODUCTOS CON PRECIOS POR CATEGORÍA:")
            print("-" * 60)
            for p in scraper.productos[:10]:
                print(f"  📌 {p.nombre}")
                print(f"     💰 Desde: {p.precio.desde or 'N/A'}")
                print(f"     🏷️ Cat A: {p.precio.categoria_a or 'N/A'}")
                print(f"     🏷️ Cat B: {p.precio.categoria_b or 'N/A'}")
                print(f"     🏷️ Cat C: {p.precio.categoria_c or 'N/A'}")
                print(f"     🏷️ No afiliado: {p.precio.no_afiliado or 'N/A'}")
                print(f"     📂 {p.categoria_principal} > {p.subcategoria}")
                if p.promocion:
                    print(f"     ⚡ ¡PROMOCIÓN! {p.fecha_limite_promocion or ''}")
                print()
        else:
            print("\n⚠️ No se encontraron productos")
            
    finally:
        await scraper.stop()


if __name__ == "__main__":
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright no está instalado")
        print("   Ejecuta: pip install playwright && playwright install chromium")
    else:
        asyncio.run(main())
