"""
Procesador Completo de Facturas - Versión Mejorada
Extrae TODA la información de facturas incluyendo proveedores del exterior
"""
import re
from datetime import datetime

def procesar_factura_completa(texto):
    """
    Procesa el texto extraído de una factura y extrae TODA la información posible
    Retorna diccionario completo con todos los datos
    """
    datos = {
        # ===== IDENTIFICACIÓN FACTURA =====
        'numero_factura': None,
        'prefijo': None,
        'consecutivo': None,
        'cufe': None,
        'cude': None,
        'tipo_documento': 'Factura',
        
        # ===== FECHAS =====
        'fecha_emision': None,
        'fecha_vencimiento': None,
        'hora_emision': None,
        
        # ===== EMISOR / PROVEEDOR =====
        'nit_emisor': None,
        'tipo_documento_emisor': None,
        'numero_tercero_emisor': None,  # Nuevo campo
        'dv_emisor': None,
        'razon_social_emisor': None,
        'nombre_comercial_emisor': None,
        'direccion_emisor': None,
        'ciudad_emisor': None,
        'departamento_emisor': None,
        'pais_emisor': None,  # IMPORTANTE: País del proveedor
        'codigo_pais_emisor': None,
        'telefono_emisor': None,
        'email_emisor': None,
        'sitio_web_emisor': None,
        'es_proveedor_exterior': False,  # Nuevo: Identifica si es del exterior
        
        # ===== CLIENTE / ADQUIRIENTE =====
        'tipo_documento_adquiriente': None,
        'numero_documento_adquiriente': None,
        'numero_tercero_adquiriente': None,  # Nuevo campo
        'dv_adquiriente': None,
        'nombre_adquiriente': None,
        'razon_social_adquiriente': None,
        'direccion_adquiriente': None,
        'ciudad_adquiriente': None,
        'departamento_adquiriente': None,
        'pais_adquiriente': None,
        'codigo_pais_adquiriente': None,
        'telefono_adquiriente': None,
        'email_adquiriente': None,
        
        # ===== VALORES =====
        'moneda': 'COP',
        'codigo_moneda': None,
        'tasa_cambio': None,
        'subtotal': 0.0,
        'descuento': 0.0,
        'recargo': 0.0,
        'base_imponible': 0.0,
        'iva': 0.0,
        'inc': 0.0,
        'retencion_fuente': 0.0,
        'retencion_iva': 0.0,
        'retencion_ica': 0.0,
        'otros_impuestos': 0.0,
        'total': 0.0,
        'total_pagar': 0.0,
        
        # ===== INFORMACIÓN TRIBUTARIA =====
        'regimen_fiscal': None,
        'tipo_contribuyente': None,
        'responsabilidad_tributaria': None,
        'actividad_economica': None,
        'codigo_ciiu': None,
        'gran_contribuyente': False,
        'autorretenedor': False,
        'responsable_iva': False,
        
        # ===== PAGO =====
        'forma_pago': None,
        'medio_pago': None,
        'terminos_pago': None,
        'plazo_pago_dias': None,
        
        # ===== AUTORIZACIÓN DIAN =====
        'numero_autorizacion': None,
        'rango_desde': None,
        'rango_hasta': None,
        'vigencia_desde': None,
        'vigencia_hasta': None,
        
        # ===== ORDEN DE COMPRA =====
        'orden_compra': None,
        'orden_pedido': None,
        'referencia': None,
        
        # ===== ITEMS/PRODUCTOS =====
        'items': [],
        'total_items': 0,
        'total_cantidad': 0,
        
        # ===== OBSERVACIONES =====
        'observaciones': None,
        'notas': None,
        'condiciones': None,
        
        # ===== METADATA =====
        'proveedor_tecnologico': None,
        'xml_generado_por': None,
        'pdf_generado_por': None,
        'fecha_validacion_dian': None,
        
        # ===== CONTROL DE CALIDAD =====
        'confianza': 0,
        'campos_extraidos': 0,
        'campos_totales': 60,
        'advertencias': [],
        'errores': []
    }
    
    # EXTRAER TODA LA INFORMACIÓN
    _extract_numero_factura_completo(texto, datos)
    _extract_cufe_cude(texto, datos)
    _extract_fechas_completo(texto, datos)
    _extract_emisor_completo(texto, datos)
    _extract_adquiriente_completo(texto, datos)
    _extract_valores_completo(texto, datos)
    _extract_tributaria(texto, datos)
    _extract_pago_completo(texto, datos)
    _extract_autorizacion_dian(texto, datos)
    _extract_items_completo(texto, datos)
    _extract_observaciones_completo(texto, datos)
    _extract_metadata(texto, datos)
    
    # Identificar si es proveedor del exterior
    _identificar_proveedor_exterior(datos)
    
    # Calcular confianza final
    _calcular_confianza_completa(datos)
    
    return datos


# ========================================
# FUNCIONES DE EXTRACCIÓN MEJORADAS
# ========================================

def _extract_numero_factura_completo(texto, datos):
    """Extrae número de factura con TODOS los formatos posibles"""
    patterns = [
        # Formato colombiano estándar
        r'Número de Factura[:\s]*([A-Z0-9-]+)',
        r'Factura[:\s]*No[:\.\s]*([A-Z0-9-]+)',
        r'FACTURA[^:]*:[:\s]*([A-Z0-9-]+)',
        
        # Formato con prefijo y consecutivo
        r'PREFIJO\s*([A-Z]+)\s*CONSECUTIVO\s*(\d+)',
        r'NIT\d+-\d+_PREFIJO([A-Z]+)_CONSECUTIVO(\d+)',
        
        # Formatos internacionales
        r'Invoice[:\s]*No[:\.\s]*([A-Z0-9-]+)',
        r'Bill[:\s]*No[:\.\s]*([A-Z0-9-]+)',
        r'Factura[:\s]*([A-Z]{2,5}[\s-]?\d{4,10})',
        
        # Formatos generales
        r'([A-Z]{2,5})[\s-](\d{4,10})',
        r'No[:\.\s]*([A-Z0-9]{5,20})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            if len(match.groups()) == 2:
                datos['prefijo'] = match.group(1).strip()
                datos['consecutivo'] = match.group(2).strip()
                datos['numero_factura'] = f"{datos['prefijo']}-{datos['consecutivo']}"
            else:
                datos['numero_factura'] = match.group(1).strip()
                # Intentar separar prefijo y consecutivo
                parts = re.match(r'([A-Z]+)[\s-]?(\d+)', datos['numero_factura'])
                if parts:
                    datos['prefijo'] = parts.group(1)
                    datos['consecutivo'] = parts.group(2)
            
            datos['campos_extraidos'] += 1
            break


def _extract_cufe_cude(texto, datos):
    """Extrae CUFE o CUDE (códigos únicos)"""
    # CUFE (Factura Electrónica)
    match = re.search(r'CUFE[:\s]*([a-f0-9]{64,})', texto, re.IGNORECASE)
    if match:
        datos['cufe'] = match.group(1)
        datos['campos_extraidos'] += 1
    
    # CUDE (Documento Soporte)
    match = re.search(r'CUDE[:\s]*([a-f0-9]{64,})', texto, re.IGNORECASE)
    if match:
        datos['cude'] = match.group(1)
        datos['campos_extraidos'] += 1


def _extract_fechas_completo(texto, datos):
    """Extrae todas las fechas posibles"""
    # Fecha de emisión
    patterns_emision = [
        r'Fecha de Emisión[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
        r'Fecha Factura[:\s]*(\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})',
        r'Date[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
        r'(\d{4}-\d{2}-\d{2})T\d{2}:\d{2}',
        r'Fecha[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
    ]
    
    for pattern in patterns_emision:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            fecha_str = match.group(1)
            try:
                # Intentar parsear diferentes formatos
                for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y']:
                    try:
                        fecha = datetime.strptime(fecha_str, fmt)
                        datos['fecha_emision'] = fecha.strftime('%Y-%m-%d')
                        datos['campos_extraidos'] += 1
                        break
                    except:
                        continue
            except:
                pass
            if datos['fecha_emision']:
                break
    
    # Hora de emisión
    match = re.search(r'(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2})', texto)
    if match:
        datos['hora_emision'] = match.group(2)
        datos['campos_extraidos'] += 1
    
    # Fecha de vencimiento
    patterns_venc = [
        r'Fecha de Vencimiento[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
        r'Vencimiento[:\s]*(\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})',
        r'Due Date[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
    ]
    
    for pattern in patterns_venc:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            fecha_str = match.group(1)
            try:
                for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y']:
                    try:
                        fecha = datetime.strptime(fecha_str, fmt)
                        datos['fecha_vencimiento'] = fecha.strftime('%Y-%m-%d')
                        datos['campos_extraidos'] += 1
                        break
                    except:
                        continue
            except:
                pass
            if datos['fecha_vencimiento']:
                break


def _extract_emisor_completo(texto, datos):
    """Extrae TODOS los datos del emisor/proveedor"""
    
    # NIT / Tax ID
    patterns_nit = [
        r'Nit del Emisor[:\s]*(\d+)[\s-]*(\d)?',
        r'NIT[:\s]*(\d{9,})[\s-]*(\d)?',
        r'Tax ID[:\s]*([A-Z0-9-]+)',
        r'Nit[:\s]*(\d{9,})[\s-]*(\d)?',
    ]
    
    for pattern in patterns_nit:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            if len(match.groups()) >= 2 and match.group(2):
                datos['nit_emisor'] = f"{match.group(1)}-{match.group(2)}"
                datos['numero_tercero_emisor'] = match.group(1)
                datos['dv_emisor'] = match.group(2)
            else:
                datos['nit_emisor'] = match.group(1)
                datos['numero_tercero_emisor'] = match.group(1)
            datos['campos_extraidos'] += 1
            break
    
    # Razón Social
    patterns_razon = [
        r'Razón Social[:\s]*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s\.]+?)(?:\n|Nombre|NIT|Tax)',
        r'(?:CORPORACION|EMPRESA|COMPAÑIA|SOCIEDAD)\s+[A-ZÁÉÍÓÚÑ\s\.]+',
        r'Supplier[:\s]*([A-Za-z\s\.]+?)(?:\n|Address)',
    ]
    
    for pattern in patterns_razon:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            if match.lastindex:
                datos['razon_social_emisor'] = match.group(1).strip()[:200]
            else:
                datos['razon_social_emisor'] = match.group(0).strip()[:200]
            datos['campos_extraidos'] += 1
            break
    
    # País del emisor (MUY IMPORTANTE)
    patterns_pais = [
        r'País[:\s]*([A-Za-z\s]+?)(?:\n|Departamento|Ciudad)',
        r'Country[:\s]*([A-Za-z\s]+?)(?:\n)',
        r'Pais[:\s]*([A-Za-z\s]+?)(?:\n)',
    ]
    
    for pattern in patterns_pais:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            datos['pais_emisor'] = match.group(1).strip()
            datos['campos_extraidos'] += 1
            break
    
    # Si no encuentra país explícito, buscar países comunes
    if not datos['pais_emisor']:
        paises = [
            'Colombia', 'Estados Unidos', 'México', 'Brasil', 'Argentina',
            'Chile', 'Perú', 'Ecuador', 'Venezuela', 'España', 'China',
            'United States', 'USA', 'China', 'Germany', 'France', 'Italy'
        ]
        for pais in paises:
            if re.search(r'\b' + pais + r'\b', texto, re.IGNORECASE):
                datos['pais_emisor'] = pais
                datos['campos_extraidos'] += 1
                break
    
    # Dirección
    patterns_dir = [
        r'Dirección[:\s]*([A-Za-z0-9\s\.,#-]+?)(?:\n|Teléfono|Email)',
        r'Address[:\s]*([A-Za-z0-9\s\.,#-]+?)(?:\n|Phone|Email)',
    ]
    
    for pattern in patterns_dir:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            datos['direccion_emisor'] = match.group(1).strip()[:200]
            datos['campos_extraidos'] += 1
            break
    
    # Ciudad
    patterns_ciudad = [
        r'Ciudad[:\s]*([A-ZÁÉÍÓÚÑ][A-Za-záéíóúñ\s\.]+?)(?:\n|,|País)',
        r'City[:\s]*([A-Za-z\s]+?)(?:\n|,)',
        r'Municipio[:\s]*([A-ZÁÉÍÓÚÑ][A-Za-záéíóúñ\s\.]+?)(?:\n)',
    ]
    
    for pattern in patterns_ciudad:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            datos['ciudad_emisor'] = match.group(1).strip()
            datos['campos_extraidos'] += 1
            break
    
    # Teléfono
    patterns_tel = [
        r'Teléfono[:\s]*([+\d\s\-()]+)',
        r'Phone[:\s]*([+\d\s\-()]+)',
        r'Tel[:\s]*([+\d\s\-()]+)',
    ]
    
    for pattern in patterns_tel:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            datos['telefono_emisor'] = match.group(1).strip()
            datos['campos_extraidos'] += 1
            break
    
    # Email
    match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', texto)
    if match:
        datos['email_emisor'] = match.group(1)
        datos['campos_extraidos'] += 1


def _extract_adquiriente_completo(texto, datos):
    """Extrae TODOS los datos del cliente/adquiriente"""
    
    # Nombre / Razón Social
    patterns_nombre = [
        r'Nombre o Razón Social[:\s]*([A-Za-zÁÉÍÓÚÑáéíóúñ\s\.]+?)(?:\n|Tipo)',
        r'CLIENTE[:\s]*([A-Za-zÁÉÍÓÚÑáéíóúñ\s\.]+?)(?:\n|NIT)',
        r'Customer[:\s]*([A-Za-z\s\.]+?)(?:\n)',
    ]
    
    for pattern in patterns_nombre:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            datos['nombre_adquiriente'] = match.group(1).strip()
            datos['campos_extraidos'] += 1
            break
    
    # Documento
    patterns_doc = [
        r'Número Documento[:\s]*(\d+)',
        r'C\.C\.[:\s]*(\d+)',
        r'NIT[:\s]*(\d+)',
        r'Documento[:\s]*(\d+)',
    ]
    
    for pattern in patterns_doc:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            datos['numero_documento_adquiriente'] = match.group(1)
            datos['numero_tercero_adquiriente'] = match.group(1)
            datos['campos_extraidos'] += 1
            break
    
    # Tipo de documento
    patterns_tipo = [
        r'Tipo de Documento[:\s]*(C[ée]dula|NIT|Pasaporte|CC|CE)',
        r'Document Type[:\s]*([A-Za-z\s]+)',
    ]
    
    for pattern in patterns_tipo:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            datos['tipo_documento_adquiriente'] = match.group(1).strip()
            datos['campos_extraidos'] += 1
            break


def _extract_valores_completo(texto, datos):
    """Extrae TODOS los valores monetarios"""
    
    # Moneda
    match = re.search(r'(?:MONEDA|Currency)[:\s]*(COP|USD|EUR|MXN|[A-Z]{3})', texto, re.IGNORECASE)
    if match:
        datos['moneda'] = match.group(1).upper()
        datos['codigo_moneda'] = match.group(1).upper()
        datos['campos_extraidos'] += 1
    
    # Tasa de cambio
    match = re.search(r'(?:TASA DE CAMBIO|Exchange Rate)[:\s]*([\d,\.]+)', texto, re.IGNORECASE)
    if match:
        try:
            datos['tasa_cambio'] = float(match.group(1).replace(',', ''))
            datos['campos_extraidos'] += 1
        except:
            pass
    
    # Subtotal
    patterns_subtotal = [
        r'Subtotal[:\s]*\$?\s*([\d,\.]+)',
        r'Base[:\s]*\$?\s*([\d,\.]+)',
        r'Subtotal[:\s]*(?:COP|USD)?\s*\$?\s*([\d,\.]+)',
    ]
    
    for pattern in patterns_subtotal:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            try:
                valor = match.group(1).replace(',', '').replace('.', '')
                # Si tiene punto como separador decimal
                if '.' in match.group(1):
                    valor = match.group(1).replace(',', '')
                datos['subtotal'] = float(valor)
                datos['campos_extraidos'] += 1
                break
            except:
                pass
    
    # IVA
    patterns_iva = [
        r'IVA[:\s]*\$?\s*([\d,\.]+)',
        r'Tax[:\s]*\$?\s*([\d,\.]+)',
        r'VAT[:\s]*\$?\s*([\d,\.]+)',
    ]
    
    for pattern in patterns_iva:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            try:
                valor = match.group(1).replace(',', '')
                datos['iva'] = float(valor)
                datos['campos_extraidos'] += 1
                break
            except:
                pass
    
    # Total
    patterns_total = [
        r'Total factura[:\s]*(?:COP|USD)?\s*\$?\s*([\d,\.]+)',
        r'Total[:\s]*(?:COP|USD)?\s*\$?\s*([\d,\.]+)',
        r'Total neto[:\s]*\$?\s*([\d,\.]+)',
        r'Grand Total[:\s]*\$?\s*([\d,\.]+)',
        r'TOTAL[:\s]*\$?\s*([\d,\.]+)',
    ]
    
    for pattern in patterns_total:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            try:
                valor = match.group(1).replace(',', '')
                datos['total'] = float(valor)
                datos['total_pagar'] = float(valor)
                datos['campos_extraidos'] += 1
                break
            except:
                pass
    
    # Retenciones
    match = re.search(r'Rete fuente[:\s]*\$?\s*([\d,\.]+)', texto, re.IGNORECASE)
    if match:
        try:
            datos['retencion_fuente'] = float(match.group(1).replace(',', ''))
            datos['campos_extraidos'] += 1
        except:
            pass


def _extract_tributaria(texto, datos):
    """Extrae información tributaria"""
    
    # Régimen fiscal
    match = re.search(r'R[ée]gimen[:\s]*([\w\s-]+)', texto, re.IGNORECASE)
    if match:
        datos['regimen_fiscal'] = match.group(1).strip()
        datos['campos_extraidos'] += 1
    
    # Tipo de contribuyente
    match = re.search(r'Tipo de Contribuyente[:\s]*(Persona Jur[ií]dica|Persona Natural)', texto, re.IGNORECASE)
    if match:
        datos['tipo_contribuyente'] = match.group(1)
        datos['campos_extraidos'] += 1
    
    # Responsabilidades
    if re.search(r'Responsable de IVA', texto, re.IGNORECASE):
        datos['responsable_iva'] = True
        datos['campos_extraidos'] += 1
    
    if re.search(r'Gran Contribuyente', texto, re.IGNORECASE):
        datos['gran_contribuyente'] = True
        datos['campos_extraidos'] += 1
    
    if re.search(r'Autorretenedor', texto, re.IGNORECASE):
        datos['autorretenedor'] = True
        datos['campos_extraidos'] += 1


def _extract_pago_completo(texto, datos):
    """Extrae información de pago"""
    
    # Forma de pago
    patterns = [
        r'Forma de pago[:\s]*(Contado|Cr[ée]dito|[\w\s]+)',
        r'Payment Method[:\s]*(Cash|Credit|[\w\s]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            datos['forma_pago'] = match.group(1).strip()
            datos['campos_extraidos'] += 1
            break
    
    # Medio de pago
    match = re.search(r'Medio de Pago[:\s]*([\w\s]+?)(?:\n)', texto, re.IGNORECASE)
    if match:
        datos['medio_pago'] = match.group(1).strip()
        datos['campos_extraidos'] += 1


def _extract_autorizacion_dian(texto, datos):
    """Extrae autorización DIAN"""
    
    # Número de autorización
    match = re.search(r'Autorizaci[óo]n[:\s]*(?:No[:\.\s]*)?(\d+)', texto, re.IGNORECASE)
    if match:
        datos['numero_autorizacion'] = match.group(1)
        datos['campos_extraidos'] += 1
    
    # Rango
    match = re.search(r'(?:desde|from)[:\s]*(\d+)\s*(?:hasta|to)[:\s]*(\d+)', texto, re.IGNORECASE)
    if match:
        datos['rango_desde'] = match.group(1)
        datos['rango_hasta'] = match.group(2)
        datos['campos_extraidos'] += 1


def _extract_items_completo(texto, datos):
    """Extrae items/productos de la factura"""
    
    # Buscar tabla de productos (patrón común)
    # Item | Descripción | Cantidad | Precio | Total
    pattern = r'(\d+)\s+([^\d\n]{10,80}?)\s+([\d,\.]+)\s+([\w]{2,4})\s+([\d,\.]+)\s+([\d,\.]+)'
    
    matches = re.finditer(pattern, texto)
    for match in matches:
        try:
            item = {
                'numero': match.group(1),
                'descripcion': match.group(2).strip(),
                'cantidad': float(match.group(3).replace(',', '')),
                'unidad': match.group(4),
                'precio_unitario': float(match.group(5).replace(',', '')),
                'total': float(match.group(6).replace(',', ''))
            }
            datos['items'].append(item)
        except:
            pass
    
    datos['total_items'] = len(datos['items'])
    if datos['total_items'] > 0:
        datos['campos_extraidos'] += 1
        datos['total_cantidad'] = sum(item['cantidad'] for item in datos['items'])


def _extract_observaciones_completo(texto, datos):
    """Extrae observaciones y notas"""
    
    # Observaciones
    match = re.search(r'Observaciones[:\s]*([^\n]{10,500})', texto, re.IGNORECASE)
    if match:
        datos['observaciones'] = match.group(1).strip()
        datos['campos_extraidos'] += 1
    
    # Notas
    match = re.search(r'Notas[:\s]*([^\n]{10,500})', texto, re.IGNORECASE)
    if match:
        datos['notas'] = match.group(1).strip()
        datos['campos_extraidos'] += 1


def _extract_metadata(texto, datos):
    """Extrae metadata del documento"""
    
    # Proveedor tecnológico
    match = re.search(r'(?:Software|Proveedor)[:\s]*([A-Za-z\s]+?)\s+(?:SAS|S\.A\.S|NIT)', texto, re.IGNORECASE)
    if match:
        datos['proveedor_tecnologico'] = match.group(1).strip()
        datos['campos_extraidos'] += 1
    
    # Fecha validación DIAN
    match = re.search(r'validado por[^\d]*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})', texto, re.IGNORECASE)
    if match:
        datos['fecha_validacion_dian'] = match.group(1)
        datos['campos_extraidos'] += 1


def _identificar_proveedor_exterior(datos):
    """Identifica si el proveedor es del exterior"""
    
    paises_exterior = [
        'Estados Unidos', 'USA', 'United States', 'China', 'México',
        'Brasil', 'Argentina', 'Chile', 'Perú', 'Ecuador', 'Venezuela',
        'España', 'Germany', 'France', 'Italy', 'UK', 'Canada'
    ]
    
    if datos['pais_emisor']:
        # Si el país no es Colombia, es del exterior
        if datos['pais_emisor'].lower() not in ['colombia', 'col', 'co']:
            datos['es_proveedor_exterior'] = True
            datos['campos_extraidos'] += 1


def _calcular_confianza_completa(datos):
    """Calcula nivel de confianza basado en campos extraídos"""
    
    # Campos críticos (mayor peso)
    campos_criticos = [
        'numero_factura', 'fecha_emision', 'nit_emisor', 'razon_social_emisor',
        'total', 'nombre_adquiriente'
    ]
    
    # Campos importantes
    campos_importantes = [
        'cufe', 'pais_emisor', 'ciudad_emisor', 'subtotal', 'iva'
    ]
    
    # Campos opcionales
    campos_opcionales = [
        'telefono_emisor', 'email_emisor', 'forma_pago', 'observaciones'
    ]
    
    puntos = 0
    
    # Puntaje por campos críticos (60 puntos)
    for campo in campos_criticos:
        if datos.get(campo):
            puntos += 10
    
    # Puntaje por campos importantes (30 puntos)
    for campo in campos_importantes:
        if datos.get(campo):
            puntos += 6
    
    # Puntaje por campos opcionales (10 puntos)
    for campo in campos_opcionales:
        if datos.get(campo):
            puntos += 2.5
    
    datos['confianza'] = min(int(puntos), 100)
    
    # Advertencias
    if not datos['numero_factura']:
        datos['advertencias'].append('Falta número de factura')
    if not datos['total'] or datos['total'] == 0:
        datos['advertencias'].append('Total es cero o no se encontró')
    if not datos['pais_emisor']:
        datos['advertencias'].append('No se identificó país del proveedor')
    
    return datos