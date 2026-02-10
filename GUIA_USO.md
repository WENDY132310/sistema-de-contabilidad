# Guía Rápida de Uso - ContaSystem

## 🚀 Inicio Rápido

### Linux/Mac
```bash
./start.sh
```

### Windows
```
start.bat
```

O manualmente:
```bash
pip install -r requirements.txt
python app.py
```

Luego abre tu navegador en: **http://localhost:8000**

---

## 📋 Flujo de Trabajo Recomendado

### 1️⃣ Primera Vez - Configuración

1. **Configurar tu Empresa**
   - Ve a: Menú lateral → **Empresa**
   - Completa todos los campos obligatorios
   - Guarda la configuración

2. **Crear Resolución DIAN**
   - Ve a: **Resoluciones DIAN**
   - Click en **+ Nueva Resolución**
   - Completa:
     - Número de resolución
     - Fechas
     - Prefijo (ej: FE)
     - Rango numérico
   - Click en **Crear Resolución**

3. **Agregar Clientes**
   - Ve a: **Clientes**
   - Click en **+ Nuevo Cliente**
   - Completa datos del cliente
   - Click en **Crear Cliente**

4. **Agregar Productos**
   - Ve a: **Productos**
   - Click en **+ Nuevo Producto**
   - Completa:
     - Código único
     - Nombre
     - Precio
     - % IVA
   - Click en **Crear Producto**

### 2️⃣ Facturación Diaria

1. Ve a: **Facturación**
2. Click en **+ Nueva Factura**
3. Selecciona:
   - Cliente
   - Resolución DIAN
4. Agrega productos:
   - Selecciona del dropdown
   - Ajusta cantidades
   - Elimina si es necesario
5. Verifica totales (se calculan automáticamente)
6. Click en **Generar Factura**
7. ✅ Factura creada con número consecutivo automático

### 3️⃣ Gestión de Documentos

1. Ve a: **Documentos**
2. Click en **📤 Subir Documento**
3. Selecciona PDF o imagen
4. El sistema procesa automáticamente con OCR
5. Ve el resultado en la tabla

---

## 🎯 Características Principales

### Dashboard
- Visualiza métricas clave
- Total de documentos, facturas, clientes
- Ventas facturadas

### Empresa
- Datos generales (NIT, dirección, contacto)
- Configuración tributaria
- Responsabilidades fiscales

### Resoluciones DIAN
- Múltiples resoluciones
- Control de rangos
- Estado activo/inactivo

### Clientes
- Persona Jurídica / Natural
- Tipos de documento (NIT, CC, CE)
- Plazo de pago
- Estado activo/inactivo

### Productos
- Código único
- Servicios o productos
- Precio con IVA
- Unidad de medida

### Facturación
- Generación automática de números
- Cálculo automático de IVA
- Control de stock de resoluciones
- Múltiples productos por factura

### Documentos
- Upload de PDF e imágenes
- Procesamiento OCR
- Estados: procesado/error

---

## 💡 Tips y Consejos

### ✅ Buenas Prácticas

1. **Siempre configura primero**
   - Empresa → Resolución → Clientes → Productos → Facturar

2. **Códigos únicos**
   - Usa códigos descriptivos para productos (ej: SERV-001, PROD-123)

3. **Verifica resoluciones**
   - Revisa que tengas resolución activa antes de facturar
   - Monitorea números disponibles

4. **Backup regular**
   - Copia el archivo `contasystem.db` periódicamente

### ⚠️ Errores Comunes

1. **"No hay resolución DIAN activa"**
   - Solución: Crea una resolución en el módulo correspondiente

2. **"El código ya existe"**
   - Solución: Usa un código diferente para el producto

3. **"Se agotó el rango de la resolución"**
   - Solución: Crea una nueva resolución con un nuevo rango

---

## 🔧 Solución de Problemas

### El servidor no inicia
```bash
# Verifica que Python esté instalado
python --version

# Verifica que las dependencias estén instaladas
pip list | grep Flask

# Reinstala dependencias
pip install -r requirements.txt --force-reinstall
```

### Error de puerto ocupado
```bash
# El puerto 8000 está en uso
# Cambia en app.py la última línea:
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Base de datos corrupta
```bash
# Elimina la base de datos (CUIDADO: perderás todos los datos)
rm contasystem.db

# Reinicia la app para crear una nueva
python app.py
```

---

## 📊 Estructura de Datos

### Tabla de Impuestos
- IVA 0%: Productos exentos
- IVA 5%: Algunos alimentos
- IVA 19%: Estándar en Colombia

### Estados
- **Activo**: Disponible para uso
- **Inactivo**: No se muestra en selecciones
- **Procesado**: Documento procesado correctamente
- **Error**: Documento con problemas

---

## 🎨 Personalización

### Cambiar colores
Edita `templates/index.html`, busca la sección `<style>` y modifica:
- `#3498db` → Color primario (azul)
- `#2c3e50` → Sidebar oscuro
- `#27ae60` → Color de éxito (verde)

### Agregar campos
1. Modifica la tabla en `app.py` (función `init_db()`)
2. Agrega el campo en el formulario HTML
3. Actualiza la función de guardado en JavaScript

---

## 📞 Soporte

Si encuentras algún problema:
1. Revisa esta guía
2. Verifica los logs en la consola
3. Consulta el README.md para más detalles técnicos

---

**¡Listo! Ya puedes gestionar tu contabilidad de forma profesional 🎉**
