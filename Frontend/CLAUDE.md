# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**behuman** is a personal AI companion application built with Next.js 16 and React 19. The app provides video call interactions with a customizable AI "Human" companion. Users go through an onboarding flow to configure their Human's personality, then can make video calls for meaningful conversations.

## Commands

### Development
```bash
npm run dev       # Start development server at localhost:3000
npm run build     # Build production bundle
npm run start     # Start production server
npm run lint      # Run ESLint
```

### Environment Setup
Create `.env.local` with required Supabase credentials:
```
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

## Architecture

### Tech Stack
- **Next.js 16** with App Router (React 19.2.0)
- **TypeScript** with strict mode enabled
- **Tailwind CSS v4** with custom design system
- **Supabase** for authentication and backend (`@supabase/ssr` for SSR support)
- **React Query** (TanStack Query) for async state management
- **shadcn/ui** with Radix UI primitives (New York style)

### Application Flow

1. **Root Layout** (`app/layout.tsx`): Wraps all pages with providers in this order:
   - `QueryProvider` (React Query client)
   - `AuthProvider` (Supabase auth context)
   - `TooltipProvider` (Radix UI)
   - `Toaster` (toast notifications)

2. **Authentication**: Managed via `hooks/use-auth.tsx` which exposes:
   - `user`, `session`, `loading` state
   - `signIn(email, password)`, `signUp(email, password, metadata)`, `signOut()` methods
   - Must be used within `AuthProvider`

3. **User Journey**:
   - `/register` → `/login` → `/onboarding` → `/app` (main application)
   - Onboarding collects: Human age, gender, name, life axes, goals (10-year & short-term), hobbies, emotional history
   - Main app provides video call interface with call controls

### Supabase Client Architecture

**IMPORTANT**: There are THREE separate Supabase client instances:

1. **Browser Client** (`utils/supabase/client.ts`):
   - Singleton pattern with memoization
   - Use in client components only
   - Access via `getSupabaseBrowserClient()`

2. **Server Client** (`utils/supabase/server.ts`):
   - For Server Components and Server Actions
   - Handles cookie-based session management
   - Access via `await getSupabaseServerClient()`

3. **Legacy Client** (`lib/supabase.ts` - if it exists):
   - Check if this exists; if so, migrate to the utils/supabase clients

**NEVER** import a client-side Supabase instance in Server Components or vice versa.

### Design System

Located in `app/globals.css`:
- **All colors MUST be HSL** (design system rule)
- Uses CSS custom properties with `--` prefix
- Supports light/dark mode via `.dark` class
- Custom theme variables for radius (sm, md, lg, xl)
- Primary color: `20 90% 55%` (warm orange)
- Warm color palette with beige/cream backgrounds
- Uses `tw-animate-css` for animations

### Path Aliases

Configured in `tsconfig.json`:
- `@/*` → Root directory
- Common patterns:
  - `@/components/ui/*` - shadcn/ui components
  - `@/components/app/*` - App-specific components
  - `@/components/onboarding/*` - Onboarding flow components
  - `@/hooks/*` - Custom React hooks
  - `@/lib/*` - Utility functions
  - `@/utils/*` - Helper utilities

### Styling Conventions

- Use `cn()` utility from `@/lib/utils` to merge Tailwind classes
- Component variants use `class-variance-authority` (cva)
- Prefer Tailwind utilities over custom CSS
- Mobile-first responsive design
- Use `use-mobile.tsx` hook for responsive behavior

### Key Patterns

1. **Client Components**: Mark with `"use client"` directive
   - Required for: hooks, event handlers, browser APIs, context consumers
   - All pages under `/app` are currently client components

2. **Multi-step Forms**: See `app/onboarding/page.tsx` for reference
   - Phase-based state machine (`intro` → `questions` → `complete`)
   - Step validation with `canProceed()` function
   - Multi-select with max item limits

3. **Component Structure**:
   - UI components in `/components/ui` (shadcn pattern)
   - Feature components in `/components/[feature-name]`
   - Shared components in `/components` root

## Localization

The application is currently in **Spanish**. All user-facing text in the onboarding flow and UI is Spanish. Maintain this language consistency when adding features.
