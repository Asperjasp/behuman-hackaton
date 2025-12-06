"""
🔍 Investigador de API de Tienda Compensar
==========================================
Busca endpoints de API que podamos usar directamente.
"""

import requests
import json
import re

def investigate_api():
    """Busca APIs internas en la página de Compensar"""
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/html, */*',
        'Accept-Language': 'es-CO,es;q=0.9',
    })
    
    print("🔍 Buscando APIs internas de Tienda Compensar...")
    print("=" * 60)
    
    # 1. Revisar el HTML base
    print("\n📄 Analizando HTML base...")
    resp = session.get("https://www.tiendacompensar.com")
    html = resp.text
    
    # Buscar URLs de API en el JavaScript
    api_patterns = [
        r'["\'](https?://[^"\']*api[^"\']*)["\']',
        r'["\'](/api[^"\']*)["\']',
        r'["\'](https?://[^"\']*\.json)["\']',
        r'["\'](/[^"\']*\.json)["\']',
        r'fetch\(["\']([^"\']+)["\']',
        r'\.get\(["\']([^"\']+)["\']',
        r'endpoint["\s:]+["\']([^"\']+)["\']',
    ]
    
    found_apis = set()
    for pattern in api_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        found_apis.update(matches)
    
    if found_apis:
        print("\n✅ APIs encontradas:")
        for api in sorted(found_apis):
            if api.startswith('/') and not api.startswith('//'):
                print(f"   {api}")
    
    # 2. Probar endpoints VTEX comunes (Compensar parece usar VTEX)
    print("\n🔍 Probando endpoints VTEX...")
    
    vtex_endpoints = [
        "/api/catalog_system/pub/products/search",
        "/api/catalog_system/pub/category/tree/3",
        "/api/io/safedata/CL/documents",
        "/_v/segment/routing/vtex.store@2.x/product",
        "/api/checkout/pub/orderForm/simulation",
    ]
    
    base_url = "https://www.tiendacompensar.com"
    
    for endpoint in vtex_endpoints:
        try:
            url = f"{base_url}{endpoint}"
            resp = session.get(url, timeout=10)
            if resp.status_code == 200:
                print(f"   ✅ {endpoint} - {resp.status_code}")
                try:
                    data = resp.json()
                    print(f"      Tipo de respuesta: {type(data).__name__}")
                    if isinstance(data, list):
                        print(f"      Items: {len(data)}")
                    elif isinstance(data, dict):
                        print(f"      Keys: {list(data.keys())[:5]}")
                except:
                    print(f"      No es JSON")
            else:
                print(f"   ❌ {endpoint} - {resp.status_code}")
        except Exception as e:
            print(f"   ⚠️ {endpoint} - Error: {e}")
    
    # 3. Buscar en la página de turismo
    print("\n🔍 Analizando página de turismo...")
    resp = session.get("https://www.tiendacompensar.com/navegacion/category/turismo")
    turismo_html = resp.text
    
    # Buscar datos JSON embebidos
    json_patterns = [
        r'window\.__STATE__\s*=\s*({[^;]+})',
        r'window\.__INITIAL_STATE__\s*=\s*({[^;]+})',
        r'__NEXT_DATA__[^>]*>([^<]+)<',
        r'data-state="([^"]+)"',
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, turismo_html)
        if matches:
            print(f"   ✅ Encontrado estado embebido: {pattern[:30]}...")
            for match in matches[:1]:
                try:
                    data = json.loads(match)
                    print(f"      Tipo: {type(data).__name__}")
                    if isinstance(data, dict):
                        print(f"      Keys: {list(data.keys())[:5]}")
                except:
                    print(f"      (No se pudo parsear como JSON)")
    
    # 4. Revisar Network calls típicas
    print("\n🔍 Probando URLs de búsqueda...")
    
    search_urls = [
        f"{base_url}/api/catalog_system/pub/products/search?fq=C:/1/",
        f"{base_url}/api/catalog_system/pub/products/search/turismo",
        f"{base_url}/_search?query=turismo",
        f"{base_url}/buscapagina?sl=&PS=12&cc=12&sm=0&O=OrderByTopSaleDESC",
    ]
    
    for url in search_urls:
        try:
            resp = session.get(url, timeout=10)
            if resp.status_code == 200 and len(resp.content) > 100:
                print(f"   ✅ {url[:50]}...")
                print(f"      Status: {resp.status_code}, Size: {len(resp.content)} bytes")
        except:
            pass
    
    # 5. Intentar GraphQL (común en VTEX)
    print("\n🔍 Probando GraphQL...")
    
    graphql_query = {
        "query": """
            query products {
                products(first: 10) {
                    items {
                        productName
                        priceRange {
                            sellingPrice {
                                lowPrice
                            }
                        }
                    }
                }
            }
        """
    }
    
    graphql_endpoints = [
        f"{base_url}/_v/public/graphql/v1",
        f"{base_url}/graphql",
        f"{base_url}/api/graphql",
    ]
    
    for endpoint in graphql_endpoints:
        try:
            resp = session.post(endpoint, json=graphql_query, timeout=10)
            if resp.status_code in [200, 400]:  # 400 puede indicar que existe pero query inválida
                print(f"   📍 GraphQL endpoint: {endpoint} - {resp.status_code}")
        except:
            pass
    
    print("\n" + "=" * 60)
    print("🎯 CONCLUSIÓN")
    print("=" * 60)
    print("""
    La página usa tecnología VTEX pero con acceso restringido.
    Se requiere Selenium para el scraping completo ya que el 
    contenido se carga dinámicamente via JavaScript (Knockout.js).
    """)


if __name__ == "__main__":
    investigate_api()
