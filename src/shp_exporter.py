#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exportador de rutas de transporte público a formato Shapefile.
Convierte relaciones de transporte público desde datos OSM procesados a shapefiles
con geometrías continuas, longitud de ruta y compatibilidad GTFS.

Autor: Leonardo Gutiérrez
"""

import os
import logging
from typing import Dict, List, Tuple, Any
import geopandas as gpd
from shapely.geometry import LineString
from shapely.ops import linemerge, unary_union

logger = logging.getLogger(__name__)

def create_continuous_geometry(ways: List[int], way_geoms: Dict[int, LineString]) -> LineString:
    """
    Crea una geometría continua a partir de una lista de ways.
    
    Args:
        ways: Lista de IDs de ways que forman la ruta
        way_geoms: Diccionario con geometrías de ways {way_id: LineString}
        
    Returns:
        LineString con la geometría continua de la ruta
        
    Raises:
        Exception: Si no se puede crear la geometría continua
    """
    lines = [way_geoms[way_id] for way_id in ways if way_id in way_geoms]
    
    if not lines:
        raise Exception("No se encontraron geometrías válidas para los ways")
    
    try:
        merged = linemerge(unary_union(lines))
        
        if merged.is_empty:
            raise Exception("La geometría resultante está vacía")
            
        return merged
        
    except Exception as e:
        raise Exception(f"Error al unir geometrías: {str(e)}")

def calculate_route_length(geometry: LineString, target_crs: str = "EPSG:3857") -> float:
    """
    Calcula la longitud de una ruta en kilómetros.
    
    Args:
        geometry: Geometría LineString en coordenadas geográficas
        target_crs: CRS métrico para el cálculo de longitud (default: Web Mercator)
        
    Returns:
        Longitud de la ruta en kilómetros
    """
    try:
        # Crear GeoDataFrame temporal para proyección
        gdf_temp = gpd.GeoDataFrame([1], geometry=[geometry], crs="EPSG:4326")
        gdf_projected = gdf_temp.to_crs(target_crs)
        
        # Calcular longitud en metros y convertir a kilómetros
        length_m = gdf_projected.geometry[0].length
        return length_m / 1000.0
        
    except Exception as e:
        logger.warning(f"Error al calcular longitud: {e}")
        return 0.0

def create_route_record(route_data: Dict[str, Any], geometry: LineString) -> Dict[str, Any]:
    """
    Crea un registro completo para el shapefile con todos los campos.
    
    Args:
        route_data: Datos de la ruta desde el procesador OSM
        geometry: Geometría LineString de la ruta
        
    Returns:
        Diccionario con todos los campos para el shapefile
    """
    # Crear campo route_long combinando origen y destino
    from_stop = route_data.get("from", "")
    to_stop = route_data.get("to", "")
    route_long = f"{from_stop} - {to_stop}".strip(" -")
    
    # Si no hay origen/destino, usar el nombre de la ruta
    if not route_long or route_long == "-":
        route_long = route_data.get("name", f"route_{route_data.get('id', '')}")
    
    # Calcular longitud
    length_km = calculate_route_length(geometry)
    
    return {
        "route_id": route_data.get("id", ""),
        "route_name": route_data.get("name", ""),
        "ref": route_data.get("ref", ""),
        "route_type": route_data.get("route", ""),
        "from_stop": from_stop,
        "to_stop": to_stop,
        "operator": route_data.get("operator", ""),
        "route_long": route_long,
        "length_km": round(length_km, 3),
        "geometry": geometry
    }

def export_routes_to_shapefile(routes: Dict[int, Dict[str, Any]], 
                             way_geoms: Dict[int, LineString],
                             output_dir: str) -> str:
    """
    Exporta rutas de transporte público a formato Shapefile.
    
    Args:
        routes: Diccionario de rutas procesadas desde OSM {route_id: route_data}
        way_geoms: Diccionario con geometrías de ways
        output_dir: Directorio de salida para el shapefile
        
    Returns:
        Ruta del archivo shapefile generado
        
    Raises:
        Exception: Si no se pueden generar geometrías válidas
    """
    logger.info(f"Exportando {len(routes)} rutas a Shapefile en {output_dir}")
    
    os.makedirs(output_dir, exist_ok=True)
    records = []
    skipped_routes = []

    for route_id, route in routes.items():
        try:
            # Crear geometría continua
            geometry = create_continuous_geometry(route["ways"], way_geoms)
            
            # Crear registro completo
            record = create_route_record(route, geometry)
            records.append(record)
            
            logger.debug(f"Ruta procesada: {route.get('name', route.get('id'))} "
                        f"({record['length_km']:.2f} km)")
            
        except Exception as e:
            route_name = route.get("name", route.get("id", "desconocida"))
            logger.warning(f"No se pudo procesar ruta '{route_name}': {e}")
            skipped_routes.append(route_name)
            continue

    if not records:
        raise Exception("No se generaron geometrías válidas para ninguna ruta")

    # Crear GeoDataFrame
    logger.info(f"Creando GeoDataFrame con {len(records)} rutas válidas")
    gdf = gpd.GeoDataFrame(records, crs="EPSG:4326")

    # Exportar shapefile
    output_path = os.path.join(output_dir, "rutas_transporte.shp")
    gdf.to_file(output_path, driver="ESRI Shapefile", encoding="utf-8")
    
    logger.info(f"Shapefile exportado correctamente: {output_path}")
    
    if skipped_routes:
        logger.info(f"Rutas omitidas ({len(skipped_routes)}): {', '.join(skipped_routes[:5])}" +
                   (f" y {len(skipped_routes)-5} más..." if len(skipped_routes) > 5 else ""))
    
    return output_path

def create_shapefile_zip(shapefile_path: str, output_zip_path: str) -> str:
    """
    Crea un archivo ZIP con todos los archivos del shapefile.
    
    Args:
        shapefile_path: Ruta al archivo .shp principal
        output_zip_path: Ruta del archivo ZIP de salida
        
    Returns:
        Ruta del archivo ZIP creado
    """
    import zipfile
    
    # Obtener directorio y nombre base del shapefile
    shp_dir = os.path.dirname(shapefile_path)
    base_name = os.path.splitext(os.path.basename(shapefile_path))[0]
    
    # Extensiones de archivos shapefile
    shp_extensions = ['.shp', '.shx', '.dbf', '.prj', '.cpg']
    
    logger.info(f"Creando archivo ZIP: {output_zip_path}")
    
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        files_added = 0
        
        for ext in shp_extensions:
            file_path = os.path.join(shp_dir, f"{base_name}{ext}")
            if os.path.exists(file_path):
                # Agregar archivo al ZIP con solo el nombre (sin ruta completa)
                arcname = f"{base_name}{ext}"
                zipf.write(file_path, arcname)
                files_added += 1
                logger.debug(f"Agregado al ZIP: {arcname}")
    
    logger.info(f"Archivo ZIP creado con {files_added} archivos: {output_zip_path}")
    return output_zip_path