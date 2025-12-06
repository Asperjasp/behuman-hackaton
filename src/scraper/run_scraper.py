#!/usr/bin/env python3
"""
Main Scraper Runner
===================
Run this script to scrape Tienda Compensar and populate the database.
"""

import argparse
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scraper.compensar_scraper import CompensarScraper
from src.scraper.database import CompensarDatabase

# Optional Selenium support
try:
    from src.scraper.selenium_scraper import SeleniumCompensarScraper
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Scrape Tienda Compensar products and services'
    )
    parser.add_argument(
        '--categories',
        nargs='+',
        help='Specific categories to scrape (default: all)'
    )
    parser.add_argument(
        '--use-selenium',
        action='store_true',
        help='Use Selenium for JavaScript-rendered content'
    )
    parser.add_argument(
        '--db-path',
        default='data/compensar/compensar.db',
        help='Path to SQLite database'
    )
    parser.add_argument(
        '--export-json',
        help='Export results to JSON file'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=1.5,
        help='Delay between requests in seconds'
    )
    parser.add_argument(
        '--discover',
        action='store_true',
        help='Discover all available categories'
    )
    
    args = parser.parse_args()
    
    # Initialize database
    db = CompensarDatabase(args.db_path)
    
    try:
        if args.discover:
            # Discover categories first
            scraper = CompensarScraper(delay=args.delay)
            categories = scraper.discover_all_categories()
            print("\n📂 Discovered Categories:")
            for cat in sorted(categories):
                print(f"  - {cat}")
            return
        
        # Get categories to scrape
        categories = args.categories or CompensarScraper.CATEGORIES_TO_SCRAPE
        
        print(f"\n🔍 Starting scraper for {len(categories)} categories...")
        print(f"   Categories: {', '.join(categories)}")
        print(f"   Database: {args.db_path}")
        print(f"   Method: {'Selenium' if args.use_selenium else 'Requests/BeautifulSoup'}")
        print()
        
        # Choose scraper
        if args.use_selenium:
            if not SELENIUM_AVAILABLE:
                print("❌ Selenium not installed. Install with: pip install selenium webdriver-manager")
                print("   Falling back to BeautifulSoup...")
                scraper = CompensarScraper(delay=args.delay)
                products = scraper.scrape_all_categories(categories)
            else:
                with SeleniumCompensarScraper(headless=True) as scraper:
                    products = scraper.scrape_all_categories(categories)
        else:
            scraper = CompensarScraper(delay=args.delay)
            products = scraper.scrape_all_categories(categories)
        
        # Save to database
        if products:
            print(f"\n💾 Saving {len(products)} products to database...")
            inserted = db.insert_products_bulk(products)
            print(f"   Inserted: {inserted} products")
            
            # Log scraping
            for category in categories:
                cat_products = [p for p in products if p.get('category') == category]
                db.log_scraping(category, len(cat_products), success=True)
        else:
            print("\n⚠️  No products found. The website might use JavaScript rendering.")
            print("   Try running with --use-selenium flag")
        
        # Export to JSON if requested
        if args.export_json:
            db.export_to_json(args.export_json)
            print(f"\n📄 Data exported to {args.export_json}")
        
        # Print statistics
        stats = db.get_statistics()
        print("\n📊 Database Statistics:")
        print(f"   Total Products: {stats['total_products']}")
        print(f"   Total Categories: {stats['total_categories']}")
        if stats.get('price_min') and stats.get('price_max'):
            print(f"   Price Range: ${stats['price_min']:,.0f} - ${stats['price_max']:,.0f}")
        print("\n   Products per Category:")
        for cat, count in stats.get('products_per_category', {}).items():
            print(f"      {cat}: {count}")
        
        print("\n✅ Scraping completed successfully!")
        
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
