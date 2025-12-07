#!/usr/bin/env python3
"""
📤 Upload productos.json to Supabase activity_catalog
=====================================================
This script:
1. Reads productos.json 
2. Adds profile_tags and situation_tags based on subcategoria
3. Uploads to Supabase activity_catalog table

Usage:
    python src/scraper/upload_to_supabase.py
"""

import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Import tag mappings from supabase_sync
from supabase_sync import (
    PROFILE_TAGS_BY_CATEGORY,
    SITUATION_TAGS_BY_CATEGORY,
    AGE_GROUP_BY_CATEGORIA_PRINCIPAL
)

try:
    from supabase import create_client
except ImportError:
    print("❌ Supabase not installed. Run: pip install supabase")
    exit(1)


def load_productos(path: str = "data/compensar/productos.json") -> list:
    """Load productos from JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def transform_producto(p: dict) -> dict:
    """Transform a producto dict to activity_catalog format."""
    subcategoria = p.get('subcategoria', 'general')
    categoria_principal = p.get('categoria_principal', 'Adultos')
    
    # Get tags based on subcategoria
    profile_tags = PROFILE_TAGS_BY_CATEGORY.get(subcategoria, ["general"])
    situation_tags = SITUATION_TAGS_BY_CATEGORY.get(subcategoria, ["bienestar general"])
    age_group = AGE_GROUP_BY_CATEGORIA_PRINCIPAL.get(categoria_principal, "adultos")
    
    # Handle price - convert to proper format
    precio = p.get('precio', {})
    if isinstance(precio, dict):
        price_obj = {
            "desde": precio.get('desde'),
            "categoria_a": precio.get('categoria_a'),
            "categoria_b": precio.get('categoria_b'),
            "categoria_c": precio.get('categoria_c'),
            "no_afiliado": precio.get('no_afiliado')
        }
    else:
        price_obj = {"desde": str(precio)}
    
    return {
        "id": str(uuid.uuid4()),
        "entity": "compensar",
        "category": subcategoria,
        "activity_title": p.get('nombre', ''),
        "description": p.get('descripcion', ''),
        "price": price_obj,
        "age_group": age_group,
        "profile_tags": profile_tags,
        "situation_tags": situation_tags,
        "image_url": p.get('imagen_url'),
        "booking_url": p.get('url'),
        "location": "Bogotá",
        "is_active": True,
        "subcategory": subcategoria,
        "categoria_principal": categoria_principal,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }


def upload_to_supabase(items: list) -> dict:
    """Upload items to Supabase activity_catalog table."""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_SERVICE_KEY')
    
    if not url or not key:
        return {"error": "SUPABASE_URL and SUPABASE_KEY required in .env", "uploaded": 0}
    
    supabase = create_client(url, key)
    print(f"✅ Connected to Supabase")
    
    # First, clear existing compensar data (optional - comment out if you want to append)
    print("🗑️  Clearing existing compensar data...")
    try:
        supabase.table('activity_catalog').delete().eq('entity', 'compensar').execute()
    except Exception as e:
        print(f"   ⚠️ Could not clear (table might be empty): {e}")
    
    # Upload in batches
    batch_size = 50
    uploaded = 0
    errors = 0
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        try:
            result = supabase.table('activity_catalog').insert(batch).execute()
            uploaded += len(batch)
            print(f"   ✅ Uploaded batch {i//batch_size + 1}: {len(batch)} items")
        except Exception as e:
            errors += len(batch)
            print(f"   ❌ Error in batch {i//batch_size + 1}: {e}")
    
    return {"uploaded": uploaded, "errors": errors, "total": len(items)}


def main():
    print("\n" + "="*60)
    print("📤 UPLOAD PRODUCTOS TO SUPABASE")
    print("="*60 + "\n")
    
    # Load productos
    productos = load_productos()
    print(f"📦 Loaded {len(productos)} productos from JSON")
    
    # Transform to activity_catalog format
    items = [transform_producto(p) for p in productos]
    print(f"🔄 Transformed to {len(items)} activity_catalog items")
    
    # Show sample
    print("\n📋 Sample item:")
    sample = items[0]
    print(f"   Title: {sample['activity_title']}")
    print(f"   Category: {sample['category']}")
    print(f"   Profile Tags: {sample['profile_tags']}")
    print(f"   Situation Tags: {sample['situation_tags']}")
    print(f"   Age Group: {sample['age_group']}")
    
    # Upload
    print("\n📤 Uploading to Supabase...")
    result = upload_to_supabase(items)
    
    print("\n" + "="*60)
    print(f"✅ DONE: {result.get('uploaded', 0)} uploaded, {result.get('errors', 0)} errors")
    print("="*60 + "\n")
    
    return result


if __name__ == "__main__":
    main()
