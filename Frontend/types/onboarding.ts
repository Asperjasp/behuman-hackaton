export interface OnboardingProfile {
  id: string
  user_id: string
  human_name: string
  human_age: string
  human_gender: string
  life_axes: string[]
  ten_year_goals: string[]
  short_term_goals: string[]
  hobbies: string[]
  emotional_history: string | null
  completed_at: string
  updated_at: string
}

export interface OnboardingFormData {
  human_name: string
  human_age: string
  human_gender: string
  life_axes: string[]
  ten_year_goals: string[]
  short_term_goals: string[]
  hobbies: string[]
  emotional_history: string
}
