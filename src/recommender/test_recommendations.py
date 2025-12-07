#!/usr/bin/env python3
"""
BeHuman - Sistema de Recomendaciones con Explicaciones Empáticas
================================================================

Este módulo permite testear el sistema de recomendaciones con casos reales,
generando explicaciones empáticas que explican el POR QUÉ de cada recomendación.

Uso:
    python src/recommender/test_recommendations.py
    python src/recommender/test_recommendations.py --caso 1
    python src/recommender/test_recommendations.py --interactive
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
import random

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# =============================================================================
# MODELOS DE DATOS
# =============================================================================

@dataclass
class UserProfile:
    """Perfil del usuario para personalización."""
    age: int
    gender: str  # male, female, other
    situation: str  # breakup, stress, anxiety, loneliness, grief, etc.
    situation_details: str  # Descripción libre de la situación
    personality_traits: list[str] = field(default_factory=list)  # activo, social, introvertido...
    interests: list[str] = field(default_factory=list)  # deportes, música, arte...
    emotional_state: str = "neutral"  # stressed, anxious, sad, angry, hopeful...
    emotional_intensity: float = 5.0  # 1-10


@dataclass 
class Recommendation:
    """Una recomendación con su explicación empática."""
    activity_name: str
    activity_category: str
    activity_subcategory: str
    price_range: dict  # {tipo_a: X, tipo_b: Y, tipo_c: Z}
    
    # Explicación empática
    empathic_message: str
    
    # Razonamiento detrás de la recomendación
    why_this_activity: list[str]  # Razones específicas
    expected_benefits: list[str]  # Beneficios esperados
    
    # Scores del sistema
    relevance_score: float
    match_details: dict  # Detalles del matching


@dataclass
class TestCase:
    """Un caso de prueba completo."""
    id: str
    name: str
    user_profile: UserProfile
    recommendations: list[Recommendation] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


# =============================================================================
# BASE DE CONOCIMIENTO: ACTIVIDADES DE COMPENSAR
# =============================================================================

# Cargar actividades del JSON si existe
def load_compensar_activities() -> list[dict]:
    """Carga las actividades scrapeadas de Compensar."""
    json_path = Path(__file__).parent.parent.parent / "data" / "compensar" / "productos.json"
    
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Fallback: actividades de ejemplo
    return get_sample_activities()


def get_sample_activities() -> list[dict]:
    """Actividades de ejemplo para testing sin datos reales."""
    return [
        {
            "nombre": "Yoga Integral",
            "subcategoria": "practicas-dirigidas",
            "descripcion": "Clases de yoga para todos los niveles",
            "precio_categoria_a": 45000,
            "precio_categoria_b": 52000,
            "precio_categoria_c": 65000,
            "tags": {
                "profile_tags": ["tranquilo", "flexible", "mindful"],
                "situation_tags": ["estrés alto", "ansiedad", "necesidad de calma"],
                "benefits": ["relajación", "flexibilidad", "conexión social", "mindfulness"]
            }
        },
        {
            "nombre": "Gimnasio - Acceso Mensual",
            "subcategoria": "gimnasio",
            "descripcion": "Acceso completo a instalaciones de gimnasio",
            "precio_categoria_a": 89000,
            "precio_categoria_b": 95000,
            "precio_categoria_c": 120000,
            "tags": {
                "profile_tags": ["activo", "disciplinado", "competitivo"],
                "situation_tags": ["estrés alto", "baja autoestima", "necesidad de rutina"],
                "benefits": ["salud física", "liberación de endorfinas", "autoestima", "rutina"]
            }
        },
        {
            "nombre": "Natación Adultos",
            "subcategoria": "natacion-y-buceo",
            "descripcion": "Clases de natación para adultos",
            "precio_categoria_a": 55000,
            "precio_categoria_b": 62000,
            "precio_categoria_c": 78000,
            "tags": {
                "profile_tags": ["activo", "autodidacta", "tranquilo"],
                "situation_tags": ["ansiedad", "estrés alto", "necesidad de desconexión"],
                "benefits": ["ejercicio completo", "relajación", "meditación activa", "resistencia"]
            }
        },
        {
            "nombre": "Pasadía Lagosol",
            "subcategoria": "pasadias",
            "descripcion": "Día completo en centro recreacional con piscina y actividades",
            "precio_categoria_a": 33800,
            "precio_categoria_b": 34500,
            "precio_categoria_c": 44400,
            "tags": {
                "profile_tags": ["social", "aventurero", "familiar"],
                "situation_tags": ["ánimo bajo", "aislamiento social", "agotamiento"],
                "benefits": ["desconexión", "naturaleza", "socialización", "diversión"]
            }
        },
        {
            "nombre": "Taller de Cerámica",
            "subcategoria": "manualidades",
            "descripcion": "Aprende a crear piezas de cerámica artesanal",
            "precio_categoria_a": 120000,
            "precio_categoria_b": 135000,
            "precio_categoria_c": 165000,
            "tags": {
                "profile_tags": ["creativo", "paciente", "artístico"],
                "situation_tags": ["ansiedad", "necesidad de expresión", "estrés alto"],
                "benefits": ["expresión creativa", "mindfulness", "logro tangible", "concentración"]
            }
        },
        {
            "nombre": "Clases de Guitarra",
            "subcategoria": "musica",
            "descripcion": "Aprende a tocar guitarra desde cero",
            "precio_categoria_a": 85000,
            "precio_categoria_b": 95000,
            "precio_categoria_c": 115000,
            "tags": {
                "profile_tags": ["creativo", "expresivo", "autodidacta"],
                "situation_tags": ["ánimo bajo", "necesidad de expresión", "aislamiento"],
                "benefits": ["expresión emocional", "nuevo skill", "comunidad musical", "concentración"]
            }
        },
        {
            "nombre": "Spa - Circuito Hidroterapia",
            "subcategoria": "spa",
            "descripcion": "Circuito completo de hidroterapia y relajación",
            "precio_categoria_a": 75000,
            "precio_categoria_b": 85000,
            "precio_categoria_c": 105000,
            "tags": {
                "profile_tags": ["tranquilo", "autocuidado", "relajado"],
                "situation_tags": ["estrés alto", "agotamiento", "ansiedad"],
                "benefits": ["relajación profunda", "autocuidado", "desconexión", "renovación"]
            }
        },
        {
            "nombre": "Tour Eje Cafetero",
            "subcategoria": "turismo",
            "descripcion": "3 días conociendo la cultura cafetera colombiana",
            "precio_categoria_a": 890000,
            "precio_categoria_b": 950000,
            "precio_categoria_c": 1150000,
            "tags": {
                "profile_tags": ["aventurero", "curioso", "social"],
                "situation_tags": ["ánimo bajo", "agotamiento", "necesidad de cambio"],
                "benefits": ["nuevas experiencias", "desconexión total", "cultura", "naturaleza"]
            }
        },
        {
            "nombre": "Curso de Cocina Italiana",
            "subcategoria": "cocina",
            "descripcion": "Aprende a preparar auténticos platos italianos",
            "precio_categoria_a": 150000,
            "precio_categoria_b": 170000,
            "precio_categoria_c": 200000,
            "tags": {
                "profile_tags": ["social", "creativo", "curioso"],
                "situation_tags": ["aislamiento social", "necesidad de rutina", "ánimo bajo"],
                "benefits": ["nuevo skill", "socialización", "creatividad", "autocuidado"]
            }
        },
        {
            "nombre": "Meditación y Mindfulness",
            "subcategoria": "bienestar-y-armonia",
            "descripcion": "Sesiones guiadas de meditación para el manejo del estrés",
            "precio_categoria_a": 40000,
            "precio_categoria_b": 48000,
            "precio_categoria_c": 60000,
            "tags": {
                "profile_tags": ["tranquilo", "mindful", "introspectivo"],
                "situation_tags": ["ansiedad", "estrés alto", "insomnio", "necesidad de calma"],
                "benefits": ["paz mental", "autoconocimiento", "manejo emocional", "mejor sueño"]
            }
        }
    ]


# =============================================================================
# MAPEOS DE SITUACIONES A TAGS
# =============================================================================

SITUATION_TO_TAGS = {
    "breakup": ["ánimo bajo", "aislamiento social", "baja autoestima", "necesidad de distracción"],
    "stress": ["estrés alto", "agotamiento", "necesidad de calma"],
    "anxiety": ["ansiedad", "necesidad de calma", "estrés alto"],
    "loneliness": ["aislamiento social", "ánimo bajo", "necesidad de conexión"],
    "grief": ["duelo", "ánimo bajo", "necesidad de expresión"],
    "burnout": ["agotamiento", "estrés alto", "necesidad de desconexión"],
    "low_self_esteem": ["baja autoestima", "necesidad de logro", "ánimo bajo"],
    "career_crisis": ["estancamiento profesional", "ansiedad", "necesidad de cambio"],
}

PERSONALITY_TO_PROFILE_TAGS = {
    "active": ["activo", "disciplinado", "competitivo"],
    "social": ["social", "extrovertido", "comunicativo"],
    "creative": ["creativo", "artístico", "expresivo"],
    "introvert": ["tranquilo", "introspectivo", "autodidacta"],
    "adventurous": ["aventurero", "curioso", "espontáneo"],
    "mindful": ["mindful", "tranquilo", "reflexivo"],
}


# =============================================================================
# MOTOR DE RECOMENDACIONES CON EXPLICACIONES
# =============================================================================

class EmpathicRecommender:
    """Motor de recomendaciones con explicaciones empáticas."""
    
    def __init__(self):
        self.activities = load_compensar_activities()
        
    def get_recommendations(
        self, 
        user: UserProfile, 
        num_recommendations: int = 3
    ) -> list[Recommendation]:
        """Genera recomendaciones con explicaciones empáticas."""
        
        # 1. Calcular scores para cada actividad
        scored_activities = []
        
        user_situation_tags = SITUATION_TO_TAGS.get(user.situation, [])
        user_profile_tags = []
        for trait in user.personality_traits:
            user_profile_tags.extend(PERSONALITY_TO_PROFILE_TAGS.get(trait, []))
        
        for activity in self.activities:
            score, match_details = self._calculate_match_score(
                activity, 
                user_situation_tags, 
                user_profile_tags,
                user
            )
            scored_activities.append((activity, score, match_details))
        
        # 2. Ordenar por score y tomar top-k
        scored_activities.sort(key=lambda x: x[1], reverse=True)
        top_activities = scored_activities[:num_recommendations]
        
        # 3. Generar explicaciones empáticas
        recommendations = []
        for activity, score, match_details in top_activities:
            recommendation = self._create_recommendation(
                activity, 
                score, 
                match_details,
                user
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _calculate_match_score(
        self, 
        activity: dict, 
        situation_tags: list[str],
        profile_tags: list[str],
        user: UserProfile
    ) -> tuple[float, dict]:
        """Calcula el score de matching entre usuario y actividad."""
        
        activity_tags = activity.get("tags", {})
        activity_situation = activity_tags.get("situation_tags", [])
        activity_profile = activity_tags.get("profile_tags", [])
        
        # Score por situación (40%)
        situation_matches = set(situation_tags) & set(activity_situation)
        situation_score = len(situation_matches) / max(len(situation_tags), 1)
        
        # Score por perfil (30%)
        profile_matches = set(profile_tags) & set(activity_profile)
        profile_score = len(profile_matches) / max(len(profile_tags), 1)
        
        # Score por intereses (20%)
        interest_score = 0
        for interest in user.interests:
            if interest.lower() in activity.get("subcategoria", "").lower():
                interest_score = 1.0
                break
            if interest.lower() in activity.get("nombre", "").lower():
                interest_score = 0.8
                break
        
        # Ajuste por intensidad emocional (10%)
        # Mayor intensidad = preferir actividades más calmantes
        intensity_factor = 1.0
        if user.emotional_intensity > 7:
            calming_tags = {"tranquilo", "relajación", "calma", "mindful"}
            if calming_tags & set(activity_profile):
                intensity_factor = 1.2
        
        total_score = (
            situation_score * 0.40 +
            profile_score * 0.30 +
            interest_score * 0.20 +
            0.10 * intensity_factor
        )
        
        match_details = {
            "situation_matches": list(situation_matches),
            "profile_matches": list(profile_matches),
            "situation_score": situation_score,
            "profile_score": profile_score,
            "interest_score": interest_score,
            "intensity_factor": intensity_factor
        }
        
        return total_score, match_details
    
    def _create_recommendation(
        self,
        activity: dict,
        score: float,
        match_details: dict,
        user: UserProfile
    ) -> Recommendation:
        """Crea una recomendación con explicación empática."""
        
        activity_tags = activity.get("tags", {})
        benefits = activity_tags.get("benefits", [])
        
        # Generar mensaje empático
        empathic_message = self._generate_empathic_message(
            activity, 
            match_details, 
            user,
            benefits
        )
        
        # Razones específicas
        why_reasons = self._generate_why_reasons(activity, match_details, user)
        
        return Recommendation(
            activity_name=activity.get("nombre", "Actividad"),
            activity_category=self._get_category(activity.get("subcategoria", "")),
            activity_subcategory=activity.get("subcategoria", ""),
            price_range={
                "tipo_a": activity.get("precio_categoria_a", 0),
                "tipo_b": activity.get("precio_categoria_b", 0),
                "tipo_c": activity.get("precio_categoria_c", 0),
            },
            empathic_message=empathic_message,
            why_this_activity=why_reasons,
            expected_benefits=benefits,
            relevance_score=round(score, 3),
            match_details=match_details
        )
    
    def _generate_empathic_message(
        self,
        activity: dict,
        match_details: dict,
        user: UserProfile,
        benefits: list[str]
    ) -> str:
        """Genera un mensaje empático personalizado."""
        
        # Componentes del mensaje
        age_ref = f"{user.age} años"
        gender_ref = {"male": "hombre", "female": "mujer", "other": "persona"}.get(user.gender, "persona")
        
        # Situación
        situation_intros = {
            "breakup": f"Sé que terminar una relación es difícil, especialmente cuando eres joven ({age_ref}). Este tipo de pérdida puede generar sentimientos de soledad y cuestionamiento personal.",
            "stress": f"Entiendo que estás atravesando un momento de mucho estrés. A los {age_ref}, las presiones pueden sentirse abrumadoras.",
            "anxiety": f"La ansiedad puede ser muy difícil de manejar. A veces nuestros pensamientos no nos dan tregua.",
            "loneliness": f"Sentirse solo/a es más común de lo que crees, y reconocerlo es el primer paso. Como {gender_ref} de {age_ref}, buscar conexión es muy valioso.",
            "grief": f"Atravesar un duelo es uno de los procesos más difíciles que enfrentamos. Date el tiempo que necesites.",
            "burnout": f"El agotamiento que sientes es real y válido. Tu cuerpo y mente están pidiendo un respiro.",
            "low_self_esteem": f"A veces es difícil vernos con buenos ojos. Pero hay mucho valor en ti que quizás no estás viendo ahora.",
            "career_crisis": f"Las crisis profesionales son oportunidades disfrazadas. A los {age_ref}, tienes tiempo para reinventarte.",
        }
        
        intro = situation_intros.get(
            user.situation, 
            f"Entiendo que estás pasando por un momento desafiante."
        )
        
        # Conexión con la actividad
        activity_name = activity.get("nombre", "esta actividad")
        subcategoria = activity.get("subcategoria", "")
        
        # Beneficios personalizados
        benefits_text = ""
        if benefits:
            if len(benefits) >= 2:
                benefits_text = f"Podrás experimentar {benefits[0]} y {benefits[1]}"
            else:
                benefits_text = f"Experimentarás {benefits[0]}"
        
        # Razón del match
        match_reason = ""
        if match_details.get("situation_matches"):
            match_reason = f"Dado que estás lidiando con {', '.join(match_details['situation_matches'][:2])}, "
        
        # Personalidad
        personality_reason = ""
        if match_details.get("profile_matches"):
            traits = match_details['profile_matches'][:2]
            personality_reason = f"Como persona {' y '.join(traits)}, "
        
        # Construir mensaje
        activity_benefits = {
            "yoga": "El yoga combina ejercicio suave con técnicas de respiración que calman la mente. Además, las clases grupales son una excelente forma de conocer gente en un ambiente tranquilo y sin presión.",
            "gimnasio": "El ejercicio libera endorfinas, las hormonas de la felicidad. Establecer una rutina de gym te dará estructura y una sensación de logro cada día.",
            "natacion": "La natación es una meditación en movimiento. El agua tiene un efecto calmante natural, y el ejercicio te ayudará a liberar tensiones acumuladas.",
            "pasadia": "Un día fuera de la rutina, rodeado de naturaleza, puede ser exactamente lo que necesitas para ganar perspectiva y renovar energías.",
            "ceramica": "Trabajar con las manos tiene un efecto terapéutico comprobado. Crear algo tangible te dará una sensación de logro y te permitirá canalizar emociones.",
            "guitarra": "La música es un lenguaje universal para las emociones. Aprender guitarra te dará una válvula de escape creativa y la posibilidad de conectar con otros músicos.",
            "spa": "A veces, lo que más necesitamos es darnos permiso para cuidarnos. Un spa no es un lujo, es una inversión en tu bienestar mental.",
            "turismo": "Cambiar de ambiente puede darte la perspectiva que necesitas. Viajar, aunque sea cerca, te permite reiniciarte.",
            "cocina": "Cocinar es un acto de amor propio. Además, las clases de cocina son espacios sociales donde es fácil conectar con otros.",
            "meditacion": "La meditación te enseña a observar tus pensamientos sin juzgarlos. Es una herramienta poderosa para el manejo emocional.",
        }
        
        # Encontrar beneficio específico
        specific_benefit = ""
        for key, benefit in activity_benefits.items():
            if key in subcategoria.lower() or key in activity_name.lower():
                specific_benefit = benefit
                break
        
        if not specific_benefit:
            specific_benefit = f"{benefits_text} en un ambiente seguro y de apoyo." if benefits_text else "Esta actividad puede ayudarte a encontrar equilibrio."
        
        # Mensaje final
        message = f"""Hey, {intro}

{match_reason}{personality_reason}te recomiendo **{activity_name}**.

{specific_benefit}

{benefits_text + ', que son exactamente lo que necesitas ahora.' if benefits_text else ''}

Dar este paso ya es un acto de cuidado hacia ti mismo/a. 💚"""
        
        return message.strip()
    
    def _generate_why_reasons(
        self,
        activity: dict,
        match_details: dict,
        user: UserProfile
    ) -> list[str]:
        """Genera las razones específicas de la recomendación."""
        
        reasons = []
        
        # Por situación
        if match_details.get("situation_matches"):
            matches = match_details["situation_matches"]
            reasons.append(f"Aborda directamente tu situación: {', '.join(matches)}")
        
        # Por perfil
        if match_details.get("profile_matches"):
            matches = match_details["profile_matches"]
            reasons.append(f"Coincide con tu personalidad: {', '.join(matches)}")
        
        # Por intereses
        if match_details.get("interest_score", 0) > 0:
            reasons.append("Se alinea con tus intereses declarados")
        
        # Por intensidad
        if match_details.get("intensity_factor", 1.0) > 1.0:
            reasons.append("Actividad calmante recomendada por tu nivel de estrés")
        
        # Beneficios de la actividad
        benefits = activity.get("tags", {}).get("benefits", [])
        if benefits:
            reasons.append(f"Beneficios esperados: {', '.join(benefits[:3])}")
        
        return reasons
    
    def _get_category(self, subcategoria: str) -> str:
        """Mapea subcategoría a categoría principal."""
        category_map = {
            "gimnasio": "Deporte",
            "natacion-y-buceo": "Deporte",
            "practicas-dirigidas": "Deporte",
            "yoga": "Bienestar",
            "spa": "Bienestar",
            "bienestar-y-armonia": "Bienestar",
            "meditacion": "Bienestar",
            "turismo": "Recreación",
            "pasadias": "Recreación",
            "musica": "Cultura",
            "manualidades": "Cultura",
            "cocina": "Cultura",
        }
        
        for key, category in category_map.items():
            if key in subcategoria.lower():
                return category
        return "General"


# =============================================================================
# CASOS DE PRUEBA
# =============================================================================

TEST_CASES = [
    TestCase(
        id="TC001",
        name="Joven tras ruptura amorosa",
        user_profile=UserProfile(
            age=19,
            gender="male",
            situation="breakup",
            situation_details="Terminó con su novia de 2 años hace una semana. Se siente solo y sin motivación.",
            personality_traits=["active", "social"],
            interests=["deportes", "música"],
            emotional_state="sad",
            emotional_intensity=7.5
        ),
        notes="Caso típico de ruptura juvenil. Buscar actividades que combinen ejercicio y socialización."
    ),
    TestCase(
        id="TC002", 
        name="Profesional con burnout",
        user_profile=UserProfile(
            age=35,
            gender="female",
            situation="burnout",
            situation_details="Trabaja 12 horas diarias en una multinacional. No puede desconectar ni los fines de semana.",
            personality_traits=["introvert", "mindful"],
            interests=["lectura", "naturaleza"],
            emotional_state="exhausted",
            emotional_intensity=8.0
        ),
        notes="Necesita desconexión total y actividades que no requieran mucha energía social."
    ),
    TestCase(
        id="TC003",
        name="Estudiante con ansiedad",
        user_profile=UserProfile(
            age=22,
            gender="female",
            situation="anxiety",
            situation_details="Está en su último año de universidad. Los exámenes finales la tienen al borde del colapso.",
            personality_traits=["creative", "introvert"],
            interests=["arte", "yoga"],
            emotional_state="anxious",
            emotional_intensity=9.0
        ),
        notes="Alta intensidad emocional. Priorizar actividades calmantes y de expresión creativa."
    ),
    TestCase(
        id="TC004",
        name="Adulto con soledad",
        user_profile=UserProfile(
            age=45,
            gender="male",
            situation="loneliness",
            situation_details="Se mudó a una nueva ciudad por trabajo. No conoce a nadie y pasa los fines de semana solo.",
            personality_traits=["social", "adventurous"],
            interests=["cocina", "viajes"],
            emotional_state="lonely",
            emotional_intensity=6.5
        ),
        notes="Buscar actividades grupales que faciliten conocer gente nueva."
    ),
    TestCase(
        id="TC005",
        name="Joven con baja autoestima",
        user_profile=UserProfile(
            age=17,
            gender="female",
            situation="low_self_esteem",
            situation_details="Comparación constante con compañeros de colegio. Siente que no es suficiente.",
            personality_traits=["creative", "introvert"],
            interests=["música", "dibujo"],
            emotional_state="insecure",
            emotional_intensity=7.0
        ),
        notes="Actividades donde pueda desarrollar habilidades y ver progreso tangible."
    ),
]


# =============================================================================
# SISTEMA DE LOGGING
# =============================================================================

class RecommendationLogger:
    """Gestiona el log de recomendaciones para análisis."""
    
    def __init__(self, log_dir: str = None):
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / "data" / "recommendation_logs"
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def log_test_case(self, test_case: TestCase) -> str:
        """Guarda un caso de prueba con sus recomendaciones."""
        
        # Nombre del archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{test_case.id}_{timestamp}.json"
        filepath = self.log_dir / filename
        
        # Convertir a dict
        data = {
            "test_case_id": test_case.id,
            "test_case_name": test_case.name,
            "timestamp": test_case.timestamp,
            "user_profile": asdict(test_case.user_profile),
            "recommendations": [asdict(r) for r in test_case.recommendations],
            "notes": test_case.notes
        }
        
        # Guardar
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return str(filepath)
    
    def generate_markdown_report(self, test_case: TestCase) -> str:
        """Genera un reporte en Markdown del caso de prueba."""
        
        report = []
        report.append(f"# 📋 Reporte de Recomendación: {test_case.name}")
        report.append(f"**ID**: {test_case.id}")
        report.append(f"**Fecha**: {test_case.timestamp}")
        report.append("")
        
        # Perfil del usuario
        user = test_case.user_profile
        report.append("## 👤 Perfil del Usuario")
        report.append(f"- **Edad**: {user.age} años")
        report.append(f"- **Género**: {user.gender}")
        report.append(f"- **Situación**: {user.situation}")
        report.append(f"- **Detalles**: {user.situation_details}")
        report.append(f"- **Personalidad**: {', '.join(user.personality_traits)}")
        report.append(f"- **Intereses**: {', '.join(user.interests)}")
        report.append(f"- **Estado emocional**: {user.emotional_state} (intensidad: {user.emotional_intensity}/10)")
        report.append("")
        
        # Recomendaciones
        report.append("## 🎯 Recomendaciones")
        report.append("")
        
        for i, rec in enumerate(test_case.recommendations, 1):
            report.append(f"### Recomendación #{i}: {rec.activity_name}")
            report.append(f"**Categoría**: {rec.activity_category} > {rec.activity_subcategory}")
            report.append(f"**Score de relevancia**: {rec.relevance_score:.1%}")
            report.append("")
            report.append("**💬 Mensaje Empático:**")
            report.append("")
            report.append(f"> {rec.empathic_message.replace(chr(10), chr(10) + '> ')}")
            report.append("")
            report.append("**🔍 Por qué esta actividad:**")
            for reason in rec.why_this_activity:
                report.append(f"- {reason}")
            report.append("")
            report.append("**✨ Beneficios esperados:**")
            for benefit in rec.expected_benefits:
                report.append(f"- {benefit}")
            report.append("")
            report.append("**💰 Precios:**")
            report.append(f"- Tipo A: ${rec.price_range.get('tipo_a', 0):,.0f}")
            report.append(f"- Tipo B: ${rec.price_range.get('tipo_b', 0):,.0f}")
            report.append(f"- Tipo C: ${rec.price_range.get('tipo_c', 0):,.0f}")
            report.append("")
            report.append("---")
            report.append("")
        
        # Notas
        if test_case.notes:
            report.append("## 📝 Notas del Caso")
            report.append(test_case.notes)
        
        return "\n".join(report)
    
    def save_markdown_report(self, test_case: TestCase) -> str:
        """Guarda el reporte en Markdown."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{test_case.id}_{timestamp}.md"
        filepath = self.log_dir / filename
        
        report = self.generate_markdown_report(test_case)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return str(filepath)


# =============================================================================
# CLI
# =============================================================================

def run_test_case(test_case: TestCase, verbose: bool = True) -> TestCase:
    """Ejecuta un caso de prueba y genera recomendaciones."""
    
    recommender = EmpathicRecommender()
    logger = RecommendationLogger()
    
    # Generar recomendaciones
    recommendations = recommender.get_recommendations(
        test_case.user_profile,
        num_recommendations=3
    )
    
    # Actualizar caso de prueba
    test_case.recommendations = recommendations
    test_case.timestamp = datetime.now().isoformat()
    
    # Guardar logs
    json_path = logger.log_test_case(test_case)
    md_path = logger.save_markdown_report(test_case)
    
    if verbose:
        print(f"\n{'='*80}")
        print(f"📋 CASO: {test_case.name} ({test_case.id})")
        print(f"{'='*80}")
        print(logger.generate_markdown_report(test_case))
        print(f"\n📁 Logs guardados en:")
        print(f"   - JSON: {json_path}")
        print(f"   - Markdown: {md_path}")
    
    return test_case


def run_all_tests():
    """Ejecuta todos los casos de prueba predefinidos."""
    
    print("\n" + "="*80)
    print("🧪 EJECUTANDO TODOS LOS CASOS DE PRUEBA")
    print("="*80)
    
    results = []
    for test_case in TEST_CASES:
        result = run_test_case(test_case)
        results.append(result)
    
    print("\n" + "="*80)
    print(f"✅ Completados {len(results)} casos de prueba")
    print("="*80)
    
    return results


def interactive_mode():
    """Modo interactivo para crear casos de prueba personalizados."""
    
    print("\n🎯 MODO INTERACTIVO - Crear Caso de Prueba")
    print("-" * 40)
    
    # Recopilar información
    age = int(input("Edad del usuario: "))
    gender = input("Género (male/female/other): ").strip().lower()
    
    print("\nSituaciones disponibles:")
    print("  1. breakup - Ruptura amorosa")
    print("  2. stress - Estrés general")
    print("  3. anxiety - Ansiedad")
    print("  4. loneliness - Soledad")
    print("  5. grief - Duelo")
    print("  6. burnout - Agotamiento laboral")
    print("  7. low_self_esteem - Baja autoestima")
    print("  8. career_crisis - Crisis profesional")
    
    situation = input("Situación (ej: breakup): ").strip().lower()
    situation_details = input("Describe la situación con más detalle: ")
    
    print("\nRasgos de personalidad (separados por coma):")
    print("  active, social, creative, introvert, adventurous, mindful")
    traits = [t.strip() for t in input("Rasgos: ").split(",")]
    
    interests = [i.strip() for i in input("Intereses (separados por coma): ").split(",")]
    
    emotional_state = input("Estado emocional actual (sad, anxious, angry, hopeful, etc.): ")
    emotional_intensity = float(input("Intensidad emocional (1-10): "))
    
    # Crear perfil
    user = UserProfile(
        age=age,
        gender=gender,
        situation=situation,
        situation_details=situation_details,
        personality_traits=traits,
        interests=interests,
        emotional_state=emotional_state,
        emotional_intensity=emotional_intensity
    )
    
    test_case = TestCase(
        id=f"TC_CUSTOM_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        name=f"Caso personalizado - {situation}",
        user_profile=user
    )
    
    return run_test_case(test_case)


def main():
    """Punto de entrada principal."""
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Sistema de Recomendaciones con Explicaciones Empáticas"
    )
    parser.add_argument(
        "--caso", "-c",
        type=int,
        help="Ejecutar caso de prueba específico (1-5)"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Ejecutar todos los casos de prueba"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Modo interactivo para crear caso personalizado"
    )
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
    elif args.caso:
        if 1 <= args.caso <= len(TEST_CASES):
            run_test_case(TEST_CASES[args.caso - 1])
        else:
            print(f"❌ Caso {args.caso} no existe. Disponibles: 1-{len(TEST_CASES)}")
    elif args.all:
        run_all_tests()
    else:
        # Por defecto, ejecutar el primer caso como demo
        print("💡 Uso: python test_recommendations.py --help")
        print("\n📌 Ejecutando caso de demo (TC001)...\n")
        run_test_case(TEST_CASES[0])


if __name__ == "__main__":
    main()
