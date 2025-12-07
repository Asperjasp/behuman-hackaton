import { NextResponse } from "next/server"
import { getSupabaseServerClient } from "@/utils/supabase/server"

export async function GET() {
  try {
    // Get authenticated user
    const supabase = await getSupabaseServerClient()
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser()

    if (authError || !user) {
      return NextResponse.json({ error: "No autenticado" }, { status: 401 })
    }

    // Query agents table to get the user's elevenlabs_agent_id
    const { data: agent, error: agentError } = await supabase
      .from("agents")
      .select("elevenlabs_agent_id")
      .eq("user_id", user.id)
      .single()

    if (agentError || !agent) {
      return NextResponse.json({ error: "No se encontró el agente. Por favor completa el onboarding." }, { status: 404 })
    }

    if (!agent.elevenlabs_agent_id) {
      return NextResponse.json({ error: "El agente no tiene un ID de ElevenLabs." }, { status: 400 })
    }

    // Call ElevenLabs API to get signed URL
    const elevenLabsApiKey = process.env.ELEVENLABS_API_KEY
    if (!elevenLabsApiKey) {
      return NextResponse.json({ error: "Configuración del servidor faltante" }, { status: 500 })
    }

    const response = await fetch(
      `https://api.elevenlabs.io/v1/convai/conversation/get-signed-url?agent_id=${agent.elevenlabs_agent_id}`,
      {
        method: "GET",
        headers: {
          "xi-api-key": elevenLabsApiKey,
        },
      }
    )

    if (!response.ok) {
      const errorText = await response.text()
      console.error("ElevenLabs API error:", errorText)
      return NextResponse.json({ error: "Error al obtener URL firmada de ElevenLabs" }, { status: response.status })
    }

    const data = await response.json()
    return NextResponse.json({ signedUrl: data.signed_url })
  } catch (error) {
    console.error("Error in signed-url route:", error)
    return NextResponse.json({ error: "Error interno del servidor" }, { status: 500 })
  }
}
