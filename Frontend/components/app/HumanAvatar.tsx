import { cn } from "@/lib/utils";

type CallState = "idle" | "connecting" | "in-call" | "ending";

interface HumanAvatarProps {
  state: CallState;
  gender?: string;
  isSpeaking?: boolean;
  className?: string;
}

const HumanAvatar = ({ state, isSpeaking = false, className }: HumanAvatarProps) => {
  const isActive = state === "in-call";
  const isConnecting = state === "connecting";

  return (
    <div className={cn("relative w-full aspect-[3/4] max-h-[60vh] rounded-3xl overflow-hidden bg-gradient-to-b from-muted/50 to-muted", className)}>
      {/* Background gradient based on state */}
      <div className={cn(
        "absolute inset-0 transition-all duration-1000",
        isActive && "bg-gradient-to-b from-primary/10 via-transparent to-primary/5",
        isConnecting && "bg-gradient-to-b from-primary/20 via-transparent to-primary/10"
      )} />

      {/* Animated rings when agent is speaking */}
      {isActive && isSpeaking && (
        <div className="absolute inset-0 flex items-center justify-center">
          {[1, 2, 3].map((ring) => (
            <div
              key={ring}
              className="absolute rounded-full border border-primary/30 animate-ping"
              style={{
                width: `${ring * 80}px`,
                height: `${ring * 80}px`,
                animationDuration: `${1.5 + ring * 0.5}s`,
                animationDelay: `${ring * 0.2}s`,
              }}
            />
          ))}
        </div>
      )}

      {/* Avatar silhouette */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className={cn(
          "relative transition-transform duration-700",
          isActive && "scale-105",
          isConnecting && "animate-pulse"
        )}>
          {/* Head */}
          <div className={cn(
            "w-24 h-24 rounded-full bg-gradient-to-b from-primary/40 to-primary/60 mb-2 mx-auto transition-all duration-500",
            isActive && "shadow-[0_0_60px_rgba(var(--primary),0.4)]"
          )} />

          {/* Body */}
          <div className="w-32 h-40 rounded-t-full bg-gradient-to-b from-primary/30 to-primary/50 mx-auto" />

          {/* Breathing animation overlay */}
          <div className={cn(
            "absolute inset-0 rounded-full",
            state === "idle" && "animate-[breathing_4s_ease-in-out_infinite]"
          )} />
        </div>
      </div>

      {/* Connecting overlay */}
      {isConnecting && (
        <div className="absolute inset-0 flex items-center justify-center bg-background/30 backdrop-blur-sm">
          <div className="flex flex-col items-center gap-4">
            <div className="w-16 h-16 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
            <p className="text-foreground font-medium">Conectando...</p>
          </div>
        </div>
      )}

      {/* Audio waveform when agent is speaking */}
      {isActive && isSpeaking && (
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex items-end gap-1 h-8">
          {[8, 16, 24, 20, 28, 16, 12].map((height, i) => (
            <div
              key={i}
              className="w-1 bg-primary/60 rounded-full animate-[waveform_0.8s_ease-in-out_infinite]"
              style={{
                animationDelay: `${i * 0.1}s`,
                height: `${height}px`,
              }}
            />
          ))}
        </div>
      )}

      <style>{`
        @keyframes breathing {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.02); opacity: 0.9; }
        }
        @keyframes waveform {
          0%, 100% { height: 8px; }
          50% { height: 24px; }
        }
      `}</style>
    </div>
  );
};

export default HumanAvatar;
