"""
Script para actualizar los productos en Supabase con los nuevos tags.

Este script:
1. Lee el catálogo actualizado con los nuevos profile_tags y situation_tags
2. Limpia la tabla actual de Compensar-Database
3. Inserta todos los productos con los nuevos tags

Profile Tags:
- Edad: joven (18-30), adulto (30-50), mayor (50+)
- Hobbies: tech, musica, deportes, arte, lectura, cocina, viajes, naturaleza, manualidades, social
- Metas: familia, amigos, bienes, carrera, salud, crecimiento_personal, estabilidad

Situation Tags (4 categorías):
- muerte_familiar: Pérdida de un ser querido
- causa_economica: Problemas financieros/laborales
- bloqueo_incapacidad: Sentirse incapaz/incompetente
- rompimiento_pareja: Ruptura amorosa
"""

import os
import json
from supabase import create_client, Client

# Configuración Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

TABLE_NAME = "Compensar-Database"


def get_supabase_client() -> Client:
    """Crear cliente Supabase"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL y SUPABASE_SERVICE_KEY deben estar configurados en las variables de entorno")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def load_catalog(file_path: str) -> list:
    """Cargar el catálogo desde archivo JSON"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('productos', [])


def clear_table(supabase: Client):
    """Limpiar toda la tabla (opcional - solo si quieres empezar desde cero)"""
    print(f"\n⚠️  ¿Deseas limpiar la tabla '{TABLE_NAME}' antes de insertar? (s/N): ", end='')
    response = input().strip().lower()
    
    if response == 's':
        print(f"\n🗑️  Eliminando todos los registros de {TABLE_NAME}...")
        # Obtener todos los IDs
        result = supabase.table(TABLE_NAME).select("id").execute()
        if result.data:
            for item in result.data:
                supabase.table(TABLE_NAME).delete().eq("id", item["id"]).execute()
            print(f"   ✅ {len(result.data)} registros eliminados")
        else:
            print("   ℹ️  La tabla ya estaba vacía")
    else:
        print("   ℹ️  No se eliminará ningún registro. Se intentará actualizar los existentes.")


def upsert_products(supabase: Client, products: list):
    """Insertar o actualizar productos en Supabase"""
    print(f"\n📦 Insertando/actualizando {len(products)} productos...")
    
    success_count = 0
    error_count = 0
    errors = []
    
    for i, product in enumerate(products, 1):
        try:
            # Preparar el producto para inserción
            product_data = {
                "nombre": product["nombre"],
                "descripcion": product.get("descripcion", ""),
                "precio_desde": product.get("precio_desde", 0),
                "subcategoria": product.get("subcategoria", ""),
                "categoria_principal": product.get("categoria_principal", ""),
                "url": product.get("url", ""),
                "profile_tags": product.get("profile_tags", []),
                "situation_tags": product.get("situation_tags", [])
            }
            
            # Upsert (insertar o actualizar si ya existe por nombre)
            result = supabase.table(TABLE_NAME).upsert(
                product_data,
                on_conflict="nombre"  # Usar nombre como clave única
            ).execute()
            
            if result.data:
                success_count += 1
                print(f"   ✅ [{i}/{len(products)}] {product['nombre'][:50]}")
            else:
                error_count += 1
                errors.append(f"   ❌ [{i}/{len(products)}] {product['nombre']}: No data returned")
                
        except Exception as e:
            error_count += 1
            error_msg = f"   ❌ [{i}/{len(products)}] {product['nombre']}: {str(e)}"
            errors.append(error_msg)
            print(error_msg)
    
    return success_count, error_count, errors


def verify_tags(supabase: Client):
    """Verificar que los tags se insertaron correctamente"""
    print("\n🔍 Verificando tags insertados...")
    
    result = supabase.table(TABLE_NAME).select("nombre, profile_tags, situation_tags").limit(5).execute()
    
    if result.data:
        print(f"\n📊 Muestra de {len(result.data)} productos:")
        for product in result.data:
            print(f"\n   📦 {product['nombre']}")
            print(f"      Profile Tags: {', '.join(product.get('profile_tags', []))}")
            print(f"      Situation Tags: {', '.join(product.get('situation_tags', []))}")
    
    # Contar productos por cada situation tag
    print("\n📊 Distribución de Situation Tags:")
    situation_tags = ["muerte_familiar", "causa_economica", "bloqueo_incapacidad", "rompimiento_pareja"]
    
    for tag in situation_tags:
        result = supabase.table(TABLE_NAME).select("id", count="exact").contains("situation_tags", [tag]).execute()
        count = result.count if hasattr(result, 'count') else len(result.data)
        print(f"   • {tag}: {count} productos")


def main():
    print("=" * 70)
    print("Actualización de Base de Datos Compensar")
    print("Nuevos Tags: Profile (edad + hobbies + metas) + Situation (4 categorías)")
    print("=" * 70)
    
    # 1. Cargar catálogo
    catalog_path = "data/compensar/catalogo_actualizado.json"
    print(f"\n📂 Cargando catálogo desde: {catalog_path}")
    
    try:
        products = load_catalog(catalog_path)
        print(f"   ✅ {len(products)} productos cargados")
    except Exception as e:
        print(f"   ❌ Error cargando catálogo: {e}")
        return
    
    # 2. Conectar a Supabase
    print(f"\n🔌 Conectando a Supabase...")
    try:
        supabase = get_supabase_client()
        print(f"   ✅ Conectado exitosamente")
    except Exception as e:
        print(f"   ❌ Error conectando a Supabase: {e}")
        print("\n💡 Asegúrate de configurar las variables de entorno:")
        print("   export SUPABASE_URL='tu-url'")
        print("   export SUPABASE_SERVICE_KEY='tu-service-key'")
        return
    
    # 3. Opcionalmente limpiar tabla
    clear_table(supabase)
    
    # 4. Insertar/actualizar productos
    success, errors_count, errors = upsert_products(supabase, products)
    
    # 5. Verificar tags
    verify_tags(supabase)
    
    # 6. Resumen final
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE ACTUALIZACIÓN")
    print("=" * 70)
    print(f"✅ Productos insertados/actualizados: {success}")
    print(f"❌ Errores: {errors_count}")
    
    if errors:
        print("\n⚠️  Errores encontrados:")
        for error in errors[:10]:  # Mostrar solo los primeros 10
            print(error)
        if len(errors) > 10:
            print(f"   ... y {len(errors) - 10} errores más")
    
    print("\n✨ Proceso completado")
    print("=" * 70)


if __name__ == "__main__":
    main()
