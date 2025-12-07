import { getSupabaseBrowserClient } from '@/utils/supabase/client'
import type { OnboardingProfile, OnboardingFormData } from '@/types/onboarding'

export class OnboardingService {
  /**
   * Save onboarding data for a user (creates or updates)
   */
  static async saveOnboarding(
    userId: string,
    data: OnboardingFormData
  ): Promise<{ data: OnboardingProfile | null; error: Error | null }> {
    try {
      const supabase = getSupabaseBrowserClient()

      // Check if Supabase client is properly configured
      if (!process.env.NEXT_PUBLIC_SUPABASE_URL || !process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
        const configError = new Error('Supabase configuration missing. Please check NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in .env.local')
        console.error('Error saving onboarding:', configError.message)
        return { data: null, error: configError }
      }

      const { data: profile, error } = await supabase
        .from('onboarding_profiles')
        .upsert({
          user_id: userId,
          human_name: data.human_name,
          human_age: data.human_age,
          human_gender: data.human_gender,
          life_axes: data.life_axes,
          ten_year_goals: data.ten_year_goals,
          short_term_goals: data.short_term_goals,
          hobbies: data.hobbies,
          emotional_history: data.emotional_history || null,
          updated_at: new Date().toISOString(),
        })
        .select()
        .single()

      if (error) {
        // Log detailed error information
        console.error('Supabase error saving onboarding:', {
          code: error.code,
          message: error.message,
          details: error.details,
          hint: error.hint,
          fullError: error
        })
        throw error
      }

      return { data: profile, error: null }
    } catch (error) {
      // Enhanced error logging
      if (error && typeof error === 'object') {
        console.error('Error saving onboarding:', {
          message: (error as any).message || 'Unknown error',
          code: (error as any).code,
          details: (error as any).details,
          error: error
        })
      } else {
        console.error('Error saving onboarding:', error)
      }
      return { data: null, error: error as Error }
    }
  }

  /**
   * Get onboarding data for a user
   */
  static async getOnboarding(
    userId: string
  ): Promise<{ data: OnboardingProfile | null; error: Error | null }> {
    try {
      const supabase = getSupabaseBrowserClient()

      // Check if Supabase client is properly configured
      if (!process.env.NEXT_PUBLIC_SUPABASE_URL || !process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
        const configError = new Error('Supabase configuration missing. Please check NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in .env.local')
        console.error('Error fetching onboarding:', configError.message)
        return { data: null, error: configError }
      }

      const { data, error } = await supabase
        .from('onboarding_profiles')
        .select('*')
        .eq('user_id', userId)
        .single()

      if (error) {
        // If no profile exists, return null without error
        if (error.code === 'PGRST116') {
          return { data: null, error: null }
        }

        // Log detailed error information
        console.error('Supabase error fetching onboarding:', {
          code: error.code,
          message: error.message,
          details: error.details,
          hint: error.hint,
          fullError: error
        })

        throw error
      }

      return { data, error: null }
    } catch (error) {
      // Enhanced error logging
      if (error && typeof error === 'object') {
        console.error('Error fetching onboarding:', {
          message: (error as any).message || 'Unknown error',
          code: (error as any).code,
          details: (error as any).details,
          error: error
        })
      } else {
        console.error('Error fetching onboarding:', error)
      }
      return { data: null, error: error as Error }
    }
  }

  /**
   * Check if user has completed onboarding
   */
  static async hasCompletedOnboarding(userId: string): Promise<boolean> {
    const { data } = await this.getOnboarding(userId)
    return data !== null
  }

  /**
   * Delete onboarding data (for testing or user reset)
   */
  static async deleteOnboarding(
    userId: string
  ): Promise<{ error: Error | null }> {
    try {
      const supabase = getSupabaseBrowserClient()
      const { error } = await supabase
        .from('onboarding_profiles')
        .delete()
        .eq('user_id', userId)

      if (error) throw error

      return { error: null }
    } catch (error) {
      console.error('Error deleting onboarding:', error)
      return { error: error as Error }
    }
  }

  /**
   * Get statistics about user's selections (for analytics)
   */
  static async getOnboardingStats(userId: string) {
    const { data } = await this.getOnboarding(userId)

    if (!data) return null

    return {
      totalLifeAxes: data.life_axes.length,
      totalTenYearGoals: data.ten_year_goals.length,
      totalShortTermGoals: data.short_term_goals.length,
      totalHobbies: data.hobbies.length,
      hasEmotionalHistory: !!data.emotional_history,
      completedAt: data.completed_at,
    }
  }
}
