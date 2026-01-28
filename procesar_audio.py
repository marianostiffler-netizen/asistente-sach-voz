#!/usr/bin/env python3
"""
Asistente de procesamiento de audio para reservas SACH
Usa Groq Whisper para transcripción y Llama 3 para extracción de datos
"""

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

# Cargar variables de entorno
load_dotenv()

class ProcesadorAudio:
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ_API_KEY no encontrada en el archivo .env")
        
        self.client = Groq(api_key=self.api_key)
        
    def transcribir_audio(self, archivo_audio):
        """
        Transcribe el archivo de audio usando Whisper de Groq
        """
        try:
            with open(archivo_audio, "rb") as file:
                transcription = self.client.audio.transcriptions.create(
                    file=(archivo_audio, file.read()),
                    model="whisper-large-v3-turbo",
                    language="es",  # Español
                    response_format="text"
                )
            return transcription
        except Exception as e:
            print(f"Error en transcripción: {e}")
            return None
    
    def extraer_datos_reserva(self, texto_transcrito):
        """
        Usa Llama 3 para extraer datos estructurados del texto transcrito
        """
        prompt = f"""
Analiza el siguiente texto de una reserva y extrae la información en formato JSON.
Solo responde con el JSON, sin texto adicional.

Texto: "{texto_transcrito}"

Extrae los siguientes campos si están presentes:
- nombre: Nombre completo del huésped
- cabana: Número o nombre de la cabaña
- fecha_entrada: Fecha de check-in (formato YYYY-MM-DD)
- noches: Cantidad de noches
- precio: Precio total de la reserva

Ejemplo de respuesta esperada:
{{
    "nombre": "Juan Pérez",
    "cabana": "Cabaña 3",
    "fecha_entrada": "2024-02-15",
    "noches": 3,
    "precio": 15000
}}

Si algún dato no está presente, usa null:
"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Eres un asistente experto en extraer datos de reservas. Responde solo con JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # Limpiar y parsear el JSON
            contenido = response.choices[0].message.content.strip()
            
            # Intentar encontrar el JSON en la respuesta
            if contenido.startswith('```json'):
                contenido = contenido[7:-3].strip()
            elif contenido.startswith('```'):
                contenido = contenido[3:-3].strip()
                
            return json.loads(contenido)
            
        except json.JSONDecodeError as e:
            print(f"Error parseando JSON: {e}")
            print(f"Contenido recibido: {contenido}")
            return None
        except Exception as e:
            print(f"Error en extracción de datos: {e}")
            return None
    
    def procesar_audio(self, archivo_audio):
        """
        Procesa el archivo de audio completo y devuelve los datos estructurados
        """
        print(f"Procesando archivo: {archivo_audio}")
        
        # Verificar que el archivo existe
        if not Path(archivo_audio).exists():
            raise FileNotFoundError(f"No se encuentra el archivo: {archivo_audio}")
        
        # Transcribir audio
        print("Transcribiendo audio...")
        texto = self.transcribir_audio(archivo_audio)
        if not texto:
            return None
        
        print(f"Texto transcrito: {texto}")
        
        # Extraer datos
        print("Extrayendo datos de la reserva...")
        datos = self.extraer_datos_reserva(texto)
        
        return datos

def main():
    if len(sys.argv) != 2:
        print("Uso: python procesar_audio.py <archivo_audio>")
        sys.exit(1)
    
    archivo_audio = sys.argv[1]
    
    try:
        procesador = ProcesadorAudio()
        resultado = procesador.procesar_audio(archivo_audio)
        
        if resultado:
            print("\n=== DATOS EXTRAÍDOS ===")
            print(json.dumps(resultado, indent=2, ensure_ascii=False))
            return resultado
        else:
            print("No se pudieron extraer los datos")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    main()
