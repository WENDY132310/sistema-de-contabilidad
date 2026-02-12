"""
Módulo de normalización de datos para facturas electrónicas
Convierte diferentes formatos y nomenclaturas a un estándar unificado
"""

import re
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import unicodedata

class NormalizadorDatos:
    """
    Normaliza datos extraídos de facturas para mantener consistencia
    Maneja diferentes formatos de fechas, monedas, nombres, etc.
    """
    
    # Mapeo de países a códigos ISO
    PAISES_ISO = {
        'colombia': 'CO',
        'mexico': 'MX', 
        'méxico': 'MX',
        'peru': 'PE',
        'perú': 'PE',
        'argentina': 'AR',
        'chile': 'CL',
        'ecuador': 'EC',
        'venezuela': 'VE',
        'estados unidos': 'US',
        'united states': 'US',
        'usa': 'US',
        'españa': 'ES',
        'spain': 'ES',
        'brasil': 'BR',
        'brazil': 'BR'
    }
    
    # Mapeo de monedas mejorado
    MONEDAS_ISO = {
        'cop': ['cop', 'colombian peso', 'peso colombiano', '$', 'pesos', 'cop$', '$cop'],
        'usd': ['usd', 'dollar', 'dólar', 'us dollar', 'american dollar', 'dólares', 'usd$', '$usd', 'usd '],
        'eur': ['eur', 'euro', 'euros', '€', 'eur€', 'eur '],
        'mxn': ['mxn', 'peso mexicano', 'mexican peso', 'pesos mxn', 'mxn$', '$mxn'],
        'pen': ['pen', 'sol', 'sol peruano', 'peruvian sol', 'soles', 'pen$', '$pen'],
        'ars': ['ars', 'peso argentino', 'argentine peso', 'ars$', '$ars'],
        'clp': ['clp', 'peso chileno', 'chilean peso', 'clp$', '$clp'],
        'brl': ['brl', 'real', 'real brasileño', 'brazilian real', 'r$', 'brl$']
    }
    
    # Mapeo de tipos de documento
    TIPOS_DOCUMENTO = {
        'nit': ['nit', 'tax id', 'ruc', 'tax identification'],
        'cc': ['cc', 'cedula', 'cédula', 'identity card', 'cédula de ciudadanía'],
        'ce': ['ce', 'cedula extranjería', 'cedula de extranjería', 'foreign id'],
        'ti': ['ti', 'tarjeta identidad', 'identity card'],
        'pp': ['pp', 'pasaporte', 'passport'],
        'rut': ['rut', 'rol único tributario', 'chilean tax id'],
        'ssn': ['ssn', 'social security', 'social security number']
    }
    
    # Palabras que indican persona jurídica
    INDICADORES_JURIDICA = [
        'sas', 'sa', 's.a.', 'ltda', 'limitada', 'cia', 'compañía',
        'company', 'corporation', 'corp', 'inc', 'llc', 'ltd',
        'sociedad', 'entidad', 'institución', 'fundación', 'asociación',
        'consorcio', 'cooperativa', 'sucursal', 'branch', 'empresa'
    ]
    
    def __init__(self):
        pass
    
    def normalizar_texto(self, texto: str) -> str:
        """Normaliza texto básico"""
        if not texto:
            return ""
        
        # Eliminar acentos y caracteres especiales
        texto = unicodedata.normalize('NFKD', texto)
        texto = texto.encode('ascii', 'ignore').decode('ascii', 'ignore')
        
        # Eliminar espacios extra y saltos de línea
        texto = re.sub(r'\s+', ' ', texto.strip())
        
        # Eliminar caracteres no deseados
        texto = re.sub(r'[^\w\s\-&.,;:@#]', '', texto)
        
        return texto.strip()
    
    def normalizar_nombre_empresa(self, nombre: str) -> str:
        """Normaliza nombres de empresas o personas"""
        if not nombre:
            return ""
        
        nombre = self.normalizar_texto(nombre)
        
        # Convertir a title case pero mantener siglas
        palabras = nombre.split()
        resultado = []
        
        for palabra in palabras:
            if palabra.upper() in ['SAS', 'SA', 'LTDA', 'CIA', 'S.A.', 'LTD.', 'INC', 'LLC']:
                resultado.append(palabra.upper())
            else:
                resultado.append(palabra.title())
        
        return ' '.join(resultado)
    
    def normalizar_documento(self, numero: str, tipo: str = None) -> Tuple[str, str]:
        """Normaliza número y tipo de documento con patrones específicos"""
        if not numero:
            return "", ""
        
        numero_limpio = str(numero)
        
        # Detectar y preservar formatos específicos
        # RFC Mexicano
        if re.match(r'^[A-Z]{3,4}[0-9]{6}[A-Z0-9]{3}$', numero_limpio.replace(' ', '').upper()):
            return numero_limpio.upper(), 'RFC'
        
        # Tax ID/EIN formato americano (XX-XXXXXXX)
        if re.match(r'^[0-9]{2}\-[0-9]{7}$', numero_limpio):
            return numero_limpio, 'EIN'
        
        # ABN Australiano
        if re.match(r'^[0-9]{2}\s?[0-9]{3}\s?[0-9]{3}\s?[0-9]{3}$', numero_limpio):
            return re.sub(r'\s', '', numero_limpio), 'ABN'
        
        # VAT Europeo
        if re.match(r'^[A-Z]{2}[0-9]{9,12}$', numero_limpio.replace(' ', '').upper()):
            return numero_limpio.replace(' ', '').upper(), 'VAT'
        
        # Limpiar número para formatos estándar
        numero = re.sub(r'[^\d]', '', str(numero))
        
        # Determinar tipo si no se proporciona
        if not tipo:
            if len(numero) >= 12:
                tipo = 'RFC'
            elif len(numero) >= 9:
                tipo = 'NIT'
            elif len(numero) >= 8:
                tipo = 'NIT'
            elif len(numero) >= 7:
                tipo = 'CC'
            else:
                tipo = 'CC'
        else:
            tipo = self.normalizar_tipo_documento(tipo)
        
        # Aplicar formato NIT colombiano si corresponde
        if tipo == 'NIT' and len(numero) >= 9:
            # Preservar formato con dígito de verificación
            if len(numero) >= 10:
                sin_dv = numero[:-1]
                dv = numero[-1]
                numero_formateado = f"{sin_dv}-{dv}"
            else:
                numero_formateado = numero
        else:
            numero_formateado = numero
        
        return numero_formateado, tipo
    
    def normalizar_tipo_documento(self, tipo: str) -> str:
        """Normaliza tipo de documento a estándar"""
        if not tipo:
            return "NIT"
        
        tipo_normalizado = self.normalizar_texto(tipo.lower())
        
        for estandar, variantes in self.TIPOS_DOCUMENTO.items():
            for variante in variantes:
                if variante.lower() in tipo_normalizado:
                    return estandar.upper()
        
        return tipo.upper()
    
    def normalizar_fecha(self, fecha: str) -> str:
        """Normaliza fecha a formato YYYY-MM-DD con patrones específicos de empresas"""
        if not fecha:
            return ""
        
        fecha_normalizada = self.normalizar_texto(fecha.lower())
        
        # Patrones específicos detectados en facturas reales
        patrones_especificos = [
            # Formato ISO mejorado
            r'(\d{4})\-(\d{2})\-(\d{2})(?:T\d{2}:\d{2}:\d{2})?',  # 2025-11-08 o 2025-11-08T18:52:34
            # Formato estándar
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',              # DD/MM/YYYY o MM/DD/YYYY
            # Formato con puntos
            r'(\d{1,2})\.(\d{1,2})\.(\d{2,4})',                  # DD.MM.YYYY
            # Formato en español detectado en Canva
            r'(\d{1,2})\s*de\s*(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s*de\s*(\d{4})',
            # Formato en inglés
            r'(\d{1,2})\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s*(\d{4})',
            # Formato abreviado
            r'(\d{1,2})\-([a-z]{3})\-(\d{4})'
        ]
        
        # Mapeo de meses en español
        meses_es = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
            'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        
        # Mapeo de meses en inglés
        meses_en = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        for i, patron in enumerate(patrones_especificos):
            match = re.search(patron, fecha_normalizada)
            if match:
                grupos = match.groups()
                
                if i == 0:  # Formato ISO
                    año, mes, dia = grupos
                elif i == 1:  # DD/MM/YYYY o MM/DD/YYYY
                    dia, mes, año = grupos
                elif i == 2:  # DD.MM.YYYY
                    dia, mes, año = grupos
                elif i == 3:  # Formato español
                    dia, mes_nombre, año = grupos
                    mes = str(meses_es.get(mes_nombre, 1))
                elif i == 4:  # Formato inglés
                    dia, mes_abr, año = grupos
                    mes = str(meses_en.get(mes_abr, 1))
                elif i == 5:  # Formato abreviado
                    dia, mes_abr, año = grupos
                    mes = str(meses_en.get(mes_abr, 1))
                else:
                    continue
                
                # Normalizar año
                if len(año) == 2:
                    año = '20' + año if int(año) < 50 else '19' + año
                
                # Intentar convertir a fecha
                try:
                    # Intentar DD/MM/YYYY primero para formatos ambiguos
                    if i == 1:
                        try:
                            # Probar formato MM/DD primero (estándar americano)
                            if int(mes) > 12:  # Si mes > 12, debe ser DD/MM
                                fecha_obj = datetime(int(año), int(dia), int(mes))
                            else:
                                # Preferir MM/DD para empresas americanas (Bitly, Microsoft)
                                try:
                                    fecha_obj = datetime(int(año), int(mes), int(dia))
                                except ValueError:
                                    fecha_obj = datetime(int(año), int(dia), int(mes))
                        except ValueError:
                            fecha_obj = datetime(int(año), int(dia), int(mes))
                    else:
                        fecha_obj = datetime(int(año), int(mes), int(dia))
                    
                    return fecha_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        
        return ""
    
    def normalizar_pais(self, pais: str) -> str:
        """Normaliza nombre de país a código ISO"""
        if not pais:
            return "CO"  # Default Colombia
        
        pais_normalizado = self.normalizar_texto(pais.lower())
        
        for codigo, nombres in self.PAISES_ISO.items():
            for nombre in nombres:
                if nombre.lower() in pais_normalizado:
                    return codigo.upper()
        
        # Devolver código si ya parece ISO
        if len(pais_normalizado) == 2 and pais_normalizado.isalpha():
            return pais_normalizado.upper()
        
        return "CO"  # Default
    
    def normalizar_moneda(self, moneda: str) -> str:
        """Normaliza moneda a código ISO de 3 letras"""
        if not moneda:
            return "COP"  # Default
        
        moneda_normalizada = self.normalizar_texto(moneda.lower())
        
        for codigo, variantes in self.MONEDAS_ISO.items():
            for variante in variantes:
                if variante.lower() in moneda_normalizada:
                    return codigo.upper()
        
        # Devolver código si ya parece ISO
        if len(moneda_normalizada) == 3 and moneda_normalizada.isalpha():
            return moneda_normalizada.upper()
        
        return "COP"  # Default
    
    def normalizar_valor(self, valor: Any) -> float:
        """Normaliza valores numéricos"""
        if valor is None or valor == "":
            return 0.0
        
        # Convertir a string si no lo es
        valor_str = str(valor)
        
        # Eliminar formato monetario
        valor_str = re.sub(r'[^\d\.,-]', '', valor_str)
        
        if not valor_str:
            return 0.0
        
        # Normalizar separadores decimales
        if '.' in valor_str and ',' in valor_str:
            # Ambos separadores presentes - asumir formato europeo: 1.234,56
            valor_str = valor_str.replace('.', '').replace(',', '.')
        elif ',' in valor_str:
            # Solo coma presente - es decimal: 1234,56
            if valor_str.count(',') == 1:
                valor_str = valor_str.replace(',', '.')
            else:
                # Múltiples comas - son separadores de miles
                valor_str = valor_str.replace(',', '')
        
        try:
            return float(valor_str)
        except ValueError:
            return 0.0
    
    def normalizar_email(self, email: str) -> str:
        """Normaliza email"""
        if not email:
            return ""
        
        email = self.normalizar_texto(email.lower())
        
        # Validación básica de email
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return email
        
        return ""
    
    def normalizar_telefono(self, telefono: str) -> str:
        """Normaliza número de teléfono"""
        if not telefono:
            return ""
        
        # Eliminar todo excepto números y +
        telefono = re.sub(r'[^\d+]', '', str(telefono))
        
        # Eliminar prefijo internacional si es de Colombia
        if telefono.startswith('+57'):
            telefono = telefono[3:]
        
        return telefono
    
    def normalizar_direccion(self, direccion: str) -> str:
        """Normaliza dirección"""
        if not direccion:
            return ""
        
        direccion = self.normalizar_texto(direccion)
        
        # Normalizar abreviaturas comunes
        abreviaciones = {
            'calle': 'Cll',
            'carrera': 'Cra',
            'avenida': 'Av',
            'transversal': 'Tv',
            'diagonal': 'Dg'
        }
        
        for completo, abrev in abreviaciones.items():
            direccion = re.sub(rf'\b{completo}\b', abrev, direccion, flags=re.IGNORECASE)
        
        return direccion
    
    def normalizar_regimen_fiscal(self, regimen: str) -> str:
        """Normaliza régimen fiscal"""
        if not regimen:
            return ""
        
        regimen_normalizado = self.normalizar_texto(regimen.lower())
        
        # Mapeos comunes
        mapeos = {
            'comun': 'Común',
            'ordinario': 'Común',
            'simple': 'Simplificado',
            'simplificado': 'Simplificado',
            'especial': 'Especial',
            'no responsable': 'No Responsable',
            'exento': 'Exento'
        }
        
        for clave, valor in mapeos.items():
            if clave in regimen_normalizado:
                return valor
        
        return regimen.title()
    
    def es_persona_natural(self, razon_social: str, tipo_documento: str = None) -> bool:
        """Determina si es persona natural basado en el nombre y tipo"""
        if not razon_social:
            return False
        
        rs_lower = self.normalizar_texto(razon_social.lower())
        tipo_doc_normalizado = self.normalizar_tipo_documento(tipo_documento or "").lower()
        
        # Indicadores de persona jurídica
        tiene_indicador_juridica = any(indicador in rs_lower for indicador in self.INDICADORES_JURIDICA)
        
        # Tipos de documento de persona natural
        es_documento_natural = tipo_doc_normalizado in ['cc', 'ce', 'ti', 'pp']
        
        # Si tiene indicador jurídica, es jurídica
        if tiene_indicador_juridica:
            return False
        
        # Si es persona natural por documento
        if es_documento_natural:
            return True
        
        # Heurística basada en longitud y formato del nombre
        palabras = rs_lower.split()
        
        # Nombres cortos (1-3 palabras) y nombres comunes
        if len(palabras) <= 3 and not any(caracter.isdigit() for caracter in razon_social):
            nombres_comunes = ['juan', 'maría', 'luis', 'carlos', 'ana', 'pedro', 'jose', 'maria', 'luisa']
            if any(nombre in rs_lower for nombre in nombres_comunes):
                return True
        
        # Por default, asumir jurídica si tiene NIT o RUT
        if tipo_doc_normalizado in ['nit', 'rut']:
            return False
        
        return False  # Default a jurídica por seguridad
    
    def normalizar_datos_completos(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza todos los datos de una factura"""
        if not datos:
            return {}
        
        datos_normalizados = datos.copy()
        
        # Datos del emisor
        if 'razon_social_emisor' in datos:
            datos_normalizados['razon_social_emisor'] = self.normalizar_nombre_empresa(datos.get('razon_social_emisor'))
        
        if 'nit_emisor' in datos or 'numero_documento_emisor' in datos:
            nit = datos.get('nit_emisor') or datos.get('numero_documento_emisor')
            nit_normalizado, tipo_doc = self.normalizar_documento(nit, datos.get('tipo_documento_emisor'))
            datos_normalizados['nit_emisor'] = nit_normalizado
            datos_normalizados['tipo_documento_emisor'] = tipo_doc
        
        if 'direccion_emisor' in datos:
            datos_normalizados['direccion_emisor'] = self.normalizar_direccion(datos.get('direccion_emisor'))
        
        if 'email_emisor' in datos:
            datos_normalizados['email_emisor'] = self.normalizar_email(datos.get('email_emisor'))
        
        if 'telefono_emisor' in datos:
            datos_normalizados['telefono_emisor'] = self.normalizar_telefono(datos.get('telefono_emisor'))
        
        if 'pais_emisor' in datos:
            datos_normalizados['pais_emisor'] = self.normalizar_pais(datos.get('pais_emisor'))
        
        # Datos del adquiriente
        if 'nombre_adquiriente' in datos or 'razon_social_adquiriente' in datos:
            nombre = datos.get('nombre_adquiriente') or datos.get('razon_social_adquiriente')
            datos_normalizados['nombre_adquiriente'] = self.normalizar_nombre_empresa(nombre)
            if 'razon_social_adquiriente' not in datos:
                datos_normalizados['razon_social_adquiriente'] = datos_normalizados['nombre_adquiriente']
        
        if 'nit_adquiriente' in datos or 'numero_documento_adquiriente' in datos:
            nit = datos.get('nit_adquiriente') or datos.get('numero_documento_adquiriente')
            nit_normalizado, tipo_doc = self.normalizar_documento(nit, datos.get('tipo_documento_adquiriente'))
            datos_normalizados['nit_adquiriente'] = nit_normalizado
            datos_normalizados['tipo_documento_adquiriente'] = tipo_doc
        
        if 'direccion_adquiriente' in datos:
            datos_normalizados['direccion_adquiriente'] = self.normalizar_direccion(datos.get('direccion_adquiriente'))
        
        if 'email_adquiriente' in datos:
            datos_normalizados['email_adquiriente'] = self.normalizar_email(datos.get('email_adquiriente'))
        
        if 'telefono_adquiriente' in datos:
            datos_normalizados['telefono_adquiriente'] = self.normalizar_telefono(datos.get('telefono_adquiriente'))
        
        if 'pais_adquiriente' in datos:
            datos_normalizados['pais_adquiriente'] = self.normalizar_pais(datos.get('pais_adquiriente'))
        
        # Fechas
        if 'fecha_emision' in datos:
            datos_normalizados['fecha_emision'] = self.normalizar_fecha(datos.get('fecha_emision'))
        
        if 'fecha_vencimiento' in datos:
            datos_normalizados['fecha_vencimiento'] = self.normalizar_fecha(datos.get('fecha_vencimiento'))
        
        # Valores
        campos_valor = ['subtotal', 'descuento', 'recargo', 'iva', 'inc', 'retencion_fuente', 
                       'retencion_iva', 'retencion_ica', 'otros_impuestos', 'total', 'total_pagar']
        
        for campo in campos_valor:
            if campo in datos:
                datos_normalizados[campo] = self.normalizar_valor(datos.get(campo))
        
        # Moneda
        if 'moneda' in datos:
            datos_normalizados['moneda'] = self.normalizar_moneda(datos.get('moneda'))
        
        # Régimen fiscal
        if 'regimen_fiscal' in datos:
            datos_normalizados['regimen_fiscal'] = self.normalizar_regimen_fiscal(datos.get('regimen_fiscal'))
        
        # Determinar tipo de persona
        if datos_normalizados.get('razon_social_emisor'):
            datos_normalizados['es_persona_natural_emisor'] = self.es_persona_natural(
                datos_normalizados.get('razon_social_emisor'),
                datos_normalizados.get('tipo_documento_emisor')
            )
        
        if datos_normalizados.get('nombre_adquiriente'):
            datos_normalizados['es_persona_natural_adquiriente'] = self.es_persona_natural(
                datos_normalizados.get('nombre_adquiriente'),
                datos_normalizados.get('tipo_documento_adquiriente')
            )
        
        return datos_normalizados

# Función de conveniencia
def normalizar_factura(datos: Dict[str, Any]) -> Dict[str, Any]:
    """Función wrapper para normalizar datos de factura"""
    normalizador = NormalizadorDatos()
    return normalizador.normalizar_datos_completos(datos)

if __name__ == "__main__":
    # Pruebas del normalizador
    datos_prueba = {
        "razon_social_emisor": "MI EMPRESA SAS LTDA",
        "nit_emisor": "123.456.789-0",
        "fecha_emision": "15/02/2024",
        "total": "$1.234.567,89",
        "moneda": "PESOS COLOMBIANOS",
        "email_emisor": "contacto@MIEMPRESA.COM"
    }
    
    normalizador = NormalizadorDatos()
    resultado = normalizador.normalizar_datos_completos(datos_prueba)
    
    print("Datos originales:")
    print(json.dumps(datos_prueba, indent=2, ensure_ascii=False))
    print("\nDatos normalizados:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))