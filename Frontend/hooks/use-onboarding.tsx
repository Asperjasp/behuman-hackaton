'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/hooks/use-auth'
import { OnboardingService } from '@/lib/onboarding-service'
import type { OnboardingProfile } from '@/types/onboarding'

export function useOnboarding() {
  const { user, loading: authLoading } = useAuth()
  const [profile, setProfile] = useState<OnboardingProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [hasCompleted, setHasCompleted] = useState(false)

  useEffect(() => {
    async function loadOnboarding() {
      if (authLoading) return

      if (!user) {
        setLoading(false)
        return
      }

      const { data } = await OnboardingService.getOnboarding(user.id)
      setProfile(data)
      setHasCompleted(data !== null)
      setLoading(false)
    }

    loadOnboarding()
  }, [user, authLoading])

  const refreshProfile = async () => {
    if (!user) return

    const { data } = await OnboardingService.getOnboarding(user.id)
    setProfile(data)
    setHasCompleted(data !== null)
  }

  return {
    profile,
    loading,
    hasCompleted,
    refreshProfile,
  }
}
