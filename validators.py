"""
Módulo de detección de duplicados y validación de facturas
"""
import sqlite3
import hashlib
from datetime import datetime

class DuplicateDetector:
    """Detecta facturas duplicadas con verificación múltiple para evitar falsos positivos"""
    
    def __init__(self, database):
        self.database = database
    
    def check_duplicate(self, cufe=None, numero_factura=None, nit_emisor=None, 
                        total=None, fecha_emision=None, archivo=None):
        """
        Verifica si ya existe una factura IDÉNTICA
        
        Criterios para considerar duplicado REAL:
        1. CUFE idéntico (más confiable)
        2. Número factura + NIT emisor + Total + Fecha (combinación única)
        3. Hash del archivo (mismo archivo subido dos veces)
        
        Returns:
            {
                'is_duplicate': bool,
                'duplicate_id': int or None,
                'duplicate_info': dict or None,
                'match_type': 'cufe' | 'factura_completa' | 'archivo' | None,
                'confidence': int (0-100) # Confianza de que es duplicado
            }
        """
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        result = {
            'is_duplicate': False,
            'duplicate_id': None,
            'duplicate_info': None,
            'match_type': None,
            'confidence': 0
        }
        
        # =====================================================
        # VERIFICACIÓN 1: CUFE (100% confiable)
        # =====================================================
        if cufe and len(cufe) >= 64:  # CUFE válido tiene 64+ caracteres
            cursor.execute("""
                SELECT id, archivo, numero_factura, total, fecha_emision, 
                       razon_social_emisor, estado, confianza
                FROM documentos 
                WHERE cufe = ? 
                ORDER BY fecha_procesamiento DESC 
                LIMIT 1
            """, (cufe,))
            
            row = cursor.fetchone()
            if row:
                result['is_duplicate'] = True
                result['duplicate_id'] = row['id']
                result['match_type'] = 'cufe'
                result['duplicate_info'] = dict(row)
                result['confidence'] = 100  # CUFE es 100% confiable
                conn.close()
                return result
        
        # =====================================================
        # VERIFICACIÓN 2: Combinación MÚLTIPLE de campos
        # Debe coincidir: Número + NIT + Total + Fecha
        # =====================================================
        if numero_factura and nit_emisor and total and fecha_emision:
            # Tolerancia en total: ±0.01 para errores de redondeo
            total_min = total - 0.01
            total_max = total + 0.01
            
            cursor.execute("""
                SELECT id, archivo, cufe, numero_factura, total, 
                       fecha_emision, razon_social_emisor, estado, confianza
                FROM documentos 
                WHERE numero_factura = ?
                  AND nit_emisor = ?
                  AND total BETWEEN ? AND ?
                  AND fecha_emision = ?
                ORDER BY fecha_procesamiento DESC 
                LIMIT 1
            """, (numero_factura, nit_emisor, total_min, total_max, fecha_emision))
            
            row = cursor.fetchone()
            if row:
                result['is_duplicate'] = True
                result['duplicate_id'] = row['id']
                result['match_type'] = 'factura_completa'
                result['duplicate_info'] = dict(row)
                result['confidence'] = 95  # Muy alta confianza
                conn.close()
                return result
        
        # =====================================================
        # VERIFICACIÓN 3: Número de factura + NIT (sin total)
        # Confianza media - podría ser factura diferente
        # =====================================================
        if numero_factura and nit_emisor:
            cursor.execute("""
                SELECT id, archivo, cufe, total, fecha_emision,
                       razon_social_emisor, estado, confianza
                FROM documentos 
                WHERE numero_factura = ?
                  AND nit_emisor = ?
                ORDER BY fecha_procesamiento DESC 
                LIMIT 1
            """, (numero_factura, nit_emisor))
            
            row = cursor.fetchone()
            if row:
                # Solo considerar duplicado si el total también coincide
                if total and abs(row['total'] - total) < 1.0:
                    result['is_duplicate'] = True
                    result['duplicate_id'] = row['id']
                    result['match_type'] = 'numero_factura'
                    result['duplicate_info'] = dict(row)
                    result['confidence'] = 85
                    conn.close()
                    return result
                else:
                    # Mismo número pero diferente total = NO es duplicado
                    # (puede ser corrección, nota crédito, etc.)
                    result['is_duplicate'] = False
                    result['confidence'] = 30  # Baja confianza
        
        # =====================================================
        # VERIFICACIÓN 4: Hash de archivo (mismo archivo físico)
        # =====================================================
        if archivo:
            file_hash = self._calculate_file_hash(archivo)
            if file_hash:
                cursor.execute("""
                    SELECT id, archivo, cufe, numero_factura, total,
                           razon_social_emisor, estado, confianza
                    FROM documentos 
                    WHERE file_hash = ?
                    ORDER BY fecha_procesamiento DESC
                    LIMIT 1
                """, (file_hash,))
                
                row = cursor.fetchone()
                if row:
                    result['is_duplicate'] = True
                    result['duplicate_id'] = row['id']
                    result['match_type'] = 'archivo_identico'
                    result['duplicate_info'] = dict(row)
                    result['confidence'] = 100  # Archivo idéntico = duplicado seguro
                    conn.close()
                    return result
        
        conn.close()
        return result
    
    def _calculate_file_hash(self, filepath):
        """Calcula hash MD5 de un archivo"""
        try:
            import hashlib
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None
    
    def merge_duplicates(self, existing_id, new_data):
        """
        Actualiza registro existente con datos adicionales del duplicado
        Solo actualiza campos que están vacíos o mejoran la confianza
        """
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        
        # Obtener datos existentes
        cursor.execute("SELECT * FROM documentos WHERE id = ?", (existing_id,))
        row = cursor.fetchone()
        if not row:
            return
        columns = [desc[0] for desc in cursor.description]
        existing = dict(zip(columns, row))
        
        # Lista de campos a actualizar si están vacíos
        campos_actualizables = [
            'numero_factura', 'cufe', 'nit_emisor', 'razon_social_emisor',
            'nit_adquiriente', 'nombre_adquiriente', 'fecha_emision',
            'pais_emisor', 'ciudad_emisor', 'telefono_emisor', 'email_emisor',
            'subtotal', 'iva', 'total', 'forma_pago', 'numero_tercero_emisor',
            'tipo_documento_emisor', 'direccion_emisor', 'departamento_emisor'
        ]
        
        updates = []
        values = []
        
        for field in campos_actualizables:
            # Actualizar si:
            # 1. El campo existente está vacío/None
            # 2. Y el nuevo dato tiene valor
            if not existing.get(field) and new_data.get(field):
                updates.append(f"{field} = ?")
                values.append(new_data[field])
        
        # Si el nuevo tiene mejor confianza, actualizar confianza
        if new_data.get('confianza', 0) > existing.get('confianza', 0):
            updates.append("confianza = ?")
            values.append(new_data['confianza'])
            
            # Actualizar estado si mejora
            if new_data.get('confianza', 0) >= 70 and existing.get('estado') != 'validado':
                updates.append("estado = ?")
                values.append('validado')
            elif new_data.get('confianza', 0) >= 50 and existing.get('estado') == 'error':
                updates.append("estado = ?")
                values.append('pendiente')
        
        # Agregar nota de actualización
        if updates:
            updates.append("observaciones = ?")
            observacion_nueva = f"Actualizado con datos adicionales el {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            if existing.get('observaciones'):
                values.append(f"{existing['observaciones']}; {observacion_nueva}")
            else:
                values.append(observacion_nueva)
            
            updates.append("fecha_actualizacion = CURRENT_TIMESTAMP")
            
            # Ejecutar actualización
            values.append(existing_id)
            query = f"UPDATE documentos SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
            
            print(f"✅ Duplicado detectado - Registro {existing_id} actualizado con {len(updates)-1} campos nuevos")
        else:
            print(f"ℹ️ Duplicado detectado - Sin campos nuevos para actualizar")
        
        conn.close()
        return True

class FacturaValidator:
    """Valida facturas y gestiona estados de radicación"""
    
    ESTADOS = {
        'pendiente': 'Pendiente de validación',
        'validado': 'Validado, listo para radicar',
        'radicado': 'Radicado en DIAN',
        'rechazado': 'Rechazado por DIAN',
        'error': 'Error en procesamiento',
        'correccion': 'Requiere corrección'
    }
    
    def __init__(self, database):
        self.database = database
    
    def validar_factura(self, documento_id):
        """
        Valida si una factura está lista para radicar en DIAN
        
        Returns:
            {
                'valido': bool,
                'errores': list,
                'advertencias': list,
                'score': int (0-100)
            }
        """
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM documentos WHERE id = ?", (documento_id,))
        doc = cursor.fetchone()
        conn.close()
        
        if not doc:
            return {'valido': False, 'errores': ['Documento no encontrado'], 'advertencias': [], 'score': 0}
        
        errores = []
        advertencias = []
        score = 100
        
        # Validaciones críticas (bloqueantes)
        if not doc['cufe']:
            errores.append('Falta CUFE (Código Único de Factura Electrónica)')
            score -= 30
        
        if not doc['numero_factura']:
            errores.append('Falta número de factura')
            score -= 20
        
        if not doc['nit_emisor']:
            errores.append('Falta NIT del emisor')
            score -= 15
        
        if not doc['total'] or doc['total'] <= 0:
            errores.append('Total inválido o cero')
            score -= 20
        
        if not doc['fecha_emision']:
            errores.append('Falta fecha de emisión')
            score -= 10
        
        # Validaciones recomendadas (advertencias)
        if not doc['razon_social_emisor']:
            advertencias.append('Falta razón social del emisor')
            score -= 3
        
        if not doc['nombre_adquiriente']:
            advertencias.append('Falta nombre del cliente')
            score -= 2
        
        if doc['confianza'] < 70:
            advertencias.append(f'Confianza baja ({doc["confianza"]}%)')
            score -= 5
        
        return {
            'valido': len(errores) == 0,
            'errores': errores,
            'advertencias': advertencias,
            'score': max(0, score)
        }
    
    def get_documentos_pendientes(self):
        """Obtiene documentos pendientes de radicar"""
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM documentos 
            WHERE estado IN ('pendiente', 'validado', 'correccion')
            ORDER BY fecha_procesamiento ASC
        """)
        
        docs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return docs
    
    def actualizar_estado(self, documento_id, nuevo_estado, observaciones=None):
        """Actualiza el estado de un documento"""
        if nuevo_estado not in self.ESTADOS:
            raise ValueError(f"Estado inválido: {nuevo_estado}")
        
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE documentos 
            SET estado = ?, 
                observaciones = COALESCE(?, observaciones),
                fecha_actualizacion = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (nuevo_estado, observaciones, documento_id))
        
        conn.commit()
        conn.close()
        return True


class ScheduledProcessor:
    """Procesador automático programado para validar y radicar facturas"""
    
    def __init__(self, database):
        self.database = database
        self.validator = FacturaValidator(database)
    
    def proceso_automatico(self):
        """
        Proceso que se ejecuta automáticamente a las 8am y 8pm
        1. Obtiene documentos pendientes
        2. Valida cada uno
        3. Si pasa validación, marca como 'validado'
        4. Si tiene errores, marca como 'correccion'
        """
        print(f"[{datetime.now()}] Iniciando proceso automático de validación...")
        
        documentos = self.validator.get_documentos_pendientes()
        
        resultados = {
            'procesados': 0,
            'validados': 0,
            'requieren_correccion': 0,
            'errores': 0
        }
        
        for doc in documentos:
            try:
                validacion = self.validator.validar_factura(doc['id'])
                
                if validacion['valido']:
                    # Marcar como validado y listo para radicar
                    self.validator.actualizar_estado(
                        doc['id'], 
                        'validado',
                        f"Validación automática exitosa. Score: {validacion['score']}%"
                    )
                    resultados['validados'] += 1
                else:
                    # Requiere corrección
                    errores_str = '; '.join(validacion['errores'])
                    self.validator.actualizar_estado(
                        doc['id'],
                        'correccion',
                        f"Errores: {errores_str}"
                    )
                    resultados['requieren_correccion'] += 1
                
                resultados['procesados'] += 1
                
            except Exception as e:
                print(f"Error procesando documento {doc['id']}: {str(e)}")
                resultados['errores'] += 1
        
        print(f"[{datetime.now()}] Proceso completado:")
        print(f"  - Procesados: {resultados['procesados']}")
        print(f"  - Validados: {resultados['validados']}")
        print(f"  - Requieren corrección: {resultados['requieren_correccion']}")
        print(f"  - Errores: {resultados['errores']}")
        
        return resultados
    
    def radicar_validados(self):
        """
        Radica en DIAN los documentos validados
        (Conectará con API DIAN cuando esté disponible)
        """
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM documentos 
            WHERE estado = 'validado'
            ORDER BY fecha_emision ASC
        """)
        
        validados = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        radicados = 0
        
        for doc in validados:
            try:
                # TODO: Integración con API DIAN
                # respuesta_dian = api_dian.radicar_factura(doc)
                
                # Por ahora, simulamos radicación exitosa
                self.validator.actualizar_estado(
                    doc['id'],
                    'radicado',
                    f"Radicado en DIAN (simulado) - {datetime.now()}"
                )
                radicados += 1
                
            except Exception as e:
                print(f"Error radicando documento {doc['id']}: {str(e)}")
                self.validator.actualizar_estado(
                    doc['id'],
                    'error',
                    f"Error en radicación: {str(e)}"
                )
        
        print(f"Radicados exitosamente: {radicados}/{len(validados)}")
        return radicados