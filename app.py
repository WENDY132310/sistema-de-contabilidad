from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime
import sqlite3
import os
import json
import PyPDF2
import re
from validators import DuplicateDetector, FacturaValidator
from scheduler import init_scheduler, get_scheduler
import atexit

app = Flask(__name__)
CORS(app)


# Configuración
DATABASE = 'contasystem.db'
UPLOAD_FOLDER = 'uploads'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Inicializar base de datos
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Tabla Empresa
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS empresa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            razon_social TEXT,
            nit TEXT,
            digito_verificacion TEXT,
            direccion TEXT,
            ciudad TEXT,
            departamento TEXT,
            telefono TEXT,
            email TEXT,
            sitio_web TEXT,
            regimen TEXT,
            tipo_organizacion TEXT,
            actividad_economica TEXT,
            codigo_ciiu TEXT,
            responsable_iva BOOLEAN,
            autorretenedor BOOLEAN,
            gran_contribuyente BOOLEAN
        )
    ''')
    
    # Tabla Resoluciones DIAN
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resoluciones_dian (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_resolucion TEXT,
            fecha_resolucion DATE,
            fecha_vigencia DATE,
            prefijo TEXT,
            numero_inicio INTEGER,
            numero_fin INTEGER,
            actual INTEGER DEFAULT 0,
            estado TEXT DEFAULT 'activo'
        )
    ''')
    
    # Tabla Clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_persona TEXT,
            razon_social TEXT,
            tipo_documento TEXT,
            numero_documento TEXT,
            dv TEXT,
            email TEXT,
            telefono TEXT,
            direccion TEXT,
            ciudad TEXT,
            departamento TEXT,
            plazo_pago INTEGER DEFAULT 30,
            responsable_iva BOOLEAN DEFAULT 0,
            estado TEXT DEFAULT 'activo',
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla Productos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            nombre TEXT,
            descripcion TEXT,
            tipo TEXT,
            precio_venta REAL,
            tarifa_iva REAL,
            unidad_medida TEXT,
            estado TEXT DEFAULT 'activo',
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla Facturas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT UNIQUE,
            prefijo TEXT,
            cliente_id INTEGER,
            resolucion_id INTEGER,
            fecha DATE,
            subtotal REAL,
            descuento REAL DEFAULT 0,
            iva REAL,
            total REAL,
            observaciones TEXT,
            estado TEXT DEFAULT 'borrador',
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id),
            FOREIGN KEY (resolucion_id) REFERENCES resoluciones_dian (id)
        )
    ''')
    
    # Tabla Detalle Facturas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detalle_facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            factura_id INTEGER,
            producto_id INTEGER,
            cantidad REAL,
            precio_unitario REAL,
            descuento REAL DEFAULT 0,
            iva REAL,
            total REAL,
            FOREIGN KEY (factura_id) REFERENCES facturas (id),
            FOREIGN KEY (producto_id) REFERENCES productos (id)
        )
    ''')
    
    # Tabla Documentos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            archivo TEXT,
            file_hash TEXT,
            tipo_documento TEXT,
            numero_factura TEXT,
            cufe TEXT UNIQUE,
            nit_emisor TEXT,
            razon_social_emisor TEXT,
            nit_adquiriente TEXT,
            nombre_adquiriente TEXT,
            fecha_emision DATE,
            fecha_vencimiento DATE,
            subtotal REAL,
            iva REAL,
            total REAL,
            forma_pago TEXT,
            confianza REAL,
            estado TEXT DEFAULT 'pendiente',
            observaciones TEXT,
            texto_extraido TEXT,
            datos_json TEXT,
            fecha_procesamiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            es_duplicado BOOLEAN DEFAULT 0,
            documento_original_id INTEGER
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cufe ON documentos(cufe)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_numero_factura ON documentos(numero_factura)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_estado ON documentos(estado)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_nit_emisor ON documentos(nit_emisor)')
    conn.commit()
    conn.close()
try:
    init_scheduler(DATABASE)
    print("Scheduler inicializado - Tareas automaticas activadas")
except Exception as e:
    print(f"Error inicializando scheduler: {e}")

# Detener scheduler al cerrar
def shutdown_scheduler():
    try:
        scheduler = get_scheduler()
        if scheduler:
            scheduler.stop()
            print("Scheduler detenido")
    except:
        pass

atexit.register(shutdown_scheduler)

@app.route('/')
def index():
    return render_template('index.html')
# Rutas - Página principal
# API - Dashboard
@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Contar documentos
    cursor.execute("SELECT COUNT(*) FROM documentos")
    total_documentos = cursor.fetchone()[0]
    
    # Contar facturas
    cursor.execute("SELECT COUNT(*) FROM facturas")
    total_facturas = cursor.fetchone()[0]
    
    # Contar clientes activos
    cursor.execute("SELECT COUNT(*) FROM clientes WHERE estado = 'activo'")
    clientes_activos = cursor.fetchone()[0]
    
    # Contar productos activos
    cursor.execute("SELECT COUNT(*) FROM productos WHERE estado = 'activo'")
    productos_activos = cursor.fetchone()[0]
    
    # Documentos procesados
    cursor.execute("SELECT COUNT(*) FROM documentos WHERE estado = 'procesado'")
    documentos_procesados = cursor.fetchone()[0]
    
    # Documentos con errores
    cursor.execute("SELECT COUNT(*) FROM documentos WHERE estado = 'error'")
    documentos_errores = cursor.fetchone()[0]
    
    # Total facturado
    cursor.execute("SELECT COALESCE(SUM(total), 0) FROM facturas WHERE estado != 'anulado'")
    total_facturado = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'documentos': total_documentos,
        'facturas': total_facturas,
        'clientes_activos': clientes_activos,
        'productos_activos': productos_activos,
        'documentos_procesados': documentos_procesados,
        'documentos_errores': documentos_errores,
        'total_facturado': total_facturado
    })

# API - Empresa
@app.route('/api/empresa', methods=['GET'])
def get_empresa():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM empresa LIMIT 1")
    empresa = cursor.fetchone()
    conn.close()
    
    if empresa:
        return jsonify(dict(empresa))
    return jsonify({})

@app.route('/api/empresa', methods=['POST'])
def save_empresa():
    data = request.json
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM empresa LIMIT 1")
    exists = cursor.fetchone()
    
    if exists:
        cursor.execute('''
            UPDATE empresa SET
                razon_social = ?, nit = ?, digito_verificacion = ?,
                direccion = ?, ciudad = ?, departamento = ?,
                telefono = ?, email = ?, sitio_web = ?,
                regimen = ?, tipo_organizacion = ?, actividad_economica = ?,
                codigo_ciiu = ?, responsable_iva = ?, autorretenedor = ?,
                gran_contribuyente = ?
            WHERE id = ?
        ''', (
            data.get('razon_social'), data.get('nit'), data.get('digito_verificacion'),
            data.get('direccion'), data.get('ciudad'), data.get('departamento'),
            data.get('telefono'), data.get('email'), data.get('sitio_web'),
            data.get('regimen'), data.get('tipo_organizacion'), data.get('actividad_economica'),
            data.get('codigo_ciiu'), data.get('responsable_iva'), data.get('autorretenedor'),
            data.get('gran_contribuyente'), exists[0]
        ))
    else:
        cursor.execute('''
            INSERT INTO empresa (
                razon_social, nit, digito_verificacion, direccion, ciudad,
                departamento, telefono, email, sitio_web, regimen,
                tipo_organizacion, actividad_economica, codigo_ciiu,
                responsable_iva, autorretenedor, gran_contribuyente
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('razon_social'), data.get('nit'), data.get('digito_verificacion'),
            data.get('direccion'), data.get('ciudad'), data.get('departamento'),
            data.get('telefono'), data.get('email'), data.get('sitio_web'),
            data.get('regimen'), data.get('tipo_organizacion'), data.get('actividad_economica'),
            data.get('codigo_ciiu'), data.get('responsable_iva'), data.get('autorretenedor'),
            data.get('gran_contribuyente')
        ))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Configuración guardada exitosamente'})

# API - Resoluciones DIAN
@app.route('/api/resoluciones', methods=['GET'])
def get_resoluciones():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM resoluciones_dian ORDER BY fecha_resolucion DESC")
    resoluciones = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(resoluciones)

@app.route('/api/resoluciones', methods=['POST'])
def create_resolucion():
    data = request.json
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO resoluciones_dian (
            numero_resolucion, fecha_resolucion, fecha_vigencia,
            prefijo, numero_inicio, numero_fin, actual
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('numero_resolucion'),
        data.get('fecha_resolucion'),
        data.get('fecha_vigencia'),
        data.get('prefijo'),
        data.get('numero_inicio'),
        data.get('numero_fin'),
        data.get('actual', 0)
    ))
    
    resolucion_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'id': resolucion_id, 'message': 'Resolución creada exitosamente'})

# API - Clientes
@app.route('/api/clientes', methods=['GET'])
def get_clientes():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes ORDER BY fecha_creacion DESC")
    clientes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(clientes)

@app.route('/api/clientes', methods=['POST'])
def create_cliente():
    data = request.json
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO clientes (
            tipo_persona, razon_social, tipo_documento, numero_documento,
            dv, email, telefono, direccion, ciudad, departamento,
            plazo_pago, responsable_iva
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('tipo_persona'),
        data.get('razon_social'),
        data.get('tipo_documento'),
        data.get('numero_documento'),
        data.get('dv'),
        data.get('email'),
        data.get('telefono'),
        data.get('direccion'),
        data.get('ciudad'),
        data.get('departamento'),
        data.get('plazo_pago', 30),
        data.get('responsable_iva', False)
    ))
    
    cliente_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'id': cliente_id, 'message': 'Cliente creado exitosamente'})

# API - Productos
@app.route('/api/productos', methods=['GET'])
def get_productos():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos ORDER BY fecha_creacion DESC")
    productos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(productos)

@app.route('/api/productos', methods=['POST'])
def create_producto():
    data = request.json
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO productos (
                codigo, nombre, descripcion, tipo, precio_venta,
                tarifa_iva, unidad_medida
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('codigo'),
            data.get('nombre'),
            data.get('descripcion'),
            data.get('tipo'),
            data.get('precio_venta'),
            data.get('tarifa_iva'),
            data.get('unidad_medida')
        ))
        
        producto_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'id': producto_id, 'message': 'Producto creado exitosamente'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': 'El código ya existe'}), 400

# API - Facturas
@app.route('/api/facturas', methods=['GET'])
def get_facturas():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT f.*, c.razon_social as cliente_nombre
        FROM facturas f
        LEFT JOIN clientes c ON f.cliente_id = c.id
        ORDER BY f.fecha_creacion DESC
    ''')
    facturas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(facturas)

@app.route('/api/facturas', methods=['POST'])
def create_factura():
    data = request.json
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Generar número de factura
    cursor.execute('''
        SELECT r.prefijo, r.actual, r.numero_fin
        FROM resoluciones_dian r
        WHERE r.id = ? AND r.estado = 'activo'
    ''', (data.get('resolucion_id'),))
    
    resolucion = cursor.fetchone()
    if not resolucion:
        conn.close()
        return jsonify({'success': False, 'message': 'No hay resolución DIAN activa'}), 400
    
    prefijo, actual, numero_fin = resolucion
    siguiente_numero = actual + 1
    
    if siguiente_numero > numero_fin:
        conn.close()
        return jsonify({'success': False, 'message': 'Se agotó el rango de la resolución'}), 400
    
    numero_factura = f"{prefijo}{siguiente_numero}"
    
    # Crear factura
    cursor.execute('''
        INSERT INTO facturas (
            numero, prefijo, cliente_id, resolucion_id, fecha,
            subtotal, descuento, iva, total, observaciones, estado
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        numero_factura,
        prefijo,
        data.get('cliente_id'),
        data.get('resolucion_id'),
        data.get('fecha', datetime.now().strftime('%Y-%m-%d')),
        data.get('subtotal'),
        data.get('descuento', 0),
        data.get('iva'),
        data.get('total'),
        data.get('observaciones'),
        'generado'
    ))
    
    factura_id = cursor.lastrowid
    
    # Actualizar número actual en resolución
    cursor.execute('''
        UPDATE resoluciones_dian SET actual = ? WHERE id = ?
    ''', (siguiente_numero, data.get('resolucion_id')))
    
    # Insertar detalles
    for detalle in data.get('detalles', []):
        cursor.execute('''
            INSERT INTO detalle_facturas (
                factura_id, producto_id, cantidad, precio_unitario,
                descuento, iva, total
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            factura_id,
            detalle.get('producto_id'),
            detalle.get('cantidad'),
            detalle.get('precio_unitario'),
            detalle.get('descuento', 0),
            detalle.get('iva'),
            detalle.get('total')
        ))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'id': factura_id,
        'numero': numero_factura,
        'message': 'Factura generada exitosamente'
    })

# API - Documentos
@app.route('/api/documentos', methods=['GET'])
def get_documentos():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documentos ORDER BY fecha_procesamiento DESC")
    documentos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(documentos)

@app.route('/api/documentos/check-duplicate', methods=['POST'])
def check_duplicate():
    """Verifica si un documento ya existe antes de procesarlo"""
    data = request.json
    
    detector = DuplicateDetector(DATABASE)
    result = detector.check_duplicate(
        cufe=data.get('cufe'),
        numero_factura=data.get('numero_factura')
    )
    
    return jsonify(result)


@app.route('/api/documentos/upload', methods=['POST'])
def upload_documento():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No se encontró archivo'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Nombre de archivo vacío'}), 400
    
    try:
        # Guardar archivo temporalmente
        temp_filename = f"temp_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        temp_filepath = os.path.join(UPLOAD_FOLDER, temp_filename)
        file.save(temp_filepath)
        
        # Calcular hash del archivo guardado
        import hashlib
        with open(temp_filepath, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        # Nombre final con hash
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_hash[:8]}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Renombrar archivo temporal
        if os.path.exists(filepath):
            os.remove(filepath)  # Si ya existe, eliminarlo
        os.rename(temp_filepath, filepath)
        
        # Procesar PDF
        datos_extraidos = {}
        texto_extraido = ""
        estado = 'pendiente'
        confianza = 0
        
        if filename.lower().endswith('.pdf'):
            # Extraer texto del PDF
            with open(filepath, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    texto_extraido += page.extract_text()
            
            # Procesar factura
            datos_extraidos = procesar_factura_completa(texto_extraido)
            confianza = datos_extraidos.get('confianza', 0)
            
            # Verificar duplicados ANTES de guardar
            detector = DuplicateDetector(DATABASE)
            duplicate_check = detector.check_duplicate(
                cufe=datos_extraidos.get('cufe'),
                numero_factura=datos_extraidos.get('numero_factura'),
                nit_emisor=datos_extraidos.get('nit_emisor'),
                total=datos_extraidos.get('total'),
                fecha_emision=datos_extraidos.get('fecha_emision'),
                archivo=filepath
            )

            
            if duplicate_check['is_duplicate'] and duplicate_check['confidence'] >= 80:
                # Es duplicado - eliminar archivo y actualizar registro existente
                os.remove(filepath)
                
                detector.merge_duplicates(
                    duplicate_check['duplicate_id'],
                    datos_extraidos
                )
                
                return jsonify({
                    'success': True,
                    'is_duplicate': True,
                    'duplicate_id': duplicate_check['duplicate_id'],
                    'match_type': duplicate_check['match_type'],
                    'message': f"Documento duplicado detectado ({duplicate_check['match_type']}). Registro actualizado.",
                    'datos': duplicate_check['duplicate_info']
                })
            
            # Determinar estado inicial
            if confianza >= 70:
                estado = 'validado'
            elif confianza >= 50:
                estado = 'pendiente'
            else:
                estado = 'error'
        
        # Guardar en BD
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO documentos (
                archivo, file_hash, tipo_documento, numero_factura, cufe,
                nit_emisor, razon_social_emisor, nit_adquiriente, nombre_adquiriente,
                fecha_emision, fecha_vencimiento, subtotal, iva, total, forma_pago,
                confianza, estado, texto_extraido, datos_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            filename, file_hash,
            datos_extraidos.get('tipo_documento', 'PDF'),
            datos_extraidos.get('numero_factura'),
            datos_extraidos.get('cufe'),
            datos_extraidos.get('nit_emisor'),
            datos_extraidos.get('razon_social_emisor'),
            datos_extraidos.get('nit_adquiriente'),
            datos_extraidos.get('nombre_adquiriente'),
            datos_extraidos.get('fecha_emision'),
            datos_extraidos.get('fecha_vencimiento'),
            datos_extraidos.get('subtotal', 0),
            datos_extraidos.get('iva', 0),
            datos_extraidos.get('total', 0),
            datos_extraidos.get('forma_pago'),
            confianza,
            estado,
            texto_extraido[:5000],
            json.dumps(datos_extraidos, ensure_ascii=False)
        ))
        
        documento_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'id': documento_id,
            'estado': estado,
            'confianza': confianza,
            'is_duplicate': False,
            'datos': datos_extraidos,
            'message': f'Documento procesado con {confianza}% de confianza'
        })
        
    except Exception as e:
        # Si hay error, eliminar archivo si existe
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        if 'temp_filepath' in locals() and os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        
        print(f"Error procesando documento: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'Error al procesar documento: {str(e)}'
        }), 500


@app.route('/api/documentos/<int:documento_id>/validar', methods=['POST'])
def validar_documento(documento_id):
    """Valida un documento manualmente"""
    validator = FacturaValidator(DATABASE)
    validacion = validator.validar_factura(documento_id)
    
    # Actualizar estado según validación
    if validacion['valido']:
        validator.actualizar_estado(documento_id, 'validado')
    else:
        validator.actualizar_estado(
            documento_id, 
            'correccion',
            'Errores: ' + '; '.join(validacion['errores'])
        )
    
    return jsonify(validacion)


@app.route('/api/documentos/<int:documento_id>/estado', methods=['PUT'])
def actualizar_estado_documento(documento_id):
    """Actualiza el estado de un documento"""
    data = request.json
    nuevo_estado = data.get('estado')
    observaciones = data.get('observaciones')
    
    validator = FacturaValidator(DATABASE)
    
    try:
        validator.actualizar_estado(documento_id, nuevo_estado, observaciones)
        return jsonify({'success': True, 'message': 'Estado actualizado'})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/api/documentos/pendientes', methods=['GET'])
def get_documentos_pendientes():
    """Obtiene documentos pendientes de radicar"""
    validator = FacturaValidator(DATABASE)
    pendientes = validator.get_documentos_pendientes()
    return jsonify(pendientes)


@app.route('/api/scheduler/status', methods=['GET'])
def get_scheduler_status():
    """Obtiene estado del scheduler"""
    scheduler = get_scheduler()
    if scheduler:
        jobs = scheduler.get_jobs_status()
        return jsonify({
            'running': scheduler.is_running,
            'jobs': jobs
        })
    return jsonify({'running': False, 'jobs': []})


@app.route('/api/scheduler/run/<job_id>', methods=['POST'])
def run_scheduler_job(job_id):
    """Ejecuta una tarea del scheduler manualmente"""
    scheduler = get_scheduler()
    if scheduler and scheduler.run_now(job_id):
        return jsonify({'success': True, 'message': f'Tarea {job_id} ejecutada'})
    return jsonify({'success': False, 'message': 'Error ejecutando tarea'}), 400

@app.route('/api/documentos/<int:documento_id>/preview', methods=['GET'])
def preview_documento(documento_id):
    """Obtiene información para previsualizar un documento"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT archivo, numero_factura, cufe, razon_social_emisor,
               nombre_adquiriente, fecha_emision, total, estado, confianza,
               texto_extraido, datos_json
        FROM documentos WHERE id = ?
    """, (documento_id,))
    
    doc = cursor.fetchone()
    conn.close()
    
    if not doc:
        return jsonify({'success': False, 'message': 'Documento no encontrado'}), 404
    
    return jsonify({
        'success': True,
        'documento': dict(doc),
        'file_path': f"/uploads/{doc['archivo']}"
    })

@app.route('/api/documentos/<int:documento_id>', methods=['DELETE'])
def delete_documento(documento_id):
    """Elimina un documento de la base de datos y del sistema de archivos"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Obtener información del documento
        cursor.execute("SELECT archivo FROM documentos WHERE id = ?", (documento_id,))
        doc = cursor.fetchone()
        
        if not doc:
            conn.close()
            return jsonify({'success': False, 'message': 'Documento no encontrado'}), 404
        
        # Eliminar archivo físico
        archivo_path = os.path.join(UPLOAD_FOLDER, doc['archivo'])
        if os.path.exists(archivo_path):
            os.remove(archivo_path)
        
        # Eliminar de la base de datos
        cursor.execute("DELETE FROM documentos WHERE id = ?", (documento_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Documento eliminado exitosamente'
        })
        
    except Exception as e:
        print(f"Error eliminando documento: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error al eliminar documento: {str(e)}'
        }), 500


@app.route('/api/documentos/delete-all', methods=['POST'])
def delete_all_documentos():
    """Elimina TODOS los documentos (usar con precaución)"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Obtener todos los archivos
        cursor.execute("SELECT archivo FROM documentos")
        docs = cursor.fetchall()
        
        # Eliminar archivos físicos
        deleted_files = 0
        for doc in docs:
            archivo_path = os.path.join(UPLOAD_FOLDER, doc['archivo'])
            if os.path.exists(archivo_path):
                os.remove(archivo_path)
                deleted_files += 1
        
        # Eliminar todos los registros de la BD
        cursor.execute("DELETE FROM documentos")
        deleted_records = cursor.rowcount
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Eliminados {deleted_records} registros y {deleted_files} archivos'
        })
        
    except Exception as e:
        print(f"Error eliminando todos los documentos: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
        
@app.route('/uploads/<filename>')
def serve_upload(filename):
    """Sirve archivos subidos"""
    return send_file(os.path.join(UPLOAD_FOLDER, filename))


def procesar_factura_completa(texto):
    """Procesa el texto extraído de una factura con muchos más patrones"""
    datos = {
        'numero_factura': None,
        'cufe': None,
        'fecha_emision': None,
        'fecha_vencimiento': None,
        'nit_emisor': None,
        'razon_social_emisor': None,
        'nit_adquiriente': None,
        'nombre_adquiriente': None,
        'subtotal': 0,
        'iva': 0,
        'total': 0,
        'forma_pago': None,
        'tipo_documento': 'Factura Electrónica',
        'confianza': 0,
        'moneda': 'COP',
        'email_emisor': None,
        'direccion_emisor': None,
        'telefono_emisor': None,
        'pais_emisor': None
    }
    
    texto_limpio = texto.replace('\n', ' ').replace('\r', ' ')
    
    # ============ NÚMERO DE FACTURA - MUCHOS MÁS PATRONES ============
    patterns_factura = [
        # Facturas Colombia
        r'PREFIJO\s*([A-Z]+)\s*CONSECUTIVO\s*(\d+)',
        r'FACTURA\s*ELECTR[ÓO]NICA[^0-9]*(\d+)',
        r'N[ÚU]MERO\s*DE\s*FACTURA[^0-9]*([A-Z0-9\-]+)',
        r'N[ÚU]MERO\s*FACTURA[^0-9]*([A-Z0-9\-]+)',
        r'Número\s*de\s*Factura[^0-9]*([A-Z0-9\-]+)',
        r'Factura\s*N[ÚU]MERO[^0-9]*([A-Z0-9\-]+)',
        
        # Facturas internacionales
        r'Invoice\s*#\s*([A-Z0-9\-\.]+)',
        r'Invoice\s*Number[^0-9]*([A-Z0-9\-\.]+)',
        r'INVOICE\s*#\s*([A-Z0-9\-\.]+)',
        r'Invoice\s*No\.?\s*([A-Z0-9\-\.]+)',
        r'Folio\s*#?\s*([A-Z0-9\-\.]+)',
        r'Factura\s*fiscal[^0-9]*([A-Z0-9\-\.]+)',
        
        # Facturas genéricas
        r'(?:FACTURA|INVOICE|FACT)[^0-9]*#?\s*([A-Z0-9\-\.]+)',
        r'N[ÚU]\.?\s*([A-Z0-9\-\.]+)\s*(?:factura|invoice)',
        r'#\s*([A-Z0-9\-]+)',
        
        # Para detectar al final si nada funcionó
        r'(?:FACT|INV|FCT)\s*([A-Z0-9]{4,})'
    ]
    
    for pattern in patterns_factura:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            if len(match.groups()) == 2:
                datos['numero_factura'] = f"{match.group(1)}-{match.group(2)}"
            else:
                val = match.group(1).strip()
                if len(val) >= 3:  # Debe tener al menos 3 caracteres
                    datos['numero_factura'] = val
            if datos['numero_factura']:
                break
    
    # ============ CUFE / CUNE / FOLIO FISCAL ============
    cufe_patterns = [
        r'CUFE[^a-f0-9]*([a-f0-9]{64,})',
        r'CUDE[^a-f0-9]*([a-f0-9]{64,})',
        r'Folio\s*Fiscal[^a-f0-9]*([a-f0-9]{64,})',
        r'UUID[^a-f0-9]*([a-f0-9]{32,})',
        r'(?:CUFE|CUDE)[:\s]*([a-f0-9]{40,})'
    ]
    
    for pattern in cufe_patterns:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            datos['cufe'] = match.group(1)
            break
    
    # ============ FECHAS - MUCHOS FORMATOS ============
    fecha_patterns = [
        # Formato Colombia
        r'Fecha\s*de\s*Emisi[ÓO]n[^0-9]*(\d{2}/\d{2}/\d{4})',
        r'FECHA\s*EMISI[ÓO]N[^0-9]*(\d{2}/\d{2}/\d{4})',
        r'Fecha\s*Emisi[ÓO]n[^0-9]*(\d{2}-\d{2}-\d{4})',
        r'Fecha\s*Factura[^0-9]*(\d{2}/\d{2}/\d{4})',
        
        # Formato internacional
        r'Invoice\s*Date[^0-9]*(\d{2}/\d{2}/\d{4})',
        r'Invoice\s*Date[^0-9]*(\d{4}-\d{2}-\d{2})',
        r'Date[^0-9]*(\d{2}/\d{2}/\d{4})',
        r'(\d{4}-\d{2}-\d{2})T\d{2}:\d{2}',
        
        # Otros formatos
        r'Fecha[^0-9]*(\d{2}\s+de\s+\w+\s+de\s+\d{4})',
        r'(\d{1,2}\s+[\w]+\s+\d{4})'
    ]
    
    for pattern in fecha_patterns:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            fecha_str = match.group(1)
            try:
                if '/' in fecha_str:
                    datos['fecha_emision'] = datetime.strptime(fecha_str, '%d/%m/%Y').strftime('%Y-%m-%d')
                elif '-' in fecha_str and len(fecha_str) == 10:
                    datos['fecha_emision'] = fecha_str[:10]
                elif 'de' in fecha_str:
                    # Fecha en formato español
                    meses = {'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
                            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
                            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'}
                    for mes, num in meses.items():
                        if mes in fecha_str.lower():
                            partes = fecha_str.split()
                            if len(partes) >= 3:
                                dia = partes[0]
                                año = partes[-1]
                                datos['fecha_emision'] = f"{año}-{num}-{int(dia):02d}"
                            break
            except:
                pass
            if datos['fecha_emision']:
                break
    
    # ============ NIT / TAX ID - MUCHOS FORMATOS ============
    nit_patterns = [
        # Colombia
        r'Nit\s*(?:del\s*)?Emisor[^0-9]*(\d{1,3}[.\s]?\d{3}[.\s]?\d{3}[-\s]?\d?)',
        r'NIT[^0-9]*(\d{9,11}[-\s]?\d?)',
        r'Nit\s*(\d{9,10})',
        r'NIT:\s*(\d+)',
        
        # Internacional
        r'Tax\s*ID[^0-9]*([A-Z0-9\-]+)',
        r'Tax\s*ID/EIN[^0-9]*([0-9]{2}-[0-9]{7})',
        r'RFC[^0-9]*([A-Z]{3,4}[0-9]{6}[A-Z0-9]{3})',
        r'VAT[^0-9]*([A-Z0-9]+)',
        r'EIN[^0-9]*([0-9]{2}-[0-9]{7})',
        
        # Genéricos
        r'Identification\s*Number[^0-9]*([A-Z0-9\-\.]+)',
        r'(?:NIT|RFC|TAX|ID)[:\s]*([A-Z0-9\-\.]+)'
    ]
    
    for pattern in nit_patterns:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            nit = match.group(1).replace('.', '').replace(' ', '').replace('-', '').strip()
            if len(nit) >= 8:
                # Formatear NIT
                if len(nit) == 9:
                    datos['nit_emisor'] = f"{nit[:3]}.{nit[3:6]}.{nit[6:]}"
                elif len(nit) == 10:
                    datos['nit_emisor'] = f"{nit[:3]}.{nit[3:6]}.{nit[6:9]}-{nit[9]}"
                else:
                    datos['nit_emisor'] = nit
                break
    
    # ============ RAZÓN SOCIAL EMISOR ============
    rs_patterns = [
        # Colombia
        r'Raz[ÓO]n\s*Social[^:]*:\s*([A-ZÁÉÍÓÚÑ\s&\.\-]+?)(?:\n|NIT| Ciudad)',
        r'Empresa[^:]*:\s*([A-ZÁÉÍÓÚÑ\s&\.\-]+)',
        r'EMISOR[^:]*:\s*([A-ZÁÉÍÓÚÑ\s&\.\-]+)',
        
        # Internacional
        r'(?:From|Bill\s*From)[^:]*:\s*([A-Z][A-Za-z\s&\.\-]+?)(?:\n|#|Account)',
        r'(?:Seller|Provider|Company)[^:]*:\s*([A-Z][A-Za-z\s&\.\-]+)',
        r'Business\s*Name[^:]*:\s*([A-Z][A-Za-z\s&\.\-]+)',
        
        # Genérico - buscar al inicio
        r'^([A-Z][A-Z\s&\.\-]{5,30})\s*(?:NIT|Tax|ID|RFC)'
    ]
    
    for pattern in rs_patterns:
        match = re.search(pattern, texto, re.IGNORECASE | re.MULTILINE)
        if match:
            val = match.group(1).strip()
            if len(val) >= 5:
                datos['razon_social_emisor'] = val[:100]
                break
    
    # Si no encontró razón social, buscar nombres de empresas conocidas
    if not datos['razon_social_emisor']:
        empresas = ['MICROSOFT', 'GOOGLE', 'AMAZON', 'FACEBOOK', 'APPLE', 'NETFLIX', 
                   'CANVA', 'LINKEDIN', 'BITLY', 'AIRBNB', 'UBER', 'DROPBOX',
                   'ZOOM', 'SLACK', 'ATLASSIAN', 'SALESFORCE', 'ORACLE']
        for emp in empresas:
            if emp in texto.upper():
                datos['razon_social_emisor'] = emp
                break
    
    # ============ CLIENTE / ADQUIRIENTE ============
    cliente_patterns = [
        r'(?:To|Bill\s*To|Cliente|Client)[^:]*:\s*([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑ\s&\.\-]+?)(?:\n|NIT|Tax|ID|Dirección)',
        r'Nombre\s*(?:del\s*)?Cliente[^:]*:\s*([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑ\s\.\-]+)',
        r'(?:Customer|Beneficiario)[^:]*:\s*([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑ\s\.\-]+)'
    ]
    
    for pattern in cliente_patterns:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            if len(val) >= 3:
                datos['nombre_adquiriente'] = val[:80]
                break
    
    # ============ DOCUMENTO CLIENTE ============
    doc_patterns = [
        r'(?:Documento|N[ÚU]mero)[^:]*:\s*(\d{6,12})',
        r'C\.C\.?\s*(\d{8,10})',
        r'NIT[^:]*:\s*(\d{9,10})'
    ]
    
    for pattern in doc_patterns:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            datos['nit_adquiriente'] = match.group(1)
            break
    
    # ============ EMAIL ============
    email_patterns = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        r'Email[^:]*:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    ]
    
    for pattern in email_patterns:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            datos['email_emisor'] = match.group(0).lower() if match else None
            break
    
    # ============ TELÉFONO ============
    tel_patterns = [
        r'Tel[eé]fono[^0-9]*(\+?[\d\s\-\(\)]{7,20})',
        r'Phone[^0-9]*(\+?[\d\s\-\(\)]{7,20})',
        r'(\+?\d{1,3}[\s\-]?\d{2,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4})',
        r'(\d{3}[\s\-]\d{3}[\s\-]\d{4})'
    ]
    
    for pattern in tel_patterns:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            tel = re.sub(r'[^\d\+]', '', match.group(1))
            if len(tel) >= 7:
                datos['telefono_emisor'] = tel
                break
    
    # ============ DIRECCIÓN ============
    dir_patterns = [
        r'Direcci[ÓO]n[^:]*:\s*([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑ0-9\s\,\.\#\-]+)',
        r'Address[^:]*:\s*([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑ0-9\s\,\.\#\-]+)',
        r'(?:Calle|Carrera|Avenida|Av)\.?\s*([A-Z0-9\s\,\.\#\-]+)'
    ]
    
    for pattern in dir_patterns:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            if len(val) >= 10:
                datos['direccion_emisor'] = val[:150]
                break
    
    # ============ PAÍS ============
        pais_patterns = [
            r'Pa[í]s[^:]*:\s*([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑ\s]+)',
            r'Country[^:]*:\s*([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑ\s]+)',
            r'(Colombia|México|Perú|Chile|Argentina|Brasil|Ecuador|Venezuela|España|United\s+States)'
        ]

        for pattern in pais_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                try:
                    pais = match.group(1).strip()
                except IndexError:
                    pais = match.group(0).strip()

            # Normalizar
            if 'colomb' in pais.lower(): datos['pais_emisor'] = 'Colombia'
            elif 'méxic' in pais.lower() or 'mexic' in pais.lower(): datos['pais_emisor'] = 'México'
            elif 'per' in pais.lower(): datos['pais_emisor'] = 'Perú'
            elif 'argentin' in pais.lower(): datos['pais_emisor'] = 'Argentina'
            elif 'chile' in pais.lower(): datos['pais_emisor'] = 'Chile'
            elif 'brasil' in pais.lower(): datos['pais_emisor'] = 'Brasil'
            elif 'españ' in pais.lower() or 'spain' in pais.lower(): datos['pais_emisor'] = 'España'
            elif 'united' in pais.lower() or 'states' in pais.lower() or 'usa' in pais.lower(): datos['pais_emisor'] = 'Estados Unidos'
            else: datos['pais_emisor'] = pais[:30]
            break
    
    # ============ MONEDA ============
    if 'USD' in texto or 'US$' in texto or 'dólar' in texto.lower() or 'dollar' in texto.lower():
        datos['moneda'] = 'USD'
    elif 'EUR' in texto or '€' in texto or 'euro' in texto.lower():
        datos['moneda'] = 'EUR'
    elif 'MXN' in texto or 'pesos mexicanos' in texto.lower():
        datos['moneda'] = 'MXN'
    elif 'PEN' in texto or 'soles' in texto.lower():
        datos['moneda'] = 'PEN'
    else:
        datos['moneda'] = 'COP'
    
    # ============ TOTALES ============
    # Buscar el valor más grande que parezca un total
    totales_encontrados = []
    
    # Patrones de total
    total_patterns = [
        r'Total\s*(?:a\s*pagar|neto|fACTURA)?[^$]*\$?\s*([\d,]+\.?\d*)',
        r'Grand\s*Total[^$]*\$?\s*([\d,]+\.?\d*)',
        r'Total\s*Due[^$]*\$?\s*([\d,]+\.?\d*)',
        r'Amount\s*Due[^$]*\$?\s*([\d,]+\.?\d*)',
        r'Importe\s*Total[^$]*\$?\s*([\d,]+\.?\d*)',
        r'Valor\s*Total[^$]*\$?\s*([\d,]+\.?\d*)',
        r'TOTAL[^$]*\$?\s*([\d,]+\.?\d*)',
        r'\$\s*([\d,]+\.?\d*)',
        r'([\d,]+\.?\d*)\s*(?:COP|USD|EUR|MXN)'
    ]
    
    for pattern in total_patterns:
        matches = re.findall(pattern, texto, re.IGNORECASE)
        for match in matches:
            try:
                valor = float(match.replace(',', ''))
                if valor > 0:
                    totales_encontrados.append(valor)
            except:
                pass
    
    if totales_encontrados:
        # Tomar el mayor valor encontrado como el total
        datos['total'] = max(totales_encontrados)
        # Estimar IVA y subtotal
        datos['iva'] = round(datos['total'] * 0.19, 2)
        datos['subtotal'] = round(datos['total'] / 1.19, 2)
    
    # ============ FORMA DE PAGO ============
    pago_patterns = [
        r'Forma\s*de\s*pago[^:]*:\s*([A-Za-z\s]+)',
        r'Payment\s*Method[^:]*:\s*([A-Za-z\s]+)',
        r'Payment\s*Terms[^:]*:\s*([A-Za-z\s]+)',
        r'(?:Transferencia|Consignación|Efectivo|Tarjeta|Cheque)\s*(?:bancaria)?'
    ]
    
    for pattern in pago_patterns:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            datos['forma_pago'] = match.group(1).strip()[:30]
            break
    
    # ============ CALCULAR CONFIANZA ============
    score = 0
    if datos['numero_factura'] and len(str(datos['numero_factura'])) >= 3:
        score += 20
    if datos['cufe']:
        score += 20
    if datos['nit_emisor'] and len(str(datos['nit_emisor'])) >= 8:
        score += 15
    if datos['razon_social_emisor']:
        score += 15
    if datos['total'] > 0:
        score += 15
    if datos['fecha_emision']:
        score += 10
    if datos['nombre_adquiriente']:
        score += 10
    if datos['email_emisor']:
        score += 5
    if datos['pais_emisor']:
        score += 5
    
    datos['confianza'] = min(score, 100)
    
    return datos

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=8000)
