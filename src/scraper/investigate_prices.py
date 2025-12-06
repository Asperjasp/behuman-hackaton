"""
🔍 Investigador de estructura de precios de Compensar
=====================================================
Este script investiga cómo están estructurados los botones A/B/C/No afiliado
para poder hacer hover correctamente.
"""

import asyncio
from playwright.async_api import async_playwright


async def investigate_price_structure():
    """Investiga la estructura de los botones de precio"""
    
    print("=" * 70)
    print("🔍 INVESTIGANDO ESTRUCTURA DE PRECIOS DE COMPENSAR")
    print("=" * 70)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # URL de un producto de ejemplo
        url = "https://www.tiendacompensar.com/lagosol/pasadia-parque-acuatico-lagosol-sin-transporte/HER-B-ALJ-PAS-PLF-002"
        
        print(f"\n📡 Navegando a: {url}")
        await page.goto(url, wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # Tomar screenshot
        await page.screenshot(path="data/compensar/debug_price_buttons.png", full_page=True)
        print("📸 Screenshot guardado en data/compensar/debug_price_buttons.png")
        
        # Buscar la sección de precios
        print("\n🔍 Buscando sección de precios...")
        
        # Buscar todos los botones
        buttons = await page.locator('button').all()
        print(f"\n📌 Encontrados {len(buttons)} botones en la página:")
        for i, btn in enumerate(buttons[:20]):  # Limitar a 20
            try:
                text = await btn.text_content()
                class_attr = await btn.get_attribute('class') or ''
                if text:
                    print(f"   {i+1}. '{text.strip()[:30]}' | class: {class_attr[:50]}")
            except:
                continue
        
        # Buscar elementos que contengan A, B, C
        print("\n🔍 Buscando elementos con texto A, B, C, No afiliado...")
        
        # Buscar por texto exacto
        for letter in ['A', 'B', 'C', 'No afiliado']:
            try:
                elements = await page.locator(f'text="{letter}"').all()
                print(f"\n   '{letter}': {len(elements)} elementos encontrados")
                
                for i, elem in enumerate(elements[:5]):
                    try:
                        tag = await elem.evaluate('el => el.tagName')
                        class_attr = await elem.get_attribute('class') or ''
                        parent_class = await elem.evaluate('el => el.parentElement?.className || ""')
                        
                        print(f"      {i+1}. <{tag}> class='{class_attr[:40]}' parent='{parent_class[:40]}'")
                        
                        # Intentar hacer hover y ver si cambia algo
                        if letter in ['A', 'B', 'C']:
                            # Obtener precio antes del hover
                            price_before = await page.locator('[class*="price"]').first.text_content()
                            
                            # Hacer hover
                            await elem.hover()
                            await page.wait_for_timeout(500)
                            
                            # Obtener precio después del hover
                            price_after = await page.locator('[class*="price"]').first.text_content()
                            
                            if price_before != price_after:
                                print(f"         ✅ ¡HOVER FUNCIONA! Precio cambió: {price_before} → {price_after}")
                            else:
                                print(f"         ℹ️ Precio no cambió: {price_before}")
                                
                    except Exception as e:
                        print(f"      Error: {e}")
            except Exception as e:
                print(f"   Error buscando '{letter}': {e}")
        
        # Buscar la estructura específica de Oracle Commerce Cloud / VTEX
        print("\n🔍 Buscando selectores específicos de precios...")
        
        selectors_to_try = [
            '[data-price]',
            '[class*="affiliation"]',
            '[class*="category"]',
            '[class*="tariff"]',
            '[class*="tarifa"]',
            '[class*="tier"]',
            '[class*="membership"]',
            '[class*="afiliado"]',
            'input[type="radio"]',
            '[role="radio"]',
            '[role="tab"]',
            '.tab',
            '.tabs',
        ]
        
        for selector in selectors_to_try:
            try:
                elements = await page.locator(selector).all()
                if elements:
                    print(f"   ✅ '{selector}': {len(elements)} elementos")
                    for i, elem in enumerate(elements[:3]):
                        text = await elem.text_content() or ""
                        print(f"      → '{text.strip()[:50]}'")
            except:
                continue
        
        # Obtener HTML de la sección de precios
        print("\n📄 HTML de la sección de precios:")
        try:
            # Buscar el contenedor de precios
            price_section = await page.locator('[class*="price"]').first
            if price_section:
                parent = await price_section.evaluate('''
                    el => {
                        let p = el.parentElement;
                        for (let i = 0; i < 5 && p; i++) {
                            if (p.innerHTML.includes('No afiliado') || 
                                p.innerHTML.includes('categoría')) {
                                return p.outerHTML;
                            }
                            p = p.parentElement;
                        }
                        return el.parentElement?.parentElement?.outerHTML || el.outerHTML;
                    }
                ''')
                
                # Guardar HTML para análisis
                with open('data/compensar/price_section.html', 'w') as f:
                    f.write(parent)
                print("   HTML guardado en data/compensar/price_section.html")
                
        except Exception as e:
            print(f"   Error: {e}")
        
        # Cerrar
        await browser.close()
        
    print("\n✅ Investigación completada!")


if __name__ == "__main__":
    asyncio.run(investigate_price_structure())
