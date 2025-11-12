#!/usr/bin/env python3
"""Script principal para exportar rutas de transporte público OSM a KML."""

import sys
import os
import logging
import tempfile
import shutil
from pathlib import Path

from validator import validate_osm_file
from osm_processor import process_osm_file
from kml_exporter import export_routes_to_kml, create_zip

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def main():
    """
    Función principal del exportador OSM a KML.
    """
    print("="*60)
    print("🚌 OSM Transport KML Exporter")
    print("="*60)
    print()
    
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("❌ Error: Debes proporcionar un archivo OSM como argumento")
        print()
        print("📚 Uso:")
        print(f"  python {sys.argv[0]} <archivo.osm>")
        print()
        print("📝 Ejemplo:")
        print(f"  python {sys.argv[0]} input/mi_ciudad.osm")
        print()
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Paso 1: Validar archivo OSM
    print(f"🔍 Validando archivo: {input_file}")
    is_valid, message = validate_osm_file(input_file)
    
    if not is_valid:
        print(f"❌ Error de validación: {message}")
        sys.exit(1)
    
    print("✅ Archivo OSM válido")
    print()
    
    # Paso 2: Procesar archivo OSM
    print("🔄 Procesando rutas de transporte público...")
    try:
        routes = process_osm_file(input_file)
    except Exception as e:
        print(f"❌ Error al procesar archivo OSM: {str(e)}")
        logger.exception("Error durante el procesamiento")
        sys.exit(1)
    
    if not routes:
        print("⚠️  No se encontraron rutas válidas para exportar")
        sys.exit(0)
    
    print(f"✅ Se encontraron {len(routes)} rutas válidas")
    print()
    
    # Paso 3: Exportar a KML en directorio temporal
    print("🗂️  Generando archivos KML...")
    temp_dir = tempfile.mkdtemp(prefix="osm_kml_")
    
    try:
        kml_files = export_routes_to_kml(routes, temp_dir)
        
        if not kml_files:
            print("⚠️  No se pudieron generar archivos KML")
            sys.exit(1)
        
        print(f"✅ Se generaron {len(kml_files)} archivos KML")
        print()
        
        # Paso 4: Crear archivo ZIP
        print("📦 Creando archivo ZIP...")
        
        # Generar nombre del archivo ZIP
        input_filename = Path(input_file).stem
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        output_zip = os.path.join(output_dir, f"{input_filename}_kml.zip")
        
        zip_path = create_zip(kml_files, output_zip)
        
        # Obtener tamaño del archivo
        zip_size = os.path.getsize(zip_path)
        zip_size_mb = zip_size / (1024 * 1024)
        
        print("✅ Archivo ZIP creado exitosamente")
        print()
        print("="*60)
        print("🎉 EXPORTACIÓN COMPLETADA")
        print("="*60)
        print(f"📄 Archivo generado: {zip_path}")
        print(f"📊 Tamaño: {zip_size_mb:.2f} MB")
        print(f"🗺️  Rutas exportadas: {len(routes)}")
        print(f"🗂️  Archivos KML: {len(kml_files)}")
        print()
        print("📌 Próximos pasos:")
        print(f"  1. Descomprime el archivo: {zip_path}")
        print("  2. Abre los archivos .kml en Google Earth o tu visor favorito")
        print("  3. Verifica las rutas de transporte público")
        print()
        
    except Exception as e:
        print(f"❌ Error durante la exportación: {str(e)}")
        logger.exception("Error durante la exportación")
        sys.exit(1)
    
    finally:
        # Limpiar directorio temporal
        try:
            shutil.rmtree(temp_dir)
            logger.debug(f"Directorio temporal eliminado: {temp_dir}")
        except Exception as e:
            logger.warning(f"No se pudo eliminar directorio temporal: {e}")

if __name__ == "__main__":
    main()