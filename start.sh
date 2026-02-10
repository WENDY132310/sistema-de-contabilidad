#!/bin/bash

echo "======================================"
echo "  ContaSystem - Sistema de Gestión   "
echo "======================================"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado"
    echo "Por favor instala Python 3.8 o superior"
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"
echo ""

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt --break-system-packages

echo ""
echo "✅ Dependencias instaladas"
echo ""

# Iniciar aplicación
echo "🚀 Iniciando ContaSystem..."
echo ""
echo "Accede a la aplicación en: http://localhost:8000"
echo ""
echo "Presiona Ctrl+C para detener el servidor"
echo ""

python3 app.py
