"use client"

import { useConversation } from "@elevenlabs/react"
import { useState, useCallback, useEffect } from "react"

interface UseElevenLabsConversationOptions {
  volume?: number
}

interface UseElevenLabsConversationReturn {
  startSession: () => Promise<void>
  endSession: () => Promise<void>
  status: "connected" | "disconnected" | "connecting" | "disconnecting"
  isSpeaking: boolean
  micMuted: boolean
  error: string | null
  setVolume: (volume: number) => void
  setMuted: (muted: boolean) => void
  getInputVolume: () => number
  getOutputVolume: () => number
}

export function useElevenLabsConversation(
  options: UseElevenLabsConversationOptions = {}
): UseElevenLabsConversationReturn {
  const [error, setError] = useState<string | null>(null)

  const conversation = useConversation({
    onConnect: () => {
      console.log("🟢 ElevenLabs: Conectado")
      console.log(`🔊 Volume: ${options.volume ?? 1.0}`)

      // Explicitly set volume after connection
      const volumeToSet = options.volume ?? 1.0
      conversation.setVolume({ volume: volumeToSet })
      console.log(`🔊 Volume set to: ${volumeToSet}`)

      // Resume AudioContext if suspended (fixes browser autoplay policy issues)
      if (typeof window !== 'undefined') {
        const audioContext = (window as any).AudioContext || (window as any).webkitAudioContext
        if (audioContext) {
          const ctx = new audioContext()
          if (ctx.state === 'suspended') {
            ctx.resume().then(() => {
              console.log('✅ AudioContext resumed')
            }).catch((err: Error) => {
              console.error('❌ Failed to resume AudioContext:', err)
            })
          } else {
            console.log(`✅ AudioContext state: ${ctx.state}`)
          }
        }
      }

      setError(null)
    },
    onDisconnect: () => {
      console.log("🔴 ElevenLabs: Desconectado")
    },
    onMessage: (message) => {
      console.log("💬 ElevenLabs mensaje:", message)
    },
    onModeChange: (mode) => {
      console.log("🔄 Mode cambió a:", mode)
    },
    onStatusChange: (status) => {
      console.log("📊 Status cambió a:", status)
    },
    onError: (error) => {
      console.error("❌ ElevenLabs error:", error)
      const errorMessage = typeof error === "string"
        ? error
        : (error as any)?.message || "Error en la conversación"
      setError(errorMessage)
    },
  })

  // Monitor isSpeaking state to debug audio
  useEffect(() => {
    if (conversation.isSpeaking) {
      console.log("🔊 Agent is speaking")
    } else {
      console.log("🔇 Agent is not speaking")
    }
  }, [conversation.isSpeaking])

  const startSession = useCallback(async () => {
    try {
      setError(null)

      // Play a test beep to verify browser audio works
      // This helps bypass browser autoplay policy
      if (typeof window !== 'undefined') {
        try {
          const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
          const oscillator = audioContext.createOscillator()
          const gainNode = audioContext.createGain()

          oscillator.connect(gainNode)
          gainNode.connect(audioContext.destination)

          oscillator.frequency.value = 440
          gainNode.gain.value = 0.1

          oscillator.start()
          setTimeout(() => {
            oscillator.stop()
            console.log("✅ Browser audio test successful - audio system is working")
          }, 100)
        } catch (audioErr) {
          console.warn("⚠️ Browser audio test failed:", audioErr)
        }
      }

      // Get signed URL from our API
      const response = await fetch("/api/elevenlabs/signed-url")
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || "Error al obtener URL firmada")
      }

      const { signedUrl } = await response.json()

      // Start the conversation with the signed URL
      // The SDK will handle microphone permission internally
      await conversation.startSession({
        signedUrl,
        clientTools: {}
      })

      // Log conversation state for debugging
      console.log("Session started. Conversation state:", {
        status: conversation.status,
        isSpeaking: conversation.isSpeaking,
      })
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Error al iniciar la sesión"
      setError(errorMessage)
      console.error("Error starting session:", err)
      throw err
    }
  }, [conversation])

  const endSession = useCallback(async () => {
    try {
      await conversation.endSession()
      setError(null)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Error al finalizar la sesión"
      setError(errorMessage)
      console.error("Error ending session:", err)
      throw err
    }
  }, [conversation])

  const setVolume = useCallback((volume: number) => {
    conversation.setVolume({ volume })
  }, [conversation])

  const setMuted = useCallback((muted: boolean) => {
    // The ElevenLabs SDK may expose muting through the conversation object
    // Check if the method exists and call it
    if (typeof (conversation as any).setMicrophoneMuted === 'function') {
      (conversation as any).setMicrophoneMuted(muted)
    } else if (typeof (conversation as any).setInputMuted === 'function') {
      (conversation as any).setInputMuted(muted)
    } else {
      console.warn('⚠️ Mute control not available in current SDK version')
    }
  }, [conversation])

  return {
    startSession,
    endSession,
    status: conversation.status,
    isSpeaking: conversation.isSpeaking,
    micMuted: conversation.micMuted ?? false,
    error,
    setVolume,
    setMuted,
    getInputVolume: conversation.getInputVolume,
    getOutputVolume: conversation.getOutputVolume,
  }
}
