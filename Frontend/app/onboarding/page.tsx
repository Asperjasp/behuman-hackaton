"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import BehumanLogo from "@/components/BehumanLogo";
import OnboardingIntro from "@/components/onboarding/OnboardingIntro";
import OnboardingComplete from "@/components/onboarding/OnboardingComplete";
import OnboardingOption from "@/components/onboarding/OnboardingOption";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { useOnboarding } from "@/hooks/use-onboarding";
import { OnboardingService } from "@/lib/onboarding-service";
import { toast } from "sonner";

type OnboardingPhase = "intro" | "questions" | "complete";

export default function OnboardingPage() {
  const router = useRouter();
  const { user } = useAuth();
  const { hasCompleted, loading: onboardingLoading } = useOnboarding();
  const [phase, setPhase] = useState<OnboardingPhase>("intro");
  const [currentStep, setCurrentStep] = useState(1);
  const [saving, setSaving] = useState(false);

  // Form data
  const [humanAge, setHumanAge] = useState("");
  const [humanGender, setHumanGender] = useState("");
  const [humanName, setHumanName] = useState("");
  const [lifeAxes, setLifeAxes] = useState<string[]>([]);
  const [tenYearGoals, setTenYearGoals] = useState<string[]>([]);
  const [shortTermGoals, setShortTermGoals] = useState<string[]>([]);
  const [hobbies, setHobbies] = useState<string[]>([]);
  const [emotionalHistory, setEmotionalHistory] = useState("");

  const totalSteps = 8;

  // Redirect to /app if onboarding is already completed
  useEffect(() => {
    if (!onboardingLoading && hasCompleted) {
      router.push("/app");
    }
  }, [hasCompleted, onboardingLoading, router]);

  const handleMultiSelect = (
    value: string,
    selected: string[],
    setSelected: (val: string[]) => void,
    maxItems?: number
  ) => {
    if (selected.includes(value)) {
      setSelected(selected.filter((v) => v !== value));
    } else if (!maxItems || selected.length < maxItems) {
      setSelected([...selected, value]);
    }
  };

  const handleNext = async () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
    } else {
      // Last step - save to database
      await handleComplete();
    }
  };

  const handleComplete = async () => {
    if (!user) {
      toast.error("Error", {
        description: "Debes iniciar sesión para completar el onboarding",
      });
      router.push("/login");
      return;
    }

    setSaving(true);

    try {
      const { error } = await OnboardingService.saveOnboarding(user.id, {
        human_name: humanName,
        human_age: humanAge,
        human_gender: humanGender,
        life_axes: lifeAxes,
        ten_year_goals: tenYearGoals,
        short_term_goals: shortTermGoals,
        hobbies: hobbies,
        emotional_history: emotionalHistory,
      });

      if (error) {
        throw error;
      }

      toast.success("¡Onboarding completado!", {
        description: "Tu Human ha sido creado exitosamente",
      });

      setPhase("complete");
    } catch (error) {
      console.error("Error saving onboarding:", error);
      toast.error("Error", {
        description: "No se pudo guardar tu información. Intenta nuevamente.",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="text-2xl font-bold text-foreground">Escoge la edad de tu Human</h2>
              <p className="text-muted-foreground">Define la personalidad y energía de tu Human</p>
            </div>
            <div className="grid gap-3">
              {["18–22 años", "23–28 años", "29–35 años", "36–45 años", "46–55 años", "55+ años"].map((age) => (
                <OnboardingOption
                  key={age}
                  label={age}
                  selected={humanAge === age}
                  onClick={() => setHumanAge(age)}
                />
              ))}
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="text-2xl font-bold text-foreground">¿Cómo quieres que se identifique tu Human?</h2>
            </div>
            <div className="grid gap-3">
              {["Masculino", "Femenino", "No binario"].map((gender) => (
                <OnboardingOption
                  key={gender}
                  label={gender}
                  selected={humanGender === gender}
                  onClick={() => setHumanGender(gender)}
                />
              ))}
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="text-2xl font-bold text-foreground">Nombre del Human</h2>
              <p className="text-muted-foreground">Dale un nombre único a tu Human</p>
            </div>
            <Input
              value={humanName}
              onChange={(e) => setHumanName(e.target.value)}
              placeholder="Escribe un nombre..."
              className="text-lg py-6"
            />
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="text-2xl font-bold text-foreground">¿Cuáles son tus ejes centrales en la vida?</h2>
              <p className={`text-sm ${lifeAxes.length >= 3 ? 'text-orange-500 font-medium' : 'text-muted-foreground'}`}>
                {lifeAxes.length}/3 seleccionados {lifeAxes.length === 0 ? '(escoge al menos 1)' : ''}
              </p>
            </div>
            <div className="grid gap-3">
              {[
                "Familia", "Trabajo / carrera", "Dinero / estabilidad financiera",
                "Diversión / disfrute", "Salud física / mental", "Conexiones sociales / amigos",
                "Espiritualidad / sentido de vida", "Impacto en el mundo / ayudar a otros"
              ].map((axis) => (
                <OnboardingOption
                  key={axis}
                  label={axis}
                  selected={lifeAxes.includes(axis)}
                  onClick={() => handleMultiSelect(axis, lifeAxes, setLifeAxes, 3)}
                  multiSelect
                />
              ))}
            </div>
          </div>
        );

      case 5:
        return (
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="text-2xl font-bold text-foreground">En 10 años, ¿qué te gustaría haber logrado?</h2>
              <p className="text-sm text-muted-foreground">
                {tenYearGoals.length} seleccionados {tenYearGoals.length === 0 ? '(escoge al menos 1)' : ''}
              </p>
            </div>
            <div className="grid gap-3 max-h-[50vh] overflow-y-auto pr-2">
              {[
                "Tener mi propia empresa", "Estar financieramente estable", "Formar una familia",
                "Tener 1 o varios hijos", "Haber viajado por el mundo", "Tener excelente salud física",
                "Tener estabilidad emocional", "Vivir en otro país", "Convertirme en líder en mi área",
                "Tener propiedades o inversiones", "Haber creado algo que impacte a otros"
              ].map((goal) => (
                <OnboardingOption
                  key={goal}
                  label={goal}
                  selected={tenYearGoals.includes(goal)}
                  onClick={() => handleMultiSelect(goal, tenYearGoals, setTenYearGoals)}
                  multiSelect
                />
              ))}
            </div>
          </div>
        );

      case 6:
        return (
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="text-2xl font-bold text-foreground">¿Cuáles son tus objetivos a corto plazo?</h2>
              <p className={`text-sm ${shortTermGoals.length >= 3 ? 'text-orange-500 font-medium' : 'text-muted-foreground'}`}>
                {shortTermGoals.length}/3 seleccionados {shortTermGoals.length === 0 ? '(escoge al menos 1)' : ''}
              </p>
            </div>
            <div className="grid gap-3 max-h-[50vh] overflow-y-auto pr-2">
              {[
                "Conseguir pareja o mejorar mi vida sentimental", "Aumentar mi salario",
                "Empezar a emprender", "Mejorar mi forma física", "Irme a vivir solo",
                "Cambiar de empleo", "Construir hábitos saludables",
                "Sanar emocionalmente / trabajar en terapia", "Ahorrar dinero o empezar a invertir",
                "Viajar más", "Expandir mi círculo social",
                "Mejorar habilidades profesionales (inglés, IA, programación, etc.)"
              ].map((goal) => (
                <OnboardingOption
                  key={goal}
                  label={goal}
                  selected={shortTermGoals.includes(goal)}
                  onClick={() => handleMultiSelect(goal, shortTermGoals, setShortTermGoals, 3)}
                  multiSelect
                />
              ))}
            </div>
          </div>
        );

      case 7:
        return (
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="text-2xl font-bold text-foreground">¿Cuáles son tus hobbies favoritos?</h2>
              <p className={`text-sm ${hobbies.length >= 5 ? 'text-orange-500 font-medium' : 'text-muted-foreground'}`}>
                {hobbies.length}/5 seleccionados {hobbies.length === 0 ? '(escoge al menos 1)' : ''}
              </p>
            </div>
            <div className="grid gap-3 max-h-[50vh] overflow-y-auto pr-2">
              {[
                "Salir de fiesta", "Leer libros", "Escuchar música", "Hacer ejercicio / gimnasio",
                "Correr / trotar", "Caminar largos trayectos", "Bailar", "Viajar", "Cocinar",
                "Ver series o películas", "Jugar videojuegos", "Meditar", "Pintar / dibujar",
                "Escribir", "Fotografiar", "Programar / proyectos personales", "Aprender temas nuevos",
                "Emprender / crear ideas", "Salir con amigos", "Citas / conocer gente",
                "Senderismo / naturaleza", "Deportes en equipo", "Deportes extremos",
                "Jardinería / plantas", "Tocar instrumentos", "Podcasts", "Juegos de mesa",
                "Yoga / pilates", "Voluntariado / ayudar a otros", "Diseño / manualidades",
                "Coleccionar cosas", "Crear contenido (videos, TikTok, etc.)"
              ].map((hobby) => (
                <OnboardingOption
                  key={hobby}
                  label={hobby}
                  selected={hobbies.includes(hobby)}
                  onClick={() => handleMultiSelect(hobby, hobbies, setHobbies, 5)}
                  multiSelect
                />
              ))}
            </div>
          </div>
        );

      case 8:
        return (
          <div className="space-y-6">
            <div className="space-y-2">
              <h2 className="text-2xl font-bold text-foreground">¿Qué te gustaría que tu Human conozca sobre tu historia emocional?</h2>
              <p className="text-muted-foreground">Esto es opcional pero ayuda a personalizar tu experiencia</p>
            </div>
            <Textarea
              value={emotionalHistory}
              onChange={(e) => setEmotionalHistory(e.target.value)}
              placeholder="Comparte lo que quieras..."
              className="min-h-[200px] text-base"
            />
          </div>
        );

      default:
        return null;
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1: return humanAge.length > 0;
      case 2: return humanGender.length > 0;
      case 3: return humanName.trim().length > 0;
      case 4: return lifeAxes.length > 0 && lifeAxes.length <= 3;
      case 5: return tenYearGoals.length > 0;
      case 6: return shortTermGoals.length > 0 && shortTermGoals.length <= 3;
      case 7: return hobbies.length > 0 && hobbies.length <= 5;
      case 8: return true; // Optional
      default: return false;
    }
  };

  // Show loading while checking onboarding status
  if (onboardingLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <BehumanLogo size={64} />
          <p className="text-muted-foreground">Cargando...</p>
        </div>
      </div>
    );
  }

  if (phase === "intro") {
    return <OnboardingIntro onComplete={() => setPhase("questions")} />;
  }

  if (phase === "complete") {
    return <OnboardingComplete humanName={humanName} />;
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Content */}
      <main className="flex-1 px-4 py-8 overflow-y-auto">
        <div className="max-w-lg mx-auto">
          {/* Logo */}
          <div className="flex justify-center mb-8">
            <BehumanLogo size={48} />
          </div>
          
          {/* Step content */}
          <div className="animate-fade-in">
            {renderStep()}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="sticky bottom-0 bg-background/95 backdrop-blur-sm border-t border-border px-4 py-4">
        <div className="max-w-lg mx-auto flex gap-3">
          {currentStep > 1 && (
            <Button
              variant="outline"
              onClick={handleBack}
              className="flex-1 py-6"
              disabled={saving}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Atrás
            </Button>
          )}
          <Button
            onClick={handleNext}
            disabled={!canProceed() || saving}
            className="flex-1 py-6"
          >
            {saving ? (
              "Guardando..."
            ) : currentStep === totalSteps ? (
              "Finalizar"
            ) : (
              "Continuar"
            )}
            {currentStep !== totalSteps && !saving && <ArrowRight className="w-4 h-4 ml-2" />}
          </Button>
        </div>
      </footer>
    </div>
  );
}
