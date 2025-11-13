#!/usr/bin/env python3
"""Script principal para exportar rutas de transporte público OSM a KML y Shapefile."""

import sys
import os
import logging
import tempfile
import shutil
import argparse
from pathlib import Path

from validator import validate_osm_file
from osm_processor import process_osm_file
from kml_exporter import export_routes_to_kml, create_zip
from shp_exporter import export_routes_to_shapefile, create_shapefile_zip

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def parse_arguments():
    """
    Parsea los argumentos de línea de comandos.
    """
    parser = argparse.ArgumentParser(
        description="Exportador de rutas de transporte público OSM a KML y Shapefile",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Ejemplos:
  %(prog)s input/ciudad.osm                    # Solo KML (por defecto)
  %(prog)s input/ciudad.osm --format shp      # Solo Shapefile  
  %(prog)s input/ciudad.osm --format both     # KML y Shapefile
  %(prog)s input/ciudad.osm --kml --shp       # KML y Shapefile (alternativo)"""
    )
    
    parser.add_argument(
        "input_file",
        help="Archivo OSM de entrada"
    )
    
    parser.add_argument(
        "--format", 
        choices=["kml", "shp", "shapefile", "both"],
        default="kml",
        help="Formato de salida (default: kml)"
    )
    
    parser.add_argument(
        "--kml",
        action="store_true",
        help="Exportar a formato KML"
    )
    
    parser.add_argument(
        "--shp",
        action="store_true", 
        help="Exportar a formato Shapefile"
    )
    
    return parser.parse_args()

def determine_export_formats(args):
    """
    Determina qué formatos exportar basado en los argumentos.
    """
    export_kml = False
    export_shp = False
    
    if args.kml or args.shp:
        export_kml = args.kml
        export_shp = args.shp
    else:
        if args.format in ["kml"]:
            export_kml = True
        elif args.format in ["shp", "shapefile"]:
            export_shp = True
        elif args.format == "both":
            export_kml = True
            export_shp = True
    
    # Si no se especificó nada, usar KML por defecto
    if not export_kml and not export_shp:
        export_kml = True
    
    return export_kml, export_shp

def main():
    """
    Función principal del exportador OSM a KML y Shapefile.
    """
    args = parse_arguments()
    export_kml, export_shp = determine_export_formats(args)
    
    formats = []
    if export_kml:
        formats.append("KML")
    if export_shp:
        formats.append("Shapefile")
    
    print("="*60)
    print(f"🚌 OSM Transport Exporter - {' + '.join(formats)}")
    print("="*60)
    print()
    
    input_file = args.input_file
    
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
    
    # Obtener geometrías de ways para ambos exportadores
    from osm_processor import get_way_geometries
    way_geoms = get_way_geometries(input_file)
    
    # Configurar directorios de salida
    input_filename = Path(input_file).stem
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    generated_files = []
    
    # Paso 3: Exportar a KML si se solicita
    if export_kml:
        print("🗂️  Generando archivos KML...")
        temp_dir = tempfile.mkdtemp(prefix="osm_kml_")
        
        try:
            kml_files = export_routes_to_kml(routes, temp_dir)
            
            if not kml_files:
                print("⚠️  No se pudieron generar archivos KML")
            else:
                print(f"✅ Se generaron {len(kml_files)} archivos KML")
                
                # Crear archivo ZIP para KML
                print("📦 Creando archivo ZIP para KML...")
                output_zip_kml = os.path.join(output_dir, f"{input_filename}_kml.zip")
                zip_path_kml = create_zip(kml_files, output_zip_kml)
                generated_files.append(("KML", zip_path_kml))
                print("✅ Archivo ZIP KML creado exitosamente")
                
        except Exception as e:
            print(f"❌ Error durante la exportación KML: {str(e)}")
            logger.exception("Error durante la exportación KML")
        
        finally:
            # Limpiar directorio temporal KML
            try:
                shutil.rmtree(temp_dir)
                logger.debug(f"Directorio temporal KML eliminado: {temp_dir}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar directorio temporal KML: {e}")
        
        print()
    
    # Paso 4: Exportar a Shapefile si se solicita
    if export_shp:
        print("🗂️  Generando Shapefile...")
        temp_shp_dir = tempfile.mkdtemp(prefix="osm_shp_")
        
        try:
            shp_path = export_routes_to_shapefile(routes, way_geoms, temp_shp_dir)
            print(f"✅ Shapefile generado: {len(routes)} rutas")
            
            # Crear archivo ZIP para Shapefile
            print("📦 Creando archivo ZIP para Shapefile...")
            output_zip_shp = os.path.join(output_dir, f"{input_filename}_shp.zip")
            zip_path_shp = create_shapefile_zip(shp_path, output_zip_shp)
            generated_files.append(("Shapefile", zip_path_shp))
            print("✅ Archivo ZIP Shapefile creado exitosamente")
            
        except Exception as e:
            print(f"❌ Error durante la exportación Shapefile: {str(e)}")
            logger.exception("Error durante la exportación Shapefile")
        
        finally:
            # Limpiar directorio temporal Shapefile
            try:
                shutil.rmtree(temp_shp_dir)
                logger.debug(f"Directorio temporal Shapefile eliminado: {temp_shp_dir}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar directorio temporal Shapefile: {e}")
        
        print()
    
    # Resumen final
    if generated_files:
        print("="*60)
        print("🎉 EXPORTACIÓN COMPLETADA")
        print("="*60)
        
        for format_type, file_path in generated_files:
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            print(f"📄 {format_type}: {file_path}")
            print(f"📊 Tamaño: {file_size:.2f} MB")
            print()
        
        print(f"🗺️  Rutas exportadas: {len(routes)}")
        print()
        print("📌 Próximos pasos:")
        
        if export_kml:
            print("  KML: Descomprime el ZIP y abre los .kml en Google Earth")
        if export_shp:
            print("  Shapefile: Descomprime el ZIP y abre en QGIS/ArcGIS")
        
        print()
    else:
        print("❌ No se pudo generar ningún archivo de salida")
        sys.exit(1)

if __name__ == "__main__":
    main()