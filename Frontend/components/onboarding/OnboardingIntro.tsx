import { useEffect, useState } from "react";
import BehumanLogo from "@/components/BehumanLogo";

interface OnboardingIntroProps {
  onComplete: () => void;
}

const OnboardingIntro = ({ onComplete }: OnboardingIntroProps) => {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 500),
      setTimeout(() => setPhase(2), 1500),
      setTimeout(() => setPhase(3), 2500),
      setTimeout(() => onComplete(), 4000),
    ];

    return () => timers.forEach(clearTimeout);
  }, [onComplete]);

  return (
    <div className="fixed inset-0 bg-background flex flex-col items-center justify-center z-50">
      {/* Logo container with pulse animation */}
      <div
        className={`transition-all duration-700 ease-out ${
          phase >= 1 ? "opacity-100 scale-100" : "opacity-0 scale-75"
        }`}
      >
        <div className="relative">
          {/* Glow effect */}
          <div
            className={`absolute inset-0 blur-2xl transition-opacity duration-1000 ${
              phase >= 2 ? "opacity-40" : "opacity-0"
            }`}
          >
            <BehumanLogo size={120} className="text-primary" />
          </div>
          
          {/* Main logo with pulse */}
          <BehumanLogo
            size={120}
            className={`relative z-10 ${phase >= 1 ? "animate-pulse" : ""}`}
          />
        </div>
      </div>

      {/* Text content */}
      <div className="mt-10 text-center space-y-3">
        <h1
          className={`text-3xl font-bold text-foreground transition-all duration-700 delay-300 ${
            phase >= 2 ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
          }`}
        >
          Vamos a crear
        </h1>
        <p
          className={`text-4xl font-bold text-primary transition-all duration-700 delay-500 ${
            phase >= 2 ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
          }`}
        >
          tu Human
        </p>
      </div>

      {/* Animated dots */}
      <div
        className={`mt-12 flex gap-2 transition-opacity duration-500 ${
          phase >= 3 ? "opacity-100" : "opacity-0"
        }`}
      >
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="w-2 h-2 rounded-full bg-primary animate-bounce"
            style={{ animationDelay: `${i * 150}ms` }}
          />
        ))}
      </div>
    </div>
  );
};

export default OnboardingIntro;
