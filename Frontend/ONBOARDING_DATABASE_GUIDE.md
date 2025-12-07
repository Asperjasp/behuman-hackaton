# Onboarding Database Setup Guide

This guide explains how to store onboarding answers in Supabase for the behuman application.

## Overview

The onboarding collects 8 pieces of information:
1. Human age (single choice)
2. Human gender (single choice)
3. Human name (text input)
4. Life axes/priorities (up to 3 selections)
5. 10-year goals (multiple selections)
6. Short-term goals (up to 3 selections)
7. Hobbies (up to 5 selections)
8. Emotional history (optional long text)

## Database Schema Options

### Option 1: Single Table (Recommended)

Store all onboarding data in one table with JSONB arrays for multi-select fields.

**Pros:**
- Simple to query
- Easy to update all onboarding data at once
- Good for analytics (can use JSONB operators)
- Fast reads for displaying user profile

**Cons:**
- Less normalized (but fine for this use case)

### Option 2: Normalized Tables

Separate tables for each multi-select field with junction tables.

**Pros:**
- Fully normalized
- Easy to add/remove individual selections
- Good for complex queries on specific categories

**Cons:**
- More complex queries (requires joins)
- More tables to manage
- Overkill for this use case

## Recommended Schema (Option 1)

```sql
-- Create the onboarding_profiles table
CREATE TABLE public.onboarding_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Human characteristics
  human_name VARCHAR(100) NOT NULL,
  human_age VARCHAR(50) NOT NULL,
  human_gender VARCHAR(50) NOT NULL,

  -- User goals and preferences (stored as JSONB arrays)
  life_axes JSONB NOT NULL DEFAULT '[]'::jsonb,
  ten_year_goals JSONB NOT NULL DEFAULT '[]'::jsonb,
  short_term_goals JSONB NOT NULL DEFAULT '[]'::jsonb,
  hobbies JSONB NOT NULL DEFAULT '[]'::jsonb,

  -- Optional emotional history
  emotional_history TEXT,

  -- Metadata
  completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Ensure one profile per user
  CONSTRAINT unique_user_onboarding UNIQUE(user_id)
);

-- Create index for faster user lookups
CREATE INDEX idx_onboarding_profiles_user_id ON public.onboarding_profiles(user_id);

-- Enable Row Level Security
ALTER TABLE public.onboarding_profiles ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only read their own onboarding data
CREATE POLICY "Users can view their own onboarding profile"
  ON public.onboarding_profiles
  FOR SELECT
  USING (auth.uid() = user_id);

-- Policy: Users can insert their own onboarding data
CREATE POLICY "Users can create their own onboarding profile"
  ON public.onboarding_profiles
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own onboarding data
CREATE POLICY "Users can update their own onboarding profile"
  ON public.onboarding_profiles
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Policy: Users can delete their own onboarding data
CREATE POLICY "Users can delete their own onboarding profile"
  ON public.onboarding_profiles
  FOR DELETE
  USING (auth.uid() = user_id);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at on every update
CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON public.onboarding_profiles
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();
```

## TypeScript Types

Create `types/onboarding.ts`:

```typescript
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
```

## Database Service

Create `lib/onboarding-service.ts`:

```typescript
import { supabase } from '@/lib/supabase'
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

      if (error) throw error

      return { data: profile, error: null }
    } catch (error) {
      console.error('Error saving onboarding:', error)
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
        throw error
      }

      return { data, error: null }
    } catch (error) {
      console.error('Error fetching onboarding:', error)
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
```

## Updated Onboarding Page

Update `app/onboarding/page.tsx` to save data:

```typescript
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { OnboardingService } from "@/lib/onboarding-service";
import { useToast } from "@/hooks/use-toast";
// ... other imports

export default function OnboardingPage() {
  const router = useRouter();
  const { user } = useAuth();
  const { toast } = useToast();
  const [saving, setSaving] = useState(false);

  // ... existing state variables

  const handleNext = async () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
    } else {
      // Last step - save to database
      await handleComplete();
    }
  };

  const handleComplete = async () => {
    if (!user) {
      toast({
        title: "Error",
        description: "Debes iniciar sesión para completar el onboarding",
        variant: "destructive",
      });
      router.push("/login");
      return;
    }

    setSaving(true);

    try {
      const { error } = await OnboardingService.saveOnboarding(user.id, {
        human_name: humanName,
        human_age: humanAge,
        human_gender: humanGender,
        life_axes: lifeAxes,
        ten_year_goals: tenYearGoals,
        short_term_goals: shortTermGoals,
        hobbies: hobbies,
        emotional_history: emotionalHistory,
      });

      if (error) {
        throw error;
      }

      toast({
        title: "¡Onboarding completado!",
        description: "Tu Human ha sido creado exitosamente",
      });

      setPhase("complete");
    } catch (error) {
      console.error("Error saving onboarding:", error);
      toast({
        title: "Error",
        description: "No se pudo guardar tu información. Intenta nuevamente.",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  // ... rest of component

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* ... existing content ... */}

      <footer className="sticky bottom-0 bg-background/95 backdrop-blur-sm border-t border-border px-4 py-4">
        <div className="max-w-lg mx-auto flex gap-3">
          {currentStep > 1 && (
            <Button
              variant="outline"
              onClick={handleBack}
              className="flex-1 py-6"
              disabled={saving}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Atrás
            </Button>
          )}
          <Button
            onClick={handleNext}
            disabled={!canProceed() || saving}
            className="flex-1 py-6"
          >
            {saving ? (
              <>Guardando...</>
            ) : currentStep === totalSteps ? (
              "Finalizar"
            ) : (
              <>
                Continuar
                <ArrowRight className="w-4 h-4 ml-2" />
              </>
            )}
          </Button>
        </div>
      </footer>
    </div>
  );
}
```

## Checking Onboarding Status

Create a hook `hooks/use-onboarding.tsx`:

```typescript
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
```

## Protecting Routes (Redirect if Onboarding Not Complete)

Create `app/app/page.tsx` with onboarding check:

```typescript
'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useOnboarding } from '@/hooks/use-onboarding'

export default function AppPage() {
  const router = useRouter()
  const { hasCompleted, loading } = useOnboarding()

  useEffect(() => {
    if (!loading && !hasCompleted) {
      router.push('/onboarding')
    }
  }, [hasCompleted, loading, router])

  if (loading) {
    return <div>Loading...</div>
  }

  if (!hasCompleted) {
    return null // Will redirect
  }

  return (
    <div>
      {/* Your app content */}
    </div>
  )
}
```

## Querying Data (Advanced Examples)

### Get users with specific hobbies:

```typescript
const { data, error } = await supabase
  .from('onboarding_profiles')
  .select('*')
  .contains('hobbies', ['Leer libros', 'Escribir'])
```

### Get users with specific life axes:

```typescript
const { data, error } = await supabase
  .from('onboarding_profiles')
  .select('*')
  .contains('life_axes', ['Familia'])
```

### Count users by age group:

```sql
SELECT human_age, COUNT(*) as count
FROM onboarding_profiles
GROUP BY human_age
ORDER BY count DESC;
```

### Get most popular hobbies:

```sql
SELECT
  jsonb_array_elements_text(hobbies) as hobby,
  COUNT(*) as count
FROM onboarding_profiles
GROUP BY hobby
ORDER BY count DESC
LIMIT 10;
```

## Migration Steps

1. **Run SQL in Supabase:**
   - Go to Supabase dashboard > SQL Editor
   - Copy and paste the schema SQL
   - Execute it

2. **Create TypeScript files:**
   - `types/onboarding.ts`
   - `lib/onboarding-service.ts`
   - `hooks/use-onboarding.tsx`

3. **Update onboarding page:**
   - Add save functionality to `app/onboarding/page.tsx`

4. **Test the flow:**
   - Complete onboarding
   - Check Supabase dashboard to verify data was saved
   - Test retrieval in app

## Data Privacy Considerations

- **JSONB arrays** store exact user selections
- **Row Level Security (RLS)** ensures users can only access their own data
- **Emotional history** is optional and can contain sensitive info
- Consider adding a privacy policy checkbox before saving
- Consider encrypting `emotional_history` field for extra security

## Future Enhancements

1. **Add versioning:**
   ```sql
   ALTER TABLE onboarding_profiles ADD COLUMN version INTEGER DEFAULT 1;
   ```

2. **Track partial completion:**
   ```sql
   ALTER TABLE onboarding_profiles ADD COLUMN last_completed_step INTEGER;
   ```

3. **Store timestamps per step:**
   ```sql
   ALTER TABLE onboarding_profiles ADD COLUMN step_timestamps JSONB;
   ```

4. **Analytics table for selections:**
   ```sql
   CREATE TABLE onboarding_selections (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     profile_id UUID REFERENCES onboarding_profiles(id),
     category VARCHAR(50),
     selection VARCHAR(200),
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   ```

## Testing Queries

After setting up, test with these queries in Supabase SQL Editor:

```sql
-- View all onboarding profiles
SELECT * FROM onboarding_profiles;

-- Get profile with user email
SELECT
  op.*,
  au.email
FROM onboarding_profiles op
JOIN auth.users au ON au.id = op.user_id;

-- Count profiles by human age
SELECT human_age, COUNT(*)
FROM onboarding_profiles
GROUP BY human_age;

-- Find users interested in specific goals
SELECT human_name, ten_year_goals
FROM onboarding_profiles
WHERE ten_year_goals @> '["Tener mi propia empresa"]'::jsonb;
```

## Troubleshooting

**Error: "new row violates row-level security policy"**
- Make sure user is authenticated
- Verify `auth.uid()` matches `user_id` in insert

**Error: "duplicate key value violates unique constraint"**
- User already has a profile
- Use `upsert()` instead of `insert()`

**JSONB arrays not working:**
- Ensure you're passing arrays: `['item1', 'item2']`
- Not strings: `"['item1', 'item2']"`

**Can't query JSONB fields:**
- Use `@>` operator for contains
- Use `jsonb_array_elements_text()` for array elements
- Cast to jsonb: `'["item"]'::jsonb`
