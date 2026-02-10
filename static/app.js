// API Base URL
const API_URL = 'http://localhost:8000/api';

// Estado global
let currentPage = 'dashboard';
let productosFactura = [];
let todosProductos = [];
let todosClientes = [];

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    initMenuNavigation();
    loadDashboard();
    loadEmpresa();
});

// Navegación del menú
function initMenuNavigation() {
    const menuItems = document.querySelectorAll('.menu-item');
    menuItems.forEach(item => {
        item.addEventListener('click', function() {
            const page = this.dataset.page;
            navigateToPage(page);
        });
    });
}

function navigateToPage(page) {
    // Ocultar todas las páginas
    document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
    
    // Mostrar página seleccionada
    document.getElementById(`page-${page}`).classList.remove('hidden');
    
    // Actualizar menú activo
    document.querySelectorAll('.menu-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === page) {
            item.classList.add('active');
        }
    });
    
    currentPage = page;
    
    // Cargar datos según la página
    switch(page) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'empresa':
            loadEmpresa();
            break;
        case 'resoluciones':
            loadResoluciones();
            break;
        case 'clientes':
            loadClientes();
            break;
        case 'productos':
            loadProductos();
            break;
        case 'facturacion':
            loadFacturas();
            break;
        case 'documentos':
            loadDocumentos();
            break;
    }
}

// Dashboard
async function loadDashboard() {
    try {
        const response = await fetch(`${API_URL}/dashboard`);
        const data = await response.json();
        
        document.getElementById('stat-documentos').textContent = data.documentos;
        document.getElementById('stat-facturas').textContent = data.facturas;
        document.getElementById('stat-clientes').textContent = data.clientes_activos;
        document.getElementById('stat-productos').textContent = data.productos_activos;
        document.getElementById('stat-procesados').textContent = data.documentos_procesados;
        document.getElementById('stat-errores').textContent = data.documentos_errores;
        document.getElementById('stat-ventas').textContent = `$ ${formatNumber(data.total_facturado)}`;
    } catch (error) {
        console.error('Error cargando dashboard:', error);
    }
}

// Empresa
async function loadEmpresa() {
    try {
        const response = await fetch(`${API_URL}/empresa`);
        const data = await response.json();
        
        if (data.id) {
            const form = document.getElementById('form-empresa');
            Object.keys(data).forEach(key => {
                const input = form.elements[key];
                if (input) {
                    if (input.type === 'checkbox') {
                        input.checked = data[key] == 1;
                    } else {
                        input.value = data[key] || '';
                    }
                }
            });
        }
    } catch (error) {
        console.error('Error cargando empresa:', error);
    }
}

document.getElementById('form-empresa').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const data = {};
    
    formData.forEach((value, key) => {
        data[key] = value;
    });
    
    // Checkboxes
    data.responsable_iva = this.elements.responsable_iva.checked ? 1 : 0;
    data.autorretenedor = this.elements.autorretenedor.checked ? 1 : 0;
    data.gran_contribuyente = this.elements.gran_contribuyente.checked ? 1 : 0;
    
    try {
        const response = await fetch(`${API_URL}/empresa`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (result.success) {
            showAlert('success', result.message);
        }
    } catch (error) {
        showAlert('error', 'Error al guardar la configuración');
        console.error(error);
    }
});

// Resoluciones DIAN
async function loadResoluciones() {
    try {
        const response = await fetch(`${API_URL}/resoluciones`);
        const resoluciones = await response.json();
        
        const tbody = document.querySelector('#table-resoluciones tbody');
        
        if (resoluciones.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="empty-state">
                        <div class="empty-state-icon">📋</div>
                        <p>No hay resoluciones registradas</p>
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = resoluciones.map(r => {
            const disponibles = r.numero_fin - r.actual;
            return `
                <tr>
                    <td>${r.numero_resolucion}</td>
                    <td>${r.prefijo}</td>
                    <td>${r.numero_inicio} - ${r.numero_fin}</td>
                    <td>${r.actual}</td>
                    <td>${formatDate(r.fecha_vigencia)}</td>
                    <td>${disponibles}</td>
                    <td><span class="badge ${r.estado === 'activo' ? 'badge-success' : 'badge-error'}">${r.estado}</span></td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Error cargando resoluciones:', error);
    }
}

async function saveResolucion(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });
    data.actual = parseInt(data.numero_inicio) - 1;
    
    try {
        const response = await fetch(`${API_URL}/resoluciones`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (result.success) {
            showAlert('success', result.message);
            closeModal('modal-resolucion');
            e.target.reset();
            loadResoluciones();
        }
    } catch (error) {
        showAlert('error', 'Error al crear la resolución');
        console.error(error);
    }
}

// Clientes
async function loadClientes() {
    try {
        const response = await fetch(`${API_URL}/clientes`);
        const clientes = await response.json();
        todosClientes = clientes;
        
        const tbody = document.querySelector('#table-clientes tbody');
        
        if (clientes.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="empty-state">
                        <div class="empty-state-icon">👥</div>
                        <p>No hay clientes</p>
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = clientes.map(c => `
            <tr>
                <td>${c.razon_social}</td>
                <td>${c.tipo_documento} ${c.numero_documento}${c.dv ? '-' + c.dv : ''}</td>
                <td>${c.email || '-'}</td>
                <td>${c.ciudad || '-'}</td>
                <td><span class="badge ${c.estado === 'activo' ? 'badge-success' : 'badge-error'}">${c.estado}</span></td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error cargando clientes:', error);
    }
}

async function saveCliente(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });
    data.responsable_iva = e.target.elements.responsable_iva.checked ? 1 : 0;
    
    try {
        const response = await fetch(`${API_URL}/clientes`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (result.success) {
            showAlert('success', result.message);
            closeModal('modal-cliente');
            e.target.reset();
            loadClientes();
        }
    } catch (error) {
        showAlert('error', 'Error al crear el cliente');
        console.error(error);
    }
}

// Productos
async function loadProductos() {
    try {
        const response = await fetch(`${API_URL}/productos`);
        const productos = await response.json();
        todosProductos = productos;
        
        const tbody = document.querySelector('#table-productos tbody');
        
        if (productos.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="empty-state">
                        <div class="empty-state-icon">📦</div>
                        <p>No hay productos</p>
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = productos.map(p => `
            <tr>
                <td>${p.codigo}</td>
                <td>${p.nombre}</td>
                <td>${p.tipo}</td>
                <td>$ ${formatNumber(p.precio_venta)}</td>
                <td>${p.tarifa_iva}%</td>
                <td><span class="badge ${p.estado === 'activo' ? 'badge-success' : 'badge-error'}">${p.estado}</span></td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error cargando productos:', error);
    }
}

async function saveProducto(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });
    
    try {
        const response = await fetch(`${API_URL}/productos`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (result.success) {
            showAlert('success', result.message);
            closeModal('modal-producto');
            e.target.reset();
            loadProductos();
        } else {
            showAlert('error', result.message);
        }
    } catch (error) {
        showAlert('error', 'Error al crear el producto');
        console.error(error);
    }
}

// Facturas
async function loadFacturas() {
    try {
        const response = await fetch(`${API_URL}/facturas`);
        const facturas = await response.json();
        
        const tbody = document.querySelector('#table-facturas tbody');
        
        if (facturas.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="empty-state">
                        <div class="empty-state-icon">🧾</div>
                        <p>No hay facturas</p>
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = facturas.map(f => `
            <tr>
                <td>${f.numero}</td>
                <td>${f.cliente_nombre || '-'}</td>
                <td>${formatDate(f.fecha)}</td>
                <td>$ ${formatNumber(f.subtotal)}</td>
                <td>$ ${formatNumber(f.iva)}</td>
                <td><strong>$ ${formatNumber(f.total)}</strong></td>
                <td><span class="badge ${f.estado === 'generado' ? 'badge-success' : 'badge-error'}">${f.estado}</span></td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error cargando facturas:', error);
    }
}

// Cargar datos para el modal de factura
async function loadFacturaModalData() {
    try {
        // Cargar clientes
        const clientesResponse = await fetch(`${API_URL}/clientes`);
        const clientes = await clientesResponse.json();
        
        const clienteSelect = document.querySelector('[name="cliente_id"]');
        clienteSelect.innerHTML = '<option value="">Seleccionar cliente...</option>' +
            clientes.filter(c => c.estado === 'activo').map(c => 
                `<option value="${c.id}">${c.razon_social}</option>`
            ).join('');
        
        // Cargar resoluciones
        const resolucionesResponse = await fetch(`${API_URL}/resoluciones`);
        const resoluciones = await resolucionesResponse.json();
        
        const resolucionSelect = document.querySelector('[name="resolucion_id"]');
        const resolucionesActivas = resoluciones.filter(r => r.estado === 'activo');
        
        if (resolucionesActivas.length === 0) {
            resolucionSelect.innerHTML = '<option value="">Sin resolución</option>';
            document.getElementById('alert-resolucion').classList.remove('hidden');
        } else {
            document.getElementById('alert-resolucion').classList.add('hidden');
            resolucionSelect.innerHTML = '<option value="">Seleccionar resolución...</option>' +
                resolucionesActivas.map(r => 
                    `<option value="${r.id}">${r.prefijo} (${r.actual + 1} - ${r.numero_fin})</option>`
                ).join('');
        }
        
        // Cargar productos
        const productosResponse = await fetch(`${API_URL}/productos`);
        const productos = await productosResponse.json();
        todosProductos = productos;
        
        const productoSelector = document.getElementById('producto-selector');
        productoSelector.innerHTML = '<option value="">Seleccionar producto...</option>' +
            productos.filter(p => p.estado === 'activo').map(p => 
                `<option value="${p.id}">${p.nombre} - $${formatNumber(p.precio_venta)}</option>`
            ).join('');
        
        // Agregar listener para agregar productos
        productoSelector.onchange = function() {
            if (this.value) {
                agregarProductoFactura(parseInt(this.value));
                this.value = '';
            }
        };
        
    } catch (error) {
        console.error('Error cargando datos del modal:', error);
    }
}

function agregarProductoFactura(productoId) {
    const producto = todosProductos.find(p => p.id === productoId);
    if (!producto) return;
    
    // Verificar si ya existe
    const existe = productosFactura.find(p => p.producto_id === productoId);
    if (existe) {
        existe.cantidad++;
    } else {
        productosFactura.push({
            producto_id: productoId,
            nombre: producto.nombre,
            cantidad: 1,
            precio_unitario: producto.precio_venta,
            tarifa_iva: producto.tarifa_iva,
            descuento: 0
        });
    }
    
    renderProductosFactura();
}

function eliminarProductoFactura(index) {
    productosFactura.splice(index, 1);
    renderProductosFactura();
}

function actualizarCantidadProducto(index, cantidad) {
    if (cantidad > 0) {
        productosFactura[index].cantidad = cantidad;
        renderProductosFactura();
    }
}

function renderProductosFactura() {
    const container = document.getElementById('productos-factura');
    
    if (productosFactura.length === 0) {
        container.innerHTML = '<p style="color: #999; font-size: 14px;">No hay productos agregados</p>';
        actualizarTotalesFactura();
        return;
    }
    
    container.innerHTML = productosFactura.map((p, index) => {
        const subtotal = p.cantidad * p.precio_unitario;
        const iva = subtotal * (p.tarifa_iva / 100);
        const total = subtotal + iva;
        
        return `
            <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <strong>${p.nombre}</strong>
                    <button type="button" onclick="eliminarProductoFactura(${index})" 
                        style="background: #e74c3c; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer;">
                        ✕
                    </button>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; font-size: 13px;">
                    <div>
                        <label style="color: #666;">Cantidad:</label><br>
                        <input type="number" value="${p.cantidad}" min="1" 
                            onchange="actualizarCantidadProducto(${index}, parseInt(this.value))"
                            style="width: 60px; padding: 4px; border: 1px solid #ddd; border-radius: 4px;">
                    </div>
                    <div>
                        <label style="color: #666;">Precio:</label><br>
                        <span>$${formatNumber(p.precio_unitario)}</span>
                    </div>
                    <div>
                        <label style="color: #666;">Total:</label><br>
                        <strong>$${formatNumber(total)}</strong>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    actualizarTotalesFactura();
}

function actualizarTotalesFactura() {
    let subtotal = 0;
    let descuento = 0;
    let iva = 0;
    
    productosFactura.forEach(p => {
        const subtotalProducto = p.cantidad * p.precio_unitario;
        subtotal += subtotalProducto;
        descuento += p.descuento || 0;
        iva += subtotalProducto * (p.tarifa_iva / 100);
    });
    
    const total = subtotal - descuento + iva;
    
    document.getElementById('factura-subtotal').textContent = `$ ${formatNumber(subtotal)}`;
    document.getElementById('factura-descuento').textContent = `$ ${formatNumber(descuento)}`;
    document.getElementById('factura-iva').textContent = `$ ${formatNumber(iva)}`;
    document.getElementById('factura-total').textContent = `$ ${formatNumber(total)}`;
}

async function saveFactura(e) {
    e.preventDefault();
    
    if (productosFactura.length === 0) {
        showAlert('error', 'Debe agregar al menos un producto');
        return;
    }
    
    const formData = new FormData(e.target);
    const data = {
        cliente_id: parseInt(formData.get('cliente_id')),
        resolucion_id: parseInt(formData.get('resolucion_id')),
        observaciones: formData.get('observaciones'),
        detalles: []
    };
    
    // Calcular totales
    let subtotal = 0;
    let descuento = 0;
    let iva = 0;
    
    productosFactura.forEach(p => {
        const subtotalProducto = p.cantidad * p.precio_unitario;
        const ivaProducto = subtotalProducto * (p.tarifa_iva / 100);
        const totalProducto = subtotalProducto + ivaProducto;
        
        subtotal += subtotalProducto;
        descuento += p.descuento || 0;
        iva += ivaProducto;
        
        data.detalles.push({
            producto_id: p.producto_id,
            cantidad: p.cantidad,
            precio_unitario: p.precio_unitario,
            descuento: p.descuento || 0,
            iva: ivaProducto,
            total: totalProducto
        });
    });
    
    data.subtotal = subtotal;
    data.descuento = descuento;
    data.iva = iva;
    data.total = subtotal - descuento + iva;
    
    try {
        const response = await fetch(`${API_URL}/facturas`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (result.success) {
            showAlert('success', `Factura ${result.numero} generada exitosamente`);
            closeModal('modal-factura');
            e.target.reset();
            productosFactura = [];
            renderProductosFactura();
            loadFacturas();
        } else {
            showAlert('error', result.message);
        }
    } catch (error) {
        showAlert('error', 'Error al generar la factura');
        console.error(error);
    }
}

// Documentos
async function loadDocumentos() {
    try {
        const response = await fetch(`${API_URL}/documentos`);
        const documentos = await response.json();
        
        const tbody = document.querySelector('#table-documentos tbody');
        
        if (documentos.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="empty-state">
                        <div class="empty-state-icon">📄</div>
                        <p>No hay documentos procesados</p>
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = documentos.map(d => {
            const confianzaColor = d.confianza >= 70 ? '#27ae60' : d.confianza >= 50 ? '#f39c12' : '#e74c3c';
            return `
                <tr>
                    <td><strong>${d.numero_factura || d.archivo}</strong></td>
                    <td>${d.fecha_emision ? formatDate(d.fecha_emision) : '—'}</td>
                    <td>
                        ${d.razon_social_emisor || '—'}<br>
                        <small style="color: #999;">NIT: ${d.nit_emisor || '—'}</small>
                    </td>
                    <td>
                        ${d.nombre_adquiriente || '—'}<br>
                        <small style="color: #999;">${d.nit_adquiriente || ''}</small>
                    </td>
                    <td><strong>$${formatNumber(d.total || 0)}</strong></td>
                    <td>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <div style="flex: 1; background: #f0f0f0; height: 8px; border-radius: 4px; overflow: hidden;">
                                <div style="width: ${d.confianza}%; background: ${confianzaColor}; height: 100%;"></div>
                            </div>
                            <span style="font-size: 12px; font-weight: 600; color: ${confianzaColor};">${d.confianza}%</span>
                        </div>
                    </td>
                    <td><span class="badge ${d.estado === 'procesado' ? 'badge-success' : 'badge-error'}">${d.estado}</span></td>
                    <td>
                        <button class="btn btn-secondary" onclick="verDetalleDocumento(${d.id})" 
                            style="padding: 6px 12px; font-size: 12px;">👁️ Ver</button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Error cargando documentos:', error);
    }
}

function verDetalleDocumento(id) {
    showAlert('info', 'Función de visualización en desarrollo');
}

async function uploadDocument(input) {
    const file = input.files[0];
    if (!file) return;
    
    // Validar tipo de archivo
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showAlert('error', 'Solo se permiten archivos PDF');
        input.value = '';
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        showAlert('info', `Procesando documento: ${file.name}...`);
        
        const response = await fetch(`${API_URL}/documentos/upload`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        if (result.success) {
            // Mostrar resultado detallado
            const datos = result.datos || {};
            let mensaje = `Documento procesado con ${result.confianza}% de confianza\n\n`;
            
            if (datos.numero_factura) {
                mensaje += `📄 Factura: ${datos.numero_factura}\n`;
            }
            if (datos.razon_social_emisor) {
                mensaje += `🏢 Emisor: ${datos.razon_social_emisor}\n`;
            }
            if (datos.nit_emisor) {
                mensaje += `🆔 NIT: ${datos.nit_emisor}\n`;
            }
            if (datos.nombre_adquiriente) {
                mensaje += `👤 Cliente: ${datos.nombre_adquiriente}\n`;
            }
            if (datos.fecha_emision) {
                mensaje += `📅 Fecha: ${datos.fecha_emision}\n`;
            }
            if (datos.total) {
                mensaje += `💰 Total: $${formatNumber(datos.total)}\n`;
            }
            
            console.log(mensaje);
            
            if (result.confianza >= 70) {
                showAlert('success', `✅ ${result.message}`);
            } else if (result.confianza >= 50) {
                showAlert('warning', `⚠️ ${result.message} (Revisar datos)`);
            } else {
                showAlert('error', `❌ Confianza baja: ${result.confianza}%`);
            }
            
            loadDocumentos();
        } else {
            showAlert('error', result.message);
        }
    } catch (error) {
        showAlert('error', 'Error al subir el documento');
        console.error(error);
    }
    
    input.value = '';
}

// Utilidades
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.add('active');
    
    // Si es modal de factura, cargar datos
    if (modalId === 'modal-factura') {
        loadFacturaModalData();
        productosFactura = [];
        renderProductosFactura();
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.remove('active');
}

function showAlert(type, message) {
    // Crear elemento de alerta
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <span>${type === 'error' ? '⚠️' : type === 'success' ? '✅' : 'ℹ️'}</span>
        <span>${message}</span>
    `;
    
    // Insertar al inicio del contenido
    const content = document.querySelector('.content');
    content.insertBefore(alert, content.firstChild);
    
    // Eliminar después de 5 segundos
    setTimeout(() => {
        alert.remove();
    }, 8000);
}

function formatNumber(num) {
    return new Intl.NumberFormat('es-CO', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(num);
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-CO');
}
