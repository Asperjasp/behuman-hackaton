from typing import Dict, List, Any
from dataclasses import asdict
import random

from .recommendation_engine import (
    BeHumanRecommender,
    UserProfile,
    Situation,
    Recommendation,
)


def _estimate_productivity_uplift(recommendation: Recommendation) -> float:
    """Heurística simple para estimar uplift de productividad en %.

    Basada en score y tipos de actividad. Resultado entre 3% y 30%.
    """
    base = recommendation.score
    # Normalize score roughly (scores are multiples of 30/15/10 etc.)
    norm = min(max(base / 100.0, 0.03), 0.3)
    # add small randomised but stable factor
    jitter = (hash(recommendation.product.id) % 5) / 100.0
    uplift = min(0.30, norm + jitter)
    return round(uplift * 100, 1)


class HRWorkflow:
    """Flujo para que RRHH reciba una notificación anónima y proponga opciones.

    - `create_hr_cards` genera dos tarjetas con recomendaciones accionables.
    - `hr_accept` simula la aceptación por parte de RRHH y genera el mensaje
      que será enviado al empleado (sin revelar identidad).
    """

    def __init__(self, products_path: str = "data/compensar/productos.json"):
        self.recommender = BeHumanRecommender(products_path)

    def create_hr_cards(self, profile: UserProfile, situation: Situation) -> List[Dict[str, Any]]:
        """Genera dos tarjetas con opciones basadas en el sistema de recomendación.

        Cada tarjeta incluye: product data, breve explicación y una estimación
        numérica de mejora de productividad.
        """
        result = self.recommender.recommend(profile, situation, top_n=4)
        recs = result.get("recommendations", [])

        # pick top 2 distinct activity types/products
        cards = []
        used = set()
        for rec in recs:
            pid = rec["product"].get("id")
            if pid in used:
                continue
            used.add(pid)
            # build an actionable summary
            title = rec["product"].get("nombre")
            subtitle = f"{rec['product'].get('categoria', '')} · {rec['product'].get('subcategoria', '')}"
            reasons = rec.get("reasons", [])

            # safer uplift computation from dict
            uplift = min(30.0, max(3.0, rec.get("score", 0) / 5.0))

            card = {
                "product": rec["product"],
                "title": title,
                "subtitle": subtitle,
                "explanation": (
                    f"Esta opción ayuda porque {reasons[0] if reasons else 'encaja con la situación'}; "
                    f"favorece bienestar y puede reducir ausentismo."
                ),
                "estimated_productivity_uplift_percent": round(uplift, 1),
                "score": rec.get("score", 0),
            }

            cards.append(card)
            if len(cards) >= 2:
                break

        return cards

    def hr_accept(self, profile: UserProfile, situation: Situation, accepted_card: Dict[str, Any]) -> Dict[str, Any]:
        """Simula que RRHH acepta una de las tarjetas y prepara la notificación.

        Devuelve un dict con la notificación que debería llegar al empleado.
        La notificación preserva anonimato: no incluye `user_id`.
        """
        # Use the top product info in accepted_card to craft message
        product_info = accepted_card.get("product", {})

        # Generate empathic message using BeHumanRecommender's generator
        result = self.recommender.recommend(profile, situation, top_n=3)

        # Select the message and include a note to the employee
        message = result.get("message")

        employee_card = {
            "to_employee": True,
            "anonymous": True,
            "message": (
                f"Hemos recibido una notificación anónima sobre tu situación. {message} "
                "RRHH ha aprobado una intervención que podría ayudarte. Si deseas más detalles, "
                "puedes responder a este mensaje y te conectaremos con el equipo de bienestar."
            ),
            "intervention": {
                "title": product_info.get("nombre"),
                "url": product_info.get("url"),
                "estimated_productivity_uplift_percent": accepted_card.get("estimated_productivity_uplift_percent")
            }
        }

        return employee_card


if __name__ == "__main__":
    # Small demo
    from .recommendation_engine import UserProfile, Situation

    wf = HRWorkflow()
    profile = UserProfile(user_id="anon-123", name="Empleado Anónimo", age=34, gender="no-binario", hobbies=["yoga", "lectura"], goals=["recuperar equilibrio"]) 
    situation = Situation(type="estres_laboral", subtype="burnout", context="Sobrecarga de tareas y falta de descansos")

    cards = wf.create_hr_cards(profile, situation)
    print("HR Cards:\n", cards)
    if cards:
        emp = wf.hr_accept(profile, situation, cards[0])
        print("\nEmployee notification:\n", emp)
