#!/usr/bin/env python3
"""
Script de debug para analizar la página de login de SACH
"""

from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv

load_dotenv()

def debug_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("Navegando a SACH...")
        page.goto("https://reservation.sach.com.ar/")
        
        # Esperar a que cargue
        page.wait_for_timeout(3000)
        
        print(f"Título: {page.title()}")
        print(f"URL actual: {page.url}")
        
        # Listar todos los inputs
        inputs = page.locator('input')
        print(f"\nInputs encontrados: {inputs.count()}")
        
        for i in range(inputs.count()):
            input_elem = inputs.nth(i)
            print(f"Input {i}: id='{input_elem.get_attribute('id')}', name='{input_elem.get_attribute('name')}', type='{input_elem.get_attribute('type')}', placeholder='{input_elem.get_attribute('placeholder')}'")
        
        # Intentar llenar los campos directamente
        try:
            page.fill('input#usuario', 'marians_rc@hotmail.com')
            print("✅ Campo usuario llenado")
        except Exception as e:
            print(f"❌ Error llenando usuario: {e}")
        
        try:
            page.fill('input#password', '4556320Mar')
            print("✅ Campo contraseña llenado")
        except Exception as e:
            print(f"❌ Error llenando contraseña: {e}")
        
        # Screenshot
        page.screenshot(path="debug_after_fill.png")
        print("Screenshot guardado como debug_after_fill.png")
        
        print("\nPresioná Enter para cerrar...")
        input()
        
        browser.close()

if __name__ == "__main__":
    debug_login()
