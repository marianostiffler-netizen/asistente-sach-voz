# Asistente de Carga de Reservas SACH

Asistente completo de voz para procesar reservas y cargarlas automáticamente en SACH usando IA de Groq (Whisper + Llama 3) y automatización con Playwright.

## Configuración

1. **Activar entorno virtual:**
   ```bash
   source venv/bin/activate
   ```

2. **Configurar API Keys y credenciales:**
   - Edita el archivo `.env`
   - **GROQ_API_KEY**: Tu API key de Groq (https://console.groq.com/)
   - **SACH_USER**: Tu usuario de SACH
   - **SACH_PASS**: Tu contraseña de SACH

3. **Instalar dependencias (ya hecho):**
   ```bash
   pip install groq python-dotenv playwright
   playwright install
   ```

## Uso

### Opción 1: Asistente completo (recomendado)
Procesa audio y carga automáticamente en SACH:
```bash
python asistente_completo.py audios_prueba/tu_audio.wav
```

### Opción 2: Solo procesar audio
```bash
python procesar_audio.py audios_prueba/tu_audio.wav
```

### Opción 3: Solo cargar reserva (con JSON)
```bash
python cargar_reserva.py '{"nombre":"Juan Pérez","cabana":"Cabaña 3","fecha_entrada":"2024-02-15","noches":3,"precio":15000}'
```

## Formato de salida JSON

```json
{
    "nombre": "Juan Pérez",
    "cabana": "Cabaña 3", 
    "fecha_entrada": "2024-02-15",
    "noches": 3,
    "precio": 15000
}
```

## Mapeo de campos

| Dato Audio → Campo SACH | Estado |
|------------------------|---------|
| `nombre` → `Cliente` | ✅ Compatible |
| `cabana` → `Cabaña` | ✅ Compatible |
| `fecha_entrada` → `Fecha Ingreso` | ✅ Compatible |
| `noches` → `Fecha Egreso` | ⚠️ Calculado automáticamente |
| `precio` → `Tarifa` | ✅ Compatible |

## Estructura del proyecto

```
asistente-sach-voz/
├── .env                     # Configuración de API keys y credenciales
├── procesar_audio.py       # Procesamiento de audio con IA
├── cargar_reserva.py       # Robot de carga en SACH
├── asistente_completo.py   # Integración completa
├── audios_prueba/         # Carpeta para audios de prueba
├── venv/                  # Entorno virtual
└── README.md             # Este archivo
```

## Tecnologías

- **Groq Whisper**: Transcripción de audio a texto
- **Groq Llama 3.3**: Extracción de datos estructurados
- **Playwright**: Automatización web para SACH
- **Python**: Lenguaje principal

## Flujo de trabajo

1. 🎙️ **Procesar audio**: Whisper transcribe el audio
2. 🧠 **Extraer datos**: Llama 3 extrae datos estructurados
3. 🤖 **Cargar reserva**: Playwright automatiza la carga en SACH
4. ✅ **Confirmar**: Revisión manual antes de guardar
