# ContaSystem - Sistema de Gestión Contable

Sistema completo de gestión contable con facturación electrónica, gestión de clientes, productos y procesamiento OCR de documentos.

## Características

- 📊 **Dashboard** - Resumen general del sistema
- 🏢 **Gestión de Empresa** - Configuración de datos empresariales y tributarios
- 📋 **Resoluciones DIAN** - Gestión de resoluciones de facturación
- 👥 **Clientes** - Administración completa de clientes
- 📦 **Productos** - Catálogo de productos y servicios
- 🧾 **Facturación Electrónica** - Generación automática de facturas
- 📄 **Documentos** - Procesamiento OCR de documentos

## Tecnologías

### Backend
- Python 3.8+
- Flask (Framework web)
- SQLite (Base de datos)
- Pytesseract (OCR)

### Frontend
- HTML5
- CSS3 (Diseño moderno y responsive)
- JavaScript (Vanilla)

## Instalación

### 1. Requisitos previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### 2. Instalar dependencias

```bash
cd contasystem
pip install -r requirements.txt
```

### 3. Ejecutar la aplicación

```bash
python app.py
```

La aplicación estará disponible en: `http://localhost:8000`

## Uso

### Configuración inicial

1. **Configurar Empresa**: Ve a la sección "Empresa" y completa los datos de tu empresa
2. **Crear Resolución DIAN**: En "Resoluciones DIAN", crea una resolución de facturación
3. **Agregar Clientes**: Registra tus clientes en la sección "Clientes"
4. **Agregar Productos**: Crea tu catálogo en la sección "Productos"

### Facturación

1. Ve a "Facturación"
2. Click en "+ Nueva Factura"
3. Selecciona cliente y resolución
4. Agrega productos
5. Click en "Generar Factura"

### Documentos

1. Ve a "Documentos"
2. Click en "📤 Subir Documento"
3. Selecciona un PDF o imagen
4. El sistema procesará automáticamente el documento con OCR

## Estructura del Proyecto

```
contasystem/
├── app.py                 # Backend Flask
├── requirements.txt       # Dependencias Python
├── contasystem.db        # Base de datos SQLite (se crea automáticamente)
├── uploads/              # Carpeta para documentos (se crea automáticamente)
├── templates/
│   └── index.html        # Frontend HTML
└── static/
    └── app.js            # JavaScript del frontend
```

## API Endpoints

### Dashboard
- `GET /api/dashboard` - Obtener estadísticas generales

### Empresa
- `GET /api/empresa` - Obtener datos de la empresa
- `POST /api/empresa` - Guardar/actualizar empresa

### Resoluciones DIAN
- `GET /api/resoluciones` - Listar resoluciones
- `POST /api/resoluciones` - Crear resolución

### Clientes
- `GET /api/clientes` - Listar clientes
- `POST /api/clientes` - Crear cliente

### Productos
- `GET /api/productos` - Listar productos
- `POST /api/productos` - Crear producto

### Facturas
- `GET /api/facturas` - Listar facturas
- `POST /api/facturas` - Generar factura

### Documentos
- `GET /api/documentos` - Listar documentos
- `POST /api/documentos/upload` - Subir documento

## Base de Datos

El sistema utiliza SQLite con las siguientes tablas:

- `empresa` - Datos de la empresa
- `resoluciones_dian` - Resoluciones de facturación
- `clientes` - Información de clientes
- `productos` - Catálogo de productos/servicios
- `facturas` - Facturas generadas
- `detalle_facturas` - Líneas de productos en facturas
- `documentos` - Documentos procesados con OCR

## Características Destacadas

### 1. Facturación Automática
- Generación automática de números consecutivos
- Control de rangos de resolución DIAN
- Cálculo automático de IVA y totales

### 2. Interfaz Moderna
- Diseño limpio y profesional
- Navegación intuitiva
- Responsive design
- Modales para formularios

### 3. Dashboard Informativo
- Tarjetas con métricas clave
- Estadísticas en tiempo real
- Vista general del negocio

### 4. Gestión Completa
- CRUD completo para todas las entidades
- Validaciones de formularios
- Manejo de errores

## Notas de Desarrollo

### Mejoras Futuras Sugeridas

1. **Autenticación**: Agregar sistema de login y usuarios
2. **Reportes**: Generar PDFs de facturas
3. **Gráficos**: Dashboard con visualizaciones
4. **Exportación**: Excel de listados
5. **Email**: Envío automático de facturas
6. **API DIAN**: Integración real con DIAN
7. **Backups**: Sistema de respaldos automáticos

### Personalización

El código está estructurado de manera modular para facilitar:
- Agregar nuevos módulos
- Modificar estilos CSS
- Extender la API
- Agregar validaciones personalizadas

## Soporte

Para reportar problemas o sugerencias, crea un issue en el repositorio.

## Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

---

**Desarrollado con ❤️ para facilitar la gestión contable de pequeñas y medianas empresas**
