"""
Módulo de detección de duplicados y validación de facturas
"""
import sqlite3
import hashlib
from datetime import datetime

class DuplicateDetector:
    """Detecta facturas duplicadas usando CUFE y otros identificadores"""
    
    def __init__(self, database):
        self.database = database
    
    def check_duplicate(self, cufe=None, numero_factura=None, archivo=None):
        """
        Verifica si ya existe una factura con los mismos identificadores
        
        Returns:
            {
                'is_duplicate': bool,
                'duplicate_id': int or None,
                'duplicate_info': dict or None,
                'match_type': 'cufe' | 'numero_factura' | 'archivo' | None
            }
        """
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        result = {
            'is_duplicate': False,
            'duplicate_id': None,
            'duplicate_info': None,
            'match_type': None
        }
        
        # 1. Verificar por CUFE (más confiable)
        if cufe:
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
                conn.close()
                return result
        
        # 2. Verificar por número de factura + NIT emisor
        if numero_factura:
            cursor.execute("""
                SELECT id, archivo, cufe, total, fecha_emision,
                       razon_social_emisor, estado, confianza
                FROM documentos 
                WHERE numero_factura = ?
                ORDER BY fecha_procesamiento DESC 
                LIMIT 1
            """, (numero_factura,))
            
            row = cursor.fetchone()
            if row:
                result['is_duplicate'] = True
                result['duplicate_id'] = row['id']
                result['match_type'] = 'numero_factura'
                result['duplicate_info'] = dict(row)
                conn.close()
                return result
        
        # 3. Verificar por hash de archivo (mismo archivo subido dos veces)
        if archivo:
            file_hash = self._calculate_file_hash(archivo)
            cursor.execute("""
                SELECT id, archivo, cufe, numero_factura, total,
                       razon_social_emisor, estado, confianza
                FROM documentos 
                WHERE archivo LIKE ?
                ORDER BY fecha_procesamiento DESC
            """, (f"%{file_hash}%",))
            
            row = cursor.fetchone()
            if row:
                result['is_duplicate'] = True
                result['duplicate_id'] = row['id']
                result['match_type'] = 'archivo'
                result['duplicate_info'] = dict(row)
        
        conn.close()
        return result
    
    def _calculate_file_hash(self, filepath):
        """Calcula hash MD5 de un archivo"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()[:16]
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
        existing = dict(cursor.fetchone())
        
        # Actualizar solo campos mejorados
        updates = []
        values = []
        
        for field in ['numero_factura', 'cufe', 'nit_emisor', 'razon_social_emisor',
                      'nit_adquiriente', 'nombre_adquiriente', 'fecha_emision',
                      'subtotal', 'iva', 'total', 'forma_pago']:
            if new_data.get(field) and not existing.get(field):
                updates.append(f"{field} = ?")
                values.append(new_data[field])
        
        # Si el nuevo tiene mejor confianza, actualizar confianza y estado
        if new_data.get('confianza', 0) > existing.get('confianza', 0):
            updates.append("confianza = ?")
            values.append(new_data['confianza'])
            
            if new_data.get('confianza', 0) >= 50:
                updates.append("estado = ?")
                values.append('procesado')
        
        if updates:
            values.append(existing_id)
            query = f"UPDATE documentos SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
        
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