-- ============================================================================
-- BeHuman: Esquema de Base de Datos para Sistema de Recomendaciones
-- Basado en FACE Framework (NeurIPS 2025)
-- ============================================================================

-- Extensión pgvector para embeddings (ya debería estar habilitada en Supabase)
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- TABLA: user_interactions
-- Trackea todas las interacciones usuario-actividad para Collaborative Filtering
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    activity_id UUID NOT NULL REFERENCES activity_catalog(id) ON DELETE CASCADE,
    
    -- Tipo de interacción (ordenado por engagement implícito)
    interaction_type TEXT NOT NULL CHECK (interaction_type IN (
        'impression',     -- 0.05: La actividad apareció en pantalla
        'view',           -- 0.10: Usuario vio la tarjeta por >2 segundos
        'click',          -- 0.30: Click para ver detalles
        'bookmark',       -- 0.50: Guardó para después
        'share',          -- 0.60: Compartió con alguien
        'start',          -- 0.70: Comenzó/registró en la actividad
        'complete',       -- 1.00: Completó la actividad
        'rate',           -- Variable: Calificó (usa rating field)
        'review'          -- 0.80: Dejó reseña escrita
    )),
    
    -- Métricas de engagement detalladas
    view_duration_seconds INTEGER DEFAULT 0,    -- Tiempo viendo la tarjeta
    detail_time_seconds INTEGER DEFAULT 0,      -- Tiempo en página de detalles
    scroll_depth_percent NUMERIC(5,2),          -- Qué tanto scrolleó (0-100)
    rating NUMERIC(2,1) CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    
    -- Contexto emocional (detectado por el agente AI)
    detected_emotion TEXT,                       -- anxious, stressed, sad, happy, etc.
    emotional_intensity NUMERIC(2,1) CHECK (emotional_intensity >= 1 AND emotional_intensity <= 5),
    conversation_context JSONB,                  -- Resumen del contexto de la conversación
    
    -- Contexto temporal
    time_of_day TEXT CHECK (time_of_day IN ('morning', 'afternoon', 'evening', 'night')),
    day_of_week TEXT CHECK (day_of_week IN ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')),
    is_weekend BOOLEAN GENERATED ALWAYS AS (day_of_week IN ('saturday', 'sunday')) STORED,
    
    -- Contexto de sesión
    session_id UUID,
    device_type TEXT CHECK (device_type IN ('mobile', 'tablet', 'desktop')),
    platform TEXT,                               -- ios, android, web
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para queries eficientes de CF
CREATE INDEX IF NOT EXISTS idx_interactions_user ON user_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_interactions_activity ON user_interactions(activity_id);
CREATE INDEX IF NOT EXISTS idx_interactions_type ON user_interactions(interaction_type);
CREATE INDEX IF NOT EXISTS idx_interactions_created ON user_interactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_interactions_session ON user_interactions(session_id);

-- Índice compuesto para queries de CF (user-activity pairs)
CREATE INDEX IF NOT EXISTS idx_interactions_user_activity ON user_interactions(user_id, activity_id);

-- ============================================================================
-- VISTA MATERIALIZADA: user_activity_matrix
-- Matriz de interacciones para Collaborative Filtering
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS user_activity_matrix AS
SELECT 
    user_id,
    activity_id,
    
    -- Score de engagement implícito (weighted sum)
    SUM(
        CASE interaction_type
            WHEN 'impression' THEN 0.05
            WHEN 'view' THEN 0.10
            WHEN 'click' THEN 0.30
            WHEN 'bookmark' THEN 0.50
            WHEN 'share' THEN 0.60
            WHEN 'start' THEN 0.70
            WHEN 'complete' THEN 1.00
            WHEN 'rate' THEN COALESCE(rating, 3) / 5.0
            WHEN 'review' THEN 0.80
            ELSE 0.20
        END
        -- Boost por tiempo de engagement
        * CASE 
            WHEN view_duration_seconds > 30 THEN 1.2
            WHEN view_duration_seconds > 10 THEN 1.1
            ELSE 1.0
        END
    ) as implicit_score,
    
    -- Conteo por tipo
    COUNT(*) as total_interactions,
    COUNT(*) FILTER (WHERE interaction_type = 'complete') as completions,
    COUNT(*) FILTER (WHERE interaction_type = 'bookmark') as bookmarks,
    AVG(rating) as avg_rating,
    
    -- Temporales
    MAX(created_at) as last_interaction,
    MIN(created_at) as first_interaction
    
FROM user_interactions
GROUP BY user_id, activity_id;

-- Índice único para refresh concurrente
CREATE UNIQUE INDEX IF NOT EXISTS idx_uam_user_activity 
ON user_activity_matrix(user_id, activity_id);

-- Refrescar la vista (ejecutar periódicamente via cron o trigger)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY user_activity_matrix;

-- ============================================================================
-- TABLA: user_embeddings
-- Embeddings de usuarios generados por Collaborative Filtering (LightGCN)
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_embeddings (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Embedding de CF (256 dimensiones, LightGCN)
    cf_embedding vector(256),
    
    -- Descriptores FACE (tokens LLM interpretables)
    -- Ejemplo: ["social", "adventurous", "cultural", "morning_person"]
    descriptors TEXT[],
    
    -- Embedding de descriptores (para búsqueda semántica)
    descriptor_embedding vector(384),  -- MiniLM output
    
    -- Profile tags inferidos (para fallback)
    inferred_profile_tags TEXT[],
    inferred_situation_tags TEXT[],
    
    -- Metadata de entrenamiento
    model_version TEXT,
    training_interactions_count INTEGER,
    last_trained_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índice para búsqueda vectorial
CREATE INDEX IF NOT EXISTS idx_user_emb_cf 
ON user_embeddings USING ivfflat (cf_embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_user_emb_desc 
ON user_embeddings USING ivfflat (descriptor_embedding vector_cosine_ops)
WITH (lists = 100);

-- ============================================================================
-- TABLA: activity_embeddings
-- Embeddings de actividades generados por CF y FACE
-- ============================================================================

CREATE TABLE IF NOT EXISTS activity_embeddings (
    activity_id UUID PRIMARY KEY REFERENCES activity_catalog(id) ON DELETE CASCADE,
    
    -- Embedding de CF
    cf_embedding vector(256),
    
    -- Descriptores FACE
    -- Ejemplo: ["outdoor", "group_activity", "stress_relief", "weekend"]
    descriptors TEXT[],
    
    -- Embedding de descriptores
    descriptor_embedding vector(384),
    
    -- Embedding de contenido (de la descripción, generado por MiniLM)
    content_embedding vector(384),
    
    -- Metadata
    model_version TEXT,
    last_trained_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices vectoriales
CREATE INDEX IF NOT EXISTS idx_activity_emb_cf 
ON activity_embeddings USING ivfflat (cf_embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_activity_emb_desc 
ON activity_embeddings USING ivfflat (descriptor_embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_activity_emb_content 
ON activity_embeddings USING ivfflat (content_embedding vector_cosine_ops)
WITH (lists = 100);

-- ============================================================================
-- FUNCIÓN: get_hybrid_recommendations
-- Recomendaciones híbridas combinando CF + Tags + Embeddings
-- ============================================================================

CREATE OR REPLACE FUNCTION get_hybrid_recommendations(
    p_user_id UUID,
    p_situation_tags TEXT[] DEFAULT '{}',
    p_emotional_state TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT 10,
    -- Pesos para cada componente
    p_cf_weight NUMERIC DEFAULT 0.30,
    p_tag_weight NUMERIC DEFAULT 0.25,
    p_semantic_weight NUMERIC DEFAULT 0.25,
    p_context_weight NUMERIC DEFAULT 0.20
)
RETURNS TABLE (
    activity_id UUID,
    name TEXT,
    description TEXT,
    final_score NUMERIC,
    cf_score NUMERIC,
    tag_score NUMERIC,
    semantic_score NUMERIC,
    context_score NUMERIC,
    explanation TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_user_embedding vector(256);
    v_user_descriptors TEXT[];
    v_user_profile_tags TEXT[];
    v_current_hour INTEGER;
    v_is_weekend BOOLEAN;
BEGIN
    -- Obtener embedding y descriptores del usuario
    SELECT ue.cf_embedding, ue.descriptors, ue.inferred_profile_tags
    INTO v_user_embedding, v_user_descriptors, v_user_profile_tags
    FROM user_embeddings ue
    WHERE ue.user_id = p_user_id;
    
    -- Contexto temporal
    v_current_hour := EXTRACT(HOUR FROM NOW());
    v_is_weekend := EXTRACT(DOW FROM NOW()) IN (0, 6);
    
    RETURN QUERY
    WITH 
    -- Score de Collaborative Filtering
    cf_scores AS (
        SELECT 
            ae.activity_id,
            CASE 
                WHEN v_user_embedding IS NULL THEN 0
                ELSE 1 - (ae.cf_embedding <=> v_user_embedding)
            END as score
        FROM activity_embeddings ae
    ),
    
    -- Score de Tag Matching
    tag_scores AS (
        SELECT 
            ac.id as activity_id,
            (
                -- Match con profile tags
                COALESCE(array_length(ac.profile_tags & v_user_profile_tags, 1), 0)::NUMERIC / 
                    GREATEST(array_length(ac.profile_tags, 1), 1)
                +
                -- Match con situation tags (del contexto emocional)
                COALESCE(array_length(ac.situation_tags & p_situation_tags, 1), 0)::NUMERIC / 
                    GREATEST(array_length(ac.situation_tags, 1), 1)
            ) / 2 as score
        FROM activity_catalog ac
    ),
    
    -- Score Semántico (descriptores)
    semantic_scores AS (
        SELECT 
            ae.activity_id,
            CASE 
                WHEN v_user_descriptors IS NULL OR ae.descriptors IS NULL THEN 0
                ELSE COALESCE(array_length(ae.descriptors & v_user_descriptors, 1), 0)::NUMERIC /
                    GREATEST(array_length(ae.descriptors, 1), 1)
            END as score
        FROM activity_embeddings ae
    ),
    
    -- Score Contextual
    context_scores AS (
        SELECT 
            ac.id as activity_id,
            (
                -- Boost por hora del día (mañana para actividades outdoor, etc.)
                CASE 
                    WHEN v_current_hour BETWEEN 6 AND 11 AND 'morning_activity' = ANY(ac.profile_tags) THEN 0.3
                    WHEN v_current_hour BETWEEN 12 AND 17 AND 'afternoon_activity' = ANY(ac.profile_tags) THEN 0.3
                    WHEN v_current_hour BETWEEN 18 AND 22 AND 'evening_activity' = ANY(ac.profile_tags) THEN 0.3
                    ELSE 0
                END
                +
                -- Boost por fin de semana
                CASE WHEN v_is_weekend AND 'weekend' = ANY(ac.profile_tags) THEN 0.2 ELSE 0 END
                +
                -- Boost por estado emocional
                CASE 
                    WHEN p_emotional_state = 'stressed' AND 'stress_relief' = ANY(ac.situation_tags) THEN 0.5
                    WHEN p_emotional_state = 'anxious' AND 'calming' = ANY(ac.situation_tags) THEN 0.5
                    WHEN p_emotional_state = 'sad' AND 'mood_boost' = ANY(ac.situation_tags) THEN 0.5
                    WHEN p_emotional_state = 'lonely' AND 'social' = ANY(ac.profile_tags) THEN 0.5
                    ELSE 0
                END
            ) as score
        FROM activity_catalog ac
    )
    
    SELECT 
        ac.id as activity_id,
        ac.name,
        ac.description,
        (
            COALESCE(cf.score, 0) * p_cf_weight +
            COALESCE(ts.score, 0) * p_tag_weight +
            COALESCE(ss.score, 0) * p_semantic_weight +
            COALESCE(cs.score, 0) * p_context_weight
        )::NUMERIC(4,3) as final_score,
        COALESCE(cf.score, 0)::NUMERIC(4,3) as cf_score,
        COALESCE(ts.score, 0)::NUMERIC(4,3) as tag_score,
        COALESCE(ss.score, 0)::NUMERIC(4,3) as semantic_score,
        COALESCE(cs.score, 0)::NUMERIC(4,3) as context_score,
        -- Explicación básica (el LLM genera mejores explicaciones)
        CASE 
            WHEN cf.score > 0.7 THEN 'Usuarios similares a ti disfrutaron esta actividad'
            WHEN ts.score > 0.7 THEN 'Coincide perfectamente con tu perfil y situación actual'
            WHEN cs.score > 0.5 THEN 'Ideal para este momento del día y tu estado emocional'
            ELSE 'Recomendado basado en tus preferencias'
        END as explanation
    FROM activity_catalog ac
    LEFT JOIN cf_scores cf ON cf.activity_id = ac.id
    LEFT JOIN tag_scores ts ON ts.activity_id = ac.id
    LEFT JOIN semantic_scores ss ON ss.activity_id = ac.id
    LEFT JOIN context_scores cs ON cs.activity_id = ac.id
    WHERE ac.is_active = true
    ORDER BY (
        COALESCE(cf.score, 0) * p_cf_weight +
        COALESCE(ts.score, 0) * p_tag_weight +
        COALESCE(ss.score, 0) * p_semantic_weight +
        COALESCE(cs.score, 0) * p_context_weight
    ) DESC
    LIMIT p_limit;
END;
$$;

-- ============================================================================
-- FUNCIÓN: log_interaction
-- Helper para registrar interacciones de forma fácil
-- ============================================================================

CREATE OR REPLACE FUNCTION log_interaction(
    p_user_id UUID,
    p_activity_id UUID,
    p_interaction_type TEXT,
    p_metadata JSONB DEFAULT '{}'
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    v_interaction_id UUID;
    v_hour INTEGER;
    v_dow TEXT;
BEGIN
    v_hour := EXTRACT(HOUR FROM NOW());
    v_dow := LOWER(TO_CHAR(NOW(), 'day'));
    
    INSERT INTO user_interactions (
        user_id,
        activity_id,
        interaction_type,
        view_duration_seconds,
        detail_time_seconds,
        rating,
        detected_emotion,
        emotional_intensity,
        time_of_day,
        day_of_week,
        session_id,
        device_type,
        conversation_context
    ) VALUES (
        p_user_id,
        p_activity_id,
        p_interaction_type,
        (p_metadata->>'view_duration_seconds')::INTEGER,
        (p_metadata->>'detail_time_seconds')::INTEGER,
        (p_metadata->>'rating')::NUMERIC,
        p_metadata->>'detected_emotion',
        (p_metadata->>'emotional_intensity')::NUMERIC,
        CASE 
            WHEN v_hour BETWEEN 5 AND 11 THEN 'morning'
            WHEN v_hour BETWEEN 12 AND 17 THEN 'afternoon'
            WHEN v_hour BETWEEN 18 AND 21 THEN 'evening'
            ELSE 'night'
        END,
        TRIM(v_dow),
        (p_metadata->>'session_id')::UUID,
        p_metadata->>'device_type',
        p_metadata->'conversation_context'
    )
    RETURNING id INTO v_interaction_id;
    
    RETURN v_interaction_id;
END;
$$;

-- ============================================================================
-- TRIGGER: Actualizar updated_at automáticamente
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_interactions_updated_at
    BEFORE UPDATE ON user_interactions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_embeddings_updated_at
    BEFORE UPDATE ON user_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_activity_embeddings_updated_at
    BEFORE UPDATE ON activity_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- RLS (Row Level Security) Policies
-- ============================================================================

ALTER TABLE user_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_embeddings ENABLE ROW LEVEL SECURITY;

-- Usuarios solo pueden ver sus propias interacciones
CREATE POLICY user_interactions_select ON user_interactions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY user_interactions_insert ON user_interactions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Embeddings de usuario son privados
CREATE POLICY user_embeddings_select ON user_embeddings
    FOR SELECT USING (auth.uid() = user_id);

-- Activity embeddings son públicos (lectura)
ALTER TABLE activity_embeddings ENABLE ROW LEVEL SECURITY;
CREATE POLICY activity_embeddings_select ON activity_embeddings
    FOR SELECT USING (true);

-- ============================================================================
-- COMENTARIOS DE DOCUMENTACIÓN
-- ============================================================================

COMMENT ON TABLE user_interactions IS 'Historial de interacciones usuario-actividad para Collaborative Filtering';
COMMENT ON TABLE user_embeddings IS 'Embeddings de usuarios generados por LightGCN + FACE';
COMMENT ON TABLE activity_embeddings IS 'Embeddings de actividades para búsqueda vectorial';
COMMENT ON MATERIALIZED VIEW user_activity_matrix IS 'Matriz de scores implícitos para entrenar CF';
COMMENT ON FUNCTION get_hybrid_recommendations IS 'Recomendaciones híbridas: CF + Tags + Semántico + Contextual';
COMMENT ON FUNCTION log_interaction IS 'Helper para registrar interacciones de usuario';
