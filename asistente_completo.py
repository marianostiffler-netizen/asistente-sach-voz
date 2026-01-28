#!/usr/bin/env python3
"""
Asistente Completo de Reservas SACH
Procesa audio y carga automáticamente la reserva en SACH
"""

import os
import json
import sys
from procesar_audio import ProcesadorAudio
from cargar_reserva import RobotSACH

class AsistenteCompleto:
    def __init__(self):
        self.procesador_audio = ProcesadorAudio()
        self.robot_sach = RobotSACH()
    
    def procesar_y_cargar(self, archivo_audio):
        """Procesa el audio y carga el cliente en SACH"""
        print("🎙️  FASE 1: Procesando audio...")
        
        # Procesar audio
        datos_cliente = self.procesador_audio.procesar_audio(archivo_audio)
        
        if not datos_cliente:
            print("❌ No se pudieron extraer datos del audio")
            return False
        
        print(f"✅ Datos extraídos: {json.dumps(datos_cliente, indent=2, ensure_ascii=False)}")
        
        # Pausar para confirmación
        print("\n⏸️  ¿Querés continuar con la carga del cliente en SACH? (Enter para continuar, Ctrl+C para cancelar)")
        input()
        
        print("\n🤖 FASE 2: Cargando cliente en SACH...")
        
        # Cargar en SACH
        resultado = self.robot_sach.procesar_cliente(datos_cliente)
        
        return resultado

def main():
    if len(sys.argv) != 2:
        print("Uso: python asistente_completo.py <archivo_audio>")
        print("Ejemplo: python asistente_completo.py audios_prueba/reserva.wav")
        sys.exit(1)
    
    archivo_audio = sys.argv[1]
    
    try:
        asistente = AsistenteCompleto()
        resultado = asistente.procesar_y_cargar(archivo_audio)
        
        if resultado:
            print("\n🎉 ¡Proceso completado exitosamente!")
            print("✅ Audio procesado y cliente cargado en SACH")
        else:
            print("\n❌ El proceso falló")
            
    except KeyboardInterrupt:
        print("\n⏹️  Proceso cancelado por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
