/**
 * BeHuman - Motor de Recomendación
 * =================================
 * Sistema de clasificación de situaciones y recomendación de productos.
 * 
 * FLUJO:
 * 1. Recibe transcript del voice agent → clasifica situación
 * 2. Consulta productos en Supabase con tags relevantes
 * 3. Rankea productos según perfil + situación
 * 4. Genera mensaje empático
 * 
 * SITUACIONES (4 categorías principales):
 * - muerte_familiar: Pérdida de un ser querido
 * - causa_economica: Problemas financieros/laborales
 * - bloqueo_incapacidad: Sentirse incapaz/incompetente
 * - rompimiento_pareja: Ruptura amorosa
 * 
 * PROFILE TAGS:
 * - Edad: joven (18-30), adulto (30-50), mayor (50+)
 * - Hobbies: tech, musica, deportes, arte, lectura, cocina, viajes, naturaleza
 * - Metas: familia, amigos, bienes, carrera, salud, crecimiento_personal
 */

import type { 
  Profile, 
  Situation, 
  SituationType,
  SituationTag,
  Product, 
  ScoredProduct,
  SituationConfig,
  SituationConfigMap,
  AgeCategory
} from './types';

// ============================================================================
// BASE DE CONOCIMIENTO: Configuración por Situación (4 categorías)
// ============================================================================

export const SITUATION_CONFIG: SituationConfigMap = {
  muerte_familiar: {
    beneficial: ['tranquilo', 'introspectivo', 'naturaleza', 'mindfulness', 'expresivo', 'arte', 'musica'],
    avoid: ['competitivo', 'fiesta', 'alta_estimulacion'],
    keywords: [
      'murió', 'falleció', 'partió', 'muerte', 'duelo', 'perdí', 'perdida',
      'padre', 'madre', 'abuelo', 'abuela', 'hermano', 'hermana', 'hijo', 'hija',
      'funeral', 'luto', 'extraño mucho', 'ya no está', 'se fue'
    ],
    description: 'La pérdida requiere espacios de calma para procesar el duelo'
  },
  
  causa_economica: {
    beneficial: ['carrera', 'tech', 'crecimiento_personal', 'bienes', 'social'],
    avoid: ['lujo', 'exclusivo'],
    keywords: [
      'dinero', 'plata', 'deudas', 'despido', 'despidieron', 'sin trabajo',
      'desempleo', 'no me alcanza', 'crisis económica', 'quiebra', 'bancarrota',
      'salario', 'sueldo', 'laboral', 'jefe', 'oficina', 'empresa', 'negocio',
      'freelance', 'emprendimiento', 'navidad', 'diciembre'
    ],
    description: 'Desarrollar habilidades y encontrar nuevas oportunidades'
  },
  
  bloqueo_incapacidad: {
    beneficial: ['crecimiento_personal', 'tech', 'carrera', 'salud', 'social', 'arte'],
    avoid: ['competitivo', 'alta_presion'],
    keywords: [
      'incapaz', 'no puedo', 'no sirvo', 'inútil', 'incompetente', 'perdido',
      'caso perdido', 'fracasado', 'impostor', 'síndrome impostor', 'no entiendo',
      'no aprendo', 'torpe', 'no sé nada', 'tecnología', 'no rindo', 'bloqueado',
      'estancado', 'sin futuro', 'acabado', 'vida acabada', 'no valgo'
    ],
    description: 'Reconstruir confianza a través de logros pequeños y conexión'
  },
  
  rompimiento_pareja: {
    beneficial: ['activo', 'social', 'deportes', 'viajes', 'amigos', 'musica'],
    avoid: ['romantico', 'parejas', 'citas'],
    keywords: [
      'ruptura', 'terminamos', 'separación', 'divorcio', 'ex', 'dejó', 'dejé',
      'corazón roto', 'infiel', 'infidelidad', 'engañó', 'tusa', 'despecho',
      'soltera', 'soltero', 'relación', 'pareja', 'novio', 'novia', 'amor'
    ],
    description: 'El movimiento físico y las conexiones sociales ayudan a sanar'
  }
};

// ============================================================================
// HELPER: Clasificar edad en categoría
// ============================================================================

export function classifyAge(age: number): AgeCategory {
  if (age < 30) return 'joven';
  if (age < 50) return 'adulto';
  return 'mayor';
}

// ============================================================================
// CLASIFICADOR DE SITUACIÓN (4 categorías)
// ============================================================================

/**
 * Clasifica la situación del usuario basándose en el transcript de la conversación.
 * Usa keywords para detectar el tipo de situación emocional.
 * 
 * Las 4 categorías en orden de prioridad:
 * 1. muerte_familiar - Más urgente emocionalmente
 * 2. rompimiento_pareja - Alta carga emocional
 * 3. bloqueo_incapacidad - Puede llevar a otros problemas
 * 4. causa_economica - Base de muchas situaciones
 */
export function classifySituation(transcript: string): Situation {
  const t = transcript.toLowerCase();
  
  // Orden de prioridad para clasificación
  const situationPriority: SituationTag[] = [
    'muerte_familiar',
    'rompimiento_pareja',
    'bloqueo_incapacidad',
    'causa_economica'
  ];
  
  let bestMatch: { type: SituationTag; score: number; keywords: string[] } | null = null;
  
  for (const situationType of situationPriority) {
    const config = SITUATION_CONFIG[situationType];
    const matchedKeywords = config.keywords.filter(kw => t.includes(kw.toLowerCase()));
    const score = matchedKeywords.length;
    
    if (score > 0 && (!bestMatch || score > bestMatch.score)) {
      bestMatch = { type: situationType, score, keywords: matchedKeywords };
    }
  }
  
  if (bestMatch) {
    // Detectar subtipo si es posible
    let subtype = 'general';
    
    if (bestMatch.type === 'muerte_familiar') {
      if (t.includes('padre') || t.includes('madre') || t.includes('padres')) subtype = 'padres';
      else if (t.includes('abuelo') || t.includes('abuela')) subtype = 'abuelos';
      else if (t.includes('hermano') || t.includes('hermana')) subtype = 'hermanos';
      else if (t.includes('hijo') || t.includes('hija')) subtype = 'hijos';
    } else if (bestMatch.type === 'causa_economica') {
      if (t.includes('despido') || t.includes('despidieron')) subtype = 'despido';
      else if (t.includes('deuda') || t.includes('deudas')) subtype = 'deudas';
      else if (t.includes('negocio') || t.includes('empresa')) subtype = 'negocio';
      else if (t.includes('navidad') || t.includes('diciembre')) subtype = 'temporada';
    } else if (bestMatch.type === 'bloqueo_incapacidad') {
      if (t.includes('tecnología') || t.includes('tech') || t.includes('computador')) subtype = 'tech';
      else if (t.includes('trabajo') || t.includes('laboral')) subtype = 'laboral';
      else if (t.includes('estudios') || t.includes('aprender')) subtype = 'aprendizaje';
    } else if (bestMatch.type === 'rompimiento_pareja') {
      if (t.includes('divorcio')) subtype = 'divorcio';
      else if (t.includes('infiel') || t.includes('engañó')) subtype = 'infidelidad';
    }
    
    return {
      type: bestMatch.type,
      subtype,
      context: `Detectado: ${bestMatch.keywords.slice(0, 3).join(', ')}`,
      confidence: Math.min(bestMatch.score / 3, 1)
    };
  }
  
  // Default: bloqueo_incapacidad (más común y general)
  return {
    type: 'bloqueo_incapacidad',
    subtype: 'general',
    context: 'Sin situación específica detectada - asumiendo necesidad de apoyo general',
    confidence: 0.3
  };
}

// Alias para compatibilidad
export const classifySituationFromTranscript = classifySituation;

// ============================================================================
// MOTOR DE SCORING
// ============================================================================

/**
 * Calcula el score de un producto para una situación y perfil dados.
 */
export function scoreProduct(
  product: Product, 
  situation: Situation, 
  profile: Profile
): { score: number; reasons: string[] } {
  let score = 0;
  const reasons: string[] = [];
  
  const config = SITUATION_CONFIG[situation.type as SituationTag] || SITUATION_CONFIG['bloqueo_incapacidad'];
  const productTags = [...(product.profile_tags || []), ...(product.situation_tags || [])];
  const productText = `${product.nombre} ${product.subcategoria} ${product.descripcion || ''}`.toLowerCase();
  
  // 1. Match directo con situation_tags (+40 - más importante ahora)
  const situationTagMatch = (product.situation_tags || []).some(tag => 
    tag === situation.type
  );
  if (situationTagMatch) {
    score += 40;
    reasons.push('Recomendado específicamente para tu situación');
  }
  
  // 2. Match con profile_tags beneficiosos (+25 por cada match)
  const beneficialMatches = config.beneficial.filter(b => 
    productTags.some(t => t.toLowerCase() === b.toLowerCase())
  );
  if (beneficialMatches.length > 0) {
    score += 25 * Math.min(beneficialMatches.length, 2);
    reasons.push(`Actividad de tipo '${beneficialMatches[0]}' ayuda en tu situación`);
  }
  
  // 3. Match con edad del usuario (+20)
  if (profile.age) {
    const ageCategory = classifyAge(profile.age);
    const ageMatch = (product.profile_tags || []).some(tag => tag === ageCategory);
    if (ageMatch) {
      score += 20;
      reasons.push('Adecuado para tu grupo de edad');
    }
  }
  
  // 4. Match con hobbies del usuario (+20)
  if (profile.hobbies && profile.hobbies.length > 0) {
    const hobbyMatches = profile.hobbies.filter(hobby => 
      productTags.some(tag => tag.toLowerCase() === hobby.toLowerCase()) ||
      productText.includes(hobby.toLowerCase())
    );
    if (hobbyMatches.length > 0) {
      score += 20;
      reasons.push(`Conecta con tu interés en ${hobbyMatches[0]}`);
    }
  }
  
  // 5. Match con metas del usuario (+15)
  if (profile.goals && profile.goals.length > 0) {
    const goalMatches = profile.goals.filter(goal => 
      productTags.some(tag => tag.toLowerCase().includes(goal.toLowerCase()))
    );
    if (goalMatches.length > 0) {
      score += 15;
      reasons.push(`Alineado con tu meta de ${goalMatches[0]}`);
    }
  }
  
  // 6. Keywords en nombre/descripción (+10)
  const keywordMatches = config.keywords.filter(kw => productText.includes(kw.toLowerCase()));
  if (keywordMatches.length > 0) {
    score += 10 * Math.min(keywordMatches.length, 2);
  }
  
  // 7. Penalización por tags a evitar (-50)
  const avoidMatches = config.avoid.filter(a => 
    productTags.some(t => t.toLowerCase().includes(a.toLowerCase()))
  );
  if (avoidMatches.length > 0) {
    score -= 50;
  }
  
  // 8. Bonus por precio accesible (+10)
  if (product.precio_desde && product.precio_desde < 100000) {
    score += 10;
    reasons.push('Precio accesible');
  }
  
  return { score, reasons };
}

/**
 * Genera recomendaciones rankeadas para un perfil y situación.
 */
export function rankProducts(
  products: Product[],
  situation: Situation,
  profile: Profile,
  topN: number = 4
): ScoredProduct[] {
  const scored = products.map(product => {
    const { score, reasons } = scoreProduct(product, situation, profile);
    return { product, score, reasons };
  });
  
  // Ordenar por score descendente
  scored.sort((a, b) => b.score - a.score);
  
  // Retornar top N con score positivo
  return scored
    .filter(r => r.score > 0)
    .slice(0, topN);
}

// ============================================================================
// GENERADOR DE MENSAJES EMPÁTICOS
// ============================================================================

/**
 * Frases de confrontación para cada situación
 * Personalizadas por subtipo cuando aplica
 */
const CONFRONTATION_PHRASES: Record<string, Record<string, string>> = {
  muerte_familiar: {
    padres: 'enfrentarte a la pérdida de tus padres',
    abuelos: 'despedirte de quien te vio crecer',
    hermanos: 'sobrellevar la partida de tu hermano/a',
    hijos: 'atravesar la pérdida más dolorosa que existe',
    general: 'enfrentar la partida de alguien que amabas profundamente'
  },
  
  causa_economica: {
    despido: 'levantarte después de perder tu trabajo',
    deudas: 'salir adelante con el peso de las deudas',
    negocio: 'reconstruir después de un golpe al negocio',
    temporada: 'manejar las presiones económicas de la temporada',
    general: 'encontrar estabilidad en medio de la incertidumbre económica'
  },
  
  bloqueo_incapacidad: {
    tech: 'superar el bloqueo con la tecnología',
    laboral: 'recuperar la confianza en tu trabajo',
    aprendizaje: 'encontrar tu forma de aprender',
    general: 'reconstruir la confianza en ti mismo/a'
  },
  
  rompimiento_pareja: {
    divorcio: 'reconstruirte después del divorcio',
    infidelidad: 'sanar después de una traición',
    general: 'levantarte después de una ruptura'
  }
};

/**
 * Frases de calma realista para cada situación
 */
const CALMING_PHRASES: Record<string, string[]> = {
  muerte_familiar: [
    'Este dolor es parte de haber amado profundamente.',
    'No hay tiempo correcto para sanar, solo el tuyo.',
    'Cada día que enfrentas es un acto de valentía.',
    'Su memoria vive en ti, y eso nadie te lo quita.'
  ],
  
  causa_economica: [
    'Las crisis económicas son temporales, tus habilidades no.',
    'Muchos han estado donde estás y salieron adelante.',
    'Tu valor no se define por tu situación financiera.',
    'Cada paso pequeño te acerca a la estabilidad.'
  ],
  
  bloqueo_incapacidad: [
    'Sentirte perdido no significa que lo estés.',
    'Todos empezamos sin saber, y todos podemos aprender.',
    'Tu capacidad de mejorar es mayor de lo que crees.',
    'El primer paso siempre se siente imposible hasta que lo das.'
  ],
  
  rompimiento_pareja: [
    'Lo que sientes ahora no es permanente.',
    'El vacío actual dejará espacio para algo nuevo.',
    'Mereces tiempo para reconstruirte.',
    'Esta ruptura no define tu capacidad de amar o ser amado/a.'
  ]
};

/**
 * Beneficios por tipo de actividad para mensajes empáticos
 */
const ACTIVITY_BENEFITS: Record<string, string> = {
  tranquilo: 'la calma te ayudará a reconectar contigo mismo',
  activo: 'el movimiento físico libera tensión y mejora el ánimo',
  social: 'conectar con otros nos recuerda que no estamos solos',
  creativo: 'expresar lo que las palabras no alcanzan sana',
  aventurero: 'cambiar de ambiente ayuda a ganar perspectiva',
  introspectivo: 'el autoconocimiento es el primer paso hacia la paz',
  disciplinado: 'la rutina puede ser un ancla en tiempos difíciles',
  autocuidado: 'cuidarte a ti mismo es lo más valiente que puedes hacer',
  tech: 'dominar nuevas herramientas te dará confianza',
  musica: 'la música expresa lo que las palabras no pueden',
  deportes: 'el ejercicio libera endorfinas y despeja la mente',
  arte: 'crear algo te conecta con una parte profunda de ti',
  naturaleza: 'la naturaleza tiene un poder sanador comprobado',
  carrera: 'desarrollar nuevas habilidades abre puertas'
};

/**
 * Genera un mensaje empático personalizado (≤500 caracteres).
 */
export function generateEmpathicMessage(
  profile: Profile,
  situation: Situation,
  topProduct: Product | null
): string {
  if (!topProduct) {
    return `${profile.name}, estamos buscando las mejores opciones para apoyarte en este momento.`;
  }
  
  // 1. Confrontación
  const sitPhrases = CONFRONTATION_PHRASES[situation.type] || CONFRONTATION_PHRASES['bloqueo_incapacidad'];
  const confrontation = sitPhrases[situation.subtype || 'general'] || sitPhrases['general'];
  
  // 2. Calma
  const calmOptions = CALMING_PHRASES[situation.type] || CALMING_PHRASES['bloqueo_incapacidad'];
  const calming = calmOptions[Math.floor(Math.random() * calmOptions.length)];
  
  // 3. Conexión hobby → actividad
  let hobbyPhrase: string;
  const productText = `${topProduct.nombre} ${topProduct.subcategoria}`.toLowerCase();
  const matchedHobby = (profile.hobbies || []).find(h => productText.includes(h.toLowerCase()));
  
  if (matchedHobby) {
    hobbyPhrase = `aprovechando tu gusto por ${matchedHobby.toLowerCase()}, te recomendamos ${topProduct.nombre}`;
  } else if (profile.hobbies && profile.hobbies.length > 0) {
    hobbyPhrase = `combinando tu interés en ${profile.hobbies[0].toLowerCase()} con algo nuevo, te sugerimos ${topProduct.nombre}`;
  } else {
    hobbyPhrase = `te recomendamos ${topProduct.nombre}`;
  }
  
  // 4. Beneficio
  const productTags = topProduct.profile_tags || [];
  let benefit = '';
  for (const tag of productTags) {
    const tagLower = tag.toLowerCase();
    if (ACTIVITY_BENEFITS[tagLower]) {
      benefit = ACTIVITY_BENEFITS[tagLower];
      break;
    }
  }
  
  // Construir mensaje
  let message = `${profile.name}, sé que hoy te toca ${confrontation}. ${calming} Por eso, ${hobbyPhrase}`;
  
  if (benefit) {
    message += ` — ${benefit}.`;
  } else {
    message += '.';
  }
  
  // 5. Meta si hay espacio
  if (profile.goals && profile.goals.length > 0 && message.length < 420) {
    message += ` Un paso hacia ${profile.goals[0].toLowerCase()}.`;
  }
  
  // Truncar si necesario
  if (message.length > 500) {
    const lastPeriod = message.substring(0, 497).lastIndexOf('.');
    if (lastPeriod > 300) {
      message = message.substring(0, lastPeriod + 1);
    } else {
      message = message.substring(0, 497) + '...';
    }
  }
  
  return message;
}

// ============================================================================
// FUNCIÓN PRINCIPAL DE RECOMENDACIÓN
// ============================================================================

import { fetchProductsBySituation, fetchProducts } from './supabaseClient';
import type { RecommendationResult, ScoredProduct } from './types';

/**
 * Función principal que orquesta todo el flujo de recomendación.
 * 
 * @param profile - Perfil del usuario
 * @param situation - Situación clasificada
 * @param transcript - Transcript original (para contexto)
 * @param topN - Número de recomendaciones a retornar
 * @returns Resultado completo con recomendaciones y mensaje empático
 */
export async function getRecommendations(
  profile: Profile,
  situation: Situation,
  transcript: string,
  topN: number = 4
): Promise<RecommendationResult> {
  // 1. Obtener productos relevantes de Supabase
  let products: Product[];
  try {
    // Intentar primero con filtro de situación
    products = await fetchProductsBySituation(situation.type);
    
    // Si no hay suficientes, obtener todos
    if (products.length < topN * 2) {
      const allProducts = await fetchProducts();
      // Combinar sin duplicados
      const existingIds = new Set(products.map(p => p.id));
      for (const p of allProducts) {
        if (!existingIds.has(p.id)) {
          products.push(p);
        }
      }
    }
  } catch (error) {
    console.error('Error fetching products:', error);
    products = [];
  }
  
  // 2. Rankear productos
  const recommendations = rankProducts(products, situation, profile, topN);
  
  // 3. Generar mensaje empático
  const topProduct = recommendations.length > 0 ? recommendations[0].product : null;
  const empathicMessage = generateEmpathicMessage(profile, situation, topProduct);
  
  // 4. Construir resultado
  return {
    situation,
    recommendations,
    empathicMessage,
    messageLength: empathicMessage.length,
    profile,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Versión sincrónica de scoring (para uso sin Supabase)
 */
export function scoreProducts(
  products: Product[],
  situation: Situation,
  profile: Profile,
  topN: number = 4
): ScoredProduct[] {
  return rankProducts(products, situation, profile, topN);
}

// ============================================================================
// EXPORTS ADICIONALES
// ============================================================================

export { CONFRONTATION_PHRASES, CALMING_PHRASES, ACTIVITY_BENEFITS };
