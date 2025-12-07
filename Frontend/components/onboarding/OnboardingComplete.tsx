"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import BehumanLogo from "@/components/BehumanLogo";

interface OnboardingCompleteProps {
  humanName: string;
}

const OnboardingComplete = ({ humanName }: OnboardingCompleteProps) => {
  const router = useRouter();
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 300),
      setTimeout(() => setPhase(2), 1200),
      setTimeout(() => setPhase(3), 2200),
      setTimeout(() => setPhase(4), 3200),
      setTimeout(() => router.push("/app"), 5500),
    ];

    return () => timers.forEach(clearTimeout);
  }, [router]);

  return (
    <div className="fixed inset-0 bg-background flex flex-col items-center justify-center z-50 overflow-hidden">
      {/* Background radial lines */}
      <div
        className={`absolute inset-0 transition-opacity duration-1000 ${
          phase >= 2 ? "opacity-30" : "opacity-0"
        }`}
      >
        {[...Array(12)].map((_, i) => (
          <div
            key={i}
            className="absolute top-1/2 left-1/2 w-0.5 h-[150vh] bg-gradient-to-b from-primary/0 via-primary to-primary/0 origin-top"
            style={{
              transform: `translate(-50%, -50%) rotate(${i * 30}deg)`,
            }}
          />
        ))}
      </div>

      {/* Concentric circles */}
      <div className="absolute inset-0 flex items-center justify-center">
        {[1, 2, 3].map((ring) => (
          <div
            key={ring}
            className={`absolute rounded-full border border-primary/20 transition-all duration-1000 ease-out ${
              phase >= 2 ? "opacity-100 scale-100" : "opacity-0 scale-0"
            }`}
            style={{
              width: `${ring * 200}px`,
              height: `${ring * 200}px`,
              transitionDelay: `${ring * 200}ms`,
            }}
          />
        ))}
      </div>

      {/* Logo morphing animation */}
      <div className="relative z-10">
        {/* Outer glow pulsing */}
        <div
          className={`absolute inset-0 transition-all duration-700 ${
            phase >= 1 ? "opacity-100" : "opacity-0"
          }`}
        >
          <div className="absolute -inset-8 bg-primary/20 rounded-full blur-3xl animate-pulse" />
        </div>

        {/* Logo with scale and rotation */}
        <div
          className={`transition-all duration-1000 ease-out ${
            phase >= 1 ? "scale-100 rotate-0 opacity-100" : "scale-50 -rotate-180 opacity-0"
          }`}
        >
          <div
            className={`transition-all duration-700 delay-500 ${
              phase >= 3 ? "scale-110" : "scale-100"
            }`}
          >
            <BehumanLogo
              size={140}
              className={`drop-shadow-2xl ${phase >= 2 ? "" : ""}`}
            />
          </div>
        </div>

        {/* Particle effects */}
        {phase >= 2 && (
          <div className="absolute inset-0">
            {[...Array(8)].map((_, i) => (
              <div
                key={i}
                className="absolute top-1/2 left-1/2 w-2 h-2 rounded-full bg-primary animate-ping"
                style={{
                  transform: `translate(-50%, -50%) rotate(${i * 45}deg) translateY(-60px)`,
                  animationDelay: `${i * 100}ms`,
                  animationDuration: "1.5s",
                }}
              />
            ))}
          </div>
        )}
      </div>

      {/* Text reveals */}
      <div className="relative z-10 mt-12 text-center space-y-4">
        <p
          className={`text-xl text-muted-foreground transition-all duration-700 ${
            phase >= 3 ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"
          }`}
        >
          Tu Human está listo
        </p>
        <h1
          className={`text-4xl font-bold text-primary transition-all duration-700 delay-200 ${
            phase >= 3 ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"
          }`}
        >
          {humanName || "Human"}
        </h1>
        <p
          className={`text-lg text-foreground transition-all duration-700 delay-500 ${
            phase >= 4 ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"
          }`}
        >
          Bienvenido a behuman
        </p>
      </div>

      {/* Loading bar at bottom */}
      <div
        className={`absolute bottom-12 left-1/2 -translate-x-1/2 w-48 h-1 bg-muted rounded-full overflow-hidden transition-opacity duration-500 ${
          phase >= 4 ? "opacity-100" : "opacity-0"
        }`}
      >
        <div className="h-full bg-primary animate-[loading_1.5s_ease-in-out_forwards]" />
      </div>

      <style>{`
        @keyframes loading {
          from { width: 0%; }
          to { width: 100%; }
        }
      `}</style>
    </div>
  );
};

export default OnboardingComplete;
