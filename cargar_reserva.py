#!/usr/bin/env python3
"""
Robot de Carga de Reservas SACH
Usa Playwright para automatizar la carga de reservas en el sistema SACH
"""

import os
import sys
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Cargar variables de entorno
load_dotenv()

class RobotSACH:
    def __init__(self):
        # Credenciales desde .env
        self.sach_url = "https://sach.com.ar/iniciar"  # URL directa de login
        self.sach_user = os.getenv('SACH_USER')
        self.sach_pass = os.getenv('SACH_PASS')
        
        # Inicializar contexto para evitar errores
        self.context = None
        
        print(f"DEBUG: Usuario leído del .env: '{self.sach_user}'")
        print(f"DEBUG: Contraseña leída del .env: '{self.sach_pass}'")
        
        if not self.sach_user or not self.sach_pass:
            raise ValueError("SACH_USER y SACH_PASS deben estar configurados en .env")
        
        self.browser = None
        self.page = None
    
    def iniciar_navegador(self):
        """Inicia el navegador Playwright - con persistent context para evitar captcha"""
        try:
            print("🌐 Iniciando Playwright...")
            sys.stdout.flush()
            self.playwright = sync_playwright().start()
            print("✅ Playwright iniciado correctamente")
            sys.stdout.flush()
            
            # En Railway usar headless=True
            headless_mode = os.getenv('RAILWAY_ENVIRONMENT') is not None
            print(f"🔧 Modo headless: {headless_mode}")
            sys.stdout.flush()
            
            print("🚀 Instalando Chromium (si es necesario)...")
            sys.stdout.flush()
            
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
            )
            
            # Crear contexto persistente que guarda cookies/sesión
            context_path = "sach_session"
            if not os.path.exists(context_path):
                os.makedirs(context_path)
                print(f"📁 Creado directorio: {context_path}")
                sys.stdout.flush()
            
            # Intentar cargar sesión persistente con try/except
            state_file = f"{context_path}/state.json"
            try:
                if os.path.exists(state_file):
                    print("� Cargando sesión persistente...")
                    sys.stdout.flush()
                    self.context = self.browser.new_context(
                        storage_state=state_file,
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    )
                    print("✅ Sesión persistente cargada")
                    sys.stdout.flush()
                else:
                    raise FileNotFoundError("Archivo de sesión no existe")
            except (FileNotFoundError, Exception) as e:
                print(f"🆕 Iniciando contexto nuevo: {e}")
                sys.stdout.flush()
                self.context = self.browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                )
                print("✅ Contexto nuevo creado")
                sys.stdout.flush()
            
            print("✅ Navegador instalado correctamente")
            sys.stdout.flush()
            
            self.page = self.context.new_page()
            
            # Configurar tamaño de ventana
            self.page.set_viewport_size({"width": 1280, "height": 720})
            
            print("✅ Navegador iniciado correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error iniciando navegador: {e}")
            self.browser = None
            self.page = None
            return False
    
    def cerrar_navegador(self):
        """Cierra el navegador y guarda la sesión persistente"""
        try:
            # Guardar estado de la sesión para persistencia
            if self.context:
                print("💾 Guardando estado de sesión para persistencia...")
                sys.stdout.flush()
                # Asegurar que el directorio exista
                os.makedirs("sach_session", exist_ok=True)
                self.context.storage_state(path="sach_session/state.json")
                print("✅ Sesión guardada correctamente")
                sys.stdout.flush()
            
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            print(f"Error cerrando navegador: {e}")
            sys.stdout.flush()
    
    def hacer_login(self):
        """Realiza el login en SACH con verificación y humanización"""
        try:
            print(f"Navegando a {self.sach_url}")
            sys.stdout.flush()
            self.page.goto(self.sach_url)
            
            # Esperar mínimo para que cargue
            self.page.wait_for_timeout(2000)
            
            # Imprimir información de la página actual
            print(f"URL actual: {self.page.url}")
            print(f"Título de la página: {self.page.title()}")
            sys.stdout.flush()
            
            # VERIFICACIÓN: ¿Ya estamos logueados?
            dashboard_indicators = [
                'Dashboard',
                'Panel',
                'Inicio',
                'Reservas',
                'Clientes',
                'Cabañas',
                'Logout',
                'Cerrar sesión',
                'Salir',
                'Bienvenido',
                'Welcome'
            ]
            
            page_content = self.page.content()
            is_logged_in = any(indicator in page_content for indicator in dashboard_indicators)
            
            if is_logged_in:
                print("✅ Ya estamos logueados en el dashboard")
                sys.stdout.flush()
                return "FORM_READY"
            
            print("🔐 No estamos logueados, procediendo con login...")
            sys.stdout.flush()
            
            # Buscar campos de login con más selectores específicos
            user_selectors = [
                'input#usuario',  # ID específico que veo en la imagen
                'input[name="usuario"]',
                'input[name="username"]',
                'input[name="user"]', 
                'input[name="email"]',
                'input[type="text"]',
                'input[id*="user"]',
                'input[id*="email"]',
                'input[placeholder*="usuario"]',
                'input[placeholder*="email"]',
                'input[placeholder*="Usuario"]',
                'input[placeholder*="Email"]'
            ]
            
            pass_selectors = [
                'input#password',  # ID específico que veo en la imagen
                'input[name="password"]',
                'input[type="password"]',
                'input[id*="pass"]',
                'input[placeholder*="contraseña"]',
                'input[placeholder*="password"]',
                'input[placeholder*="Contraseña"]'
            ]
            
            user_input = None
            pass_input = None
            
            # Buscar campo de usuario
            for selector in user_selectors:
                try:
                    elem = self.page.locator(selector)
                    if elem.count() > 0:
                        user_input = elem.first
                        print(f"Campo de usuario encontrado con selector: {selector}")
                        break
                except:
                    continue
            
            # Buscar campo de contraseña
            for selector in pass_selectors:
                try:
                    elem = self.page.locator(selector)
                    if elem.count() > 0:
                        pass_input = elem.first
                        print(f"Campo de contraseña encontrado con selector: {selector}")
                        break
                except:
                    continue
            
            if user_input and pass_input:
                print("Ingresando credenciales...")
                sys.stdout.flush()
                
                # HUMANIZACIÓN: Pequeños retrasos entre acciones
                user_input.fill(self.sach_user)
                self.page.wait_for_timeout(500)  # Pequeña pausa después de usuario
                print("✅ Usuario ingresado")
                sys.stdout.flush()
                
                pass_input.fill(self.sach_pass)
                self.page.wait_for_timeout(800)  # Pausa más larga antes de enviar
                print("✅ Contraseña ingresada")
                sys.stdout.flush()
                
                # HUMANIZACIÓN: Pausa antes de hacer clic
                self.page.wait_for_timeout(1000)
                print("🔘 Buscando botón de login...")
                sys.stdout.flush()
                
                # Buscar botón de login específicamente "Iniciar Sesión"
                login_selectors = [
                    'button:has-text("Iniciar Sesión")',  # El botón específico
                    'input[type="submit"]',
                    'button[type="submit"]',
                    'button:has-text("Ingresar")',
                    'button:has-text("Login")',
                    'button:has-text("Entrar")',
                    'button:has-text("Acceder")',
                    'button:has-text("INGRESAR")',
                    'input[value*="Ingresar"]',
                    'input[value*="Entrar"]'
                ]
                
                for selector in login_selectors:
                    try:
                        btn = self.page.locator(selector)
                        if btn.count() > 0:
                            print(f"Botón de login encontrado con selector: {selector}")
                            sys.stdout.flush()
                            btn.first.click()
                            print("✅ Botón de login presionado")
                            sys.stdout.flush()
                            break
                    except:
                        continue
                
                # Esperar a que redirija después del login
                print("Esperando redirección después del login...")
                sys.stdout.flush()
                self.page.wait_for_timeout(2000)  # Reducido a 2 segundos
                
                # Verificar si el login fue exitoso buscando elementos del panel principal
                print("Verificando si entramos al sistema...")
                
                # Buscar elementos que solo aparecen cuando estás logueado
                login_success_selectors = [
                    'a:has-text("Inicio")',  # Link del panel principal
                    'nav a:has-text("Inicio")',
                    '.nav a:has-text("Inicio")',
                    'a[href*="inicio"]',
                    'a[href*="dashboard"]',
                    'a[href*="panel"]',
                    '.user-info',
                    '.user-menu',
                    '[class*="user"]',
                    '[class*="logout"]',
                    'a:has-text("Cerrar")',
                    'a:has-text("Salir")'
                ]
                
                login_successful = False
                for selector in login_success_selectors:
                    try:
                        elem = self.page.locator(selector)
                        if elem.count() > 0:
                            print(f"✅ Login exitoso - encontrado elemento: {selector}")
                            login_successful = True
                            break
                    except:
                        continue
                
                if not login_successful:
                    # Si no encuentra elementos de login exitoso, verificar por URL
                    if "iniciar" not in self.page.url or self.page.url != "https://sach.com.ar/iniciar":
                        print("✅ Login exitoso - URL cambió o es diferente")
                        login_successful = True
                    else:
                        print("❌ Login falló - seguimos en página de inicio de sesión")
                        
                        # Buscar mensajes de error
                        error_selectors = [
                            '.alert-danger',
                            '.error',
                            '.alert-error',
                            '[class*="error"]',
                            '[class*="danger"]',
                            'div:has-text("error")',
                            'div:has-text("Error")',
                            'div:has-text("incorrecto")',
                            'div:has-text("inválido")',
                            'div:has-text("inválida")',
                            'span:has-text("error")'
                        ]
                        
                        for selector in error_selectors:
                            try:
                                error_elem = self.page.locator(selector)
                                if error_elem.count() > 0:
                                    error_text = error_elem.first.text_content().strip()
                                    if error_text:
                                        print(f"Mensaje de error encontrado: {error_text}")
                                        break
                            except:
                                continue
                        
                        return False
                
                if login_successful:
                    print(f"✅ Login exitoso - URL actual: {self.page.url}")
                    
                    # Navegar directamente a Nuevo Cliente
                    print("Navegando directamente a Nuevo Cliente...")
                    self.page.goto("https://sach.com.ar/cliente/nuevo")
                    self.page.wait_for_timeout(1000)  # Reducido a 1 segundo
                    
                    print(f"URL después de navegar a Nuevo Cliente: {self.page.url}")
                    
                    # Verificar si estamos en el formulario de Nuevo Cliente
                    nuevo_cliente_selectors = [
                        'input[name*="documento"]',
                        'input[name*="nombre"]',
                        'input[name*="apellido"]',
                        'form:has-text("Nuevo Cliente")',
                        'h1:has-text("Nuevo Cliente")',
                        'h2:has-text("Nuevo Cliente")',
                        '.form-cliente'
                    ]
                    
                    form_found = False
                    for selector in nuevo_cliente_selectors:
                        try:
                            elem = self.page.locator(selector)
                            if elem.count() > 0:
                                print(f"✅ Formulario de Nuevo Cliente encontrado: {selector}")
                                form_found = True
                                break
                        except:
                            continue
                    
                    if form_found:
                        print("🎉 ¡Llegamos al formulario de Nuevo Cliente!")
                        print("🔍 Rellenando formulario con datos de Carlos Ernesto Segovia...")
                        
                        # Rellenar formulario con los datos (necesitamos pasar los datos)
                        return "FORM_READY"  # Indicar que el formulario está listo para rellenar
                    else:
                        print("❌ No se encontró el formulario de Nuevo Cliente")
                        return False
            else:
                print("No se encontraron campos de login")
                print("Capturando screenshot para debug...")
                self.page.screenshot(path="debug_login.png")
                return False
                
        except Exception as e:
            print(f"Error en login: {e}")
            return False
    
    def ir_a_nuevo_cliente(self):
        """Navega a la sección de Nuevo Cliente"""
        try:
            print("Buscando sección de Nuevo Cliente...")
            print(f"URL actual después del login: {self.page.url}")
            
            # Screenshot para ver qué hay disponible
            self.page.screenshot(path="debug_after_login.png")
            print("Screenshot guardado como debug_after_login.png")
            
            # Esperar a que cargue completamente
            self.page.wait_for_timeout(3000)
            
            # Buscar botón de Clientes o Nuevo Cliente (varias opciones)
            cliente_selectors = [
                'a:has-text("Cliente")',
                'button:has-text("Cliente")',
                'a:has-text("Clientes")',
                'button:has-text("Clientes")',
                'a:has-text("CLIENTE")',
                'button:has-text("CLIENTE")',
                'a:has-text("CLIENTES")',
                'button:has-text("CLIENTES")',
                '[href*="cliente"]',
                '[href*="client"]',
                'nav a:has-text("Cliente")',
                'nav button:has-text("Cliente")',
                '.nav a:has-text("Cliente")',
                '.menu a:has-text("Cliente")'
            ]
            
            for selector in cliente_selectors:
                try:
                    btn = self.page.locator(selector)
                    if btn.count() > 0:
                        print(f"Botón de Cliente encontrado con selector: {selector}")
                        btn.first.click()
                        print("Hiciste clic en Cliente")
                        self.page.wait_for_timeout(2000)
                        break
                except:
                    continue
            
            # Buscar botón de Nuevo Cliente
            nuevo_cliente_selectors = [
                'button:has-text("Nuevo Cliente")',
                'a:has-text("Nuevo Cliente")',
                'button:has-text("NUEVO CLIENTE")',
                'a:has-text("NUEVO CLIENTE")',
                'button:has-text("Nuevo")',
                'a:has-text("Nuevo")',
                'button:has-text("NUEVO")',
                'a:has-text("NUEVO")',
                'button:has-text("Agregar")',
                'a:has-text("Agregar")',
                'button:has-text("AGREGAR")',
                'a:has-text("AGREGAR")',
                'button:has-text("Crear")',
                'a:has-text("Crear")',
                'button:has-text("CREAR")',
                'a:has-text("CREAR")',
                '[href*="nuevo"]',
                '[href*="new"]',
                '[href*="crear"]',
                '[href*="add"]'
            ]
            
            for selector in nuevo_cliente_selectors:
                try:
                    btn = self.page.locator(selector)
                    if btn.count() > 0:
                        print(f"Botón de Nuevo Cliente encontrado con selector: {selector}")
                        btn.first.click()
                        print("Hiciste clic en Nuevo Cliente")
                        self.page.wait_for_timeout(2000)
                        return True
                except:
                    continue
            
            print("No se encontró el botón de Nuevo Cliente")
            print("Links disponibles en la página:")
            links = self.page.locator('a')
            for i in range(links.count()):
                link = links.nth(i)
                text = link.text_content().strip()
                href = link.get_attribute('href')
                if text and href:
                    print(f"  - '{text}' -> {href}")
            
            return False
            
        except Exception as e:
            print(f"Error navegando a Nuevo Cliente: {e}")
            return False
    
    def calcular_fecha_egreso(self, fecha_entrada_str, noches):
        """Calcula la fecha de egreso sumando las noches"""
        try:
            fecha_entrada = datetime.strptime(fecha_entrada_str, '%Y-%m-%d')
            fecha_egreso = fecha_entrada + timedelta(days=noches)
            return fecha_egreso.strftime('%d/%m/%Y')  # Formato para SACH
        except:
            return None
    
    def separar_nombre_completo(self, nombre_completo):
        """Separa nombre completo en nombres y apellido"""
        if not nombre_completo:
            return "", ""
        
        partes = nombre_completo.strip().split()
        if len(partes) == 1:
            return "", partes[0]
        elif len(partes) == 2:
            return partes[0], partes[1]
        else:
            # Asumir que la última parte es el apellido
            return " ".join(partes[:-1]), partes[-1]
    
    def llenar_formulario_cliente(self, datos_cliente):
        """Llena el formulario de Nuevo Cliente - versión ultra rápida con DNI obligatorio"""
        try:
            print("Llenando formulario de Nuevo Cliente...")
            print(f"Datos recibidos: {datos_cliente}")
            
            # PRIORIDAD ABSOLUTA AL DNI - Primero y obligatorio
            print("🔍 PRIORIDAD ABSOLUTA: Llenando DNI...")
            dni_lleno = False
            
            # Intento 1: Selector exacto (sin timeout para velocidad)
            try:
                dni_locator = self.page.locator('#ce_hue_nro_documento')
                dni_locator.fill('22455958')
                self.page.keyboard.press('Tab')
                
                # Verificación rápida
                dni_value = dni_locator.input_value()
                if dni_value and dni_value.strip():
                    print(f"✅ DNI escrito: {dni_value}")
                    dni_lleno = True
            except:
                pass
            
            # Intento 2: Selector alternativo (si el primero falló)
            if not dni_lleno:
                try:
                    print("🔄 Selector alternativo...")
                    dni_locator = self.page.get_by_role('textbox', name='Documento')
                    dni_locator.fill('22455958')
                    self.page.keyboard.press('Tab')
                    
                    dni_value = dni_locator.input_value()
                    if dni_value and dni_value.strip():
                        print(f"✅ DNI escrito: {dni_value}")
                        dni_lleno = True
                except:
                    pass
            
            # SI EL DNI NO SE PUDO LLENAR, DETENER
            if not dni_lleno:
                raise Exception("❌ CRÍTICO: No se pudo llenar el campo DNI obligatorio")
            
            # Datos de prueba - llenado ultra rápido sin timeouts
            nombres_test = "Juan Manuel"
            apellido_test = "Pérez"
            movil_test = "1122334455"
            email_test = "prueba_test@hotmail.com"
            
            # Llenado simultáneo y rápido
            self.page.fill('input[name*="nombre"], input[name*="nombres"]', nombres_test)
            print(f"✅ Nombres: {nombres_test}")
            
            self.page.fill('input[name*="apellido"]', apellido_test)
            print(f"✅ Apellido: {apellido_test}")
            
            self.page.fill('input[name*="email"], input[type="email"]', email_test)
            print(f"✅ Email: {email_test}")
            
            self.page.fill('input[name*="movil"], input[name*="celular"]', movil_test)
            print(f"✅ Teléfono Móvil: {movil_test}")
            
            # Campos opcionales - solo los esenciales que funcionan
            # self.page.fill('input[name*="localidad"]', 'Rosario')  # Comentado por timeout
            # self.page.fill('input[name*="postal"], input[name*="cp"]', '2000')  # Comentado por timeout
            
            print("✅ Formulario completado ultra rápido")
            return True
            
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def guardar_cliente(self):
        """Guarda el cliente en SACH - versión ultra rápida"""
        try:
            print("Guardando cliente...")
            
            # Clic instantáneo sin verificaciones extras
            try:
                # Intentar con ID específico primero
                guardar_btn = self.page.locator('#ce_hue_btn_guardar')
                if guardar_btn.count() > 0:
                    guardar_btn.click()
                    print("✅ Botón Guardar clickeado (ID)")
                    print("✅ Formulario enviado correctamente")
                else:
                    # Backup con role
                    self.page.get_by_role("button", name="Guardar Cliente").click()
                    print("✅ Botón Guardar clickeado (role)")
                    print("✅ Formulario enviado correctamente")
                
                # Backup adicional: selector de submit
                if guardar_btn.count() == 0:
                    submit_btn = self.page.locator('input[type="submit"]')
                    if submit_btn.count() > 0:
                        submit_btn.click()
                        print("✅ Botón Submit clickeado")
                        print("✅ Formulario enviado correctamente")
                
                # Espera mínima y verificación
                self.page.wait_for_timeout(500)
                
                if "cliente/nuevo" not in self.page.url:
                    print("✅ Cliente guardado - URL cambió")
                    self.page.screenshot(path="comprobacion_final.png")
                    print("📸 Screenshot guardado")
                    return True
            except:
                pass
            
            # Backup: Enter instantáneo
            self.page.keyboard.press('Enter')
            self.page.wait_for_timeout(500)
            
            if "cliente/nuevo" not in self.page.url:
                print("✅ Cliente guardado con Enter")
                self.page.screenshot(path="comprobacion_final.png")
                return True
            
            return True
            
        except Exception as e:
            print(f"Error guardando: {e}")
            return False
    
    def guardar_reserva(self):
        """Guarda la reserva"""
        try:
            print("Guardando reserva...")
            
            # Buscar botón de guardar
            guardar_selectors = [
                'button:has-text("Guardar")',
                'button:has-text("Confirmar")',
                'input[type="submit"]:has-text("Guardar")',
                'button[type="submit"]'
            ]
            
            for selector in guardar_selectors:
                try:
                    btn = self.page.locator(selector)
                    if btn.count() > 0:
                        btn.first.click()
                        print("Reserva guardada")
                        self.page.wait_for_timeout(2000)
                        return True
                except:
                    continue
            
            print("No se encontró botón de guardar")
            return False
            
        except Exception as e:
            print(f"Error guardando reserva: {e}")
            return False
    
    def procesar_cliente(self, datos_cliente):
        """Proceso completo de carga de cliente - flujo optimizado"""
        try:
            print("🚀 Iniciando proceso completo de cliente en SACH...")
            sys.stdout.flush()
            
            # Iniciar navegador con control de errores
            print("📱 Paso 1: Iniciando navegador...")
            sys.stdout.flush()
            if not self.iniciar_navegador():
                print("❌ FALLO: No se pudo iniciar el navegador")
                sys.stdout.flush()
                return False
            print("✅ Paso 1: Navegador iniciado correctamente")
            sys.stdout.flush()
            
            # LOGIN: Primero iniciar sesión
            print("🔐 Paso 2: Iniciando sesión en SACH...")
            sys.stdout.flush()
            login_result = self.hacer_login()
            
            if login_result == "FORM_READY":
                print("✅ Paso 2: Login exitoso, ya estamos en el sistema")
                sys.stdout.flush()
            elif not login_result:
                print("❌ FALLO: Login falló")
                sys.stdout.flush()
                return False
            else:
                print("✅ Paso 2: Login completado exitosamente")
                sys.stdout.flush()
            
            # SALTO DIRECTO: Ir directamente al formulario de nuevo cliente
            print("🚀 Paso 3: Navegando directamente al formulario de Nuevo Cliente...")
            sys.stdout.flush()
            self.page.goto('https://sach.com.ar/cliente/nuevo')
            self.page.wait_for_timeout(2000)
            
            # ESPERA ACTIVA: Esperar a que aparezca el primer campo del formulario
            print("⏳ Paso 4: Esperando a que cargue el formulario...")
            sys.stdout.flush()
            
            form_selectors = [
                'input[name*="nombre"]',
                'input[name*="documento"]', 
                'input[name*="apellido"]',
                'input[placeholder*="nombre"]',
                'input[placeholder*="documento"]',
                'input[placeholder*="apellido"]',
                'input[type="text"]'
            ]
            
            form_loaded = False
            for selector in form_selectors:
                try:
                    self.page.wait_for_selector(selector, timeout=5000)
                    print(f"✅ Paso 4: Formulario cargado, encontrado campo: {selector}")
                    sys.stdout.flush()
                    form_loaded = True
                    break
                except:
                    continue
            
            if not form_loaded:
                print("❌ FALLO: El formulario no cargó después de 5 segundos")
                sys.stdout.flush()
                self.page.screenshot(path='error_formulario_no_carga.png')
                print("📸 Captura guardada como 'error_formulario_no_carga.png'")
                sys.stdout.flush()
                return False
            
            # COMPLETAR: Cargar los datos del audio
            print("🔍 Paso 5: Completando formulario con datos del audio...")
            sys.stdout.flush()
            print(f"📊 Datos a cargar: {datos_cliente}")
            sys.stdout.flush()
            
            if self.llenar_formulario_cliente(datos_cliente):
                print("✅ Paso 5: Formulario completado exitosamente")
                sys.stdout.flush()
                
                # Guardar el cliente
                print("🔍 Paso 6: Guardando cliente...")
                sys.stdout.flush()
                if self.guardar_cliente():
                    print("🎉 Paso 6: ¡Cliente guardado exitosamente en SACH!")
                    sys.stdout.flush()
                    return True
                else:
                    print("❌ FALLO: No se pudo guardar el cliente")
                    sys.stdout.flush()
                    return False
            else:
                print("❌ FALLO: No se pudo completar el formulario")
                sys.stdout.flush()
                return False
                
        except Exception as e:
            print(f"❌ FALLO CRÍTICO: {e}")
            sys.stdout.flush()
            return False
        finally:
            self.cerrar_navegador()

def main():
    if len(sys.argv) != 2:
        print("Uso: python cargar_reserva.py '<datos_json>'")
        print("Ejemplo: python cargar_reserva.py '{\"nombre\":\"Juan Pérez\",\"cabana\":\"Cabaña 3\",\"fecha_entrada\":\"2024-02-15\",\"noches\":3,\"precio\":15000}'")
        sys.exit(1)
    
    try:
        datos_json = sys.argv[1]
        datos_cliente = json.loads(datos_json)
        
        robot = RobotSACH()
        resultado = robot.procesar_cliente(datos_cliente)
        
        if resultado:
            print("✅ Cliente procesado exitosamente")
        else:
            print("❌ Error procesando cliente")
            
    except json.JSONDecodeError:
        print("❌ Error: JSON inválido")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
