#!/usr/bin/env python3
"""
🎯 Scraper Completo de Tienda Compensar + Sync a Supabase
=========================================================

Este script:
1. Scrapea TODAS las categorías de Compensar (no solo Adulto Mayor)
2. Guarda en JSON local
3. Sincroniza con Supabase para tu compañero

Categorías a scrapear:
- Deportes: gimnasio, natación, prácticas dirigidas/libres
- Bienestar: yoga, spa, bienestar y armonía
- Cultura: música, talleres, manualidades, cocina
- Recreación: turismo, pasadías, cine
- Educación: cursos, sistemas

Uso:
    python src/scraper/scrape_all.py                    # Scrapea todo
    python src/scraper/scrape_all.py --categories yoga spa  # Solo algunas
    python src/scraper/scrape_all.py --sync             # Scrapea y sube a Supabase
    python src/scraper/scrape_all.py --sync-only        # Solo sube JSON existente
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scraper.compensar_playwright_scraper import CompensarPlaywrightScraper, PLAYWRIGHT_AVAILABLE
from src.scraper.supabase_sync import SupabaseSync, load_productos_from_json


# ============================================================================
# CONFIGURACIÓN DE CATEGORÍAS
# ============================================================================

# Categorías principales y sus subcategorías
CATEGORIAS_A_SCRAPEAR = {
    "adultos": {
        "nombre": "Adultos",
        "subcategorias": [
            # Deportes
            "gimnasio",
            "natacion-y-buceo",
            "practicas-dirigidas",
            "practicas-libres",
            "bolos",
            # Bienestar
            "spa",
            "bienestar-y-armonia",
            # Cultura
            "musica",
            "actividades-culturales",
            "manualidades",
            "cocina",
            # Recreación
            "turismo",
            "pasadias",
            "actividades-recreativas",
            "cine-y-entretenimiento",
            # Educación
            "cursos",
            "sistemas",
            "biblioteca",
            "clases-personalizadas",
        ]
    },
    "adulto-mayor": {
        "nombre": "Adulto Mayor",
        "subcategorias": [
            "turismo",
            "activacion-adulto-mayor",
            "salud-para-adulto-mayor",
            "cuidado-adulto-mayor",
            "spa",
            "musica",
        ]
    },
    "adolescentes": {
        "nombre": "Adolescentes",
        "subcategorias": [
            "gimnasio",
            "natacion-y-buceo",
            "musica",
            "actividades-recreativas",
            "cursos",
        ]
    },
    "ninos": {
        "nombre": "Niños",
        "subcategorias": [
            "natacion-y-buceo",
            "musica",
            "actividades-recreativas",
            "manualidades",
            "cursos",
        ]
    }
}

# Subcategorías específicas para hobbies/situaciones
SUBCATEGORIAS_PRIORITARIAS = {
    # Mindfulness y bienestar mental
    "yoga": "bienestar-y-armonia",  # Yoga está bajo bienestar-y-armonia en Compensar
    "meditacion": "bienestar-y-armonia",
    "spa": "spa",
    
    # Ejercicio
    "gimnasio": "gimnasio",
    "natacion": "natacion-y-buceo",
    "deportes": "practicas-dirigidas",
    
    # Expresión artística
    "musica": "musica",
    "arte": "actividades-culturales",
    "manualidades": "manualidades",
    "cocina": "cocina",
    
    # Social
    "turismo": "turismo",
    "pasadias": "pasadias",
    "cine": "cine-y-entretenimiento",
    
    # Educación
    "cursos": "cursos",
    "tecnologia": "sistemas",
}


async def scrape_categoria(
    scraper: CompensarPlaywrightScraper,
    categoria_slug: str,
    categoria_nombre: str,
    subcategoria: str
) -> list:
    """Scrapea una subcategoría específica."""
    try:
        # El método scrape_category usa la URL base navegacion/category
        productos = await scraper.scrape_category(
            subcategoria=subcategoria,
            categoria_principal=categoria_nombre,
            fetch_detail_prices=False  # Más rápido sin precios detallados
        )
        return productos
    except Exception as e:
        print(f"   ⚠️ Error scrapeando {subcategoria}: {e}")
        return []


async def scrape_all_categories(
    categorias: dict = None,
    headless: bool = True
) -> list:
    """
    Scrapea todas las categorías configuradas.
    Más robusto: reinicia el navegador si hay errores.
    
    Args:
        categorias: Dict de categorías a scrapear (default: todas)
        headless: Navegador invisible
        
    Returns:
        Lista de todos los productos scrapeados
    """
    if categorias is None:
        categorias = CATEGORIAS_A_SCRAPEAR
    
    all_productos = []
    
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright no disponible. Instálalo con:")
        print("   pip install playwright")
        print("   playwright install chromium")
        return []
    
    # Crear lista plana de todas las subcategorías a procesar
    all_subcats = []
    for cat_slug, cat_config in categorias.items():
        cat_nombre = cat_config["nombre"]
        for subcat in cat_config["subcategorias"]:
            all_subcats.append((cat_slug, cat_nombre, subcat))
    
    print(f"\n📋 Total subcategorías a procesar: {len(all_subcats)}")
    
    # Procesar en batches, reiniciando navegador entre batches
    batch_size = 5
    
    for i in range(0, len(all_subcats), batch_size):
        batch = all_subcats[i:i + batch_size]
        
        print(f"\n{'='*60}")
        print(f"🔄 Batch {i//batch_size + 1}/{(len(all_subcats) + batch_size - 1)//batch_size}")
        print(f"   Procesando {len(batch)} subcategorías...")
        print('='*60)
        
        scraper = CompensarPlaywrightScraper(headless=headless)
        
        try:
            await scraper.start()
            
            for cat_slug, cat_nombre, subcat in batch:
                try:
                    productos = await scrape_categoria(scraper, cat_slug, cat_nombre, subcat)
                    
                    # Actualizar categoria_principal
                    for p in productos:
                        if hasattr(p, 'categoria_principal'):
                            p.categoria_principal = cat_nombre
                    
                    all_productos.extend(productos)
                    print(f"   ✅ {subcat}: {len(productos)} productos")
                    
                except Exception as e:
                    print(f"   ❌ {subcat}: {str(e)[:50]}")
                
                # Pausa entre requests
                await asyncio.sleep(2)
            
        except Exception as e:
            print(f"   ⚠️ Error en batch: {e}")
        finally:
            try:
                await scraper.stop()
            except:
                pass
        
        # Pausa entre batches
        if i + batch_size < len(all_subcats):
            print("   💤 Pausa entre batches (3s)...")
            await asyncio.sleep(3)
    
    return all_productos


def save_productos(productos: list, filepath: str = "data/compensar/productos.json"):
    """Guarda productos en JSON."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Convertir productos a dict si son objetos
    productos_dict = []
    for p in productos:
        if hasattr(p, 'to_dict'):
            productos_dict.append(p.to_dict())
        elif isinstance(p, dict):
            productos_dict.append(p)
    
    # Eliminar duplicados por ID
    seen = set()
    unique = []
    for p in productos_dict:
        pid = p.get('id', p.get('nombre', ''))
        if pid not in seen:
            seen.add(pid)
            unique.append(p)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Guardados {len(unique)} productos únicos en: {filepath}")
    return unique


def print_summary(productos: list):
    """Imprime resumen de productos scrapeados."""
    print("\n" + "="*60)
    print("📊 RESUMEN DE SCRAPING")
    print("="*60)
    
    # Contar por categoría
    by_category = {}
    by_subcategory = {}
    
    for p in productos:
        if hasattr(p, 'categoria_principal'):
            cat = p.categoria_principal
            subcat = p.subcategoria
        else:
            cat = p.get('categoria_principal', 'Sin categoría')
            subcat = p.get('subcategoria', 'sin subcategoría')
        
        by_category[cat] = by_category.get(cat, 0) + 1
        by_subcategory[subcat] = by_subcategory.get(subcat, 0) + 1
    
    print("\n📂 Por Categoría Principal:")
    for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
        print(f"   • {cat}: {count} productos")
    
    print("\n🏷️  Por Subcategoría:")
    for subcat, count in sorted(by_subcategory.items(), key=lambda x: -x[1]):
        print(f"   • {subcat}: {count} productos")
    
    print(f"\n📦 TOTAL: {len(productos)} productos")


async def main():
    """CLI principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="🎯 Scraper completo de Tienda Compensar",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python src/scraper/scrape_all.py                      # Scrapea todo
  python src/scraper/scrape_all.py --visible            # Ver el navegador
  python src/scraper/scrape_all.py --category adultos   # Solo adultos
  python src/scraper/scrape_all.py --sync               # Scrapea y sube a Supabase
  python src/scraper/scrape_all.py --sync-only          # Solo sube JSON existente
        """
    )
    
    parser.add_argument("--category", "-c", nargs="+",
                        help="Categorías específicas a scrapear")
    parser.add_argument("--visible", "-v", action="store_true",
                        help="Mostrar navegador (no headless)")
    parser.add_argument("--output", "-o", default="data/compensar/productos.json",
                        help="Archivo de salida JSON")
    parser.add_argument("--sync", "-s", action="store_true",
                        help="Sincronizar con Supabase después de scrapear")
    parser.add_argument("--sync-only", action="store_true",
                        help="Solo sincronizar JSON existente (no scrapear)")
    parser.add_argument("--supabase-url", help="Supabase URL")
    parser.add_argument("--supabase-key", help="Supabase Key")
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🎯 SCRAPER TIENDA COMPENSAR - TODAS LAS CATEGORÍAS")
    print("="*60)
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Si solo sincronizar
    if args.sync_only:
        print(f"\n📂 Cargando productos de: {args.output}")
        try:
            productos = load_productos_from_json(args.output)
            print(f"   ✅ {len(productos)} productos cargados")
        except FileNotFoundError:
            print(f"   ❌ Archivo no encontrado. Ejecuta primero sin --sync-only")
            return
        
        print_summary(productos)
        
        print("\n📤 Sincronizando con Supabase...")
        sync = SupabaseSync(url=args.supabase_url, key=args.supabase_key)
        if sync.client:
            stats = sync.upload_productos(productos)
            print(f"\n✅ Sincronización completada")
            print(f"   📊 Total en Supabase: {sync.get_activities_count()} actividades")
        return
    
    # Determinar qué categorías scrapear
    if args.category:
        categorias = {
            k: v for k, v in CATEGORIAS_A_SCRAPEAR.items() 
            if k in args.category
        }
        if not categorias:
            print(f"❌ Categorías no encontradas: {args.category}")
            print(f"   Disponibles: {list(CATEGORIAS_A_SCRAPEAR.keys())}")
            return
    else:
        categorias = CATEGORIAS_A_SCRAPEAR
    
    print(f"\n📋 Categorías a scrapear: {list(categorias.keys())}")
    total_subcats = sum(len(c['subcategorias']) for c in categorias.values())
    print(f"   Total subcategorías: {total_subcats}")
    
    # Scrapear
    productos = await scrape_all_categories(
        categorias=categorias,
        headless=not args.visible
    )
    
    if not productos:
        print("\n⚠️ No se obtuvieron productos")
        return
    
    # Guardar
    productos = save_productos(productos, args.output)
    print_summary(productos)
    
    # Sincronizar con Supabase si se pidió
    if args.sync:
        print("\n📤 Sincronizando con Supabase...")
        sync = SupabaseSync(url=args.supabase_url, key=args.supabase_key)
        if sync.client:
            stats = sync.upload_productos(productos)
            print(f"\n✅ Sincronización completada")
            print(f"   📊 Total en Supabase: {sync.get_activities_count()} actividades")
        else:
            print("⚠️ Supabase no configurado. Configura SUPABASE_URL y SUPABASE_KEY")
    
    print(f"\n⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
