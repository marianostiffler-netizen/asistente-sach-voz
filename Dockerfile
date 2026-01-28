# Usamos la imagen oficial de Playwright que ya incluye Python y los navegadores
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

# Establecer directorio de trabajo
WORKDIR /app

# Copiar los archivos del proyecto
COPY . .

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Instalar el navegador explícitamente (por seguridad)
RUN playwright install chromium

# Comando para iniciar la app
CMD ["python", "app.py"]
