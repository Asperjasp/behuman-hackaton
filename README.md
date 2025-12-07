# 🧠 BeHuman - Sistema Operativo de Manejo de Emociones

Plataforma de bienestar emocional que integra asesoramiento psicológico, actividades terapéuticas y recomendaciones personalizadas para mejorar la calidad de vida del usuario.

## 🎯 Concepto

BeHuman es un **sistema operativo emocional** - un agente de IA que acompaña al usuario en su bienestar mental a través de múltiples canales:

### Pilares del Sistema

| Pilar | Descripción | Estado |
|-------|-------------|--------|
| 🧭 **Orientación Emocional** | Detección de estado emocional y situaciones de vida | Core |
| 🎯 **Actividades Terapéuticas** | Recomendación de actividades, talleres y experiencias | ✅ En desarrollo |
| 🎵 **Música Terapéutica** | Playlists personalizadas según estado emocional | Feature |
| 📊 **Seguimiento** | Tracking de progreso y patrones emocionales | Roadmap |

### Factores de Personalización

1. **Situación Psicológica**: Identificación del estado emocional (estrés, ansiedad, duelo, etc.)
2. **Perfil del Usuario**: Características personales (activo, social, introvertido, etc.)
3. **Contexto Cultural**: Temporada, región y preferencias culturales
4. **Historial de Interacciones**: Aprendizaje continuo de preferencias

---

## 🔄 Arquitectura del Sistema de Recomendaciones

### Niveles de Sofisticación

El sistema implementa una arquitectura de recomendaciones escalable con 4 niveles:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    NIVEL 4: HÍBRIDO + CONTEXTUAL                       │
│  Combina todos los niveles + contexto temporal, ubicación, clima       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                 NIVEL 3: COLLABORATIVE FILTERING                 │   │
│  │  "Usuarios similares a ti también disfrutaron..."               │   │
│  │  ┌─────────────────────────────────────────────────────────┐    │   │
│  │  │            NIVEL 2: EMBEDDINGS SEMÁNTICOS               │    │   │
│  │  │  Vectores de 1536 dimensiones con pgvector             │    │   │
│  │  │  ┌─────────────────────────────────────────────────┐   │    │   │
│  │  │  │         NIVEL 1: TAG MATCHING (Actual)          │   │    │   │
│  │  │  │  profile_tags + situation_tags                  │   │    │   │
│  │  │  └─────────────────────────────────────────────────┘   │    │   │
│  │  └─────────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Nivel 1: Tag Matching (Implementado ✅)
```sql
-- Matching simple por etiquetas
SELECT * FROM activity_catalog
WHERE profile_tags && ARRAY['social', 'activo']
  AND situation_tags && ARRAY['estrés alto'];
```

#### Nivel 2: Embeddings Semánticos (Roadmap)
```sql
-- Búsqueda por similitud vectorial
SELECT *, 
       1 - (embedding <=> query_embedding) as similarity
FROM activity_catalog
ORDER BY embedding <=> query_embedding
LIMIT 10;
```
- Requiere: OpenAI API para generar embeddings de descripción + tags
- Tecnología: pgvector en Supabase

#### Nivel 3: Collaborative Filtering (Roadmap)
```sql
-- Usuarios similares con gustos parecidos
WITH similar_users AS (
  SELECT user_id, similarity_score
  FROM calculate_user_similarity(current_user_id)
  ORDER BY similarity_score DESC
  LIMIT 50
)
SELECT activity_id, AVG(rating) as predicted_score
FROM user_activities ua
JOIN similar_users su ON ua.user_id = su.user_id
GROUP BY activity_id
ORDER BY predicted_score DESC;
```

#### Nivel 4: Híbrido + Contextual (Roadmap)
```python
def get_hybrid_recommendations(user, context):
    # Combinar scores de cada nivel
    tag_score = get_tag_matches(user.profile_tags, user.situation_tags)
    semantic_score = get_embedding_similarity(user.embedding, activities)
    collab_score = get_collaborative_predictions(user.id)
    
    # Factores contextuales
    context_boost = calculate_context_boost(
        time_of_day=context.hour,
        day_of_week=context.weekday,
        weather=context.weather,
        location=context.city
    )
    
    # Score final ponderado
    final_score = (
        tag_score * 0.2 +
        semantic_score * 0.3 +
        collab_score * 0.3 +
        context_boost * 0.2
    )
    return sort_by_score(final_score)
```

### Tabla de Madurez del Sistema

| Nivel | Precisión | Complejidad | Data Requerida | Estado |
|-------|-----------|-------------|----------------|--------|
| Tag Matching | ~60% | Baja | Tags manuales | ✅ Implementado |
| Embeddings | ~75% | Media | Descripciones | 🔜 Próximo |
| Collaborative | ~85% | Alta | Historial usuarios | 📋 Roadmap |
| Híbrido | ~90%+ | Muy Alta | Todo lo anterior | 📋 Roadmap |

## 📁 Estructura del Proyecto

```
behuman-hackaton/
├── src/
│   ├── spotify/                    # Integración con Spotify API
│   │   ├── auth/                   # Autenticación OAuth 2.0
│   │   │   ├── SpotifyAuthService.cs
│   │   │   ├── TokenManager.cs
│   │   │   └── OAuthCallbackHandler.cs
│   │   ├── client/                 # Cliente API Spotify
│   │   │   ├── SpotifyApiClient.cs
│   │   │   ├── UserProfileService.cs
│   │   │   └── PlaylistService.cs
│   │   └── models/                 # Modelos de datos Spotify
│   │       ├── SpotifyUser.cs
│   │       ├── TopArtists.cs
│   │       ├── TopTracks.cs
│   │       └── UserPreferences.cs
│   │
│   ├── playlists/                  # Sistema de Playlists Curadas
│   │   ├── catalog/                # Catálogo de playlists por situación
│   │   │   ├── PlaylistCatalog.cs
│   │   │   ├── SituationCategory.cs
│   │   │   └── CopingStyleMapper.cs
│   │   ├── cultural/               # Contexto cultural
│   │   │   ├── CulturalContextService.cs
│   │   │   ├── SeasonalDetector.cs
│   │   │   └── RegionalPreferences.cs
│   │   └── models/                 # Modelos de playlists
│   │       ├── CuratedPlaylist.cs
│   │       ├── MusicRecommendation.cs
│   │       └── EmotionalTag.cs
│   │
│   ├── psychology/                 # Motor de Análisis Psicológico
│   │   ├── analysis/               # Análisis de situación
│   │   │   ├── SituationDetector.cs
│   │   │   ├── EmotionAnalyzer.cs
│   │   │   └── CopingStyleIdentifier.cs
│   │   ├── recommendations/        # Sistema de recomendaciones
│   │   │   ├── RecommendationEngine.cs
│   │   │   ├── PersonalizationService.cs
│   │   │   └── HybridMatcher.cs
│   │   └── models/                 # Modelos psicológicos
│   │       ├── PsychologicalSituation.cs
│   │       ├── CopingStyle.cs
│   │       └── UserEmotionalProfile.cs
│   │
│   ├── ai/                         # Integración con IA Generativa
│   │   ├── agents/                 # Agentes de conversación
│   │   │   ├── PsychoCulturalAgent.cs
│   │   │   └── ConversationManager.cs
│   │   ├── prompts/                # Templates de prompts
│   │   │   ├── SituationDetectionPrompt.cs
│   │   │   └── RecommendationPrompt.cs
│   │   └── models/
│   │       └── AgentResponse.cs
│   │
│   └── api/                        # API REST
│       ├── Controllers/
│       │   ├── AuthController.cs
│       │   ├── RecommendationController.cs
│       │   └── UserPreferencesController.cs
│       └── DTOs/
│           ├── RecommendationRequest.cs
│           └── RecommendationResponse.cs
│
├── data/                           # Datos y Configuración
│   ├── playlists/                  # Playlists curadas (JSON/YAML)
│   │   ├── situations/             # Por situación
│   │   │   ├── tusa-ruptura.json
│   │   │   ├── duelo-familiar.json
│   │   │   ├── estres-financiero.json
│   │   │   └── ansiedad-general.json
│   │   ├── coping-styles/          # Por estilo de afrontamiento
│   │   │   ├── extrovertido-despecho.json
│   │   │   ├── introvertido-nostalgia.json
│   │   │   └── reflexivo-sanacion.json
│   │   └── cultural/               # Por contexto cultural
│   │       ├── colombia-navidad.json
│   │       ├── mexico-dia-muertos.json
│   │       └── latam-general.json
│   └── mappings/                   # Mapeos de géneros y emociones
│       ├── genre-emotion-map.json
│       └── cultural-genre-map.json
│
├── tests/                          # Tests
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/                           # Documentación adicional
│   ├── spotify-integration.md
│   ├── playlist-curation-guide.md
│   └── psychological-framework.md
│
├── .env.example                    # Variables de entorno ejemplo
├── appsettings.json
└── BeHuman.sln
```

---

## 🔐 Integración con Spotify (Punto 2: Gustos Personales)

### Flujo de Autenticación OAuth 2.0

```
┌─────────────┐     1. Click "Conectar Spotify"      ┌──────────────┐
│   Usuario   │ ─────────────────────────────────────▶│   BeHuman    │
└─────────────┘                                       └──────────────┘
       │                                                      │
       │  2. Redirect a Spotify                               │
       ▼                                                      │
┌─────────────────┐                                          │
│ Spotify Login   │                                          │
│ + Autorización  │                                          │
└─────────────────┘                                          │
       │                                                      │
       │  3. Callback con código                              │
       ▼                                                      │
┌─────────────────┐     4. Intercambio por tokens    ┌──────────────┐
│ Redirect URI    │ ─────────────────────────────────▶│ Spotify API  │
└─────────────────┘                                   └──────────────┘
       │                                                      │
       │  5. Access Token + Refresh Token                     │
       ▼                                                      │
┌─────────────────┐                                          │
│ BeHuman guarda  │◀─────────────────────────────────────────┘
│ tokens seguros  │
└─────────────────┘
```

### Scopes (Permisos) Requeridos

| Scope | Descripción | Uso en BeHuman |
|-------|-------------|----------------|
| `user-top-read` | Top artistas y canciones | Conocer géneros favoritos |
| `user-read-recently-played` | Historial reciente | Estado emocional actual |
| `playlist-read-private` | Playlists privadas | Analizar categorías personales |
| `user-read-private` | Perfil básico | País/región del usuario |

### Configuración Spotify Developer

1. Crear app en [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Configurar Redirect URI: `https://tudominio.com/api/auth/spotify/callback`
3. Obtener `Client ID` y `Client Secret`
4. Configurar en `.env`:

```env
SPOTIFY_CLIENT_ID=tu_client_id
SPOTIFY_CLIENT_SECRET=tu_client_secret
SPOTIFY_REDIRECT_URI=https://tudominio.com/api/auth/spotify/callback
```

Sabemos que el Callback en entorno de producción que vamos a poneren el entorno de desarrolladores de spotify https://developer.spotify.com/dashboard/create en el entorno asociado a la cuenta vividbehuman@gmail,com, va a utilizar el entorno local con la URL de entonro local http://127.0.0.1:8888/callback , y con la URL en producción https://behuman.chat lo cual 

---

## 🎭 Sistema de Playlists Curadas (Punto 1: Asesoramiento Base)

### Categorías de Situaciones Psicológicas

```json
{
  "situaciones": [
    {
      "id": "tusa-ruptura",
      "nombre": "Ruptura Amorosa (Tusa)",
      "descripcion": "Fin de relación sentimental",
      "estilosAfrontamiento": [
        {
          "id": "extrovertido-despecho",
          "nombre": "Despecho Activo",
          "descripcion": "Quiere sentirse fuerte y superar",
          "indicadores": ["desahogarme", "superarlo", "olvidarlo", "fuerte"],
          "generos": ["reggaeton", "salsa", "pop-latino"],
          "ejemplos": ["Tusa - Karol G", "Corazón Sin Cara"]
        },
        {
          "id": "introvertido-nostalgia", 
          "nombre": "Nostalgia Reflexiva",
          "descripcion": "Procesar el duelo con tristeza",
          "indicadores": ["extraño", "recuerdos", "duele", "llorar"],
          "generos": ["balada", "rock-español", "bolero"],
          "ejemplos": ["De Música Ligera - Soda Stereo", "Hasta Que Te Conocí"]
        },
        {
          "id": "cultural-vallenato",
          "nombre": "Despecho Vallenato (Colombia)",
          "descripcion": "Afrontamiento cultural colombiano",
          "indicadores": ["colombiano", "vallenato", "parranda"],
          "generos": ["vallenato", "cumbia"],
          "ejemplos": ["Volver - Diomedes Díaz", "La Bilirrubina"]
        }
      ]
    },
    {
      "id": "duelo-familiar",
      "nombre": "Muerte de Familiar",
      "descripcion": "Pérdida de un ser querido",
      "estilosAfrontamiento": [
        {
          "id": "homenaje-celebracion",
          "nombre": "Celebrar su Vida",
          "indicadores": ["recordar", "homenaje", "celebrar"],
          "ejemplos": ["In Loving Memory - Alter Bridge", "See You Again"]
        },
        {
          "id": "procesamiento-tristeza",
          "nombre": "Procesar el Dolor",
          "indicadores": ["duele", "falta", "vacío"],
          "ejemplos": ["Tears in Heaven - Eric Clapton"]
        }
      ]
    },
    {
      "id": "estres-financiero",
      "nombre": "Problemas Económicos",
      "descripcion": "Dificultades financieras y estrés por dinero",
      "estilosAfrontamiento": [
        {
          "id": "humor-realista",
          "nombre": "Humor y Realismo",
          "indicadores": ["reírme", "realidad", "todos pasamos"],
          "generos": ["cumbia", "reggaeton", "regional-mexicano"],
          "ejemplos": ["No Hay Pesos - Grupo Cañaveral", "El Listón de tu Pelo"]
        },
        {
          "id": "motivacional",
          "nombre": "Motivación para Salir Adelante",
          "indicadores": ["salir adelante", "esfuerzo", "lograr"],
          "generos": ["hip-hop-latino", "rock"],
          "ejemplos": ["Vivir Mi Vida - Marc Anthony"]
        }
      ]
    }
  ]
}
```

### Contexto Cultural y Estacional

```json
{
  "contextoCultural": {
    "colombia": {
      "navidad": {
        "fechas": ["2024-12-01", "2024-12-31"],
        "situacion": "tristeza-navidad",
        "playlists": {
          "nostalgico": ["Faltan Cinco Pa Las Doce", "Los Caminos de la Vida"],
          "animarse": ["La Pollera Colorá", "El Año Viejo"]
        },
        "mensaje": "La Navidad en Colombia es época de familia. Es normal sentir nostalgia o tristeza si algo falta."
      }
    },
    "mexico": {
      "dia-muertos": {
        "fechas": ["2024-11-01", "2024-11-02"],
        "situacion": "recuerdo-difuntos",
        "playlists": {
          "homenaje": ["La Llorona", "Recuérdame - Coco"],
          "celebracion": ["Son de la Negra"]
        }
      }
    }
  }
}
```

---

## 🤖 Motor de Recomendación Híbrido

### Flujo del Algoritmo

```
┌────────────────────────────────────────────────────────────────────┐
│                    ENTRADA DEL USUARIO                              │
│  "Me siento muy mal, terminé con mi novia y quiero desahogarme"    │
└────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│  PASO 1: DETECCIÓN DE SITUACIÓN (IA)                               │
│  ────────────────────────────────────                              │
│  Input: Texto del usuario                                          │
│  Output: situacion = "tusa-ruptura"                                │
│  Confidence: 0.95                                                   │
└────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│  PASO 2: IDENTIFICACIÓN DE AFRONTAMIENTO                           │
│  ────────────────────────────────────────                          │
│  Indicadores detectados: ["desahogarme"]                           │
│  Estilo: "extrovertido-despecho"                                   │
│  Géneros base: ["reggaeton", "salsa", "pop-latino"]                │
└────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│  PASO 3: CONTEXTO CULTURAL                                         │
│  ─────────────────────────                                         │
│  Ubicación: Colombia                                                │
│  Fecha: Diciembre 2024                                              │
│  Contexto: Navidad                                                  │
│  Ajuste: Incluir música navideña colombiana si aplica              │
└────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│  PASO 4: PERSONALIZACIÓN (API Spotify)                             │
│  ─────────────────────────────────────                             │
│  Top Géneros Usuario: ["metal", "rock-español", "alternativo"]     │
│  Top Artistas: ["Mägo de Oz", "Héroes del Silencio"]              │
│                                                                     │
│  CRUCE INTELIGENTE:                                                │
│  ┌─────────────────────┐   ┌─────────────────────┐                │
│  │ Estilo Afrontamiento│ + │  Gustos Personales  │                │
│  │ (Despecho Activo)   │   │  (Rock/Metal)       │                │
│  └─────────────────────┘   └─────────────────────┘                │
│              │                       │                             │
│              └───────────┬───────────┘                             │
│                          ▼                                         │
│  Resultado: Rock Latino de Empoderamiento                          │
└────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│  PASO 5: RECOMENDACIÓN FINAL                                       │
│  ───────────────────────────                                       │
│                                                                     │
│  🎵 Playlist Personalizada: "Rock para Superar - Despecho"         │
│                                                                     │
│  Canciones:                                                         │
│  1. "Florecita Rockera" - Aterciopelados                           │
│  2. "Labios Compartidos" - Maná                                    │
│  3. "No Me Compares" - Alejandro Sanz                              │
│  4. "Lamento Boliviano" - Enanitos Verdes                          │
│  5. "Persiana Americana" - Soda Stereo                             │
│                                                                     │
│  Spotify URI: spotify:playlist:xxxxx                               │
│  Mensaje: "He seleccionado rock latino que te ayudará a sentirte  │
│            fuerte y superar este momento. La música que elegí      │
│            combina energía con letras de empoderamiento."          │
└────────────────────────────────────────────────────────────────────┘
```

---

## 💻 Implementación Código Base

### 1. Servicio de Autenticación Spotify

```csharp
// src/spotify/auth/SpotifyAuthService.cs
public class SpotifyAuthService
{
    private readonly string _clientId;
    private readonly string _clientSecret;
    private readonly string _redirectUri;
    
    private readonly string[] _scopes = new[]
    {
        "user-top-read",
        "user-read-recently-played",
        "playlist-read-private",
        "user-read-private"
    };
    
    public string GetAuthorizationUrl(string state)
    {
        var scopeString = string.Join(" ", _scopes);
        return $"https://accounts.spotify.com/authorize?" +
               $"client_id={_clientId}&" +
               $"response_type=code&" +
               $"redirect_uri={Uri.EscapeDataString(_redirectUri)}&" +
               $"scope={Uri.EscapeDataString(scopeString)}&" +
               $"state={state}";
    }
    
    public async Task<SpotifyTokens> ExchangeCodeForTokens(string code);
    public async Task<SpotifyTokens> RefreshAccessToken(string refreshToken);
}
```

### 2. Cliente API Spotify

```csharp
// src/spotify/client/UserProfileService.cs
public class UserProfileService
{
    public async Task<UserMusicProfile> GetUserMusicProfile(string accessToken)
    {
        var topArtists = await GetTopArtists(accessToken, "medium_term", 20);
        var topTracks = await GetTopTracks(accessToken, "medium_term", 50);
        var recentlyPlayed = await GetRecentlyPlayed(accessToken, 50);
        
        return new UserMusicProfile
        {
            TopGenres = ExtractTopGenres(topArtists),
            TopArtists = topArtists,
            RecentMood = AnalyzeRecentMood(recentlyPlayed),
            PreferredLanguages = DetectLanguagePreferences(topTracks)
        };
    }
    
    private List<string> ExtractTopGenres(List<Artist> artists)
    {
        return artists
            .SelectMany(a => a.Genres)
            .GroupBy(g => g)
            .OrderByDescending(g => g.Count())
            .Take(10)
            .Select(g => g.Key)
            .ToList();
    }
}
```

### 3. Motor de Recomendaciones

```csharp
// src/psychology/recommendations/RecommendationEngine.cs
public class RecommendationEngine
{
    private readonly PlaylistCatalog _catalog;
    private readonly UserProfileService _userProfile;
    private readonly CulturalContextService _culturalContext;
    
    public async Task<MusicRecommendation> GetRecommendation(
        string userId,
        PsychologicalSituation situation,
        CopingStyle copingStyle)
    {
        // 1. Obtener playlist base curada
        var basePlaylist = _catalog.GetPlaylist(situation, copingStyle);
        
        // 2. Obtener contexto cultural
        var cultural = await _culturalContext.GetContext(userId);
        
        // 3. Si el usuario conectó Spotify, personalizar
        var userProfile = await _userProfile.GetUserMusicProfile(userId);
        
        if (userProfile != null)
        {
            // Cruzar gustos del usuario con la recomendación base
            return HybridMatch(basePlaylist, userProfile, cultural);
        }
        
        // Sin perfil, usar playlist curada base
        return ApplyCulturalContext(basePlaylist, cultural);
    }
    
    private MusicRecommendation HybridMatch(
        CuratedPlaylist basePlaylist,
        UserMusicProfile userProfile,
        CulturalContext cultural)
    {
        // Encontrar intersección entre géneros terapéuticos y gustos del usuario
        var matchingGenres = basePlaylist.Genres
            .Intersect(userProfile.TopGenres)
            .ToList();
        
        if (matchingGenres.Any())
        {
            // Hay match! Filtrar canciones que combinen ambos
            return new MusicRecommendation
            {
                Playlist = FilterByGenres(basePlaylist, matchingGenres),
                PersonalizationLevel = "high",
                Message = GeneratePersonalizedMessage(matchingGenres, cultural)
            };
        }
        
        // No hay match directo, buscar géneros similares
        return FindSimilarGenreMatch(basePlaylist, userProfile);
    }
}
```

### 4. Detector de Situación con IA

```csharp
// src/psychology/analysis/SituationDetector.cs
public class SituationDetector
{
    private readonly IGenAIService _aiService;
    
    public async Task<DetectionResult> DetectSituation(string userMessage)
    {
        var prompt = $@"
Analiza el siguiente mensaje y detecta:
1. Situación psicológica principal (ruptura, duelo, estrés financiero, ansiedad, etc.)
2. Estilo de afrontamiento deseado (activo/pasivo, extrovertido/introvertido)
3. Indicadores emocionales clave
4. Contexto cultural si se menciona

Mensaje: ""{userMessage}""

Responde en JSON con el formato:
{{
  ""situacion"": ""id-situacion"",
  ""estiloAfrontamiento"": ""id-estilo"",
  ""indicadores"": [""lista"", ""de"", ""indicadores""],
  ""confianza"": 0.95,
  ""contextoCultural"": ""pais-o-null""
}}";
        
        return await _aiService.GenerateStructured<DetectionResult>(prompt);
    }
}
```

---

## 🗄️ Modelos de Datos

### Playlist Curada

```csharp
// src/playlists/models/CuratedPlaylist.cs
public class CuratedPlaylist
{
    public string Id { get; set; }
    public string Nombre { get; set; }
    public string SpotifyUri { get; set; }  // spotify:playlist:xxxxx
    public string SpotifyUrl { get; set; }  // https://open.spotify.com/playlist/xxxxx
    
    public PsychologicalSituation Situacion { get; set; }
    public CopingStyle EstiloAfrontamiento { get; set; }
    public List<string> Genres { get; set; }
    public List<string> Tags { get; set; }  // ["empoderamiento", "energético", "despecho"]
    
    public CulturalContext? Contexto { get; set; }  // Colombia, Navidad, etc.
    
    public List<CuratedTrack> Canciones { get; set; }
}

public class CuratedTrack
{
    public string SpotifyId { get; set; }
    public string Nombre { get; set; }
    public string Artista { get; set; }
    public string Genre { get; set; }
    public List<string> EmotionalTags { get; set; }
    public string WhyIncluded { get; set; }  // "Letra de empoderamiento tras ruptura"
}
```

### Perfil de Usuario

```csharp
// src/spotify/models/UserPreferences.cs
public class UserMusicProfile
{
    public string UserId { get; set; }
    public List<string> TopGenres { get; set; }
    public List<ArtistSummary> TopArtists { get; set; }
    public List<string> PreferredLanguages { get; set; }  // ["es", "en"]
    
    public string Country { get; set; }  // Detectado de Spotify
    public MoodIndicator RecentMood { get; set; }  // Basado en reproducción reciente
    
    public DateTime LastUpdated { get; set; }
}
```

---

## 🔄 Flujo de Usuario Completo

### Sin Conexión Spotify (Solo Playlists Curadas)

```
1. Usuario: "Terminé con mi novia y me siento muy mal"
2. IA detecta: Situación = Ruptura, sin preferencia clara
3. Sistema pregunta: "¿Cómo te gustaría afrontar esto? 
   - 💪 Quiero sentirme fuerte y superarlo
   - 😢 Necesito procesar la tristeza
   - 🎉 Quiero distraerme con algo alegre"
4. Usuario elige: "Quiero sentirme fuerte"
5. Sistema detecta: Colombia + Diciembre = Navidad
6. Recomendación: Playlist curada "Despecho Navideño Colombiano"
   - Incluye: Karol G, vallenato de empoderamiento
   - Mensaje personalizado sobre la temporada
```

### Con Conexión Spotify (Personalización Completa)

```
1. Usuario: "Terminé con mi novia y me siento muy mal"
2. IA detecta: Situación = Ruptura
3. Sistema pregunta estilo de afrontamiento
4. Usuario: "Quiero sentirme fuerte"
5. Sistema consulta API Spotify:
   - Top géneros: Metal, Rock en español
   - Top artistas: Maná, Mägo de Oz
6. CRUCE INTELIGENTE:
   - Base: Despecho activo → Reggaetón, Salsa
   - Usuario: Metal, Rock español
   - Match: Rock Latino de empoderamiento
7. Recomendación HÍBRIDA:
   - Playlist: "Rock para Superar"
   - Incluye: Maná, Aterciopelados, Enanitos Verdes
   - Mensaje: "Basándome en tu amor por el rock, seleccioné
     canciones que te darán fuerza para superar este momento"
```

---

## 🛠️ Instalación y Configuración

### Prerrequisitos

- .NET 8.0+
- Cuenta de Spotify Developer
- Azure OpenAI o OpenAI API Key (para IA)

### Configuración

1. Clonar repositorio:
```bash
git clone https://github.com/Asperjasp/behuman-hackaton.git
cd behuman-hackaton
```

2. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

3. Restaurar dependencias:
```bash
dotnet restore
```

4. Ejecutar:
```bash
dotnet run --project src/api
```

### Variables de Entorno

```env
# Spotify API
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=https://localhost:5001/api/auth/spotify/callback

# AI Service
OPENAI_API_KEY=your_openai_key
# O para Azure OpenAI:
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your_key
AZURE_OPENAI_DEPLOYMENT=gpt-4

# Base de datos (para guardar tokens y perfiles)
DATABASE_CONNECTION_STRING=your_connection_string
```

---

## 📊 Ejemplo de Playlist Curada (JSON)

```json
// data/playlists/situations/tusa-ruptura.json
{
  "id": "tusa-ruptura-despecho-activo",
  "situacion": "tusa-ruptura",
  "estiloAfrontamiento": "extrovertido-despecho",
  "nombre": "Despecho Power 💪",
  "descripcion": "Canciones para sentirte fuerte después de una ruptura",
  "spotifyPlaylistUri": "spotify:playlist:37i9dQZF1DX1HCSbq2Lp9V",
  "genres": ["reggaeton", "pop-latino", "salsa", "urbano"],
  "tags": ["empoderamiento", "superacion", "fuerza", "independencia"],
  "canciones": [
    {
      "spotifyId": "7MXVkk9YMctZqd1Srtv4MB",
      "nombre": "Tusa",
      "artista": "Karol G, Nicki Minaj",
      "whyIncluded": "Himno del despecho moderno, letra de superación"
    },
    {
      "spotifyId": "xxx",
      "nombre": "Soltera",
      "artista": "Lunay",
      "whyIncluded": "Celebra la independencia post-ruptura"
    }
  ],
  "mensajeTerapeutico": "Estas canciones celebran tu fuerza y capacidad de superar. El despecho puede ser un motor para crecer."
}
```

---

## 🛒 Scraper de Tienda Compensar + Integración Supabase

Sistema de web scraping para extraer productos y servicios de [Tienda Compensar](https://www.tiendacompensar.com) y sincronizarlos con la base de datos Supabase para el sistema de recomendaciones.

### 📊 Flujo de Datos Completo

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PASO 1: SCRAPING                                                       │
│  python src/scraper/run_playwright_scraper.py                           │
│                                                                         │
│  • Usa Playwright (navegador Chromium headless)                         │
│  • Extrae precios A/B/C/No afiliado con hover simulation                │
│  • Guarda en data/compensar/productos.json                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  PASO 2: SUPABASE SYNC                                                  │
│  python src/scraper/supabase_sync.py                                    │
│                                                                         │
│  • Convierte productos al formato activity_catalog                      │
│  • Agrega TAGS automáticos para recomendaciones:                        │
│    - profile_tags: ["activo", "social", "creativo", ...]               │
│    - situation_tags: ["estrés alto", "ansiedad", "ánimo bajo", ...]    │
│  • Sube a Supabase                                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  SUPABASE: activity_catalog                                             │
│                                                                         │
│  Campos principales:                                                    │
│  • activity_title: "Pasadía Lagosol"                                   │
│  • category: "recreación" | "deporte" | "cultura" | "bienestar"        │
│  • price: { tipo_a: 33800, tipo_b: 34500, tipo_c: 44400 }             │
│  • profile_tags: ["social", "aventurero"]                              │
│  • situation_tags: ["ánimo bajo", "aislamiento social"]                │
│  • age_group: "adultos" | "niños" | "tercera edad" | "familiar"        │
└─────────────────────────────────────────────────────────────────────────┘
```

### 📂 Estructura del Scraper

```
src/scraper/
├── compensar_playwright_scraper.py  # ⭐ Scraper principal (Playwright + hover)
├── run_playwright_scraper.py        # CLI para ejecutar scraping
├── supabase_sync.py                 # ⭐ Sincronización con Supabase + Tags
├── database.py                      # Base de datos SQLite local
├── compensar_selenium_scraper.py    # (Legacy) Intento con Selenium
├── compensar_vtex_scraper.py        # (Legacy) Investigación API
├── investigate_api.py               # (Debug) Investigación endpoints
└── investigate_prices.py            # (Debug) Investigación hover
```

### 🔧 Instalación

```bash
# 1. Activar entorno virtual
source Behuman-Hackaton/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Instalar navegador para Playwright
playwright install chromium

# 4. Configurar Supabase (copiar y editar)
cp .env.example .env
# Editar .env con las credenciales de Supabase
```

### 🚀 Uso: Scraping Completo

```bash
# Scrapear TODAS las categorías (23 subcategorías)
python src/scraper/run_playwright_scraper.py

# Scrapear categorías específicas
python src/scraper/run_playwright_scraper.py --categoria turismo gimnasio spa

# Ver el navegador mientras scrapea (debug)
python src/scraper/run_playwright_scraper.py --show-browser

# Modo demo (solo 3 categorías)
python src/scraper/run_playwright_scraper.py --demo
```

### 🔄 Uso: Sincronizar con Supabase

```bash
# Ver qué se subiría (sin subir)
python src/scraper/supabase_sync.py --dry-run

# Subir productos a Supabase
python src/scraper/supabase_sync.py

# Buscar actividades por tags (para probar)
python src/scraper/supabase_sync.py --search "estrés alto" "ansiedad"
```

### 🏷️ Sistema de Tags Automáticos

El módulo `supabase_sync.py` asigna tags automáticamente según la subcategoría:

| Subcategoría | profile_tags | situation_tags |
|--------------|--------------|----------------|
| gimnasio | activo, disciplinado, competitivo | estrés alto, ansiedad, baja autoestima |
| turismo | social, aventurero, curioso | ánimo bajo, aislamiento social, agotamiento |
| sistemas | tecnológico, analítico, autodidacta | estancamiento profesional, baja autoestima |
| spa | tranquilo, autocuidado, relajado | estrés alto, ansiedad, agotamiento |
| musica | creativo, expresivo, artístico | ánimo bajo, estrés alto, necesidad de expresión |

### 🎯 Ejemplo de Recomendación

**Usuario**: Adolescente 19 años, problemas de confianza, le gusta el deporte

**Perfil detectado**:
```json
{
  "age_group": "adultos",
  "profile_tags": ["activo"],
  "situation_tags": ["baja autoestima"]
}
```

**Consulta SQL en Supabase**:
```sql
SELECT * FROM activity_catalog
WHERE situation_tags && ARRAY['baja autoestima']
  AND profile_tags && ARRAY['activo']
  AND age_group IN ('adultos', 'familiar')
ORDER BY relevance_score DESC;
```

**Resultado**: Gimnasio, Natación, Prácticas dirigidas

### 📊 Subcategorías Disponibles (23 total)

| Categoría | Subcategorías |
|-----------|---------------|
| **Deporte** | gimnasio, natacion-y-buceo, practicas-dirigidas, practicas-libres |
| **Cultura** | musica, actividades-culturales, manualidades, cocina, biblioteca |
| **Bienestar** | spa, bienestar-y-armonia, salud-para-adulto-mayor |
| **Recreación** | turismo, pasadias, planes, cine-y-entretenimiento, bolos |
| **Educación** | cursos, sistemas, clases-personalizadas |

### 🗃️ Base de Datos Local (SQLite)

Además de Supabase, los datos se guardan localmente en `data/compensar/compensar.db`:

```python
import sqlite3

conn = sqlite3.connect('data/compensar/compensar.db')
cursor = conn.cursor()

# Ver productos de turismo
cursor.execute('''
    SELECT nombre, precio_categoria_a, precio_categoria_b 
    FROM productos 
    WHERE subcategoria = 'turismo'
''')
for row in cursor.fetchall():
    print(row)
```

### 🔑 Variables de Entorno (.env)

```bash
# Supabase (obtener de tu compañero)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here

# OpenAI (para embeddings - futuro)
# OPENAI_API_KEY=your-key-here
```

### 📦 Dependencias del Scraper

```txt
# Web Scraping
playwright>=1.40.0        # Navegador headless
beautifulsoup4>=4.12.0    # Parsing HTML
lxml>=4.9.0               # Parser rápido

# Database
supabase>=2.0.0           # Cliente Supabase
python-dotenv>=1.0.0      # Variables de entorno

# Utilities
tqdm>=4.66.0              # Progress bars
```


---

## 📦 Estructura de Commits Python (Scraper)

### 🗂️ Archivos por Feature

| Commit | Archivos | Descripción |
|--------|----------|-------------|
| **1. Core Scraper** | `compensar_playwright_scraper.py`, `run_playwright_scraper.py` | Scraper principal con Playwright. Extrae productos con precios A/B/C usando hover |
| **2. Database** | `database.py` | Módulo de persistencia SQLite |
| **3. Scrapers Alternativos** | `compensar_scraper.py`, `compensar_selenium_scraper.py` | Intentos con Requests y Selenium (no funcionaron por JS dinámico) |
| **4. Investigación API** | `investigate_api.py`, `investigate_prices.py`, `compensar_vtex_scraper.py` | Scripts de investigación: descubrimos que usa Oracle Commerce Cloud con Knockout.js |
| **5. Configuración** | `__init__.py`, `requirements.txt`, `.gitignore` | Setup del proyecto Python |

### 📋 Comandos Git Sugeridos

```bash
# 1. Core Scraper (lo más importante)
git add src/scraper/compensar_playwright_scraper.py
git add src/scraper/run_playwright_scraper.py
git commit -m "feat(scraper): add Playwright scraper with hover for A/B/C prices

- Uses Playwright + BeautifulSoup for JS-rendered content
- Implements hover to reveal category prices (A, B, C, No afiliado)
- Exports to JSON and SQLite
- CLI with argparse for category selection"

# 2. Database module
git add src/scraper/database.py
git commit -m "feat(scraper): add SQLite database module for product storage"

# 3. Scrapers alternativos (histórico de intentos)
git add src/scraper/compensar_scraper.py
git add src/scraper/compensar_selenium_scraper.py
git commit -m "docs(scraper): add alternative scrapers (requests, selenium)

These were attempted before Playwright but don't work because:
- requests: Can't execute JavaScript
- selenium: WSL/Windows Chrome compatibility issues"

# 4. Investigación (opcional, pero documenta el proceso)
git add src/scraper/investigate_api.py
git add src/scraper/investigate_prices.py
git add src/scraper/compensar_vtex_scraper.py
git commit -m "docs(scraper): add API investigation scripts

Discovered Compensar uses:
- Oracle Commerce Cloud (not VTEX as initially thought)
- Knockout.js for dynamic content
- Hover-based price reveal for affiliation categories"

# 5. Configuración del proyecto
git add src/scraper/__init__.py
git add requirements.txt
git add .gitignore
git commit -m "chore: add Python project configuration

- requirements.txt with playwright, beautifulsoup4, lxml
- .gitignore for data/, venv, __pycache__, test/"

# 6. Push todos los commits
git push origin main
```

### 🧹 Archivos Ignorados (No commitear)

| Carpeta/Archivo | Razón |
|-----------------|-------|
| `data/` | Datos scrapeados (generados, no código) |
| `Behuman-Hackaton/` | Virtual environment |
| `__pycache__/` | Bytecode Python compilado |
| `test/` | Tutoriales y pruebas (learn_scraping.py) |

### 🔍 Resumen Técnico del Scraper

**¿Por qué Playwright?**  
Tienda Compensar usa Oracle Commerce Cloud con Knockout.js que renderiza contenido dinámicamente. Requests/BeautifulSoup solo no pueden ver el contenido.

**¿Por qué hover?**  
Los precios por categoría (A, B, C, No afiliado) solo se muestran cuando el usuario pasa el mouse sobre los botones correspondientes. Playwright simula esto con `element.hover()`.

**Stack final:**
- `playwright` - Automatización de navegador
- `beautifulsoup4` + `lxml` - Parsing HTML
- `sqlite3` - Base de datos

---

## 🎯 Roadmap

- [x] Diseño de arquitectura
- [x] Scraper de Tienda Compensar
- [x] Extracción de precios por categoría (A/B/C/No afiliado) con hover
- [ ] Implementación autenticación Spotify OAuth
- [ ] Base de datos de playlists curadas (50+ playlists)
- [ ] Motor de detección de situaciones con IA
- [ ] Sistema de matching híbrido
- [ ] Contexto cultural automático (geolocalización + fecha)
- [ ] API REST completa
- [ ] Frontend/Chatbot de prueba
- [ ] Integración con sistemas de chat (WhatsApp, Telegram)

---

## 👥 Contribuir

### Cómo agregar nuevas playlists curadas

1. Crear archivo JSON en `data/playlists/situations/`
2. Seguir el esquema de `CuratedPlaylist`
3. Incluir `whyIncluded` para cada canción (razón terapéutica)
4. Agregar tags emocionales apropiados

### Cómo agregar contextos culturales

1. Editar `data/playlists/cultural/`
2. Incluir fechas relevantes y playlists asociadas

---

## 📄 Licencia

MIT License - Ver [LICENSE](LICENSE) para más detalles.

---

## 🙏 Agradecimientos

- Equipo de psicólogos consultores
- Curadores musicales culturales
- Spotify Web API
