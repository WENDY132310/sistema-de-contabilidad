import pdfplumber
import py7zr
import json
import os
import ollama
import tempfile

def extraer_texto_pdf(ruta_pdf):
    """Extrae texto de PDF usando pdfplumber (mucho mejor que PyPDF2)"""
    texto = ""
    with pdfplumber.open(ruta_pdf) as pdf:
        for pagina in pdf.pages:
            t = pagina.extract_text()
            if t:
                texto += t + "\n"
    return texto

def descomprimir_7z(ruta_7z, destino=None):
    """Descomprime archivo .7z y retorna lista de archivos PDF"""
    if destino is None:
        destino = tempfile.mkdtemp()
    with py7zr.SevenZipFile(ruta_7z, mode='r') as z:
        z.extractall(path=destino)
    
    archivos_pdf = []
    for root, dirs, files in os.walk(destino):
        for f in files:
            if f.lower().endswith('.pdf'):
                archivos_pdf.append(os.path.join(root, f))
    return archivos_pdf

def extraer_datos_con_ollama(texto_factura):
    """Usa Ollama (Llama 3.1) para extraer datos estructurados"""
    prompt = f"""Eres un experto en facturas electrónicas colombianas y de proveedores internacionales.
Extrae TODOS estos campos del texto de factura. Si no encuentras un campo, pon "NO ENCONTRADO".

Campos requeridos:
- numero_factura: Número de la factura
- cufe: Código Único de Factura Electrónica (CUFE/CUDE)
- fecha: Fecha de emisión (formato YYYY-MM-DD)
- emisor_razon_social: Razón social del emisor
- emisor_nit: NIT o número de identificación del emisor
- cliente_nombre: Nombre o razón social del cliente
- cliente_nit: NIT o identificación del cliente
- valor_total: Valor total de la factura
- valor_subtotal: Subtotal antes de impuestos
- valor_iva: Valor del IVA
- proveedor: Nombre del proveedor
- pais: País del emisor
- numero_tercero: Número del tercero
- nombre_tercero: Nombre del tercero
- moneda: Moneda de la factura (COP, USD, EUR, etc.)

Responde SOLO con un JSON válido, sin explicaciones.

TEXTO DE LA FACTURA:
{texto_factura}"""

    response = ollama.chat(
        model='llama3.1:8b',
        messages=[{'role': 'user', 'content': prompt}],
        options={'temperature': 0.1}  # Baja temperatura = más preciso
    )
    
    respuesta = response['message']['content']
    
    # Extraer JSON de la respuesta
    try:
        # Buscar JSON en la respuesta
        inicio = respuesta.find('{')
        fin = respuesta.rfind('}') + 1
        if inicio != -1 and fin > inicio:
            return json.loads(respuesta[inicio:fin])
    except json.JSONDecodeError:
        pass
    
    return {"error": "No se pudo parsear la respuesta", "raw": respuesta}

def detectar_duplicados(facturas):
    """Detecta facturas duplicadas por número de factura + emisor"""
    vistos = {}
    duplicados = []
    for i, f in enumerate(facturas):
        clave = f"{f.get('numero_factura', '')}-{f.get('emisor_nit', '')}"
        if clave in vistos and clave != "NO ENCONTRADO-NO ENCONTRADO":
            duplicados.append({
                "factura": f.get('numero_factura'),
                "emisor": f.get('emisor_razon_social'),
                "indices": [vistos[clave], i]
            })
        else:
            vistos[clave] = i
    return duplicados

def procesar_archivo_7z(ruta_7z):
    """Proceso completo: descomprimir → extraer texto → IA → duplicados"""
    print(f"📦 Descomprimiendo {ruta_7z}...")
    archivos = descomprimir_7z(ruta_7z)
    print(f"📄 Se encontraron {len(archivos)} PDFs\n")
    
    facturas = []
    for i, pdf_path in enumerate(archivos):
        print(f"🔍 Procesando [{i+1}/{len(archivos)}]: {os.path.basename(pdf_path)}")
        texto = extraer_texto_pdf(pdf_path)
        
        if not texto.strip():
            print("   ⚠️ PDF sin texto (posible imagen). Necesita OCR.")
            facturas.append({"archivo": pdf_path, "error": "Sin texto extraíble"})
            continue
        
        datos = extraer_datos_con_ollama(texto)
        datos['archivo_origen'] = os.path.basename(pdf_path)
        facturas.append(datos)
        print(f"   ✅ Factura: {datos.get('numero_factura', '?')}")
    
    # Detectar duplicados
    duplicados = detectar_duplicados(facturas)
    
    # Guardar resultados
    resultado = {
        "total_procesadas": len(facturas),
        "duplicados": duplicados,
        "facturas": facturas
    }
    
    with open("resultados_facturas.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*50}")
    print(f"✅ Total procesadas: {len(facturas)}")
    print(f"⚠️ Duplicados encontrados: {len(duplicados)}")
    print(f"💾 Resultados guardados en: resultados_facturas.json")
    
    return resultado

# === EJECUTAR ===
if __name__ == "__main__":
    procesar_archivo_7z("Soportes_Proveedores_Exterior.7z")
