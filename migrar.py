# ==========================================
# MIGRACIÓN DE BASE DE DATOS
# Agregar TODOS los campos nuevos
# ==========================================

# OPCIÓN 1: Eliminar BD antigua y crear nueva (RECOMENDADO si estás en desarrollo)
# -------------------------------------------------------------------------------
"""
rm contasystem.db
python app.py  # Creará la nueva BD con todos los campos
"""

# OPCIÓN 2: Migrar BD existente (si ya tienes datos importantes)
# -------------------------------------------------------------------------------

import sqlite3

def migrar_base_datos():
    """Agrega todos los campos nuevos a la tabla documentos existente"""
    
    conn = sqlite3.connect('contasystem.db')
    cursor = conn.cursor()
    
    # Lista de campos nuevos a agregar
    nuevos_campos = [
        # Emisor/Proveedor adicionales
        ("tipo_documento_emisor", "TEXT"),
        ("numero_tercero_emisor", "TEXT"),
        ("dv_emisor", "TEXT"),
        ("nombre_comercial_emisor", "TEXT"),
        ("direccion_emisor", "TEXT"),
        ("ciudad_emisor", "TEXT"),
        ("departamento_emisor", "TEXT"),
        ("pais_emisor", "TEXT"),  # ⭐ IMPORTANTE
        ("codigo_pais_emisor", "TEXT"),
        ("telefono_emisor", "TEXT"),
        ("email_emisor", "TEXT"),
        ("sitio_web_emisor", "TEXT"),
        ("es_proveedor_exterior", "BOOLEAN DEFAULT 0"),
        
        # Adquiriente adicionales
        ("tipo_documento_adquiriente", "TEXT"),
        ("numero_tercero_adquiriente", "TEXT"),
        ("dv_adquiriente", "TEXT"),
        ("razon_social_adquiriente", "TEXT"),
        ("direccion_adquiriente", "TEXT"),
        ("ciudad_adquiriente", "TEXT"),
        ("departamento_adquiriente", "TEXT"),
        ("pais_adquiriente", "TEXT"),
        ("codigo_pais_adquiriente", "TEXT"),
        ("telefono_adquiriente", "TEXT"),
        ("email_adquiriente", "TEXT"),
        
        # Valores adicionales
        ("moneda", "TEXT DEFAULT 'COP'"),
        ("codigo_moneda", "TEXT"),
        ("tasa_cambio", "REAL"),
        ("descuento", "REAL DEFAULT 0"),
        ("recargo", "REAL DEFAULT 0"),
        ("base_imponible", "REAL DEFAULT 0"),
        ("inc", "REAL DEFAULT 0"),
        ("retencion_fuente", "REAL DEFAULT 0"),
        ("retencion_iva", "REAL DEFAULT 0"),
        ("retencion_ica", "REAL DEFAULT 0"),
        ("otros_impuestos", "REAL DEFAULT 0"),
        ("total_pagar", "REAL DEFAULT 0"),
        
        # Tributaria
        ("regimen_fiscal", "TEXT"),
        ("tipo_contribuyente", "TEXT"),
        ("responsabilidad_tributaria", "TEXT"),
        ("actividad_economica", "TEXT"),
        ("codigo_ciiu", "TEXT"),
        ("gran_contribuyente", "BOOLEAN DEFAULT 0"),
        ("autorretenedor", "BOOLEAN DEFAULT 0"),
        ("responsable_iva", "BOOLEAN DEFAULT 0"),
        
        # Pago
        ("medio_pago", "TEXT"),
        ("terminos_pago", "TEXT"),
        ("plazo_pago_dias", "INTEGER"),
        
        # Autorización DIAN
        ("numero_autorizacion", "TEXT"),
        ("rango_desde", "TEXT"),
        ("rango_hasta", "TEXT"),
        ("vigencia_desde", "DATE"),
        ("vigencia_hasta", "DATE"),
        
        # Orden de compra
        ("orden_compra", "TEXT"),
        ("orden_pedido", "TEXT"),
        ("referencia", "TEXT"),
        
        # Items
        ("total_items", "INTEGER DEFAULT 0"),
        ("total_cantidad", "REAL DEFAULT 0"),
        
        # Metadata
        ("proveedor_tecnologico", "TEXT"),
        ("xml_generado_por", "TEXT"),
        ("pdf_generado_por", "TEXT"),
        ("fecha_validacion_dian", "TEXT"),
        
        # Control
        ("advertencias", "TEXT"),
        ("errores", "TEXT"),
        ("prefijo", "TEXT"),
        ("consecutivo", "TEXT"),
        ("cude", "TEXT"),
        ("hora_emision", "TEXT"),
    ]
    
    # Agregar cada campo si no existe
    for campo, tipo in nuevos_campos:
        try:
            cursor.execute(f"ALTER TABLE documentos ADD COLUMN {campo} {tipo}")
            print(f"✅ Campo agregado: {campo}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"⏭️ Campo ya existe: {campo}")
            else:
                print(f"❌ Error agregando {campo}: {e}")
    
    # Crear índices adicionales
    indices = [
        ("idx_pais_emisor", "pais_emisor"),
        ("idx_numero_tercero_emisor", "numero_tercero_emisor"),
        ("idx_fecha_emision", "fecha_emision"),
        ("idx_total", "total"),
        ("idx_file_hash", "file_hash"),
    ]
    
    for nombre_idx, campo in indices:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {nombre_idx} ON documentos({campo})")
            print(f"✅ Índice creado: {nombre_idx}")
        except Exception as e:
            print(f"❌ Error creando índice {nombre_idx}: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n🎉 Migración completada exitosamente!")
    print("📊 La base de datos ahora tiene todos los campos necesarios")


if __name__ == "__main__":
    print("="*50)
    print("MIGRACIÓN DE BASE DE DATOS")
    print("="*50)
    print()
    
    respuesta = input("¿Desea migrar la base de datos? (s/n): ")
    
    if respuesta.lower() == 's':
        migrar_base_datos()
    else:
        print("Migración cancelada")


# ==========================================
# ESTRUCTURA COMPLETA DE LA TABLA (para referencia)
# ==========================================

"""
CREATE TABLE documentos (
    -- Identificación
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    archivo TEXT,
    file_hash TEXT,
    tipo_documento TEXT,
    numero_factura TEXT,
    prefijo TEXT,
    consecutivo TEXT,
    cufe TEXT UNIQUE,
    cude TEXT,
    
    -- Fechas
    fecha_emision DATE,
    fecha_vencimiento DATE,
    hora_emision TEXT,
    
    -- Emisor/Proveedor
    nit_emisor TEXT,
    tipo_documento_emisor TEXT,
    numero_tercero_emisor TEXT,
    dv_emisor TEXT,
    razon_social_emisor TEXT,
    nombre_comercial_emisor TEXT,
    direccion_emisor TEXT,
    ciudad_emisor TEXT,
    departamento_emisor TEXT,
    pais_emisor TEXT,              -- ⭐ NUEVO
    codigo_pais_emisor TEXT,
    telefono_emisor TEXT,
    email_emisor TEXT,
    sitio_web_emisor TEXT,
    es_proveedor_exterior BOOLEAN, -- ⭐ NUEVO
    
    -- Adquiriente/Cliente
    tipo_documento_adquiriente TEXT,
    numero_documento_adquiriente TEXT,
    numero_tercero_adquiriente TEXT, -- ⭐ NUEVO
    nit_adquiriente TEXT,
    dv_adquiriente TEXT,
    nombre_adquiriente TEXT,
    razon_social_adquiriente TEXT,
    direccion_adquiriente TEXT,
    ciudad_adquiriente TEXT,
    departamento_adquiriente TEXT,
    pais_adquiriente TEXT,
    codigo_pais_adquiriente TEXT,
    telefono_adquiriente TEXT,
    email_adquiriente TEXT,
    
    -- Valores
    moneda TEXT DEFAULT 'COP',
    codigo_moneda TEXT,
    tasa_cambio REAL,
    subtotal REAL,
    descuento REAL DEFAULT 0,
    recargo REAL DEFAULT 0,
    base_imponible REAL,
    iva REAL,
    inc REAL,
    retencion_fuente REAL,
    retencion_iva REAL,
    retencion_ica REAL,
    otros_impuestos REAL,
    total REAL,
    total_pagar REAL,
    
    -- Tributaria
    regimen_fiscal TEXT,
    tipo_contribuyente TEXT,
    responsabilidad_tributaria TEXT,
    actividad_economica TEXT,
    codigo_ciiu TEXT,
    gran_contribuyente BOOLEAN,
    autorretenedor BOOLEAN,
    responsable_iva BOOLEAN,
    
    -- Pago
    forma_pago TEXT,
    medio_pago TEXT,
    terminos_pago TEXT,
    plazo_pago_dias INTEGER,
    
    -- Autorización DIAN
    numero_autorizacion TEXT,
    rango_desde TEXT,
    rango_hasta TEXT,
    vigencia_desde DATE,
    vigencia_hasta DATE,
    
    -- Orden de compra
    orden_compra TEXT,
    orden_pedido TEXT,
    referencia TEXT,
    
    -- Items
    total_items INTEGER DEFAULT 0,
    total_cantidad REAL DEFAULT 0,
    
    -- Observaciones
    observaciones TEXT,
    notas TEXT,
    
    -- Metadata
    proveedor_tecnologico TEXT,
    xml_generado_por TEXT,
    pdf_generado_por TEXT,
    fecha_validacion_dian TEXT,
    
    -- Control
    confianza REAL,
    estado TEXT DEFAULT 'pendiente',
    texto_extraido TEXT,
    datos_json TEXT,
    advertencias TEXT,
    errores TEXT,
    es_duplicado BOOLEAN DEFAULT 0,
    documento_original_id INTEGER,
    fecha_procesamiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX idx_cufe ON documentos(cufe);
CREATE INDEX idx_numero_factura ON documentos(numero_factura);
CREATE INDEX idx_estado ON documentos(estado);
CREATE INDEX idx_nit_emisor ON documentos(nit_emisor);
CREATE INDEX idx_pais_emisor ON documentos(pais_emisor);
CREATE INDEX idx_numero_tercero_emisor ON documentos(numero_tercero_emisor);
CREATE INDEX idx_fecha_emision ON documentos(fecha_emision);
CREATE INDEX idx_total ON documentos(total);
CREATE INDEX idx_file_hash ON documentos(file_hash);
"""