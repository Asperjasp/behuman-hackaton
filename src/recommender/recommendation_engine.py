"""
BeHuman - Sistema de Recomendación Empático
============================================

CÓMO FUNCIONA:
═══════════════

1. ENTRADA: El sistema recibe información del usuario
   - Perfil: nombre, edad, género, hobbies, metas
   - Situación: tipo de conflicto (duelo, ruptura, ansiedad, etc.)
   - Contexto: detalles específicos de lo que enfrenta

2. PROCESAMIENTO:
   
   ┌─────────────────────────────────────────────────────────────────┐
   │  KNOWLEDGE BASE (Base de Conocimiento Psicológico)             │
   │  ─────────────────────────────────────────────────────────────  │
   │  Mapea cada SITUACIÓN → TIPOS DE ACTIVIDAD que ayudan          │
   │                                                                 │
   │  Ejemplo:                                                       │
   │  "perdida_familiar" → [naturaleza, baja_estimulacion, social]   │
   │  "ruptura_amorosa"  → [ejercicio, social, expresion_artistica]  │
   │  "ansiedad"         → [mindfulness, agua, ejercicio_suave]      │
   └─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────────────┐
   │  PRODUCT TAGGER (Etiquetador de Productos)                     │
   │  ─────────────────────────────────────────────────────────────  │
   │  Analiza cada producto de Compensar y le asigna tags:          │
   │                                                                 │
   │  "Pasadía Lagosol" → [naturaleza, agua, baja_estimulacion]      │
   │  "Yoga grupal"     → [mindfulness, social, ejercicio_suave]     │
   │  "Taller de arte"  → [expresion_artistica, social]              │
   └─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────────────┐
   │  RECOMMENDATION ENGINE (Motor de Recomendación)                │
   │  ─────────────────────────────────────────────────────────────  │
   │  Scoring: Qué tan bien matchea cada producto con la situación  │
   │                                                                 │
   │  +30 pts: Tipo de actividad beneficioso para la situación      │
   │  +20 pts: Apropiado para la edad del usuario                   │
   │  +15 pts: Keywords relevantes en el nombre                     │
   │  +10 pts: Conecta con hobbies del usuario                      │
   │   +5 pts: En promoción                                         │
   └─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
3. SALIDA: Mensaje empático + Top recomendaciones

   ┌─────────────────────────────────────────────────────────────────┐
   │  MENSAJE EMPÁTICO (≤500 caracteres)                            │
   │  ─────────────────────────────────────────────────────────────  │
   │  Estructura:                                                    │
   │  1. [Nombre], sé que te toca [confrontar situación]             │
   │  2. [Frase de calma realista - no minimizar]                    │
   │  3. Por eso, [conectando hobby] te recomendamos [actividad]     │
   │  4. [Beneficio de la actividad]                                 │
   │  5. Un paso hacia [meta del usuario]                            │
   └─────────────────────────────────────────────────────────────────┘

EJEMPLO COMPLETO:
═════════════════

Input:
  - Usuario: Ricardo, 59 años, hobbies=[lectura, jardinería, caminar]
  - Situación: perdida_familiar/padres
  - Meta: fortalecer relaciones personales

Output:
  "Ricardo, sé que hoy te toca enfrentarte a la pérdida de tus padres. 
   Este dolor es parte de haber amado profundamente. Por eso, aprovechando 
   tu gusto por caminar, te recomendamos Caminata ecológica — la naturaleza 
   tiene un efecto restaurador comprobado. Un paso hacia fortalecer 
   relaciones personales."

"""

import json
import os
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path


# =============================================================================
# MODELOS DE DATOS
# =============================================================================

@dataclass
class UserProfile:
    """Perfil del usuario."""
    user_id: str
    name: str
    age: int
    gender: str  # masculino, femenino, no-binario
    hobbies: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)


@dataclass
class Situation:
    """Situación/conflicto que enfrenta el usuario."""
    type: str       # perdida_familiar, ruptura_amorosa, ansiedad, soledad, estres_laboral, duelo
    subtype: str    # padres, pareja, laboral, reciente, prolongado, etc.
    context: str    # Descripción libre del contexto


@dataclass
class Product:
    """Producto de Tienda Compensar."""
    id: str
    nombre: str
    categoria_principal: str
    subcategoria: str
    precio_desde: float
    url: str
    imagen_url: str
    promocion: bool = False
    descripcion: Optional[str] = None
    # Tags para matching
    activity_types: List[str] = field(default_factory=list)
    situation_tags: List[str] = field(default_factory=list)


@dataclass
class Recommendation:
    """Una recomendación con score y razones."""
    product: Product
    score: float
    reasons: List[str]


# =============================================================================
# KNOWLEDGE BASE: QUÉ TIPO DE ACTIVIDAD AYUDA EN CADA SITUACIÓN
# =============================================================================

class SituationKnowledgeBase:
    """
    Base de conocimiento psicológico.
    Mapea cada tipo de situación a los tipos de actividad que son beneficiosos.
    """
    
    SITUATION_CONFIG = {
        "perdida_familiar": {
            "beneficial": ["baja_estimulacion", "naturaleza", "social_suave", "mindfulness", "agua"],
            "avoid": ["alta_estimulacion", "competitivo", "fiesta"],
            "keywords": ["descanso", "tranquilo", "paz", "naturaleza", "spa", "estadía", "caminata"],
            "description": "La pérdida requiere espacios de calma para procesar el duelo"
        },
        "ruptura_amorosa": {
            "beneficial": ["ejercicio", "social", "expresion_artistica", "naturaleza", "agua"],
            "avoid": ["romantico", "parejas"],
            "keywords": ["deporte", "grupo", "social", "arte", "natación", "gimnasio", "taller"],
            "description": "El movimiento físico y las conexiones sociales ayudan a procesar"
        },
        "ansiedad": {
            "beneficial": ["mindfulness", "ejercicio_suave", "naturaleza", "agua", "baja_estimulacion"],
            "avoid": ["alta_estimulacion", "multitudes", "competitivo"],
            "keywords": ["yoga", "meditación", "natación", "spa", "relajación", "tranquilo"],
            "description": "Actividades que calman el sistema nervioso son clave"
        },
        "soledad": {
            "beneficial": ["social", "grupal", "club", "voluntariado"],
            "avoid": ["individual", "solitario"],
            "keywords": ["grupo", "club", "taller", "clase", "social", "comunidad"],
            "description": "Construir conexiones a través de intereses compartidos"
        },
        "estres_laboral": {
            "beneficial": ["desconexion", "naturaleza", "ejercicio", "spa", "agua"],
            "avoid": ["alta_concentracion", "competitivo"],
            "keywords": ["escapada", "descanso", "spa", "naturaleza", "deporte", "vacaciones", "parque"],
            "description": "Desconexión activa del entorno laboral"
        },
        "duelo": {
            "beneficial": ["baja_estimulacion", "naturaleza", "expresion_artistica", "social_suave"],
            "avoid": ["alta_estimulacion", "fiestas"],
            "keywords": ["tranquilo", "naturaleza", "arte", "caminata", "grupo de apoyo"],
            "description": "Espacio para procesar y honrar la pérdida"
        }
    }
    
    @classmethod
    def get_config(cls, situation_type: str) -> Dict:
        """Obtiene la configuración para una situación."""
        return cls.SITUATION_CONFIG.get(situation_type, {
            "beneficial": [],
            "avoid": [],
            "keywords": [],
            "description": ""
        })


# =============================================================================
# PRODUCT TAGGER: ASIGNA TAGS A PRODUCTOS BASADO EN SU NOMBRE/CATEGORÍA
# =============================================================================

class ProductTagger:
    """
    Analiza productos de Compensar y les asigna tags de tipo de actividad.
    Esto permite hacer matching con las situaciones.
    """
    
    # Keywords que indican tipo de actividad
    ACTIVITY_KEYWORDS = {
        "naturaleza": ["ecológic", "natural", "caminata", "senderismo", "lagosol", "parque", "jardín"],
        "agua": ["acuático", "piscina", "natación", "spa", "agua", "lagosol"],
        "ejercicio": ["deporte", "gimnasio", "natación", "fitness", "ejercicio"],
        "social": ["grupo", "club", "taller", "clase", "comunidad"],
        "mindfulness": ["yoga", "meditación", "bienestar", "relajación", "mindfulness"],
        "baja_estimulacion": ["descanso", "tranquilo", "estadía", "spa", "relax", "pasadía"],
        "expresion_artistica": ["arte", "pintura", "música", "teatro", "taller creativo", "manualidades"],
        "turismo": ["pasadía", "entrada", "tour", "viaje", "escapada"],
    }
    
    def tag_product(self, product: Product) -> Product:
        """Asigna tags de actividad a un producto."""
        text = f"{product.nombre} {product.categoria_principal} {product.subcategoria} {product.descripcion or ''}".lower()
        
        activity_types = []
        for activity_type, keywords in self.ACTIVITY_KEYWORDS.items():
            if any(kw.lower() in text for kw in keywords):
                activity_types.append(activity_type)
        
        product.activity_types = activity_types if activity_types else ["general"]
        
        # Inferir qué situaciones se benefician
        product.situation_tags = self._infer_situations(activity_types)
        
        return product
    
    def _infer_situations(self, activity_types: List[str]) -> List[str]:
        """Infiere qué situaciones se benefician de estos tipos de actividad."""
        situations = []
        for sit_type, config in SituationKnowledgeBase.SITUATION_CONFIG.items():
            if any(at in config["beneficial"] for at in activity_types):
                situations.append(sit_type)
        return situations


# =============================================================================
# RECOMMENDATION ENGINE: RANKEA PRODUCTOS SEGÚN PERFIL + SITUACIÓN
# =============================================================================

class RecommendationEngine:
    """
    Motor de recomendación que:
    1. Carga productos de Compensar
    2. Los tagea con tipos de actividad
    3. Los rankea según qué tan bien matchean con la situación del usuario
    """
    
    def __init__(self, products_path: str = "data/compensar/productos.json"):
        self.products_path = products_path
        self.tagger = ProductTagger()
        self.products: List[Product] = []
        self._load_products()
    
    def _load_products(self):
        """Carga y tagea productos desde JSON."""
        if not os.path.exists(self.products_path):
            print(f"⚠️ No se encontró {self.products_path}")
            return
        
        with open(self.products_path, 'r', encoding='utf-8') as f:
            raw_products = json.load(f)
        
        seen_ids = set()
        for raw in raw_products:
            if raw.get('id') in seen_ids:
                continue
            seen_ids.add(raw.get('id'))
            
            precio = raw.get('precio', {})
            product = Product(
                id=raw.get('id', ''),
                nombre=raw.get('nombre', ''),
                categoria_principal=raw.get('categoria_principal', ''),
                subcategoria=raw.get('subcategoria', ''),
                precio_desde=precio.get('valor_numerico', 0) if isinstance(precio, dict) else 0,
                url=raw.get('url', ''),
                imagen_url=raw.get('imagen_url', ''),
                promocion=raw.get('promocion', False),
                descripcion=raw.get('descripcion')
            )
            product = self.tagger.tag_product(product)
            self.products.append(product)
        
        print(f"✅ Cargados {len(self.products)} productos de Compensar")
    
    def recommend(
        self,
        profile: UserProfile,
        situation: Situation,
        top_n: int = 3
    ) -> List[Recommendation]:
        """
        Genera recomendaciones rankeadas.
        
        Scoring:
        - Match tipo actividad con situación: +30 pts
        - Match categoría con edad: +20 pts
        - Keywords situación en nombre: +15 pts
        - Promoción: +5 pts
        - Match con hobbies: +10 pts
        """
        if not self.products:
            return []
        
        config = SituationKnowledgeBase.get_config(situation.type)
        beneficial = config["beneficial"]
        avoid = config["avoid"]
        keywords = config["keywords"]
        
        recommendations = []
        
        for product in self.products:
            score = 0.0
            reasons = []
            
            # Match tipo de actividad
            matching_types = [at for at in product.activity_types if at in beneficial]
            if matching_types:
                score += 30 * len(matching_types)
                reasons.append(f"Actividad de tipo '{matching_types[0]}' ayuda en tu situación")
            
            # Penalizar tipos a evitar
            if any(at in avoid for at in product.activity_types):
                score -= 50
            
            # Keywords en nombre
            nombre_lower = product.nombre.lower()
            matching_kw = [kw for kw in keywords if kw.lower() in nombre_lower]
            if matching_kw:
                score += 15 * len(matching_kw)
                reasons.append(f"Incluye: {', '.join(matching_kw[:2])}")
            
            # Promoción
            if product.promocion:
                score += 5
                reasons.append("En promoción")
            
            # Match con hobbies
            for hobby in profile.hobbies:
                hobby_lower = hobby.lower()
                if hobby_lower in nombre_lower or hobby_lower in product.subcategoria.lower():
                    score += 10
                    reasons.append(f"Conecta con tu interés en {hobby}")
            
            if score > 0:
                recommendations.append(Recommendation(product, score, reasons))
        
        recommendations.sort(key=lambda r: r.score, reverse=True)
        return recommendations[:top_n]


# =============================================================================
# EMPATHIC MESSAGE: GENERA EL MENSAJE DE ≤500 CARACTERES
# =============================================================================

class EmpathicMessageGenerator:
    """
    Genera el mensaje empático que acompaña las recomendaciones.
    
    Estructura:
    1. Confrontación empática: "[Nombre], sé que te toca [situación]"
    2. Calma realista: "[Frase que valida sin minimizar]"
    3. Conexión hobby→actividad: "Por eso, [usando hobby], te recomendamos [actividad]"
    4. Beneficio: "— [por qué ayuda]"
    5. Meta: "Un paso hacia [objetivo del usuario]"
    """
    
    # Cómo confrontar cada situación
    CONFRONTATION = {
        "perdida_familiar": {
            "padres": "enfrentarte a la pérdida de tus padres",
            "pareja": "atravesar la pérdida de tu compañero/a de vida",
            "hijo": "sobrellevar la pérdida más difícil que existe",
            "hermano": "procesar la partida de tu hermano/a",
            "general": "enfrentar la partida de alguien que amabas"
        },
        "ruptura_amorosa": {
            "reciente": "procesar el fin de una relación importante",
            "larga": "cerrar un capítulo significativo de tu vida",
            "general": "sanar después de una ruptura"
        },
        "ansiedad": {
            "laboral": "manejar la presión que el trabajo pone sobre ti",
            "social": "navegar el peso de las interacciones sociales",
            "general": "lidiar con pensamientos que no te dan tregua"
        },
        "soledad": {
            "mudanza": "construir conexiones en un lugar nuevo",
            "aislamiento": "romper el ciclo de aislamiento",
            "general": "encontrar tu lugar entre otros"
        },
        "estres_laboral": {
            "burnout": "recuperarte del agotamiento profesional",
            "presion": "sostener el peso de múltiples responsabilidades",
            "general": "encontrar equilibrio entre trabajo y vida"
        },
        "duelo": {
            "reciente": "atravesar los primeros momentos del duelo",
            "prolongado": "continuar tu camino mientras honras la memoria",
            "general": "procesar una pérdida profunda"
        }
    }
    
    # Frases de calma realista
    CALMING = {
        "perdida_familiar": [
            "Este dolor es parte de haber amado profundamente.",
            "No hay tiempo correcto para sanar, solo el tuyo.",
            "Cada día que enfrentas es un acto de valentía."
        ],
        "ruptura_amorosa": [
            "Lo que sientes ahora no es permanente.",
            "El vacío actual dejará espacio para algo nuevo.",
            "Mereces tiempo para reconstruirte."
        ],
        "ansiedad": [
            "La calma es una habilidad que se entrena.",
            "Tu mente trabaja de más tratando de protegerte.",
            "Pequeños momentos de paz se acumulan."
        ],
        "soledad": [
            "Buscar conexión es señal de fortaleza.",
            "Las mejores amistades empiezan con un primer paso.",
            "Tu presencia tiene valor aunque no lo sientas."
        ],
        "estres_laboral": [
            "Tu valor no se mide en horas trabajadas.",
            "Descansar es parte del trabajo bien hecho.",
            "Nadie funciona bien con el tanque vacío."
        ],
        "duelo": [
            "El duelo no es algo que superar, sino integrar.",
            "Honrar lo que perdiste también es vivir.",
            "No tienes que estar bien, solo tienes que seguir."
        ]
    }
    
    # Beneficios por tipo de actividad
    ACTIVITY_BENEFITS = {
        "naturaleza": "la naturaleza tiene un efecto restaurador comprobado",
        "agua": "el agua ayuda a liberar tensiones acumuladas",
        "mindfulness": "calmar la mente es el primer paso hacia la paz interior",
        "ejercicio": "el movimiento físico libera tensión y mejora el ánimo",
        "social": "conectar con otros nos recuerda que no estamos solos",
        "baja_estimulacion": "a veces el mejor paso es simplemente pausar",
        "expresion_artistica": "expresar lo que las palabras no alcanzan",
        "turismo": "cambiar de ambiente ayuda a ganar perspectiva"
    }
    
    def generate(
        self,
        profile: UserProfile,
        situation: Situation,
        recommendations: List[Recommendation]
    ) -> str:
        """Genera el mensaje empático de ≤500 caracteres."""
        
        if not recommendations:
            return f"{profile.name}, estamos buscando las mejores opciones para ti."
        
        # 1. Confrontación
        sit_phrases = self.CONFRONTATION.get(situation.type, {})
        confrontation = sit_phrases.get(situation.subtype, sit_phrases.get("general", "enfrentar este momento"))
        
        # 2. Calma
        calm_options = self.CALMING.get(situation.type, ["Lo que sientes es válido."])
        calming = random.choice(calm_options)
        
        # 3. Conexión hobby → actividad
        top_rec = recommendations[0]
        hobby_phrase = self._connect_hobby(profile.hobbies, top_rec.product)
        
        # 4. Beneficio
        benefit = self._get_benefit(top_rec.product.activity_types)
        
        # Construir mensaje
        message = f"{profile.name}, sé que hoy te toca {confrontation}. {calming} Por eso, {hobby_phrase}"
        
        if benefit:
            message += f" — {benefit}."
        
        # 5. Meta si hay espacio
        if profile.goals and len(message) < 420:
            message += f" Un paso hacia {profile.goals[0].lower()}."
        
        # Truncar si necesario
        if len(message) > 500:
            last_period = message[:497].rfind('.')
            if last_period > 300:
                message = message[:last_period + 1]
            else:
                message = message[:497] + "..."
        
        return message
    
    def _connect_hobby(self, hobbies: List[str], product: Product) -> str:
        """Conecta hobbies con el producto."""
        product_text = f"{product.nombre} {product.subcategoria}".lower()
        
        for hobby in hobbies:
            if hobby.lower() in product_text:
                return f"aprovechando tu gusto por {hobby.lower()}, te recomendamos {product.nombre}"
        
        if hobbies:
            return f"combinando tu interés en {hobbies[0].lower()} con algo nuevo, te sugerimos {product.nombre}"
        
        return f"te recomendamos {product.nombre}"
    
    def _get_benefit(self, activity_types: List[str]) -> str:
        """Obtiene el beneficio basado en el tipo de actividad."""
        for at in activity_types:
            if at in self.ACTIVITY_BENEFITS:
                return self.ACTIVITY_BENEFITS[at]
        return ""


# =============================================================================
# ORQUESTADOR PRINCIPAL
# =============================================================================

class BeHumanRecommender:
    """
    Orquestador principal del sistema de recomendación.
    
    Uso:
        recommender = BeHumanRecommender()
        result = recommender.recommend(profile, situation)
        print(result["message"])  # Mensaje empático
        print(result["recommendations"])  # Top productos
    """
    
    def __init__(self, products_path: str = "data/compensar/productos.json"):
        self.engine = RecommendationEngine(products_path)
        self.message_generator = EmpathicMessageGenerator()
    
    def recommend(
        self,
        profile: UserProfile,
        situation: Situation,
        top_n: int = 3
    ) -> Dict:
        """
        Pipeline completo de recomendación.
        
        Returns:
            {
                "message": str,              # Mensaje empático ≤500 chars
                "message_length": int,       # Longitud del mensaje
                "recommendations": [...],    # Top N productos con scores
                "context": {...}             # Contexto usado
            }
        """
        # 1. Obtener recomendaciones
        recs = self.engine.recommend(profile, situation, top_n)
        
        # 2. Generar mensaje
        message = self.message_generator.generate(profile, situation, recs)
        
        # 3. Formatear resultado
        return {
            "message": message,
            "message_length": len(message),
            "recommendations": [
                {
                    "product": {
                        "id": r.product.id,
                        "nombre": r.product.nombre,
                        "categoria": r.product.categoria_principal,
                        "subcategoria": r.product.subcategoria,
                        "precio_desde": r.product.precio_desde,
                        "url": r.product.url,
                        "imagen_url": r.product.imagen_url,
                        "promocion": r.product.promocion,
                        "activity_types": r.product.activity_types
                    },
                    "score": r.score,
                    "reasons": r.reasons
                }
                for r in recs
            ],
            "context": {
                "profile_name": profile.name,
                "profile_age": profile.age,
                "hobbies": profile.hobbies,
                "goals": profile.goals,
                "situation_type": situation.type,
                "situation_subtype": situation.subtype,
                "situation_context": situation.context
            }
        }


# =============================================================================
# DEMO
# =============================================================================

def run_demo():
    """Ejecuta demostración del sistema."""
    
    print("\n" + "="*70)
    print("  🧠 BEHUMAN - Sistema de Recomendación Empático")
    print("  Situación → Recomendación → Mensaje Consolador")
    print("="*70)
    
    recommender = BeHumanRecommender()
    
    test_cases = [
        {
            "name": "Adulto mayor - Pérdida de padres",
            "profile": UserProfile(
                user_id="001",
                name="Ricardo",
                age=59,
                gender="masculino",
                hobbies=["lectura", "jardinería", "caminar"],
                goals=["fortalecer relaciones personales", "aprovechar el tiempo"]
            ),
            "situation": Situation(
                type="perdida_familiar",
                subtype="padres",
                context="Acaba de perder a sus padres por enfermedad"
            )
        },
        {
            "name": "Joven - Ruptura amorosa",
            "profile": UserProfile(
                user_id="002",
                name="Carlos",
                age=19,
                gender="masculino",
                hobbies=["música", "deportes", "videojuegos"],
                goals=["superar la ruptura", "conocer gente nueva"]
            ),
            "situation": Situation(
                type="ruptura_amorosa",
                subtype="reciente",
                context="Ruptura después de 2 años"
            )
        },
        {
            "name": "Profesional - Ansiedad laboral",
            "profile": UserProfile(
                user_id="003",
                name="María",
                age=35,
                gender="femenino",
                hobbies=["yoga", "lectura", "cocina"],
                goals=["manejar el estrés", "encontrar balance"]
            ),
            "situation": Situation(
                type="ansiedad",
                subtype="laboral",
                context="Presión constante en el trabajo"
            )
        }
    ]
    
    results = []
    
    for tc in test_cases:
        print(f"\n{'─'*70}")
        print(f"📋 CASO: {tc['name']}")
        print(f"{'─'*70}")
        
        result = recommender.recommend(tc["profile"], tc["situation"])
        
        print(f"\n👤 {tc['profile'].name}, {tc['profile'].age} años")
        print(f"📍 Situación: {tc['situation'].context}")
        print(f"🏷️  Hobbies: {', '.join(tc['profile'].hobbies)}")
        print(f"🎯 Metas: {', '.join(tc['profile'].goals)}")
        
        print(f"\n💬 MENSAJE EMPÁTICO ({result['message_length']} chars):")
        print(f"{'─'*50}")
        print(f"\n  \"{result['message']}\"\n")
        print(f"{'─'*50}")
        
        if result["recommendations"]:
            print(f"\n🎁 TOP RECOMENDACIONES:")
            for i, rec in enumerate(result["recommendations"], 1):
                print(f"\n  {i}. {rec['product']['nombre']}")
                print(f"     Score: {rec['score']:.0f} | Desde: ${rec['product']['precio_desde']:,.0f}")
                print(f"     Tipos: {', '.join(rec['product']['activity_types'])}")
                if rec["reasons"]:
                    print(f"     → {'; '.join(rec['reasons'][:2])}")
        
        results.append({"case": tc["name"], **result})
    
    # Exportar
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"logs/recommendations_{timestamp}.json"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✅ {len(results)} casos procesados")
    print(f"📁 Exportado a: {filepath}")
    print(f"{'='*70}\n")
    
    return results


if __name__ == "__main__":
    run_demo()
