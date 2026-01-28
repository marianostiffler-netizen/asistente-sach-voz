from flask import Flask, request, Response
import os
import json
import requests
from procesar_audio import ProcesadorAudio
from cargar_reserva import RobotSACH
import tempfile
import urllib.parse

app = Flask(__name__)

# Configuración de WhatsApp desde variables de entorno
WHATSAPP_VERIFY_TOKEN = os.getenv('WHATSAPP_VERIFY_TOKEN', 'mytoken')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '914504238421045')
WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')

# Log para verificar qué token se está usando
print(f'🔑 Usando token que empieza con: {WHATSAPP_TOKEN[:10] if WHATSAPP_TOKEN else "NONE"}')
print(f'📱 Phone ID: {WHATSAPP_PHONE_NUMBER_ID}')
print(f'🔐 Verify Token: {WHATSAPP_VERIFY_TOKEN}')

# Inicializar procesador de audio
procesador_audio = ProcesadorAudio()

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Verificación del webhook de WhatsApp
        if request.args.get('hub.mode') == 'subscribe' and \
           request.args.get('hub.verify_token') == WHATSAPP_VERIFY_TOKEN:
            return request.args.get('hub.challenge'), 200
        else:
            return 'Verification token mismatch', 403
    
    elif request.method == 'POST':
        # Procesar mensajes entrantes
        data = request.get_json()
        
        try:
            # Verificar si es un mensaje de WhatsApp
            if 'object' in data and data['object'] == 'whatsapp_business_account':
                for entry in data.get('entry', []):
                    for change in entry.get('changes', []):
                        if 'messages' in change.get('value', {}):
                            messages = change['value']['messages']
                            for message in messages:
                                if message.get('type') == 'audio':
                                    handle_audio_message(message)
                                elif message.get('type') == 'text':
                                    handle_text_message(message)
            
            return 'OK', 200
            
        except Exception as e:
            print(f"Error processing webhook: {e}")
            return 'Error', 500

def handle_audio_message(message):
    """Procesar mensaje de audio de WhatsApp"""
    try:
        # Obtener información del audio
        audio_id = message['audio']['id']
        from_number = message['from']
        
        print(f"🎵 Audio recibido de: {from_number}")
        print(f"📋 Audio ID: {audio_id}")
        
        # Descargar audio desde WhatsApp
        audio_url = get_media_url(audio_id)
        audio_data = download_audio(audio_url)
        
        # Guardar audio temporalmente
        with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_audio_path = temp_file.name
        
        try:
            # Procesar audio con Groq
            print("🎙️ Procesando audio...")
            texto_transcrito = procesador_audio.transcribir_audio(temp_audio_path)
            print(f"📝 Texto transcrito: {texto_transcrito}")
            
            # Extraer datos de la reserva
            print("🔍 Extrayendo datos...")
            datos_reserva = procesador_audio.extraer_datos_reserva(texto_transcrito)
            print(f"📊 Datos extraídos: {datos_reserva}")
            
            # Cargar en SACH
            print("🤖 Cargando en SACH...")
            robot = RobotSACH()
            resultado = robot.procesar_cliente(datos_reserva)
            
            if resultado:
                response_text = f"✅ ¡Reserva procesada!\n\n📋 Datos:\n• Cliente: {datos_reserva.get('nombre', 'N/A')}\n• Cabaña: {datos_reserva.get('cabana', 'N/A')}\n• Entrada: {datos_reserva.get('fecha_entrada', 'N/A')}\n• Noches: {datos_reserva.get('noches', 'N/A')}\n• Precio: ${datos_reserva.get('precio', 'N/A')}\n\n🎉 Cliente guardado en SACH"
            else:
                response_text = "❌ Error al procesar la reserva. Por favor, intenta nuevamente."
            
            # Enviar respuesta a WhatsApp
            send_whatsapp_message(from_number, response_text)
            
        finally:
            # Limpiar archivo temporal
            os.unlink(temp_audio_path)
            
    except Exception as e:
        print(f"Error processing audio message: {e}")
        error_text = "❌ Error al procesar el audio. Por favor, intenta nuevamente."
        send_whatsapp_message(message['from'], error_text)

def handle_text_message(message):
    """Procesar mensaje de texto de WhatsApp"""
    try:
        text = message['text']['body']
        from_number = message['from']
        
        print(f"💬 Texto recibido de {from_number}: {text}")
        
        # Mensaje de bienvenida y ayuda
        if 'hola' in text.lower() or 'help' in text.lower():
            response_text = """🤖 ¡Hola! Soy el asistente de voz para SACH.

🎙️ Para procesar una reserva:
1. Envíame un mensaje de voz con los datos de la reserva
2. Te procesaré automáticamente la información
3. Cargaré el cliente en SACH

📋 Información que mencionar:
• Nombre completo del cliente
• Número de cabaña
• Fecha de entrada
• Cantidad de noches
• Precio total

🚀 ¡Estoy listo para ayudarte!"""
        else:
            response_text = """🎙️ Por favor, envíame un mensaje de voz con los datos de la reserva.

📋 Menciona:
• Nombre del cliente
• Número de cabaña  
• Fecha de entrada
• Noches y precio

🤖 Procesaré todo automáticamente."""
        
        send_whatsapp_message(from_number, response_text)
        
    except Exception as e:
        print(f"Error processing text message: {e}")

def get_media_url(media_id):
    """Obtener URL de descarga de media de WhatsApp"""
    url = f"https://graph.facebook.com/v18.0/{media_id}"
    headers = {
        'Authorization': f'Bearer {WHATSAPP_TOKEN}'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['url']
    else:
        raise Exception(f"Error getting media URL: {response.status_code}")

def download_audio(audio_url):
    """Descargar archivo de audio"""
    headers = {
        'Authorization': f'Bearer {WHATSAPP_TOKEN}'
    }
    
    response = requests.get(audio_url, headers=headers)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Error downloading audio: {response.status_code}")

def send_whatsapp_message(to_number, message_text):
    """Enviar mensaje de WhatsApp"""
    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    
    headers = {
        'Authorization': f'Bearer {WHATSAPP_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # Formatear número para WhatsApp - eliminar prefijos para usar solo el número base
    formatted_number = to_number
    
    # Eliminar todos los prefijos para dejar solo el número de 10 dígitos
    if formatted_number.startswith('+549'):
        formatted_number = formatted_number[4:]  # Quitar +549
    elif formatted_number.startswith('549'):
        formatted_number = formatted_number[3:]  # Quitar 549
    elif formatted_number.startswith('+54'):
        formatted_number = formatted_number[3:]  # Quitar +54
    elif formatted_number.startswith('54'):
        formatted_number = formatted_number[2:]  # Quitar 54
    
    # Asegurarse de que tenga 10 dígitos (formato argentino sin prefijo)
    if len(formatted_number) == 10 and formatted_number.startswith('9'):
        formatted_number = formatted_number[1:]  # Quitar el 9 inicial
    
    print(f"📱 Número original: {to_number}")
    print(f"📱 Número formateado: {formatted_number}")
    
    data = {
        "messaging_product": "whatsapp",
        "to": formatted_number,
        "type": "text",
        "text": {
            "body": message_text
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print(f"✅ Mensaje enviado a {to_number}")
    else:
        print(f"❌ Error enviando mensaje: {response.status_code} - {response.text}")

@app.route('/')
def home():
    return Response("🤖 Asistente SACH Voz - WhatsApp Webhook Activo", status=200)

@app.route('/health')
def health():
    return Response("✅ OK", status=200)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
