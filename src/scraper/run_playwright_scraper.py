#!/usr/bin/env python3
"""
🎯 Ejecutar Scraper de Tienda Compensar (Playwright)
=====================================================

Este script es el punto de entrada principal para el scraping.
Usa Playwright que funciona bien en WSL.

USO:
    # Scraping completo (todas las categorías)
    python src/scraper/run_playwright_scraper.py

    # Solo algunas categorías
    python src/scraper/run_playwright_scraper.py --categoria turismo --categoria musica
    
    # Sin mostrar navegador (más rápido)
    python src/scraper/run_playwright_scraper.py --headless

    # Ver navegador en acción (debug)
    python src/scraper/run_playwright_scraper.py --show-browser
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Añadir el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Importar el scraper
try:
    from src.scraper.compensar_playwright_scraper import (
        CompensarPlaywrightScraper,
        PLAYWRIGHT_AVAILABLE
    )
except ImportError as e:
    print(f"❌ Error importando scraper: {e}")
    PLAYWRIGHT_AVAILABLE = False


def parse_args():
    """Parsea argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description="🎯 Scraper de Tienda Compensar",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
SUBCATEGORÍAS DISPONIBLES:
  turismo, spa, gimnasio, natacion-y-buceo, cursos, planes, musica,
  actividades-recreativas, actividades-culturales, cocina, bienestar-y-armonia,
  pasadias, practicas-dirigidas, practicas-libres, sistemas, biblioteca,
  bolos, cine-y-entretenimiento, manualidades, salud-para-adulto-mayor,
  clases-personalizadas, cuidado-adulto-mayor, activacion-adulto-mayor

EJEMPLOS:
    %(prog)s                                    # Scraping completo
    %(prog)s --categoria turismo                # Solo turismo
    %(prog)s --categoria turismo musica spa     # Varias categorías
    %(prog)s --show-browser                     # Ver navegador (debug)
        """
    )
    
    parser.add_argument(
        '--categoria', '-c',
        nargs='+',
        dest='categorias',
        help='Subcategorías a scrapear (si no se especifica, scrapea todas)'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        default=True,
        help='Ejecutar sin ventana de navegador (default)'
    )
    
    parser.add_argument(
        '--show-browser',
        action='store_true',
        help='Mostrar ventana de navegador (útil para debug)'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='data/compensar',
        help='Directorio de salida (default: data/compensar)'
    )
    
    parser.add_argument(
        '--slow',
        type=int,
        default=0,
        metavar='MS',
        help='Milisegundos de delay entre acciones (para debug)'
    )
    
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Ejecutar demo con solo 3 categorías'
    )
    
    return parser.parse_args()


async def run_scraper(args):
    """Ejecuta el scraper"""
    
    # Determinar si mostrar navegador
    headless = not args.show_browser
    
    print("=" * 70)
    print("🎯 SCRAPER DE TIENDA COMPENSAR")
    print("=" * 70)
    print(f"   Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Modo: {'Headless (sin ventana)' if headless else 'Con ventana visible'}")
    
    if not PLAYWRIGHT_AVAILABLE:
        print("\n❌ Playwright no está instalado.")
        print("   Ejecuta estos comandos:")
        print("   pip install playwright")
        print("   playwright install chromium")
        return 1
    
    # Crear scraper
    scraper = CompensarPlaywrightScraper(
        headless=headless,
        slow_mo=args.slow
    )
    
    try:
        await scraper.start()
        
        # Determinar categorías
        if args.demo:
            subcategorias = ["turismo", "musica", "gimnasio"]
            print(f"\n📋 Modo DEMO: {subcategorias}")
        elif args.categorias:
            subcategorias = args.categorias
            print(f"\n📋 Categorías seleccionadas: {subcategorias}")
        else:
            subcategorias = None  # Todas
            print(f"\n📋 Scrapeando TODAS las categorías ({len(scraper.SUBCATEGORIAS)} total)")
        
        # Ejecutar scraping
        await scraper.scrape_all(
            subcategorias=subcategorias,
            categoria_principal="General"
        )
        
        # Guardar resultados
        if scraper.productos:
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Guardar JSON
            json_path = output_dir / "productos.json"
            scraper.save_to_json(str(json_path))
            
            # Guardar SQLite
            db_path = output_dir / "compensar.db"
            scraper.save_to_sqlite(str(db_path))
            
            # Resumen
            print("\n" + "=" * 70)
            print("📊 RESUMEN FINAL")
            print("=" * 70)
            print(f"   ✅ Total productos: {len(scraper.productos)}")
            print(f"   🏷️  En promoción: {sum(1 for p in scraper.productos if p.promocion)}")
            
            # Productos por subcategoría
            subcats = {}
            for p in scraper.productos:
                subcats[p.subcategoria] = subcats.get(p.subcategoria, 0) + 1
            
            print("\n   📂 Productos por subcategoría:")
            for subcat, count in sorted(subcats.items()):
                print(f"      {subcat}: {count}")
            
            print(f"\n   💾 Archivos guardados:")
            print(f"      JSON: {json_path}")
            print(f"      SQLite: {db_path}")
            
            return 0
        else:
            print("\n⚠️ No se encontraron productos")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
        
    finally:
        await scraper.stop()


def main():
    """Punto de entrada"""
    args = parse_args()
    
    try:
        exit_code = asyncio.run(run_scraper(args))
    except KeyboardInterrupt:
        print("\n\n⚠️ Scraping cancelado por el usuario")
        exit_code = 130
    
    print("\n✅ Proceso terminado")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
