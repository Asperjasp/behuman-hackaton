"""
Script para actualizar los tags de productos en Supabase según las nuevas categorías.

Profile Tags (basados en características del perfil):
- Edad: joven (18-30), adulto (30-50), mayor (50+)
- Hobbies: tech, musica, deportes, arte, lectura, cocina, viajes, naturaleza
- Metas: familia, amigos, bienes, carrera, salud, crecimiento_personal

Situation Tags (4 categorías principales):
- muerte_familiar: Pérdida de un ser querido
- causa_economica: Problemas financieros/laborales/bloqueo profesional
- bloqueo_incapacidad: Sentirse incapaz/incompetente/caso perdido
- rompimiento_pareja: Ruptura amorosa
"""

import os
import json
from supabase import create_client, Client

# Configuración Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

# Nuevas definiciones de tags
PROFILE_TAGS = {
    # Por edad
    "edad": ["joven", "adulto", "mayor"],  # 18-30, 30-50, 50+
    
    # Hobbies
    "hobbies": ["tech", "musica", "deportes", "arte", "lectura", "cocina", "viajes", "naturaleza", "manualidades", "social"],
    
    # Metas
    "metas": ["familia", "amigos", "bienes", "carrera", "salud", "crecimiento_personal", "estabilidad"]
}

SITUATION_TAGS = {
    "muerte_familiar": {
        "descripcion": "Pérdida de un ser querido, duelo",
        "keywords": ["duelo", "perdida", "fallecimiento", "luto", "muerte"]
    },
    "causa_economica": {
        "descripcion": "Problemas financieros, laborales, despido, deudas",
        "keywords": ["economico", "laboral", "despido", "dinero", "deudas", "trabajo", "desempleo"]
    },
    "bloqueo_incapacidad": {
        "descripcion": "Sentirse incapaz, incompetente, sin valor, caso perdido",
        "keywords": ["incapaz", "incompetente", "perdido", "no puedo", "bloqueo", "impostor", "inutil"]
    },
    "rompimiento_pareja": {
        "descripcion": "Ruptura amorosa, divorcio, separación",
        "keywords": ["ruptura", "separacion", "divorcio", "ex", "terminar", "corazon roto"]
    }
}

# Mapeo de productos a nuevos tags
# Cada producto tiene profile_tags (edad + hobbies + metas) y situation_tags (las 4 categorías)

PRODUCT_TAG_MAPPING = {
    # === YOGA ===
    "Yoga Hatha - Nivel Básico": {
        "profile_tags": ["joven", "adulto", "mayor", "salud", "crecimiento_personal"],
        "situation_tags": ["muerte_familiar", "bloqueo_incapacidad", "rompimiento_pareja"]
    },
    "Yoga Vinyasa Flow": {
        "profile_tags": ["joven", "adulto", "deportes", "salud"],
        "situation_tags": ["bloqueo_incapacidad", "causa_economica"]
    },
    "Yoga Restaurativo": {
        "profile_tags": ["adulto", "mayor", "salud", "crecimiento_personal"],
        "situation_tags": ["muerte_familiar", "rompimiento_pareja", "bloqueo_incapacidad"]
    },
    
    # === GIMNASIO ===
    "Gimnasio - Plan Mensual": {
        "profile_tags": ["joven", "adulto", "deportes", "salud"],
        "situation_tags": ["bloqueo_incapacidad", "rompimiento_pareja", "causa_economica"]
    },
    "Gimnasio - Plan Trimestral": {
        "profile_tags": ["joven", "adulto", "deportes", "salud", "crecimiento_personal"],
        "situation_tags": ["bloqueo_incapacidad", "rompimiento_pareja"]
    },
    
    # === NATACIÓN ===
    "Natación Adultos - Principiantes": {
        "profile_tags": ["joven", "adulto", "mayor", "deportes", "salud"],
        "situation_tags": ["bloqueo_incapacidad", "muerte_familiar"]
    },
    "Natación Adultos - Intermedio": {
        "profile_tags": ["joven", "adulto", "deportes", "salud"],
        "situation_tags": ["bloqueo_incapacidad", "causa_economica"]
    },
    "Buceo PADI Open Water": {
        "profile_tags": ["joven", "adulto", "viajes", "naturaleza", "crecimiento_personal"],
        "situation_tags": ["rompimiento_pareja", "bloqueo_incapacidad"]
    },
    
    # === TENIS / SQUASH ===
    "Tenis - Clases Grupales": {
        "profile_tags": ["joven", "adulto", "deportes", "social", "amigos"],
        "situation_tags": ["rompimiento_pareja", "bloqueo_incapacidad"]
    },
    "Squash - Nivel Básico": {
        "profile_tags": ["joven", "adulto", "deportes", "salud"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad"]
    },
    
    # === MÚSICA ===
    "Guitarra Acústica - Principiantes": {
        "profile_tags": ["joven", "adulto", "mayor", "musica", "crecimiento_personal"],
        "situation_tags": ["muerte_familiar", "rompimiento_pareja", "bloqueo_incapacidad"]
    },
    "Guitarra Eléctrica": {
        "profile_tags": ["joven", "adulto", "musica", "crecimiento_personal"],
        "situation_tags": ["rompimiento_pareja", "bloqueo_incapacidad"]
    },
    "Piano Clásico": {
        "profile_tags": ["joven", "adulto", "mayor", "musica", "crecimiento_personal"],
        "situation_tags": ["muerte_familiar", "bloqueo_incapacidad"]
    },
    "Piano Moderno": {
        "profile_tags": ["joven", "adulto", "musica", "crecimiento_personal"],
        "situation_tags": ["bloqueo_incapacidad", "rompimiento_pareja"]
    },
    "Violín - Nivel Básico": {
        "profile_tags": ["joven", "adulto", "mayor", "musica", "crecimiento_personal"],
        "situation_tags": ["muerte_familiar", "bloqueo_incapacidad"]
    },
    "Canto - Técnica Vocal": {
        "profile_tags": ["joven", "adulto", "musica", "crecimiento_personal", "social"],
        "situation_tags": ["bloqueo_incapacidad", "rompimiento_pareja"]
    },
    "Coro Compensar": {
        "profile_tags": ["joven", "adulto", "mayor", "musica", "social", "amigos"],
        "situation_tags": ["muerte_familiar", "rompimiento_pareja", "bloqueo_incapacidad"]
    },
    "Batería y Percusión": {
        "profile_tags": ["joven", "adulto", "musica", "deportes"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad", "rompimiento_pareja"]
    },
    "Producción Musical Digital": {
        "profile_tags": ["joven", "tech", "musica", "carrera"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad"]
    },
    "Ukulele para Principiantes": {
        "profile_tags": ["joven", "adulto", "mayor", "musica", "crecimiento_personal"],
        "situation_tags": ["rompimiento_pareja", "bloqueo_incapacidad"]
    },
    
    # === ARTE ===
    "Pintura al Óleo": {
        "profile_tags": ["adulto", "mayor", "arte", "crecimiento_personal"],
        "situation_tags": ["muerte_familiar", "bloqueo_incapacidad"]
    },
    "Acuarela Creativa": {
        "profile_tags": ["joven", "adulto", "mayor", "arte", "crecimiento_personal"],
        "situation_tags": ["muerte_familiar", "rompimiento_pareja", "bloqueo_incapacidad"]
    },
    "Dibujo Artístico": {
        "profile_tags": ["joven", "adulto", "arte", "crecimiento_personal"],
        "situation_tags": ["bloqueo_incapacidad", "rompimiento_pareja"]
    },
    "Escultura en Arcilla": {
        "profile_tags": ["adulto", "mayor", "arte", "manualidades"],
        "situation_tags": ["muerte_familiar", "bloqueo_incapacidad"]
    },
    "Fotografía Digital": {
        "profile_tags": ["joven", "adulto", "tech", "arte", "carrera"],
        "situation_tags": ["bloqueo_incapacidad", "causa_economica"]
    },
    "Fotografía con Smartphone": {
        "profile_tags": ["joven", "adulto", "tech", "arte"],
        "situation_tags": ["bloqueo_incapacidad"]
    },
    "Cerámica Artesanal": {
        "profile_tags": ["adulto", "mayor", "arte", "manualidades"],
        "situation_tags": ["muerte_familiar", "bloqueo_incapacidad"]
    },
    "Ilustración Digital": {
        "profile_tags": ["joven", "adulto", "tech", "arte", "carrera"],
        "situation_tags": ["bloqueo_incapacidad", "causa_economica"]
    },
    "Vitral y Vidrio": {
        "profile_tags": ["adulto", "mayor", "arte", "manualidades"],
        "situation_tags": ["muerte_familiar", "bloqueo_incapacidad"]
    },
    "Joyería Artesanal": {
        "profile_tags": ["joven", "adulto", "arte", "manualidades", "bienes"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad"]
    },
    
    # === SPA ===
    "Masaje Relajante - Sesión": {
        "profile_tags": ["joven", "adulto", "mayor", "salud"],
        "situation_tags": ["muerte_familiar", "causa_economica", "bloqueo_incapacidad", "rompimiento_pareja"]
    },
    "Masaje Descontracturante": {
        "profile_tags": ["adulto", "mayor", "salud"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad"]
    },
    "Día de Spa Completo": {
        "profile_tags": ["joven", "adulto", "mayor", "salud", "crecimiento_personal"],
        "situation_tags": ["muerte_familiar", "rompimiento_pareja", "bloqueo_incapacidad"]
    },
    "Circuito de Aguas": {
        "profile_tags": ["joven", "adulto", "mayor", "salud"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad"]
    },
    "Tratamiento Facial Premium": {
        "profile_tags": ["adulto", "mayor", "salud"],
        "situation_tags": ["rompimiento_pareja", "bloqueo_incapacidad"]
    },
    "Aromaterapia y Relajación": {
        "profile_tags": ["joven", "adulto", "mayor", "salud", "crecimiento_personal"],
        "situation_tags": ["muerte_familiar", "rompimiento_pareja", "bloqueo_incapacidad"]
    },
    "Reflexología Podal": {
        "profile_tags": ["adulto", "mayor", "salud"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad"]
    },
    "Masaje con Piedras Calientes": {
        "profile_tags": ["adulto", "mayor", "salud"],
        "situation_tags": ["muerte_familiar", "causa_economica", "bloqueo_incapacidad"]
    },
    
    # === TURISMO ===
    "Tour Villa de Leyva - Fin de Semana": {
        "profile_tags": ["joven", "adulto", "mayor", "viajes", "familia", "amigos"],
        "situation_tags": ["muerte_familiar", "rompimiento_pareja", "bloqueo_incapacidad"]
    },
    "Excursión Laguna de Guatavita": {
        "profile_tags": ["joven", "adulto", "viajes", "naturaleza"],
        "situation_tags": ["rompimiento_pareja", "bloqueo_incapacidad"]
    },
    "Tour Eje Cafetero - 3 Días": {
        "profile_tags": ["joven", "adulto", "mayor", "viajes", "familia"],
        "situation_tags": ["muerte_familiar", "rompimiento_pareja", "causa_economica"]
    },
    "Cartagena - Paquete 4 Días": {
        "profile_tags": ["joven", "adulto", "viajes", "amigos", "familia"],
        "situation_tags": ["rompimiento_pareja", "causa_economica"]
    },
    "San Andrés - Todo Incluido": {
        "profile_tags": ["joven", "adulto", "viajes", "amigos"],
        "situation_tags": ["rompimiento_pareja", "bloqueo_incapacidad"]
    },
    "Amazonia Colombiana - Expedición": {
        "profile_tags": ["joven", "adulto", "viajes", "naturaleza", "crecimiento_personal"],
        "situation_tags": ["rompimiento_pareja", "bloqueo_incapacidad"]
    },
    "Nevado del Ruiz - Trekking": {
        "profile_tags": ["joven", "adulto", "deportes", "viajes", "naturaleza"],
        "situation_tags": ["rompimiento_pareja", "bloqueo_incapacidad"]
    },
    "Desierto de la Tatacoa": {
        "profile_tags": ["joven", "adulto", "viajes", "naturaleza", "crecimiento_personal"],
        "situation_tags": ["muerte_familiar", "rompimiento_pareja", "bloqueo_incapacidad"]
    },
    "Santander Extremo - Aventura": {
        "profile_tags": ["joven", "deportes", "viajes"],
        "situation_tags": ["rompimiento_pareja", "bloqueo_incapacidad"]
    },
    "Providencia - Paraíso Secreto": {
        "profile_tags": ["joven", "adulto", "viajes", "naturaleza"],
        "situation_tags": ["rompimiento_pareja", "bloqueo_incapacidad", "muerte_familiar"]
    },
    
    # === COCINA ===
    "Cocina Italiana Básica": {
        "profile_tags": ["joven", "adulto", "mayor", "cocina", "social"],
        "situation_tags": ["rompimiento_pareja", "bloqueo_incapacidad"]
    },
    "Cocina Colombiana Tradicional": {
        "profile_tags": ["joven", "adulto", "mayor", "cocina", "familia"],
        "situation_tags": ["muerte_familiar", "causa_economica", "bloqueo_incapacidad"]
    },
    "Sushi y Cocina Japonesa": {
        "profile_tags": ["joven", "adulto", "cocina", "crecimiento_personal"],
        "situation_tags": ["bloqueo_incapacidad", "rompimiento_pareja"]
    },
    "Panadería Artesanal": {
        "profile_tags": ["joven", "adulto", "mayor", "cocina", "bienes"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad"]
    },
    "Pastelería Profesional": {
        "profile_tags": ["joven", "adulto", "cocina", "carrera", "bienes"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad"]
    },
    "Cocina Vegana y Saludable": {
        "profile_tags": ["joven", "adulto", "cocina", "salud"],
        "situation_tags": ["bloqueo_incapacidad", "rompimiento_pareja"]
    },
    "Cocina Thai y Asiática": {
        "profile_tags": ["joven", "adulto", "cocina", "crecimiento_personal"],
        "situation_tags": ["bloqueo_incapacidad", "rompimiento_pareja"]
    },
    "Chocolatería Fina": {
        "profile_tags": ["joven", "adulto", "cocina", "bienes"],
        "situation_tags": ["rompimiento_pareja", "bloqueo_incapacidad"]
    },
    "Cocteles y Mixología": {
        "profile_tags": ["joven", "adulto", "cocina", "social", "amigos"],
        "situation_tags": ["rompimiento_pareja", "bloqueo_incapacidad"]
    },
    "Café de Origen - Barismo": {
        "profile_tags": ["joven", "adulto", "cocina", "carrera", "bienes"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad"]
    },
    
    # === DANZA ===
    "Salsa y Ritmos Latinos": {
        "profile_tags": ["joven", "adulto", "deportes", "social", "amigos"],
        "situation_tags": ["rompimiento_pareja", "bloqueo_incapacidad"]
    },
    "Bachata Sensual": {
        "profile_tags": ["joven", "adulto", "deportes", "social"],
        "situation_tags": ["rompimiento_pareja", "bloqueo_incapacidad"]
    },
    "Ballet Adultos - Principiantes": {
        "profile_tags": ["joven", "adulto", "arte", "deportes", "crecimiento_personal"],
        "situation_tags": ["bloqueo_incapacidad", "rompimiento_pareja"]
    },
    "Danza Contemporánea": {
        "profile_tags": ["joven", "adulto", "arte", "crecimiento_personal"],
        "situation_tags": ["muerte_familiar", "bloqueo_incapacidad", "rompimiento_pareja"]
    },
    "Hip Hop y Urbano": {
        "profile_tags": ["joven", "deportes", "social"],
        "situation_tags": ["bloqueo_incapacidad", "rompimiento_pareja"]
    },
    "Tango Argentino": {
        "profile_tags": ["adulto", "mayor", "arte", "social"],
        "situation_tags": ["muerte_familiar", "rompimiento_pareja"]
    },
    "Flamenco": {
        "profile_tags": ["adulto", "mayor", "arte", "crecimiento_personal"],
        "situation_tags": ["muerte_familiar", "rompimiento_pareja", "bloqueo_incapacidad"]
    },
    "Danza Árabe": {
        "profile_tags": ["joven", "adulto", "arte", "crecimiento_personal"],
        "situation_tags": ["rompimiento_pareja", "bloqueo_incapacidad"]
    },
    "Zumba Fitness": {
        "profile_tags": ["joven", "adulto", "deportes", "social", "salud"],
        "situation_tags": ["bloqueo_incapacidad", "rompimiento_pareja", "causa_economica"]
    },
    "Danzas Folclóricas Colombianas": {
        "profile_tags": ["joven", "adulto", "mayor", "arte", "social"],
        "situation_tags": ["muerte_familiar", "rompimiento_pareja", "bloqueo_incapacidad"]
    },
    
    # === IDIOMAS ===
    "Inglés Conversacional": {
        "profile_tags": ["joven", "adulto", "carrera", "crecimiento_personal"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad"]
    },
    "Inglés Intensivo": {
        "profile_tags": ["joven", "adulto", "carrera", "crecimiento_personal"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad"]
    },
    "Francés Básico": {
        "profile_tags": ["joven", "adulto", "carrera", "viajes"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad"]
    },
    "Portugués Brasileño": {
        "profile_tags": ["joven", "adulto", "carrera", "viajes"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad"]
    },
    "Italiano para Viajeros": {
        "profile_tags": ["joven", "adulto", "viajes", "crecimiento_personal"],
        "situation_tags": ["rompimiento_pareja", "bloqueo_incapacidad"]
    },
    "Alemán Nivel 1": {
        "profile_tags": ["joven", "adulto", "carrera", "crecimiento_personal"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad"]
    },
    "Mandarín Básico": {
        "profile_tags": ["joven", "adulto", "carrera", "crecimiento_personal"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad"]
    },
    "Lengua de Señas Colombiana": {
        "profile_tags": ["joven", "adulto", "mayor", "crecimiento_personal", "social"],
        "situation_tags": ["bloqueo_incapacidad", "familia"]
    },
    
    # === TEATRO ===
    "Teatro - Iniciación": {
        "profile_tags": ["joven", "adulto", "arte", "social", "crecimiento_personal"],
        "situation_tags": ["bloqueo_incapacidad", "rompimiento_pareja"]
    },
    "Improvisación Teatral": {
        "profile_tags": ["joven", "adulto", "arte", "social"],
        "situation_tags": ["bloqueo_incapacidad", "causa_economica"]
    },
    "Teatro Musical": {
        "profile_tags": ["joven", "adulto", "arte", "musica", "social"],
        "situation_tags": ["bloqueo_incapacidad", "rompimiento_pareja"]
    },
    "Expresión Corporal": {
        "profile_tags": ["joven", "adulto", "arte", "crecimiento_personal"],
        "situation_tags": ["muerte_familiar", "bloqueo_incapacidad", "rompimiento_pareja"]
    },
    "Stand Up Comedy": {
        "profile_tags": ["joven", "adulto", "arte", "social"],
        "situation_tags": ["rompimiento_pareja", "bloqueo_incapacidad"]
    },
    
    # === MEDITACIÓN ===
    "Meditación Mindfulness": {
        "profile_tags": ["joven", "adulto", "mayor", "salud", "crecimiento_personal"],
        "situation_tags": ["muerte_familiar", "causa_economica", "bloqueo_incapacidad", "rompimiento_pareja"]
    },
    "Técnicas de Respiración": {
        "profile_tags": ["joven", "adulto", "mayor", "salud", "crecimiento_personal"],
        "situation_tags": ["muerte_familiar", "causa_economica", "bloqueo_incapacidad"]
    },
    "Retiro de Meditación - Fin de Semana": {
        "profile_tags": ["adulto", "mayor", "salud", "crecimiento_personal", "naturaleza"],
        "situation_tags": ["muerte_familiar", "rompimiento_pareja", "bloqueo_incapacidad"]
    },
    
    # === TECNOLOGÍA ===
    "Excel Avanzado": {
        "profile_tags": ["joven", "adulto", "tech", "carrera"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad"]
    },
    "Programación Python Básico": {
        "profile_tags": ["joven", "adulto", "tech", "carrera"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad"]
    },
    "Marketing Digital": {
        "profile_tags": ["joven", "adulto", "tech", "carrera", "bienes"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad"]
    },
    "Diseño Gráfico - Canva y Photoshop": {
        "profile_tags": ["joven", "adulto", "tech", "arte", "carrera"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad"]
    },
    "Community Manager": {
        "profile_tags": ["joven", "adulto", "tech", "carrera", "social"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad"]
    },
    "Desarrollo Web Frontend": {
        "profile_tags": ["joven", "adulto", "tech", "carrera"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad"]
    },
    "Inteligencia Artificial para Todos": {
        "profile_tags": ["joven", "adulto", "tech", "carrera", "crecimiento_personal"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad"]
    },
    "Emprendimiento Digital": {
        "profile_tags": ["joven", "adulto", "tech", "carrera", "bienes"],
        "situation_tags": ["causa_economica", "bloqueo_incapacidad"]
    }
}

# Default tags para productos no mapeados
DEFAULT_PROFILE_TAGS = ["adulto", "crecimiento_personal"]
DEFAULT_SITUATION_TAGS = ["bloqueo_incapacidad"]


def get_supabase_client() -> Client:
    """Crear cliente Supabase"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL y SUPABASE_SERVICE_KEY deben estar configurados")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def update_product_tags(supabase: Client, product_id: int, nombre: str) -> dict:
    """Actualizar tags de un producto"""
    # Buscar en el mapeo
    if nombre in PRODUCT_TAG_MAPPING:
        tags = PRODUCT_TAG_MAPPING[nombre]
        profile_tags = tags["profile_tags"]
        situation_tags = tags["situation_tags"]
    else:
        # Usar defaults
        print(f"  ⚠️  Producto no mapeado: {nombre}, usando defaults")
        profile_tags = DEFAULT_PROFILE_TAGS
        situation_tags = DEFAULT_SITUATION_TAGS
    
    # Actualizar en Supabase
    result = supabase.table("Compensar-Database").update({
        "profile_tags": profile_tags,
        "situation_tags": situation_tags
    }).eq("id", product_id).execute()
    
    return {
        "id": product_id,
        "nombre": nombre,
        "profile_tags": profile_tags,
        "situation_tags": situation_tags,
        "updated": len(result.data) > 0
    }


def main():
    print("=" * 60)
    print("Actualizando tags de productos en Supabase")
    print("=" * 60)
    
    # Conectar
    supabase = get_supabase_client()
    
    # Obtener todos los productos
    print("\n📦 Obteniendo productos...")
    result = supabase.table("Compensar-Database").select("id, nombre").execute()
    products = result.data
    print(f"   Encontrados: {len(products)} productos")
    
    # Actualizar cada producto
    print("\n🔄 Actualizando tags...")
    updated = 0
    errors = 0
    
    for product in products:
        try:
            result = update_product_tags(supabase, product["id"], product["nombre"])
            if result["updated"]:
                updated += 1
                print(f"   ✅ {product['nombre'][:40]}")
            else:
                errors += 1
                print(f"   ❌ {product['nombre'][:40]}")
        except Exception as e:
            errors += 1
            print(f"   ❌ Error en {product['nombre']}: {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ Actualizados: {updated}")
    print(f"❌ Errores: {errors}")
    print("=" * 60)
    
    # Mostrar resumen de tags
    print("\n📊 Resumen de Situation Tags:")
    for tag, info in SITUATION_TAGS.items():
        print(f"   • {tag}: {info['descripcion']}")
    
    print("\n📊 Profile Tags disponibles:")
    for category, tags in PROFILE_TAGS.items():
        print(f"   • {category}: {', '.join(tags)}")


if __name__ == "__main__":
    main()
