"""
BeHuman - Generador de Mensajes Empáticos
==========================================

Genera mensajes cortos (≤500 caracteres) que acompañan las recomendaciones.
El mensaje debe:
1. Confrontar con empatía la situación real
2. Calmar de manera realista  
3. Motivar usando hobbies hacia una actividad de Compensar

El tono es conversacional y humano, no robótico ni segmentado.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import json
import os
import random


@dataclass
class UserProfile:
    """Perfil del usuario."""
    name: str
    age: int
    gender: str  # "masculino", "femenino", "no-binario"
    hobbies: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)


@dataclass  
class Situation:
    """Situación que enfrenta el usuario."""
    type: str  # "perdida_familiar", "ruptura", "ansiedad", etc.
    subtype: str  # "padres", "pareja", "laboral", etc.
    context: str  # Descripción específica


@dataclass
class Activity:
    """Actividad de Compensar."""
    name: str
    category: str  # "baja_estimulacion", "ejercicio", "mindfulness", etc.
    benefit: str  # Por qué ayuda en situaciones difíciles


class EmpathicMessageGenerator:
    """
    Genera mensajes empáticos de ≤500 caracteres.
    
    Estructura:
    "[Nombre], sé que hoy te toca [situación]. [Frase de calma]. 
    Por eso, [conexión hobby-actividad] — [beneficio]. [Meta]."
    """
    
    # Cómo describir cada situación (confrontación)
    SITUATIONS = {
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
    
    # Frases de calma realista (no minimizar)
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
            "Tu mente trabaja de más tratando de protegerte.",
            "La calma es una habilidad que se entrena.",
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
    
    # Conexiones entre hobbies y tipos de actividad
    HOBBY_CONNECTIONS = {
        "lectura": ["club de lectura", "literatura", "libros"],
        "música": ["música", "concierto", "melodía"],
        "arte": ["arte", "pintura", "creatividad", "taller"],
        "deportes": ["ejercicio", "deporte", "natación"],
        "naturaleza": ["naturaleza", "caminata", "ecológica"],
        "yoga": ["yoga", "meditación", "mindfulness"],
        "jardinería": ["jardín", "naturaleza", "plantas"],
        "caminar": ["caminata", "senderismo", "paseo"],
        "cocina": ["cocina", "gastronomía", "culinario"],
        "tejido": ["taller", "manualidades", "artesanía"],
    }
    
    def generate(
        self,
        profile: UserProfile,
        situation: Situation,
        activity: Activity
    ) -> str:
        """
        Genera el mensaje empático de ≤500 caracteres.
        """
        # 1. Obtener descripción de situación
        sit_phrases = self.SITUATIONS.get(situation.type, {})
        confrontation = sit_phrases.get(
            situation.subtype, 
            sit_phrases.get("general", "enfrentar este momento difícil")
        )
        
        # 2. Obtener frase de calma
        calm_phrases = self.CALMING.get(situation.type, ["Lo que sientes es válido."])
        calming = random.choice(calm_phrases)
        
        # 3. Conectar hobby con actividad
        hobby_phrase = self._connect_hobby_activity(profile.hobbies, activity)
        
        # 4. Construir mensaje
        message = f"{profile.name}, sé que hoy te toca {confrontation}. {calming} "
        message += f"Por eso, {hobby_phrase}"
        
        # Agregar beneficio de la actividad
        if activity.benefit:
            message += f"— {activity.benefit}."
        
        # Agregar meta si hay espacio
        if profile.goals and len(message) < 420:
            message += f" Un paso hacia {profile.goals[0].lower()}."
        
        # Asegurar límite de 500 chars
        if len(message) > 500:
            message = self._trim_to_limit(message)
        
        return message
    
    def _connect_hobby_activity(self, hobbies: List[str], activity: Activity) -> str:
        """Conecta los hobbies del usuario con la actividad."""
        if not hobbies:
            return f"te recomendamos {activity.name.lower()}"
        
        # Buscar match entre hobbies y actividad
        activity_lower = (activity.name + " " + activity.category).lower()
        
        for hobby in hobbies:
            hobby_lower = hobby.lower()
            keywords = self.HOBBY_CONNECTIONS.get(hobby_lower, [hobby_lower])
            
            if any(kw in activity_lower for kw in keywords):
                return f"aprovechando tu gusto por {hobby.lower()}, te recomendamos {activity.name.lower()}"
        
        # Si no hay match, usar el primer hobby de forma general
        return f"combinando tu interés en {hobbies[0].lower()} con algo nuevo, te sugerimos {activity.name.lower()}"
    
    def _trim_to_limit(self, message: str, limit: int = 500) -> str:
        """Recorta el mensaje de forma inteligente."""
        if len(message) <= limit:
            return message
        
        # Buscar último punto antes del límite
        truncated = message[:limit - 3]
        last_period = truncated.rfind('.')
        
        if last_period > limit * 0.6:
            return truncated[:last_period + 1]
        
        last_space = truncated.rfind(' ')
        return truncated[:last_space] + "..."


# =============================================================================
# CASOS DE PRUEBA
# =============================================================================

def create_test_cases():
    """Casos de prueba basados en escenarios reales."""
    
    activities = {
        "estadia": Activity(
            name="Estadía de descanso",
            category="baja_estimulacion",
            benefit="a veces el mejor paso es simplemente pausar"
        ),
        "yoga": Activity(
            name="Yoga grupal",
            category="mindfulness", 
            benefit="un espacio para reconectar con tu cuerpo y calmar la mente"
        ),
        "natacion": Activity(
            name="Natación libre",
            category="ejercicio",
            benefit="el agua ayuda a liberar tensiones acumuladas"
        ),
        "caminata": Activity(
            name="Caminata ecológica",
            category="naturaleza",
            benefit="la naturaleza tiene un efecto restaurador comprobado"
        ),
        "arte": Activity(
            name="Taller de arte-terapia",
            category="expresion",
            benefit="expresar lo que las palabras no alcanzan"
        ),
        "lectura": Activity(
            name="Club de lectura",
            category="socialización",
            benefit="conectar con otros a través de historias compartidas"
        )
    }
    
    return [
        {
            "name": "Adulto mayor - Pérdida de padres (tu ejemplo exacto)",
            "profile": UserProfile(
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
            ),
            "activity": activities["estadia"]
        },
        {
            "name": "Joven - Ruptura amorosa",
            "profile": UserProfile(
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
            ),
            "activity": activities["natacion"]
        },
        {
            "name": "Profesional - Ansiedad laboral",
            "profile": UserProfile(
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
            ),
            "activity": activities["yoga"]
        },
        {
            "name": "Adulta mayor - Duelo de esposo",
            "profile": UserProfile(
                name="Carmen",
                age=65,
                gender="femenino",
                hobbies=["jardinería", "tejido", "caminar"],
                goals=["procesar la pérdida", "mantener actividad"]
            ),
            "situation": Situation(
                type="duelo",
                subtype="prolongado",
                context="Perdió a su esposo hace 6 meses"
            ),
            "activity": activities["caminata"]
        },
        {
            "name": "Adulto joven - Soledad post-mudanza",
            "profile": UserProfile(
                name="Alex",
                age=28,
                gender="no-binario",
                hobbies=["arte", "música", "cine"],
                goals=["hacer amigos", "sentir comunidad"]
            ),
            "situation": Situation(
                type="soledad",
                subtype="mudanza",
                context="Se mudó a nueva ciudad hace 3 meses"
            ),
            "activity": activities["arte"]
        }
    ]


def run_demo():
    """Ejecuta demostración del generador."""
    
    print("\n" + "="*70)
    print("  🧠 BEHUMAN - Generador de Mensajes Empáticos")
    print("  Mensajes de ≤500 caracteres para acompañar recomendaciones")
    print("="*70)
    
    generator = EmpathicMessageGenerator()
    test_cases = create_test_cases()
    results = []
    
    for tc in test_cases:
        print(f"\n{'─'*70}")
        print(f"📋 CASO: {tc['name']}")
        print(f"{'─'*70}")
        
        profile = tc["profile"]
        situation = tc["situation"]
        activity = tc["activity"]
        
        message = generator.generate(profile, situation, activity)
        
        print(f"\n👤 {profile.name}, {profile.age} años")
        print(f"📍 {situation.context}")
        print(f"🎯 {activity.name} ({activity.category})")
        print(f"🏷️  Hobbies: {', '.join(profile.hobbies)}")
        print(f"🎯 Metas: {', '.join(profile.goals)}")
        
        print(f"\n💬 MENSAJE ({len(message)} chars):")
        print(f"{'─'*50}")
        print(f"\n  \"{message}\"\n")
        print(f"{'─'*50}")
        
        results.append({
            "case": tc["name"],
            "profile": {
                "name": profile.name,
                "age": profile.age,
                "hobbies": profile.hobbies,
                "goals": profile.goals
            },
            "situation": {
                "type": situation.type,
                "subtype": situation.subtype,
                "context": situation.context
            },
            "activity": activity.name,
            "message": message,
            "char_count": len(message)
        })
    
    # Exportar resultados
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"logs/empathic_messages_{timestamp}.json"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✅ {len(results)} mensajes generados")
    print(f"📁 Exportado a: {filepath}")
    print(f"{'='*70}\n")
    
    return results


if __name__ == "__main__":
    run_demo()
