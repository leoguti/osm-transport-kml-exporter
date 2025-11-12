"""Procesador de archivos OSM para extraer rutas de transporte público."""

import osmium
import logging
from typing import Dict, List, Tuple
from shapely.geometry import LineString

logger = logging.getLogger(__name__)


class PTHandler(osmium.SimpleHandler):
    """Handler para extraer relaciones de transporte público de archivos OSM."""
    
    TRANSPORT_TYPES = ["bus", "trolleybus", "tram", "train", "subway", "light_rail"]
    
    def __init__(self):
        super(PTHandler, self).__init__()
        self.routes: Dict[int, Dict] = {}
    
    def relation(self, r):
        """Procesa relaciones OSM y extrae las de transporte público."""
        route_type = r.tags.get("route")
        
        if r.tags.get("type") == "route" and route_type in self.TRANSPORT_TYPES:
            route_id = r.id
            route_name = r.tags.get("name", f"route_{route_id}")
            route_ref = r.tags.get("ref", "")
            
            members = []
            for m in r.members:
                if m.type == "w":  # Solo ways (vías)
                    members.append(m.ref)
            
            self.routes[route_id] = {
                "name": route_name,
                "ref": route_ref,
                "type": route_type,
                "ways": members
            }
            
            logger.debug(f"Ruta encontrada: {route_name} ({route_type}) con {len(members)} ways")


def process_osm_file(input_path: str) -> Dict[int, Dict]:
    """
    Procesa un archivo OSM y extrae todas las rutas de transporte público con sus geometrías.
    
    Args:
        input_path: Ruta al archivo OSM
        
    Returns:
        Diccionario con información de rutas y geometrías:
        {
            route_id: {
                "name": str,
                "ref": str,
                "type": str,
                "ways": List[int],
                "geometries": List[LineString]
            }
        }
    """
    logger.info(f"Procesando archivo OSM: {input_path}")
    
    # Paso 1: Extraer relaciones de transporte público
    handler = PTHandler()
    handler.apply_file(input_path)
    
    logger.info(f"Se encontraron {len(handler.routes)} rutas de transporte público")
    
    # Paso 2: Recolectar nodos
    node_store: Dict[int, Tuple[float, float]] = {}
    
    class NodeCollector(osmium.SimpleHandler):
        def node(self, n):
            try:
                node_store[n.id] = (n.location.lon, n.location.lat)
            except osmium.InvalidLocationError:
                logger.warning(f"Nodo {n.id} tiene ubicación inválida")
    
    NodeCollector().apply_file(input_path)
    logger.info(f"Se recolectaron {len(node_store)} nodos")
    
    # Paso 3: Construir geometrías de ways
    way_geoms: Dict[int, LineString] = {}
    
    class WayCollector(osmium.SimpleHandler):
        def way(self, w):
            coords = []
            missing_nodes = 0
            
            for n in w.nodes:
                if n.ref in node_store:
                    coords.append(node_store[n.ref])
                else:
                    missing_nodes += 1
            
            if coords and len(coords) >= 2:
                way_geoms[w.id] = LineString(coords)
            elif missing_nodes > 0:
                logger.warning(f"Way {w.id} tiene {missing_nodes} nodos faltantes")
    
    WayCollector().apply_file(input_path)
    logger.info(f"Se procesaron {len(way_geoms)} ways con geometría")
    
    # Paso 4: Asignar geometrías a rutas
    routes_with_geometry = {}
    
    for route_id, route_data in handler.routes.items():
        geometries = []
        missing_ways = 0
        
        for way_id in route_data["ways"]:
            if way_id in way_geoms:
                geometries.append(way_geoms[way_id])
            else:
                missing_ways += 1
        
        if geometries:
            routes_with_geometry[route_id] = {
                **route_data,
                "geometries": geometries
            }
            
            if missing_ways > 0:
                logger.warning(
                    f"Ruta '{route_data['name']}' ({route_id}): "
                    f"{missing_ways} ways no tienen geometría"
                )
        else:
            logger.warning(
                f"Ruta '{route_data['name']}' ({route_id}) "
                f"no tiene geometrías válidas y será omitida"
            )
    
    logger.info(f"Se procesaron {len(routes_with_geometry)} rutas con geometría válida")
    
    return routes_with_geometry
