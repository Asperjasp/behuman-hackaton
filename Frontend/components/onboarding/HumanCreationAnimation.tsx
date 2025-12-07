import { useEffect, useState } from "react";
import BehumanLogo from "@/components/BehumanLogo";

interface HumanCreationAnimationProps {
  onComplete: () => void;
}

const HumanCreationAnimation = ({ onComplete }: HumanCreationAnimationProps) => {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 400),
      setTimeout(() => setPhase(2), 1200),
      setTimeout(() => setPhase(3), 2400),
      setTimeout(() => onComplete(), 4000),
    ];

    return () => timers.forEach(clearTimeout);
  }, [onComplete]);

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center px-6">
      {/* Central animation container */}
      <div className="relative">
        {/* DNA-like helix lines */}
        <div
          className={`absolute inset-0 transition-opacity duration-1000 ${
            phase >= 1 ? "opacity-100" : "opacity-0"
          }`}
        >
          <svg
            viewBox="0 0 200 200"
            className="w-64 h-64 -mt-8"
            style={{ transform: "translateX(-25%)" }}
          >
            <defs>
              <linearGradient id="helixGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity="0.2" />
                <stop offset="50%" stopColor="hsl(var(--primary))" stopOpacity="0.8" />
                <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity="0.2" />
              </linearGradient>
            </defs>
            {[0, 1, 2].map((i) => (
              <circle
                key={i}
                cx="100"
                cy="100"
                r={40 + i * 25}
                fill="none"
                stroke="url(#helixGradient)"
                strokeWidth="1"
                strokeDasharray="10 5"
                className="animate-spin"
                style={{
                  animationDuration: `${8 + i * 4}s`,
                  animationDirection: i % 2 === 0 ? "normal" : "reverse",
                }}
              />
            ))}
          </svg>
        </div>

        {/* Logo with morph effect */}
        <div
          className={`relative z-10 transition-all duration-1000 ease-out ${
            phase >= 1 ? "scale-100 opacity-100" : "scale-0 opacity-0"
          }`}
        >
          {/* Glow */}
          <div
            className={`absolute inset-0 blur-3xl transition-opacity duration-1000 ${
              phase >= 2 ? "opacity-50" : "opacity-0"
            }`}
          >
            <BehumanLogo size={100} />
          </div>
          
          <BehumanLogo
            size={100}
            className={`relative z-10 transition-transform duration-700 ${
              phase >= 2 ? "scale-110" : "scale-100"
            }`}
          />
        </div>
      </div>

      {/* Text content */}
      <div className="mt-12 text-center space-y-4">
        <h2
          className={`text-2xl font-bold text-foreground transition-all duration-700 ${
            phase >= 2 ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
          }`}
        >
          Creando tu Human
        </h2>
        <p
          className={`text-muted-foreground transition-all duration-700 delay-200 ${
            phase >= 2 ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
          }`}
        >
          Personalizando tu experiencia...
        </p>
      </div>

      {/* Progress dots */}
      <div
        className={`mt-10 flex gap-3 transition-opacity duration-500 ${
          phase >= 3 ? "opacity-100" : "opacity-0"
        }`}
      >
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className="w-3 h-3 rounded-full bg-primary/30 animate-pulse"
            style={{
              animationDelay: `${i * 200}ms`,
              backgroundColor: `hsl(var(--primary) / ${0.3 + i * 0.2})`,
            }}
          />
        ))}
      </div>
    </div>
  );
};

export default HumanCreationAnimation;
