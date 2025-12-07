"""
🔄 Sincronización con Supabase para BeHuman
============================================
Convierte productos scrapeados al formato activity_catalog de Supabase.

FLUJO:
1. Scraper extrae productos de Compensar
2. Este módulo aplica tags automáticos (profile_tags, situation_tags)
3. Sube a Supabase en la tabla activity_catalog

TAGS AUTOMÁTICOS basados en categoría:
- turismo → ["social", "aventurero"] + ["estrés alto", "bienestar general"]
- gimnasio → ["activo", "disciplinado"] + ["ansiedad", "estrés alto"]
- música → ["creativo", "expresivo"] + ["ánimo bajo", "estrés alto"]
- etc.
"""

import os
import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

# Supabase client
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️ Supabase no instalado. Ejecuta: pip install supabase")


# ============================================================================
# SISTEMA DE TAGS AUTOMÁTICOS
# ============================================================================

# Profile tags: características del usuario que encajan con esta actividad
PROFILE_TAGS_BY_CATEGORY = {
    # Deportes y actividad física
    "gimnasio": ["activo", "disciplinado", "competitivo"],
    "natacion-y-buceo": ["activo", "aventurero", "tranquilo"],
    "practicas-dirigidas": ["activo", "social", "disciplinado"],
    "practicas-libres": ["activo", "independiente", "autodidacta"],
    "bolos": ["social", "competitivo", "recreativo"],
    
    # Cultura y creatividad
    "musica": ["creativo", "expresivo", "artístico"],
    "actividades-culturales": ["creativo", "curioso", "intelectual"],
    "manualidades": ["creativo", "paciente", "detallista"],
    "cocina": ["creativo", "social", "práctico"],
    
    # Bienestar y relajación
    "spa": ["tranquilo", "autocuidado", "relajado"],
    "bienestar-y-armonia": ["tranquilo", "espiritual", "introspectivo"],
    
    # Social y recreativo
    "turismo": ["social", "aventurero", "curioso"],
    "pasadias": ["social", "familiar", "recreativo"],
    "actividades-recreativas": ["social", "activo", "recreativo"],
    "cine-y-entretenimiento": ["social", "recreativo", "relajado"],
    
    # Educación y desarrollo
    "cursos": ["curioso", "autodidacta", "intelectual"],
    "sistemas": ["tecnológico", "analítico", "autodidacta"],
    "biblioteca": ["intelectual", "tranquilo", "curioso"],
    "clases-personalizadas": ["disciplinado", "enfocado", "autodidacta"],
    
    # Planes y paquetes
    "planes": ["social", "familiar", "recreativo"],
    
    # Adulto mayor
    "activacion-adulto-mayor": ["activo", "social", "saludable"],
    "salud-para-adulto-mayor": ["saludable", "autocuidado", "tranquilo"],
    "cuidado-adulto-mayor": ["saludable", "tranquilo", "acompañado"],
}

# Situation tags: situaciones emocionales que esta actividad puede ayudar
SITUATION_TAGS_BY_CATEGORY = {
    # Deportes - buenos para estrés y ansiedad
    "gimnasio": ["estrés alto", "ansiedad", "baja autoestima"],
    "natacion-y-buceo": ["estrés alto", "ansiedad", "insomnio"],
    "practicas-dirigidas": ["estrés alto", "ansiedad", "aislamiento social"],
    "practicas-libres": ["estrés alto", "necesidad de espacio personal"],
    "bolos": ["estrés alto", "aislamiento social", "bienestar general"],
    
    # Cultura - buenos para ánimo bajo y expresión
    "musica": ["ánimo bajo", "estrés alto", "necesidad de expresión"],
    "actividades-culturales": ["ánimo bajo", "aislamiento social", "bienestar general"],
    "manualidades": ["ansiedad", "estrés alto", "necesidad de enfoque"],
    "cocina": ["ánimo bajo", "aislamiento social", "bienestar general"],
    
    # Bienestar - relajación y autocuidado
    "spa": ["estrés alto", "ansiedad", "agotamiento"],
    "bienestar-y-armonia": ["ansiedad", "estrés alto", "crisis existencial"],
    
    # Social - contra el aislamiento
    "turismo": ["ánimo bajo", "aislamiento social", "agotamiento"],
    "pasadias": ["estrés alto", "aislamiento social", "problemas familiares"],
    "actividades-recreativas": ["ánimo bajo", "aislamiento social", "bienestar general"],
    "cine-y-entretenimiento": ["estrés alto", "ánimo bajo", "bienestar general"],
    
    # Educación - desarrollo personal
    "cursos": ["baja autoestima", "estancamiento profesional", "bienestar general"],
    "sistemas": ["estancamiento profesional", "baja autoestima", "necesidad de propósito"],
    "biblioteca": ["estrés alto", "necesidad de espacio personal", "bienestar general"],
    "clases-personalizadas": ["baja autoestima", "estancamiento profesional", "ansiedad"],
    
    # Planes
    "planes": ["aislamiento social", "problemas familiares", "bienestar general"],
    
    # Adulto mayor
    "activacion-adulto-mayor": ["aislamiento social", "ánimo bajo", "pérdida de movilidad"],
    "salud-para-adulto-mayor": ["ansiedad", "preocupación por salud", "bienestar general"],
    "cuidado-adulto-mayor": ["ansiedad", "necesidad de acompañamiento", "bienestar general"],
}

# Mapeo de categoría principal a age_group
AGE_GROUP_BY_CATEGORIA_PRINCIPAL = {
    "Embarazadas": "adultos",
    "Bebés": "bebes",
    "Niños": "niños",
    "Adolescentes": "adolescentes",
    "Adultos": "adultos",
    "Adulto Mayor": "tercera edad",
    "General": "familiar",  # default
}


@dataclass
class ActivityCatalogItem:
    """
    Estructura que mapea directamente a activity_catalog de Supabase.
    """
    entity: str = "compensar"
    category: str = ""
    activity_title: str = ""
    description: Optional[str] = None
    price: Dict[str, Any] = None  # JSONB
    age_group: Optional[str] = None
    profile_tags: List[str] = None
    situation_tags: List[str] = None
    image_url: Optional[str] = None
    booking_url: Optional[str] = None
    location: Optional[str] = None
    is_active: bool = True
    
    # Campos extra para trazabilidad
    subcategory: Optional[str] = None  # Campo adicional
    scraped_at: Optional[str] = None
    
    def to_supabase_dict(self) -> dict:
        """Convierte a diccionario para insertar en Supabase"""
        return {
            "entity": self.entity,
            "category": self.category,
            "activity_title": self.activity_title,
            "description": self.description,
            "price": self.price,
            "age_group": self.age_group,
            "profile_tags": self.profile_tags or [],
            "situation_tags": self.situation_tags or [],
            "image_url": self.image_url,
            "booking_url": self.booking_url,
            "location": self.location,
            "is_active": self.is_active,
            # embedding se genera después con OpenAI
        }


def price_string_to_number(price_str: Optional[str]) -> Optional[int]:
    """Convierte '$33.800' a 33800"""
    if not price_str:
        return None
    clean = re.sub(r'[^\d]', '', price_str)
    try:
        return int(clean)
    except:
        return None


def convert_producto_to_activity(producto: dict) -> ActivityCatalogItem:
    """
    Convierte un producto del scraper al formato activity_catalog.
    
    Args:
        producto: Dict con estructura del scraper (Producto.to_dict())
        
    Returns:
        ActivityCatalogItem listo para Supabase
    """
    subcategoria = producto.get("subcategoria", "general")
    categoria_principal = producto.get("categoria_principal", "General")
    precio = producto.get("precio", {})
    
    # Obtener tags automáticos basados en la subcategoría
    profile_tags = PROFILE_TAGS_BY_CATEGORY.get(subcategoria, ["general"])
    situation_tags = SITUATION_TAGS_BY_CATEGORY.get(subcategoria, ["bienestar general"])
    
    # Determinar age_group
    age_group = AGE_GROUP_BY_CATEGORIA_PRINCIPAL.get(categoria_principal, "familiar")
    
    # Construir precio JSONB
    price_jsonb = {
        "desde": price_string_to_number(precio.get("desde")),
        "tipo_a": price_string_to_number(precio.get("categoria_a")),
        "tipo_b": price_string_to_number(precio.get("categoria_b")),
        "tipo_c": price_string_to_number(precio.get("categoria_c")),
        "no_afiliado": price_string_to_number(precio.get("no_afiliado")),
    }
    
    # Mapear categoría para Supabase (más general)
    category_mapping = {
        "gimnasio": "deporte",
        "natacion-y-buceo": "deporte",
        "practicas-dirigidas": "deporte",
        "practicas-libres": "deporte",
        "bolos": "recreación",
        "musica": "cultura",
        "actividades-culturales": "cultura",
        "manualidades": "cultura",
        "cocina": "cultura",
        "spa": "bienestar",
        "bienestar-y-armonia": "bienestar",
        "turismo": "recreación",
        "pasadias": "recreación",
        "actividades-recreativas": "recreación",
        "cine-y-entretenimiento": "recreación",
        "cursos": "educación",
        "sistemas": "educación",
        "biblioteca": "cultura",
        "clases-personalizadas": "educación",
        "planes": "recreación",
        "activacion-adulto-mayor": "bienestar",
        "salud-para-adulto-mayor": "bienestar",
        "cuidado-adulto-mayor": "bienestar",
    }
    
    category = category_mapping.get(subcategoria, "recreación")
    
    return ActivityCatalogItem(
        entity="compensar",
        category=category,
        activity_title=producto.get("nombre", ""),
        description=producto.get("descripcion"),
        price=price_jsonb,
        age_group=age_group,
        profile_tags=profile_tags,
        situation_tags=situation_tags,
        image_url=producto.get("imagen_url"),
        booking_url=producto.get("url"),
        location="Bogotá",  # Default para Compensar
        is_active=True,
        subcategory=subcategoria,
        scraped_at=producto.get("fecha_scraping", datetime.now().isoformat()),
    )


class SupabaseSync:
    """
    Cliente para sincronizar productos con Supabase.
    
    Uso:
        sync = SupabaseSync()
        sync.upload_productos(lista_productos)
    """
    
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """
        Inicializa el cliente de Supabase.
        
        Args:
            url: Supabase project URL (o env SUPABASE_URL)
            key: Supabase anon/service key (o env SUPABASE_KEY)
        """
        self.url = url or os.getenv("SUPABASE_URL")
        self.key = key or os.getenv("SUPABASE_KEY")
        
        if not self.url or not self.key:
            print("⚠️ Configura SUPABASE_URL y SUPABASE_KEY en variables de entorno")
            print("   O pásalos como parámetros: SupabaseSync(url='...', key='...')")
            self.client = None
        elif SUPABASE_AVAILABLE:
            self.client: Client = create_client(self.url, self.key)
            print("✅ Conectado a Supabase")
        else:
            self.client = None
    
    def upload_productos(self, productos: List[dict], batch_size: int = 50) -> dict:
        """
        Sube productos a activity_catalog en Supabase.
        
        Args:
            productos: Lista de productos (formato scraper)
            batch_size: Productos por batch
            
        Returns:
            Dict con estadísticas de la operación
        """
        if not self.client:
            return {"error": "Supabase no configurado", "uploaded": 0}
        
        stats = {"uploaded": 0, "errors": 0, "skipped": 0}
        activities = []
        
        # Convertir productos a formato activity_catalog
        print(f"\n🔄 Convirtiendo {len(productos)} productos...")
        for prod in productos:
            try:
                activity = convert_producto_to_activity(prod)
                activities.append(activity.to_supabase_dict())
            except Exception as e:
                print(f"   ⚠️ Error convirtiendo: {e}")
                stats["errors"] += 1
        
        print(f"   ✅ {len(activities)} actividades listas para subir")
        
        # Subir en batches
        print(f"\n📤 Subiendo a Supabase (batches de {batch_size})...")
        
        for i in range(0, len(activities), batch_size):
            batch = activities[i:i + batch_size]
            try:
                # Upsert: inserta o actualiza si ya existe
                result = self.client.table("activity_catalog").upsert(
                    batch,
                    on_conflict="activity_title,entity"  # Evitar duplicados
                ).execute()
                
                stats["uploaded"] += len(batch)
                print(f"   ✅ Batch {i//batch_size + 1}: {len(batch)} actividades")
                
            except Exception as e:
                print(f"   ❌ Error en batch {i//batch_size + 1}: {e}")
                stats["errors"] += len(batch)
        
        print(f"\n📊 Resumen: {stats['uploaded']} subidas, {stats['errors']} errores")
        return stats
    
    def get_activities_count(self) -> int:
        """Retorna el número de actividades en Supabase"""
        if not self.client:
            return 0
        try:
            result = self.client.table("activity_catalog").select("id", count="exact").execute()
            return result.count
        except:
            return 0
    
    def search_by_tags(self, situation_tags: List[str] = None, 
                       profile_tags: List[str] = None,
                       age_group: str = None,
                       limit: int = 10) -> List[dict]:
        """
        Busca actividades que coincidan con los tags dados.
        
        Args:
            situation_tags: ["estrés alto", "ansiedad"]
            profile_tags: ["activo", "social"]
            age_group: "adultos"
            limit: Máximo de resultados
            
        Returns:
            Lista de actividades que coinciden
        """
        if not self.client:
            return []
        
        query = self.client.table("activity_catalog").select("*").eq("is_active", True)
        
        if age_group:
            query = query.eq("age_group", age_group)
        
        if situation_tags:
            # Buscar actividades que contengan AL MENOS UNO de los tags
            query = query.overlaps("situation_tags", situation_tags)
        
        if profile_tags:
            query = query.overlaps("profile_tags", profile_tags)
        
        query = query.limit(limit)
        
        try:
            result = query.execute()
            return result.data
        except Exception as e:
            print(f"❌ Error buscando: {e}")
            return []


def load_productos_from_json(filepath: str) -> List[dict]:
    """Carga productos desde el JSON del scraper"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI para sincronizar con Supabase"""
    import argparse
    
    parser = argparse.ArgumentParser(description="🔄 Sincronizar productos con Supabase")
    parser.add_argument("--json", default="data/compensar/productos.json",
                        help="Archivo JSON con productos")
    parser.add_argument("--url", help="Supabase URL (o env SUPABASE_URL)")
    parser.add_argument("--key", help="Supabase Key (o env SUPABASE_KEY)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Solo mostrar qué se subiría, sin subir")
    parser.add_argument("--search", nargs="+",
                        help="Buscar actividades por situation_tags")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🔄 SINCRONIZACIÓN COMPENSAR → SUPABASE")
    print("=" * 70)
    
    # Si es búsqueda
    if args.search:
        sync = SupabaseSync(url=args.url, key=args.key)
        print(f"\n🔍 Buscando actividades para: {args.search}")
        results = sync.search_by_tags(situation_tags=args.search)
        
        if results:
            print(f"\n✅ {len(results)} actividades encontradas:\n")
            for act in results:
                print(f"  📌 {act['activity_title']}")
                print(f"     💰 Precio: {act['price']}")
                print(f"     🏷️ Tags: {act['situation_tags']}")
                print(f"     👤 Perfil: {act['profile_tags']}")
                print()
        else:
            print("   No se encontraron actividades")
        return
    
    # Cargar productos
    print(f"\n📂 Cargando productos de: {args.json}")
    try:
        productos = load_productos_from_json(args.json)
        print(f"   ✅ {len(productos)} productos cargados")
    except FileNotFoundError:
        print(f"   ❌ Archivo no encontrado: {args.json}")
        print("   Ejecuta primero el scraper: python src/scraper/run_playwright_scraper.py")
        return
    
    # Mostrar ejemplo de conversión
    if productos:
        print("\n📋 Ejemplo de conversión:")
        ejemplo = convert_producto_to_activity(productos[0])
        print(f"   Producto: {productos[0].get('nombre', '')[:50]}")
        print(f"   → category: {ejemplo.category}")
        print(f"   → age_group: {ejemplo.age_group}")
        print(f"   → profile_tags: {ejemplo.profile_tags}")
        print(f"   → situation_tags: {ejemplo.situation_tags}")
        print(f"   → price: {ejemplo.price}")
    
    if args.dry_run:
        print("\n⚠️ Modo DRY-RUN: No se subirá nada")
        print(f"   Se subirían {len(productos)} actividades a Supabase")
        return
    
    # Subir a Supabase
    sync = SupabaseSync(url=args.url, key=args.key)
    if sync.client:
        stats = sync.upload_productos(productos)
        print(f"\n✅ Sincronización completada")
        print(f"   Actividades en Supabase: {sync.get_activities_count()}")


if __name__ == "__main__":
    main()
