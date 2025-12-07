import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

type CallState = "idle" | "connecting" | "in-call" | "ending";

interface CallStatusProps {
  humanName: string;
  callState: CallState;
  className?: string;
}

const CallStatus = ({ humanName, callState, className }: CallStatusProps) => {
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (callState === "in-call") {
      interval = setInterval(() => {
        setDuration((prev) => prev + 1);
      }, 1000);
    } else {
      setDuration(0);
    }

    return () => clearInterval(interval);
  }, [callState]);

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const getStatusText = () => {
    switch (callState) {
      case "connecting":
        return "Conectando...";
      case "in-call":
        return formatDuration(duration);
      case "ending":
        return "Finalizando...";
      default:
        return "Toca para llamar";
    }
  };

  return (
    <div className={cn("text-center", className)}>
      <h1 className="text-2xl font-bold text-foreground">{humanName}</h1>
      <div className="flex items-center justify-center gap-2 mt-1">
        {callState === "in-call" && (
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
        )}
        {callState === "connecting" && (
          <span className="w-2 h-2 rounded-full bg-primary animate-ping" />
        )}
        <p className={cn(
          "text-sm transition-colors",
          callState === "in-call" ? "text-green-500" : "text-muted-foreground"
        )}>
          {getStatusText()}
        </p>
      </div>
    </div>
  );
};

export default CallStatus;
