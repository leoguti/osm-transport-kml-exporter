"""Validador de archivos OSM para transporte público."""

import os
import xml.etree.ElementTree as ET
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

def validate_osm_file(file_path: str) -> Tuple[bool, str]:
    """
    Valida que un archivo OSM sea válido y contenga relaciones de transporte público.
    
    Args:
        file_path: Ruta al archivo OSM a validar
        
    Returns:
        Tupla (es_válido, mensaje)
        - es_válido: True si el archivo es válido, False en caso contrario
        - mensaje: "OK" si es válido, descripción del error si no lo es
    """
    # Verificar que el archivo existe
    if not os.path.exists(file_path):
        return False, f"El archivo no existe: {file_path}"
    
    # Verificar que tiene extensión .osm
    if not file_path.lower().endswith('.osm'):
        return False, "El archivo debe tener extensión .osm"
    
    try:
        # Intentar parsear como XML
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Verificar que sea un archivo OSM válido
        if root.tag != 'osm':
            return False, "El archivo no es un archivo OSM válido (elemento raíz no es 'osm')"
        
        # Buscar al menos una relación de transporte público
        has_transport_relation = False
        transport_types = ["bus", "trolleybus", "tram", "train", "subway", "light_rail"]
        
        for relation in root.findall('.//relation'):
            tags = {tag.get('k'): tag.get('v') for tag in relation.findall('tag')}
            
            if tags.get('type') == 'route' and tags.get('route') in transport_types:
                has_transport_relation = True
                break
        
        if not has_transport_relation:
            return False, (
                "El archivo no contiene relaciones de transporte público válidas.\n"
                f"Tipos soportados: {', '.join(transport_types)}\n"
                "Asegúrate de que las relaciones tengan type=route y route=<tipo_transporte>"
            )
        
        logger.info(f"Archivo OSM validado correctamente: {file_path}")
        return True, "OK"
        
    except ET.ParseError as e:
        return False, f"Error al parsear XML: {str(e)}"
    except Exception as e:
        return False, f"Error inesperado durante la validación: {str(e)}"