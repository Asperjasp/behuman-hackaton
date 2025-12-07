/**
 * BeHuman TypeScript Integration
 * ==============================
 * 
 * Main entry point for the BeHuman recommendation system.
 * 
 * This module provides:
 * - Situation classification from voice transcripts
 * - Product recommendations from Compensar Tienda
 * - Empathic message generation
 * - HR workflow for intervention approval
 * - Employee notification system
 * 
 * Usage in Next.js:
 * ```typescript
 * import { 
 *   getRecommendations,
 *   generateHRWorkflow,
 *   hrAccept,
 *   fetchProducts 
 * } from '@/lib/behuman';
 * ```
 * 
 * @module behuman
 */

// ============================================================================
// TYPE EXPORTS
// ============================================================================

export type {
  // User
  Profile,
  UserProfile,
  
  // Situations
  SituationType,
  Situation,
  SituationConfig,
  SituationConfigMap,
  
  // Products
  Product,
  ScoredProduct,
  Recommendation,
  SupabaseProduct,
  
  // HR Workflow
  HRCard,
  Intervention,
  EmployeeNotification,
  
  // Results
  RecommendationResult,
  
  // API
  RecommendationRequest,
  HRDecisionRequest,
  ApiResponse,
} from './types';

export { normalizeProduct } from './types';

// ============================================================================
// SUPABASE CLIENT EXPORTS
// ============================================================================

export {
  getSupabaseClient,
  fetchProducts,
  fetchProductsBySituation,
  fetchProductsByCategory,
} from './supabaseClient';

// ============================================================================
// RECOMMENDER EXPORTS
// ============================================================================

export {
  SITUATION_CONFIG,
  classifySituation,
  scoreProducts,
  generateEmpathicMessage,
  getRecommendations,
} from './recommender';

// ============================================================================
// HR WORKFLOW EXPORTS
// ============================================================================

export {
  createHRCards,
  generateHRWorkflow,
  hrAccept,
  hrReject,
  runFullWorkflow,
} from './hrWorkflow';

// ============================================================================
// CONVENIENCE FUNCTIONS
// ============================================================================

import type { Profile, Situation, RecommendationResult, EmployeeNotification } from './types';
import { classifySituation } from './recommender';
import { generateHRWorkflow, hrAccept } from './hrWorkflow';

/**
 * Main entry point for processing a voice transcript
 * 
 * This is the most common use case - takes a transcript and profile,
 * returns full recommendation results with HR cards.
 * 
 * @param transcript - Voice transcript from ElevenLabs
 * @param profile - Anonymous user profile
 * @returns Complete recommendation result
 * 
 * @example
 * ```typescript
 * const result = await processTranscript(
 *   "Me siento muy estresado con el trabajo...",
 *   { userId: 'anon-1', name: 'Usuario', hobbies: ['yoga'], goals: ['relajarme'] }
 * );
 * console.log(result.empathicMessage);
 * console.log(result.hrCards);
 * ```
 */
export async function processTranscript(
  transcript: string,
  profile: Profile
): Promise<RecommendationResult> {
  const situation = classifySituation(transcript);
  return generateHRWorkflow(profile, situation, transcript);
}

/**
 * Complete flow: process transcript, auto-accept first card, get notification
 * 
 * Useful for demos or when auto-approval is enabled.
 * 
 * @param transcript - Voice transcript
 * @param profile - User profile
 * @returns Result with employee notification ready
 */
export async function processAndAutoApprove(
  transcript: string,
  profile: Profile
): Promise<{
  result: RecommendationResult;
  notification: EmployeeNotification | null;
}> {
  const result = await processTranscript(transcript, profile);
  
  let notification: EmployeeNotification | null = null;
  if (result.hrCards && result.hrCards.length > 0) {
    const acceptedCard = {
      ...result.hrCards[0],
      status: 'accepted' as const,
    };
    const situation = classifySituation(transcript);
    notification = hrAccept(profile, situation, acceptedCard, result.empathicMessage);
  }
  
  return { result, notification };
}

// ============================================================================
// VERSION & INFO
// ============================================================================

export const VERSION = '1.0.0';
export const MODULE_NAME = 'behuman-typescript';

/**
 * Get module info
 */
export function getModuleInfo() {
  return {
    name: MODULE_NAME,
    version: VERSION,
    description: 'BeHuman Empathic Recommendation System',
    features: [
      'Situation classification from voice transcripts',
      'Product recommendations from Compensar Tienda',
      'Empathic message generation (≤500 chars)',
      'HR workflow for intervention approval',
      'Anonymous employee notifications',
    ],
    supabaseTable: 'Compensar-Database',
    situationTypes: [
      'perdida_familiar',
      'ruptura_amorosa',
      'ansiedad',
      'soledad',
      'estres_laboral',
      'duelo',
    ],
  };
}
