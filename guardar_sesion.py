#!/usr/bin/env python3
"""
Script para guardar la sesión de SACH (Storage State)
Permite evitar el captcha guardando las cookies y estado de autenticación
"""

from playwright.sync_api import sync_playwright

def guardar_sesion():
    print("--- VENTANA ABIERTA: LOGUEATE AHORA ---")
    
    with sync_playwright() as p:
        print("🚀 Iniciando navegador...")
        browser = p.chromium.launch(headless=False)  # Ventana visible
        context = browser.new_context()
        page = context.new_page()
        
        print("📝 Navegando a https://sach.com.ar/iniciar")
        page.goto("https://sach.com.ar/iniciar")
        
        print("🔐 LOGUEATE MANUALMENTE Y RESOLVÉ EL CAPTCHA")
        print("💾 Cuando termines, volvé a esta terminal y presioná Enter")
        
        # Esperar a que el usuario termine de loguearse
        print("⏳ Esperando a que termines...")
        input("Presioná Enter después de loguearte...")
        
        # Guardar el estado de autenticación
        print("💾 Guardando estado de autenticación...")
        context.storage_state(path="auth.json")
        
        print("✅ Sesión guardada en auth.json")
        print("🎉 Ahora el robot podrá usar esta sesión para evitar el captcha")
        
        browser.close()
        print("🔒 Navegador cerrado")

if __name__ == "__main__":
    guardar_sesion()
