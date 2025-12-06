"""
Compensar Database Module
=========================
SQLite database for storing scraped Compensar data.
"""

import sqlite3
import json
from typing import Dict, List, Optional
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class CompensarDatabase:
    """
    SQLite database manager for Compensar scraped data.
    """
    
    def __init__(self, db_path: str = "data/compensar/compensar.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection: Optional[sqlite3.Connection] = None
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Create database tables if they don't exist."""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        
        cursor = self.connection.cursor()
        
        # Categories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                name TEXT,
                description TEXT,
                parent_category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Products/Services table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_id TEXT,
                category_id INTEGER,
                category_slug TEXT,
                name TEXT NOT NULL,
                description TEXT,
                price TEXT,
                price_numeric REAL,
                price_from BOOLEAN DEFAULT FALSE,
                image_url TEXT,
                product_url TEXT UNIQUE,
                availability TEXT,
                rating REAL,
                location TEXT,
                target_audience TEXT,
                additional_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        ''')
        
        # Scraping logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraping_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_slug TEXT,
                products_found INTEGER,
                success BOOLEAN,
                error_message TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_slug)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_price ON products(price_numeric)')
        
        self.connection.commit()
        logger.info(f"Database initialized at {self.db_path}")
    
    def _parse_price(self, price_str: Optional[str]) -> Optional[float]:
        """
        Parse price string to numeric value.
        
        Args:
            price_str: Price string like "$65.000" or "Desde: $10.300"
            
        Returns:
            Numeric price value or None
        """
        if not price_str:
            return None
        
        try:
            # Remove common text and symbols
            clean = price_str.lower()
            clean = clean.replace('desde:', '').replace('desde', '')
            clean = clean.replace('$', '').replace(',', '').replace('.', '')
            clean = clean.strip()
            
            # Try to extract number
            import re
            numbers = re.findall(r'\d+', clean)
            if numbers:
                return float(numbers[0])
        except Exception:
            pass
        
        return None
    
    def insert_category(self, slug: str, name: Optional[str] = None, 
                       description: Optional[str] = None,
                       parent_category: Optional[str] = None) -> int:
        """
        Insert or update a category.
        
        Args:
            slug: Category slug (URL-friendly name)
            name: Display name
            description: Category description
            parent_category: Parent category slug
            
        Returns:
            Category ID
        """
        cursor = self.connection.cursor()
        
        cursor.execute('''
            INSERT INTO categories (slug, name, description, parent_category)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                name = COALESCE(excluded.name, categories.name),
                description = COALESCE(excluded.description, categories.description),
                parent_category = COALESCE(excluded.parent_category, categories.parent_category),
                updated_at = CURRENT_TIMESTAMP
        ''', (slug, name or slug.replace('-', ' ').title(), description, parent_category))
        
        self.connection.commit()
        
        # Get the category ID
        cursor.execute('SELECT id FROM categories WHERE slug = ?', (slug,))
        return cursor.fetchone()[0]
    
    def insert_product(self, product: Dict) -> Optional[int]:
        """
        Insert or update a product.
        
        Args:
            product: Product dictionary with fields
            
        Returns:
            Product ID or None if failed
        """
        cursor = self.connection.cursor()
        
        try:
            # Ensure category exists
            category_slug = product.get('category', 'uncategorized')
            category_id = self.insert_category(category_slug)
            
            # Parse price
            price_numeric = self._parse_price(product.get('price'))
            
            # Prepare additional data as JSON
            additional_data = {k: v for k, v in product.items() 
                            if k not in ['category', 'name', 'description', 'price', 
                                        'image_url', 'product_url', 'availability', 
                                        'rating', 'location']}
            
            cursor.execute('''
                INSERT INTO products (
                    category_id, category_slug, name, description, price, 
                    price_numeric, price_from, image_url, product_url,
                    availability, rating, location, additional_data
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(product_url) DO UPDATE SET
                    name = excluded.name,
                    description = excluded.description,
                    price = excluded.price,
                    price_numeric = excluded.price_numeric,
                    image_url = excluded.image_url,
                    availability = excluded.availability,
                    updated_at = CURRENT_TIMESTAMP
            ''', (
                category_id,
                category_slug,
                product.get('name'),
                product.get('description'),
                product.get('price'),
                price_numeric,
                product.get('price_from', False),
                product.get('image_url'),
                product.get('product_url'),
                product.get('availability'),
                product.get('rating'),
                product.get('location'),
                json.dumps(additional_data) if additional_data else None
            ))
            
            self.connection.commit()
            return cursor.lastrowid
            
        except Exception as e:
            logger.error(f"Error inserting product: {e}")
            return None
    
    def insert_products_bulk(self, products: List[Dict]) -> int:
        """
        Insert multiple products in bulk.
        
        Args:
            products: List of product dictionaries
            
        Returns:
            Number of products inserted
        """
        inserted = 0
        for product in products:
            if self.insert_product(product):
                inserted += 1
        
        logger.info(f"Inserted {inserted}/{len(products)} products")
        return inserted
    
    def log_scraping(self, category_slug: str, products_found: int, 
                    success: bool = True, error_message: Optional[str] = None) -> None:
        """
        Log a scraping operation.
        
        Args:
            category_slug: Category that was scraped
            products_found: Number of products found
            success: Whether scraping was successful
            error_message: Error message if failed
        """
        cursor = self.connection.cursor()
        cursor.execute('''
            INSERT INTO scraping_logs (category_slug, products_found, success, error_message)
            VALUES (?, ?, ?, ?)
        ''', (category_slug, products_found, success, error_message))
        self.connection.commit()
    
    def get_products_by_category(self, category_slug: str) -> List[Dict]:
        """
        Get all products in a category.
        
        Args:
            category_slug: Category slug
            
        Returns:
            List of product dictionaries
        """
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT * FROM products WHERE category_slug = ?
            ORDER BY name
        ''', (category_slug,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_products(self) -> List[Dict]:
        """Get all products from database."""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM products ORDER BY category_slug, name')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_categories(self) -> List[Dict]:
        """Get all categories from database."""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM categories ORDER BY slug')
        return [dict(row) for row in cursor.fetchall()]
    
    def search_products(self, query: str, category: Optional[str] = None,
                       min_price: Optional[float] = None,
                       max_price: Optional[float] = None) -> List[Dict]:
        """
        Search products with filters.
        
        Args:
            query: Search term for name/description
            category: Optional category filter
            min_price: Minimum price filter
            max_price: Maximum price filter
            
        Returns:
            List of matching products
        """
        cursor = self.connection.cursor()
        
        sql = '''
            SELECT * FROM products 
            WHERE (name LIKE ? OR description LIKE ?)
        '''
        params = [f'%{query}%', f'%{query}%']
        
        if category:
            sql += ' AND category_slug = ?'
            params.append(category)
        
        if min_price is not None:
            sql += ' AND price_numeric >= ?'
            params.append(min_price)
        
        if max_price is not None:
            sql += ' AND price_numeric <= ?'
            params.append(max_price)
        
        sql += ' ORDER BY name'
        
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        cursor = self.connection.cursor()
        
        stats = {}
        
        # Total products
        cursor.execute('SELECT COUNT(*) FROM products')
        stats['total_products'] = cursor.fetchone()[0]
        
        # Total categories
        cursor.execute('SELECT COUNT(*) FROM categories')
        stats['total_categories'] = cursor.fetchone()[0]
        
        # Products per category
        cursor.execute('''
            SELECT category_slug, COUNT(*) as count 
            FROM products 
            GROUP BY category_slug 
            ORDER BY count DESC
        ''')
        stats['products_per_category'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Price range
        cursor.execute('''
            SELECT MIN(price_numeric), MAX(price_numeric), AVG(price_numeric)
            FROM products WHERE price_numeric IS NOT NULL
        ''')
        row = cursor.fetchone()
        stats['price_min'] = row[0]
        stats['price_max'] = row[1]
        stats['price_avg'] = row[2]
        
        # Last scraping info
        cursor.execute('''
            SELECT * FROM scraping_logs ORDER BY scraped_at DESC LIMIT 1
        ''')
        last_log = cursor.fetchone()
        if last_log:
            stats['last_scrape'] = dict(last_log)
        
        return stats
    
    def export_to_json(self, filepath: str) -> None:
        """
        Export all data to JSON file.
        
        Args:
            filepath: Output file path
        """
        data = {
            'categories': self.get_all_categories(),
            'products': self.get_all_products(),
            'statistics': self.get_statistics(),
            'exported_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Data exported to {filepath}")
    
    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    # Test the database
    with CompensarDatabase("data/compensar/compensar.db") as db:
        # Insert test category
        cat_id = db.insert_category("turismo", "Turismo", "Planes turísticos")
        print(f"Created category with ID: {cat_id}")
        
        # Insert test product
        product = {
            'category': 'turismo',
            'name': 'Plan San Andrés',
            'description': 'Viaje todo incluido a San Andrés',
            'price': 'Desde: $1.500.000',
            'product_url': 'https://example.com/plan-san-andres',
            'image_url': 'https://example.com/image.jpg'
        }
        prod_id = db.insert_product(product)
        print(f"Created product with ID: {prod_id}")
        
        # Get statistics
        stats = db.get_statistics()
        print(f"Database stats: {stats}")
