"""Exportador de rutas a archivos KML y generación de archivo ZIP."""

import os
import zipfile
import re
import logging
from typing import Dict, List
from datetime import datetime
import simplekml
from shapely.geometry import LineString, MultiLineString
from shapely.ops import linemerge, unary_union

logger = logging.getLogger(__name__)

def sanitize_filename(name: str) -> str:
    """
    Sanitiza un nombre para usarlo como nombre de archivo.
    
    Args:
        name: Nombre original
        
    Returns:
        Nombre sanitizado sin caracteres especiales
    """
    # Reemplazar caracteres no permitidos
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Reemplazar espacios
    name = name.replace(' ', '_')
    # Eliminar caracteres no ASCII
    name = re.sub(r'[^\x00-\x7F]+', '_', name)
    # Limitar longitud
    if len(name) > 200:
        name = name[:200]
    return name

def export_routes_to_kml(routes: Dict[int, Dict], output_dir: str) -> List[str]:
    """
    Exporta rutas de transporte público a archivos KML individuales.
    
    Args:
        routes: Diccionario de rutas con geometrías
        output_dir: Directorio donde guardar los archivos KML
        
    Returns:
        Lista de rutas de archivos KML creados
    """
    os.makedirs(output_dir, exist_ok=True)
    kml_files = []
    
    logger.info(f"Exportando {len(routes)} rutas a KML en {output_dir}")
    
    for route_id, route_data in routes.items():
        try:
            # Unir geometrías
            geometries = route_data.get('geometries', [])
            if not geometries:
                logger.warning(f"Ruta {route_id} no tiene geometrías, omitiendo")
                continue
            
            merged = linemerge(unary_union(geometries))
            
            # Crear archivo KML
            kml = simplekml.Kml()
            kml.document.name = route_data['name']
            
            # Agregar descripción
            description = f"Tipo: {route_data.get('type', 'N/A')}\n"
            if route_data.get('ref'):
                description += f"Referencia: {route_data['ref']}\n"
            description += f"ID OSM: {route_id}\n"
            description += f"Exportado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Agregar geometría al KML
            if merged.geom_type == "MultiLineString":
                for i, line in enumerate(merged.geoms):
                    ls = kml.newlinestring(
                        name=f"{route_data['name']} (parte {i+1})",
                        description=description,
                        coords=list(line.coords)
                    )
                    ls.style.linestyle.color = simplekml.Color.red
                    ls.style.linestyle.width = 3
            elif merged.geom_type == "LineString":
                ls = kml.newlinestring(
                    name=route_data['name'],
                    description=description,
                    coords=list(merged.coords)
                )
                ls.style.linestyle.color = simplekml.Color.red
                ls.style.linestyle.width = 3
            else:
                logger.warning(
                    f"Ruta '{route_data['name']}' ({route_id}) tiene tipo de geometría "
                    f"no soportado: {merged.geom_type}"
                )
                continue
            
            # Generar nombre de archivo
            safe_name = sanitize_filename(route_data['name'])
            filename = f"{route_id}_{safe_name}.kml"
            filepath = os.path.join(output_dir, filename)
            
            # Guardar KML
            kml.save(filepath)
            kml_files.append(filepath)
            
            logger.debug(f"KML creado: {filename}")
            
        except Exception as e:
            logger.error(
                f"Error al exportar ruta '{route_data.get('name', route_id)}': {str(e)}"
            )
    
    logger.info(f"Se crearon {len(kml_files)} archivos KML")
    return kml_files

def create_zip(kml_files: List[str], output_zip_path: str) -> str:
    """
    Crea un archivo ZIP con todos los archivos KML.
    
    Args:
        kml_files: Lista de rutas de archivos KML
        output_zip_path: Ruta del archivo ZIP a crear
        
    Returns:
        Ruta del archivo ZIP creado
    """
    logger.info(f"Creando archivo ZIP: {output_zip_path}")
    
    # Asegurar que el directorio de salida existe
    os.makedirs(os.path.dirname(output_zip_path), exist_ok=True)
    
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for kml_file in kml_files:
            # Usar solo el nombre del archivo en el ZIP
            arcname = os.path.basename(kml_file)
            zipf.write(kml_file, arcname)
            logger.debug(f"Agregado al ZIP: {arcname}")
    
    logger.info(f"Archivo ZIP creado exitosamente: {output_zip_path}")
    return output_zip_path
