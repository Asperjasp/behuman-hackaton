"use client";

import { useState, useEffect } from "react";
import { ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import CallControls from "@/components/app/CallControls";
import CallStatus from "@/components/app/CallStatus";
import HumanAvatar from "@/components/app/HumanAvatar";
import { useOnboarding } from "@/hooks/use-onboarding";
import { useElevenLabsConversation } from "@/hooks/use-elevenlabs-conversation";
import { toast } from "sonner";

type CallState = "idle" | "connecting" | "in-call" | "ending";

export default function AppPage() {
  const router = useRouter();
  const { hasCompleted, loading, profile } = useOnboarding();
  const [callState, setCallState] = useState<CallState>("idle");
  const [isMuted, setIsMuted] = useState(false);
  const [isCameraOn, setIsCameraOn] = useState(true);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [volume, setVolumeState] = useState(1.0); // 0.0 to 1.0 - setVolumeState reserved for future volume controls

  // Pass volume state to the hook for controlled audio
  const {
    startSession,
    endSession,
    status,
    isSpeaking,
    error,
    micMuted,
    setVolume,
    setMuted,
    getInputVolume,
    getOutputVolume
  } = useElevenLabsConversation({
    volume
  });

  const humanName = profile?.human_name || "Human";

  useEffect(() => {
    if (!loading && !hasCompleted) {
      router.push('/onboarding');
    }
  }, [hasCompleted, loading, router]);

  // Sync callState with conversation status
  useEffect(() => {
    if (status === "connecting") {
      setCallState("connecting");
    } else if (status === "connected") {
      setCallState("in-call");
    } else if (status === "disconnected" && callState !== "idle") {
      setCallState("idle");
    }
  }, [status, callState]);

  // Show error toast when there's an error
  useEffect(() => {
    if (error) {
      toast.error(error);
    }
  }, [error]);

  // Debug: Log microphone state changes
  useEffect(() => {
    if (callState === "in-call") {
      console.log(`🎤 Microphone: ${micMuted ? "MUTED" : "UNMUTED"}`);
      console.log(`🔊 Volume: ${volume}`);
      console.log(`📊 Input volume: ${getInputVolume()}`);
      console.log(`📊 Output volume: ${getOutputVolume()}`);
    }
  }, [micMuted, volume, callState, getInputVolume, getOutputVolume]);

  // Debug: Periodic audio level monitoring
  useEffect(() => {
    if (callState !== "in-call") return;

    const interval = setInterval(() => {
      const inputVol = getInputVolume();
      const outputVol = getOutputVolume();
      if (inputVol > 0 || outputVol > 0) {
        console.log(`📊 Audio levels - Input: ${inputVol.toFixed(2)}, Output: ${outputVol.toFixed(2)}`);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [callState, getInputVolume, getOutputVolume]);

  const handleCall = async () => {
    try {
      setCallState("connecting");

      // Check microphone permissions before starting
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log("✅ Microphone permission granted");
        console.log("🎤 Audio tracks:", stream.getAudioTracks().map(t => ({
          label: t.label,
          enabled: t.enabled,
          muted: t.muted
        })));
        // Stop the test stream - ElevenLabs SDK will create its own
        stream.getTracks().forEach(track => track.stop());
      } catch (permErr) {
        console.error("❌ Microphone permission denied:", permErr);
        toast.error("Por favor permite el acceso al micrófono para continuar");
        setCallState("idle");
        return;
      }

      await startSession();

      // Explicitly set volume after session starts
      setTimeout(() => {
        setVolume(volume);
        console.log(`🔊 Volume explicitly set to ${volume} after session start`);
      }, 500);
    } catch (err) {
      console.error("Error starting call:", err);
      setCallState("idle");
    }
  };

  const handleHangUp = async () => {
    try {
      setCallState("ending");
      await endSession();
      setTimeout(() => {
        setCallState("idle");
      }, 500);
    } catch (err) {
      console.error("Error ending call:", err);
      setCallState("idle");
    }
  };

  const handleToggleMute = () => {
    const newMutedState = !isMuted;
    setIsMuted(newMutedState);
    setMuted(newMutedState);
  };

  const handleToggleCamera = () => {
    setIsCameraOn(!isCameraOn);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <p className="text-muted-foreground">Cargando...</p>
      </div>
    );
  }

  if (!hasCompleted) {
    return null; // Will redirect
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between p-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push("/")}
          className="text-muted-foreground"
        >
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <CallStatus
          humanName={humanName}
          callState={callState}
        />
        <div className="w-10" /> {/* Spacer for centering */}
      </header>

      {/* Main content - Human Avatar */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 pb-4">
        <HumanAvatar
          state={callState}
          gender={profile?.human_gender}
          isSpeaking={isSpeaking}
          className="w-full max-w-sm"
        />
      </main>

      {/* Call controls */}
      <footer className="pb-8 pt-4">
        <CallControls
          callState={callState}
          isMuted={isMuted}
          isCameraOn={isCameraOn}
          onCall={handleCall}
          onHangUp={handleHangUp}
          onToggleMute={handleToggleMute}
          onToggleCamera={handleToggleCamera}
        />
      </footer>
    </div>
  );
}
