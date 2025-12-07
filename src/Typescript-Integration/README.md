# BeHuman TypeScript Integration

Módulo TypeScript para el sistema de recomendación empático BeHuman. Diseñado para integrarse fácilmente en aplicaciones Next.js.

## 📦 Archivos

| Archivo | Descripción |
|---------|-------------|
| `types.ts` | Interfaces y tipos TypeScript |
| `supabaseClient.ts` | Cliente Supabase y funciones de consulta |
| `recommender.ts` | Motor de recomendación y clasificación |
| `hrWorkflow.ts` | Flujo de trabajo HR y notificaciones |
| `index.ts` | Punto de entrada y exports |

## 🚀 Instalación en Next.js

1. **Copia los archivos** a tu proyecto Next.js:

```bash
# Desde la raíz de tu proyecto Next.js
mkdir -p src/lib/behuman
cp -r /path/to/src/Typescript-Integration/*.ts src/lib/behuman/
```

2. **Instala dependencias**:

```bash
npm install @supabase/supabase-js
```

3. **Configura variables de entorno** en `.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=https://tu-proyecto.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=tu-anon-key
SUPABASE_SERVICE_ROLE_KEY=tu-service-role-key  # Solo para operaciones del servidor
```

## 💡 Uso

### Flujo completo desde transcript de voz

```typescript
import { processTranscript } from '@/lib/behuman';

// En tu API route o Server Action
export async function POST(request: Request) {
  const { transcript, profile } = await request.json();
  
  const result = await processTranscript(transcript, profile);
  
  return Response.json({
    situation: result.situation,
    empathicMessage: result.empathicMessage,
    hrCards: result.hrCards,
  });
}
```

### Clasificar situación

```typescript
import { classifySituation } from '@/lib/behuman';

const situation = classifySituation(
  "Me siento muy abrumado con el trabajo, las fechas límite me estresan..."
);

console.log(situation);
// {
//   type: 'estres_laboral',
//   subtype: 'sobrecarga',
//   context: 'Estrés relacionado con carga de trabajo...',
//   confidence: 0.85
// }
```

### Obtener recomendaciones

```typescript
import { getRecommendations } from '@/lib/behuman';

const profile = {
  userId: 'anon-123',
  name: 'Usuario',
  hobbies: ['yoga', 'música'],
  goals: ['reducir estrés'],
};

const situation = {
  type: 'estres_laboral',
  context: 'Sobrecarga de trabajo',
};

const result = await getRecommendations(profile, situation, transcript);

console.log(result.empathicMessage);
console.log(result.recommendations);
```

### Flujo HR

```typescript
import { 
  generateHRWorkflow, 
  hrAccept, 
  hrReject 
} from '@/lib/behuman';

// 1. Generar tarjetas HR
const result = await generateHRWorkflow(profile, situation, transcript);
console.log(result.hrCards); // Array de 2 tarjetas

// 2. HR acepta una tarjeta
if (result.hrCards.length > 0) {
  const acceptedCard = { ...result.hrCards[0], status: 'accepted' };
  const notification = hrAccept(profile, situation, acceptedCard, result.empathicMessage);
  
  // notification contiene el mensaje para el empleado
  console.log(notification.message);
  console.log(notification.intervention);
}

// O rechazar
const rejectedCard = hrReject(result.hrCards[1], 'No aplica para este caso');
```

## 📊 Estructura de Datos

### Perfil (Profile)
```typescript
interface Profile {
  userId: string;
  name: string;
  age?: number;
  gender?: 'masculino' | 'femenino' | 'no-binario' | string;
  hobbies: string[];
  goals: string[];
}
```

### Situación (Situation)
```typescript
interface Situation {
  type: SituationType | string;  // 'estres_laboral', 'ansiedad', etc.
  subtype?: string;
  context: string;
  confidence?: number;
}
```

### Tarjeta HR (HRCard)
```typescript
interface HRCard {
  id: string;
  product: Product;
  title: string;
  subtitle: string;
  explanation: string;
  estimatedProductivityUpliftPercent: number;
  score: number;
  status: 'pending' | 'accepted' | 'rejected';
}
```

### Notificación Empleado (EmployeeNotification)
```typescript
interface EmployeeNotification {
  id: string;
  anonymous: true;
  message: string;
  intervention: {
    title: string;
    description: string;
    url: string;
    category: string;
    price: number;
    estimatedProductivityUpliftPercent: number;
  };
}
```

## 🔧 Configuración de Situaciones

El sistema reconoce 6 tipos principales de situaciones:

| Tipo | Descripción | Actividades Beneficiosas |
|------|-------------|-------------------------|
| `perdida_familiar` | Pérdida de un familiar | Arte, música, naturaleza |
| `ruptura_amorosa` | Fin de relación | Deportes grupales, baile |
| `ansiedad` | Estados de ansiedad | Yoga, meditación, respiración |
| `soledad` | Aislamiento social | Actividades grupales, talleres |
| `estres_laboral` | Estrés del trabajo | Spa, relajación, hobbies |
| `duelo` | Proceso de duelo | Terapia, apoyo emocional |

## 📝 Base de Datos

Tabla Supabase: `Compensar-Database`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | int8 | ID único |
| `nombre` | text | Nombre del producto |
| `descripcion` | text | Descripción |
| `precio_desde` | int8 | Precio mínimo |
| `subcategoria` | text | Subcategoría |
| `categoria_principal` | text | Categoría principal |
| `url` | text | URL del producto |
| `profile_tags` | text[] | Tags de perfil |
| `situation_tags` | text[] | Tags de situación |

## 🎯 Ejemplo Completo con ElevenLabs

```typescript
// pages/api/process-voice.ts
import { processTranscript, hrAccept } from '@/lib/behuman';
import type { Profile } from '@/lib/behuman';

export async function POST(request: Request) {
  // Transcript del agente de voz ElevenLabs
  const { transcript } = await request.json();
  
  // Perfil anónimo del empleado
  const profile: Profile = {
    userId: `anon-${Date.now()}`,
    name: 'Empleado',
    hobbies: ['lectura'],  // Puede venir del transcript
    goals: ['bienestar'],
  };
  
  // Procesar y generar recomendaciones
  const result = await processTranscript(transcript, profile);
  
  return Response.json({
    success: true,
    data: {
      situation: result.situation,
      empathicMessage: result.empathicMessage,
      hrCards: result.hrCards,
    },
  });
}
```

## 📄 Licencia

MIT © BeHuman Team
