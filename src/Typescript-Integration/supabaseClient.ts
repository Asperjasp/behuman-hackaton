/**
 * BeHuman - Cliente Supabase
 * ==========================
 * Helper para conectar con Supabase y consultar productos.
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { Product } from './types';

// ============================================================================
// CONFIGURACIÓN
// ============================================================================

const SUPABASE_URL = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_KEY || process.env.SUPABASE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

let supabaseInstance: SupabaseClient | null = null;

/**
 * Obtiene o crea la instancia de Supabase
 */
export function getSupabaseClient(): SupabaseClient {
  if (!supabaseInstance) {
    if (!SUPABASE_URL || !SUPABASE_KEY) {
      throw new Error('Supabase URL and Key must be configured in environment variables');
    }
    supabaseInstance = createClient(SUPABASE_URL, SUPABASE_KEY);
  }
  return supabaseInstance;
.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5mcXZodGFsd2RveHBpcWNodXhjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUwNjMwMDMsImV4cCI6MjA4MDYzOTAwM30.X2IcMxWbF54fALebzFAlck-dynw_2rdJCRaBFXRzX7g}

// ============================================================================
// CONSULTAS DE PRODUCTOS
// ============================================================================

const TABLE_NAME = 'Compensar-Database';

/**
 * Obtiene todos los productos de la base de datos
 */
export async function getAllProducts(): Promise<Product[]> {
  const supabase = getSupabaseClient();
  
  const { data, error } = await supabase
    .from(TABLE_NAME)
    .select('*')
    .order('nombre');
  
  if (error) {
    console.error('Error fetching products:', error);
    throw error;
  }
  
  return data || [];
}

/**
 * Busca productos por tags de situación
 */
export async function getProductsBySituationTags(tags: string[]): Promise<Product[]> {
  const supabase = getSupabaseClient();
  
  // Supabase: buscar productos que contengan al menos uno de los tags
  const { data, error } = await supabase
    .from(TABLE_NAME)
    .select('*')
    .overlaps('situation_tags', tags);
  
  if (error) {
    console.error('Error fetching products by situation:', error);
    throw error;
  }
  
  return data || [];
}

/**
 * Busca productos por categoría
 */
export async function getProductsByCategory(category: string): Promise<Product[]> {
  const supabase = getSupabaseClient();
  
  const { data, error } = await supabase
    .from(TABLE_NAME)
    .select('*')
    .eq('categoria_principal', category);
  
  if (error) {
    console.error('Error fetching products by category:', error);
    throw error;
  }
  
  return data || [];
}

/**
 * Busca productos por subcategoría
 */
export async function getProductsBySubcategory(subcategory: string): Promise<Product[]> {
  const supabase = getSupabaseClient();
  
  const { data, error } = await supabase
    .from(TABLE_NAME)
    .select('*')
    .ilike('subcategoria', `%${subcategory}%`);
  
  if (error) {
    console.error('Error fetching products by subcategory:', error);
    throw error;
  }
  
  return data || [];
}

/**
 * Busca productos por texto (nombre o descripción)
 */
export async function searchProducts(query: string): Promise<Product[]> {
  const supabase = getSupabaseClient();
  
  const { data, error } = await supabase
    .from(TABLE_NAME)
    .select('*')
    .or(`nombre.ilike.%${query}%,descripcion.ilike.%${query}%`);
  
  if (error) {
    console.error('Error searching products:', error);
    throw error;
  }
  
  return data || [];
}

// ============================================================================
// INTERVENCIONES (para guardar cuando HR aprueba)
// ============================================================================

export interface Intervention {
  id?: number;
  anonymous_employee_token: string;
  product_id: number;
  product_snapshot: object;
  estimated_uplift: number;
  status: 'pending' | 'approved' | 'rejected';
  created_at?: string;
}

/**
 * Guarda una intervención aprobada por HR
 */
export async function saveIntervention(intervention: Omit<Intervention, 'id' | 'created_at'>): Promise<Intervention> {
  const supabase = getSupabaseClient();
  
  const { data, error } = await supabase
    .from('interventions')
    .insert([{
      ...intervention,
      created_at: new Date().toISOString()
    }])
    .select()
    .single();
  
  if (error) {
    console.error('Error saving intervention:', error);
    throw error;
  }
  
  return data;
}

// ============================================================================
// NOTIFICACIONES
// ============================================================================

export interface Notification {
  id?: number;
  anonymous_employee_token: string;
  title: string;
  body: string;
  metadata?: object;
  delivered: boolean;
  created_at?: string;
}

/**
 * Crea una notificación para el empleado
 */
export async function createNotification(notification: Omit<Notification, 'id' | 'created_at'>): Promise<Notification> {
  const supabase = getSupabaseClient();
  
  const { data, error } = await supabase
    .from('notifications')
    .insert([{
      ...notification,
      created_at: new Date().toISOString()
    }])
    .select()
    .single();
  
  if (error) {
    console.error('Error creating notification:', error);
    throw error;
  }
  
  return data;
}
